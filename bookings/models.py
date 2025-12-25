from django.db import models
from django.core.validators import MinValueValidator


from bookings.utils import generate_booking_code
from accounts.abstracts import UniversalIdModel, TimeStampedModel, ReferenceModel
from tickettypes.models import TicketType


class Booking(UniversalIdModel, TimeStampedModel, ReferenceModel):
    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("CONFIRMED", "Confirmed"),
        ("CANCELLED", "Cancelled"),
    )
    PAYMENT_STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
        ("REVERSED", "Reversed"),
    )

    ticket_type = models.ForeignKey(
        TicketType, on_delete=models.CASCADE, related_name="bookings"
    )
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=25)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)], default=1)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    booking_code = models.CharField(
        max_length=100, unique=True, default=generate_booking_code, editable=False
    )
    # event
    event = models.CharField(max_length=2550, blank=True, null=True)
    # payment
    checkout_request_id = models.CharField(max_length=2550, blank=True, null=True)
    callback_url = models.CharField(max_length=255, blank=True, null=True)
    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default="PENDING"
    )
    payment_status_description = models.CharField(max_length=100, blank=True, null=True)
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    confirmation_code = models.CharField(max_length=100, blank=True, null=True)
    payment_account = models.CharField(max_length=100, blank=True, null=True)
    currency = models.CharField(max_length=10, default="KES")
    payment_date = models.DateTimeField(blank=True, null=True)
    mpesa_receipt_number = models.CharField(max_length=2550, blank=True, null=True)
    mpesa_phone_number = models.CharField(max_length=255, blank=True, null=True)
    # Redirect URL
    redirect_url = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = "Booking"
        verbose_name_plural = "Bookings"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        self.amount = self.ticket_type.price * self.quantity
        self.description = f"Booking for {self.quantity} tickets of {self.ticket_type.name} by {self.name} ({self.phone})"
        self.event = self.ticket_type.event.name
        super().save(*args, **kwargs)
