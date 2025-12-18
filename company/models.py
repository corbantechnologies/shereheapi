from django.db import models
from django.contrib.auth import get_user_model
from cloudinary.models import CloudinaryField

from accounts.abstracts import UniversalIdModel, TimeStampedModel, ReferenceModel
from company.utils import generate_company_code

User = get_user_model()


class Company(UniversalIdModel, TimeStampedModel, ReferenceModel):
    """
    Event managers have to set up the companies.
    These are placeholders to be used when setting up events instead of the personal data.
    Each has one created by default upon registration.
    The manager can create multiple companies upon premium subscription.
    """

    # Manager
    manager = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="companies",
        help_text="The owner and manager of the company",
    )

    # Outlook Details
    name = models.CharField(
        max_length=255, help_text="Name of the company", unique=True
    )
    description = models.TextField(
        blank=True, null=True, help_text="Description of the company"
    )
    logo = CloudinaryField(
        "company_logo", help_text="Logo of the company", blank=True, null=True
    )
    banner = CloudinaryField(
        "company_banner", help_text="Banner of the company", blank=True, null=True
    )

    # Address
    country = models.CharField(
        max_length=255, blank=True, null=True, help_text="Country of the company"
    )
    city = models.CharField(
        max_length=255, blank=True, null=True, help_text="City of the company"
    )
    address = models.CharField(
        max_length=255, blank=True, null=True, help_text="Address of the company"
    )

    # Contact
    phone = models.CharField(
        max_length=255, blank=True, null=True, help_text="Phone number of the company"
    )
    email = models.EmailField(blank=True, null=True, help_text="Email of the company")
    website = models.URLField(blank=True, null=True, help_text="Website of the company")

    # Company Code
    company_code = models.CharField(
        max_length=100,
        unique=True,
        default=generate_company_code,
        editable=False,
        help_text="Unique code for the company",
    )

    class Meta:
        verbose_name = "Company"
        verbose_name_plural = "Companies"
        ordering = ["name"]

    def __str__(self):
        return self.name
