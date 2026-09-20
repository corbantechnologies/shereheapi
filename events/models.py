from django.db import models
from django.contrib.auth import get_user_model
from cloudinary.models import CloudinaryField
from django.core.validators import MinValueValidator
from django.utils.text import slugify

from accounts.abstracts import UniversalIdModel, TimeStampedModel, ReferenceModel
from company.models import Company
from events.utils import generate_event_code

User = get_user_model()


class Event(UniversalIdModel, TimeStampedModel, ReferenceModel):
    manager = models.ForeignKey(User, on_delete=models.CASCADE, related_name="events")
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="company_events"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(
        blank=True, null=True, help_text="Short description of the event"
    )
    content = models.JSONField(
        blank=True, null=True, help_text="Long description of the event"
    )
    start_date = models.DateField()
    start_time = models.TimeField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    venue = models.CharField(max_length=2000)
    capacity = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text="Leave blank for unlimited capacity",
    )
    image = CloudinaryField(
        "event_image", help_text="Image of the event", blank=True, null=True
    )
    is_published = models.BooleanField(
        default=False, help_text="Is the event published?"
    )
    is_closed = models.BooleanField(default=False, help_text="Is the event closed?")
    identity = models.CharField(max_length=2000, unique=True, blank=True)
    event_code = models.CharField(
        max_length=2000, unique=True, default=generate_event_code, editable=False
    )
    refund_policy = models.JSONField(
        blank=True, null=True, help_text="Refund policy of the event"
    )
    category = models.CharField(
        max_length=100,
        default="Music & Concerts",
        blank=True,
        help_text="Event Category (e.g. Music & Concerts, Festivals, Tech & Business)",
    )
    gate_passcode = models.CharField(
        max_length=12,
        blank=True,
        null=True,
        help_text="PIN for gate staff to scan tickets without login",
    )
    platform_fee_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=3.50,
        help_text="Platform commission fee percentage (default 3.5%)",
    )

    class Meta:
        verbose_name = "Event"
        verbose_name_plural = "Events"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        import secrets
        if not self.identity:
            base_identity = slugify(self.name)
            identity = base_identity
            counter = 1
            while Event.objects.filter(identity=identity).exists():
                identity = f"{base_identity}-{counter}"
                counter += 1
            self.identity = identity

        if not self.gate_passcode:
            self.gate_passcode = f"SH-{secrets.randbelow(90000) + 10000}"

        super().save(*args, **kwargs)


class PayoutRequest(UniversalIdModel, TimeStampedModel, ReferenceModel):
    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("DISBURSED", "Disbursed"),
        ("REJECTED", "Rejected"),
    )

    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="payout_requests"
    )
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="payout_requests"
    )
    requested_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="requested_payouts"
    )
    amount_requested = models.DecimalField(max_digits=12, decimal_places=2)
    platform_fee_deducted = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    net_payout_amount = models.DecimalField(max_digits=12, decimal_places=2)
    payout_phone = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    mpesa_transaction_id = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    disbursed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "Payout Request"
        verbose_name_plural = "Payout Requests"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.event.name} - KES {self.net_payout_amount} ({self.status})"

