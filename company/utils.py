import string
import secrets
from datetime import datetime


def generate_company_code():
    year = datetime.now().year % 100
    characters = string.ascii_uppercase + string.digits
    random_characters = "".join(secrets.choice(characters) for _ in range(8))
    return f"SPC-{year}{random_characters}"


# print(generate_company_code())
