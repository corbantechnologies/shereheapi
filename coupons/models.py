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
        max_length=20, choices=DISCOUNT_TYPE_CHOICES, default="PERCENTAGE"
    )
    discount_value = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Cannot be negative, Cannot be blank"
    )
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(default=0, help_text="0 means unlimited")
    usage_count = models.PositiveIntegerField(default=0)
    tickets_sold = models.PositiveIntegerField(
        default=0,
        help_text="Total number of tickets successfully purchased using this coupon",
    )
    is_active = models.BooleanField(default=True)
    # Adding Email incase we are emailing it to someone specific
    email = models.EmailField(blank=True, null=True)

    class Meta:
        verbose_name = "Coupon"
        verbose_name_plural = "Coupons"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.code} - {self.discount_type} {self.discount_value} {self.event.name}"

    def apply_discount(self, ticket_type):
        if self.discount_type == "FIXED":
            return ticket_type.price - self.discount_value
        elif self.discount_type == "PERCENTAGE":
            return ticket_type.price - (ticket_type.price * self.discount_value / 100)
        return ticket_type.price
