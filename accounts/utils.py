import resend
import logging
import string
import secrets
from datetime import datetime
from django.template.loader import render_to_string

from django.conf import settings

logger = logging.getLogger(__name__)


def generate_reference():
    characters = string.ascii_letters + string.digits
    random_string = "".join(secrets.choice(characters) for _ in range(12))
    return random_string.upper()


def generate_username():
    year = datetime.now().year % 100
    random_number = "".join(secrets.choice(string.digits) for _ in range(8))
    return f"sherehe{year}{random_number}"


def send_event_manager_account_created_email(user):
    """
    Send an email to the event manager that their account is created
    Notify the event manager of the terms and conditions of the platform
    """
    current_year = datetime.now().year

    try:
        email_body = render_to_string(
            "event_manager_account_created.html",
            {
                "user": user,
                "current_year": current_year,
                "site_url": settings.SITE_URL,
            },
        )
        params = {
            "from": "Sherehe <noreply@sherehe.co.ke>",
            "to": [user.email],  # Resend expects a list for 'to'
            "subject": "Your Sherehe Account Has Been Created",
            "html": email_body,
        }
        response = resend.Emails.send(params)
        logger.info(f"Email sent to {user.email}: {response}")
        return response

    except Exception as e:
        logger.error(f"Failed to send email to {user.email}: {str(e)}")
        return None


def send_password_reset_email(user, code):
    """
    Send a password reset email to the user
    """
    current_year = datetime.now().year

    try:
        email_body = render_to_string(
            "password_reset.html",
            {
                "user": user,
                "code": code,
                "current_year": current_year,
                "site_url": settings.SITE_URL,
            },
        )
        params = {
            "from": "Sherehe <noreply@sherehe.co.ke>",
            "to": [user.email],
            "subject": "Password Reset",
            "html": email_body,
        }
        response = resend.Emails.send(params)
        logger.info(f"Password reset email sent to {user.email}")
        return response

    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")
        return None
