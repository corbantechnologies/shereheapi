import string
import resend
import logging
import secrets
from datetime import datetime
from django.template.loader import render_to_string
from django.conf import settings

logger = logging.getLogger(__name__)

current_year = datetime.now().year


def generate_booking_code():
    year = current_year % 100
    return f"SPB{year}{secrets.token_hex(6).upper()}"


def send_booking_confirmation_email(email, booking):
    try:
        email_body = render_to_string(
            "booking_confirmation.html",
            {
                "booking": booking,
                "site_url": settings.SITE_URL,
                "support_email": settings.SUPPORT_EMAIL,
                "support_phone": settings.SUPPORT_PHONE,
                "current_year": current_year,
            },
        )
        params = {
            "from": "Sherehe Tickets Kenya <noreply@sherehe.co.ke>",
            "to": [email],
            "subject": "Your Sherehe Booking Has Been Confirmed",
            "html": email_body,
        }
        response = resend.Emails.send(params)
        logger.info(f"Email sent to {email}: {response}")
        return response
    except Exception as e:
        logger.error(f"Failed to send booking confirmation email: {str(e)}")
        return None
