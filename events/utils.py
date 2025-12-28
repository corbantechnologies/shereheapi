import string
import resend
import logging
import secrets
from datetime import datetime
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

current_year = datetime.now().year


def generate_event_code():
    year = datetime.now().year % 100
    characters = string.ascii_uppercase + string.digits
    random_characters = "".join(secrets.choice(characters) for _ in range(8))
    return f"SPE-{year}{random_characters}"


def send_event_created_email(user, event):
    """
    Send an email to the user that their event has been created
    Notify the user of the event code
    """
    try:
        email_body = render_to_string(
            "event_created.html",
            {
                "user": user,
                "event": event,
                "current_year": current_year,
            },
        )
        params = {
            "from": "Sherehe <noreply@sherehe.co.ke>",
            "to": [user.email],
            "subject": "Your Sherehe Event Has Been Created",
            "html": email_body,
        }
        response = resend.Emails.send(params)
        logger.info(f"Email sent to {user.email}: {response}")
        return response

    except Exception as e:
        logger.error(f"Failed to send email to {user.email}: {str(e)}")
        return None
