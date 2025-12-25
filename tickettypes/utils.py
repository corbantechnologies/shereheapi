import string
import resend
import logging
import secrets
from datetime import datetime
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

current_year = datetime.now().year


def generate_ticket_type_code():
    year = datetime.now().year % 100
    characters = string.ascii_uppercase + string.digits
    random_characters = "".join(secrets.choice(characters) for _ in range(8))
    return f"SPETT-{year}-{random_characters}"
