import re
import logging
import requests
import resend
from django.conf import settings
from bookings.utils import send_booking_confirmation_email

logger = logging.getLogger(__name__)


def normalize_phone_e164(phone: str) -> str:
    """Normalizes phone to 254XXXXXXXXX format."""
    if not phone:
        return ""
    digits = re.sub(r"\D", "", str(phone))
    if digits.startswith("0") and len(digits) == 10:
        return "254" + digits[1:]
    if digits.startswith("7") and len(digits) == 9:
        return "254" + digits
    if digits.startswith("1") and len(digits) == 9:
        return "254" + digits
    if digits.startswith("254") and len(digits) == 12:
        return digits
    if digits.startswith("+254"):
        return digits[1:]
    return digits


def dispatch_ticket_confirmation(booking):
    """
    Multi-channel ticket delivery pipeline:
    1. Primary: Meta WhatsApp Cloud API (via LJK Marketing Gateway).
    2. Fallback 1: SMS (via LJK Marketing Gateway) if WhatsApp fails.
    3. Fallback 2: Email via Resend if both WhatsApp and SMS fail (or as backup if email provided).
    """
    phone = normalize_phone_e164(booking.phone or booking.mpesa_phone_number)
    event = getattr(booking.ticket_type, "event", None)
    event_name = event.name if event else (booking.event or "Sherehe Event")
    event_code = event.event_code if event else "events"
    ticket_tier = booking.ticket_type.name if booking.ticket_type else "Regular"
    ticket_pass_url = f"{settings.SITE_URL}/events/{event_code}/{booking.reference}/tickets"
    date_str = str(event.start_date) if event and event.start_date else "See Ticket"
    venue_str = event.venue if event and event.venue else "Venue on Pass"

    wa_success = False
    sms_success = False

    headers = {
        "Content-Type": "application/json",
    }
    api_key = getattr(settings, "MARKETING_AGENCY_API_KEY", "")
    if api_key:
        headers["X-API-Key"] = api_key
        headers["Authorization"] = f"Bearer {api_key}"

    dispatch_url = f"{settings.MARKETING_AGENCY_API_URL}/api/v1/integrations/dispatch/single/"

    # --- STEP 1: ATTEMPT WHATSAPP ---
    if phone:
        wa_message = (
            f"🎉 Jambo {booking.name}! Your {ticket_tier} ticket for {event_name} is confirmed! 🎟️\n\n"
            f"View & Scan your Entry Pass QR: {ticket_pass_url}\n\n"
            f"📍 Venue: {venue_str}\n"
            f"📅 Date: {date_str}\n\n"
            f"Present this QR pass at the entrance scanner station for instant admission.\n"
            f"Powered by Sherehe Tickets Kenya."
        )

        wa_payload = {
            "channel": "WHATSAPP",
            "recipient": phone,
            "message": wa_message,
            "reference_id": f"TKT-WA-{booking.reference}",
        }

        try:
            logger.info(f"[DISPATCH] Attempting WhatsApp delivery to {phone} for booking {booking.reference}")
            resp = requests.post(dispatch_url, json=wa_payload, headers=headers, timeout=5)
            if resp.status_code in [200, 201] and resp.json().get("success") is not False:
                wa_success = True
                logger.info(f"[DISPATCH SUCCESS] Ticket sent via WhatsApp to {phone} for booking {booking.reference}")
            else:
                logger.warning(f"[DISPATCH WHATSAPP FAILED] Status {resp.status_code}: {resp.text}")
        except Exception as wa_err:
            logger.warning(f"[DISPATCH WHATSAPP EXCEPTION] {str(wa_err)}")

    # --- STEP 2: FALLBACK TO SMS IF WHATSAPP FAILED ---
    if not wa_success and phone:
        sms_message = (
            f"Habari {booking.name}! Your {ticket_tier} ticket for {event_name} is confirmed! "
            f"View your QR pass: {ticket_pass_url} . Sherehe Tickets"
        )
        sms_payload = {
            "channel": "SMS",
            "recipient": phone,
            "message": sms_message,
            "reference_id": f"TKT-SMS-{booking.reference}",
        }

        try:
            logger.info(f"[DISPATCH FALLBACK 1] Attempting SMS delivery to {phone} for booking {booking.reference}")
            resp = requests.post(dispatch_url, json=sms_payload, headers=headers, timeout=5)
            if resp.status_code in [200, 201] and resp.json().get("success") is not False:
                sms_success = True
                logger.info(f"[DISPATCH SUCCESS] Ticket sent via SMS to {phone} for booking {booking.reference}")
            else:
                logger.warning(f"[DISPATCH SMS FAILED] Status {resp.status_code}: {resp.text}")
        except Exception as sms_err:
            logger.warning(f"[DISPATCH SMS EXCEPTION] {str(sms_err)}")

    # --- STEP 3: FALLBACK TO EMAIL VIA RESEND IF BOTH FAIL (OR AS SAFE REPOSITORY) ---
    email_target = booking.email
    if not wa_success and not sms_success:
        logger.error(
            f"[DISPATCH FALLBACK 2] Both WhatsApp and SMS failed for booking {booking.reference}. "
            f"Failing over to Resend email to '{email_target}'!"
        )
        if email_target:
            send_booking_confirmation_email(email_target, booking)
        else:
            logger.error(f"[DISPATCH FAILED] No email provided on booking {booking.reference} for Resend fallback.")
    else:
        # If WhatsApp or SMS succeeded and email was provided, also send email confirmation
        if email_target:
            try:
                send_booking_confirmation_email(email_target, booking)
            except Exception as e:
                logger.warning(f"[COMPLEMENTARY EMAIL FAILED] {str(e)}")

    return {
        "whatsapp": wa_success,
        "sms": sms_success,
        "email_fallback": not wa_success and not sms_success,
    }
