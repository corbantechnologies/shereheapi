import string
import resend
import logging
import secrets
from datetime import datetime
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

current_year = datetime.now().year


def generate_booking_code():
    year = current_year % 100
    return f"SPB{year}{secrets.token_hex(6).upper()}"


def send_booking_confirmation_email(client, booking):
    subject = "Booking Confirmation"
    template_name = "booking_confirmation.html"
    context = {
        "client": client,
        "booking": booking,
        "current_year": current_year,
    }
    html_content = render_to_string(template_name, context)
    try:
        resend.Emails.send(
            to=[client.email],
            subject=subject,
            html_content=html_content,
        )
    except Exception as e:
        logger.error(f"Failed to send booking confirmation email: {str(e)}")
