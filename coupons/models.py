from django.db import models
from django.contrib.auth import get_user_model

from accounts.abstracts import TimeStampedModel, ReferenceModel, UniversalIdModel
from tickettypes.models import TicketType
from events.models import Event
from coupons.utils import generate_code

User = get_user_model()


class Coupon(TimeStampedModel, ReferenceModel, UniversalIdModel):
    """
    Coupon model
    """

    DISCOUNT_TYPE_CHOICES = (
        ("FIXED", "Fixed"),
        ("PERCENTAGE", "Percentage"),
    )

    manager = models.ForeignKey(User, on_delete=models.CASCADE, related_name="coupons")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="coupons")
    ticket_type = models.ManyToManyField(
        TicketType,
        related_name="coupons",
        blank=True,
        help_text="If blank, coupon applies to all ticket types",
    )
    name = models.CharField(
        max_length=2550, blank=True, null=True, help_text="Optional"
    )
    code = models.CharField(
        max_length=10, unique=True, default=generate_code, editable=False
    )
    discount_type = models.CharField(
        max_length=20, choices=DISCOUNT_TYPE_CHOICES, default="FIXED"
    )
    discount_value = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Cannot be negative, Cannot be blank"
    )
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(default=0, help_text="0 means unlimited")
    usage_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Coupon"
        verbose_name_plural = "Coupons"
        ordering = ["-created_at"]

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        self.usage_count += 1
        super().save(*args, **kwargs)

    def apply_discount(self, ticket_type):
        if self.discount_type == "FIXED":
            return ticket_type.price - self.discount_value
        elif self.discount_type == "PERCENTAGE":
            return ticket_type.price - (ticket_type.price * self.discount_value / 100)
        return ticket_type.price
