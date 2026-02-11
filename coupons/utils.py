import string
import secrets
from datetime import datetime

current_year = datetime.now().year


def generate_code():
    characters = string.digits + string.ascii_uppercase
    year = current_year % 100
    random_string = "".join(secrets.choice(characters) for _ in range(8))
    code = f"{year}{random_string}"
    return code


