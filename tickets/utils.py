import string
import resend
import logging
import secrets
from datetime import datetime
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

current_year = datetime.now().year


def generate_ticket_code():
    year = current_year % 100
    return f"ST{year}{secrets.token_hex(6).upper()}"
