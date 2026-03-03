from django.db import models
from django.core.validators import MinValueValidator
from django.utils.text import slugify

from accounts.abstracts import UniversalIdModel, TimeStampedModel, ReferenceModel
from events.models import Event
from tickettypes.utils import generate_ticket_type_code


class TicketType(UniversalIdModel, TimeStampedModel, ReferenceModel):
    """
    Ticket Type Model
    """

    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="ticket_types"
    )
    name = models.CharField(max_length=255)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    quantity_available = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text="Leave blank for unlimited tickets or when is_limited is True to use event capacity",
    )
    is_limited = models.BooleanField(
        default=False,
        help_text="Indicates if ticket type is limited; if True and quantity_available is None, uses event capacity",
    )
    sales_start = models.DateField(
        null=True,
        blank=True,
        help_text="When ticket sales begin. Leave blank to start immediately.",
    )
    sales_end = models.DateField(
        null=True,
        blank=True,
        help_text="When ticket sales end. Leave blank to sell until event ends.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Uncheck to hide this ticket type or stop sales manually.",
    )
    ticket_type_code = models.CharField(
        max_length=255, unique=True, default=generate_ticket_type_code, editable=False
    )

    @property
    def tickets_sold(self):
        return sum(
            booking.quantity
            for booking in self.bookings.filter(payment_status__in=["COMPLETED"])
        )

    @property
    def is_currently_on_sale(self):
        from django.utils import timezone

        if not self.is_active:
            return False

        now_date = timezone.now().date()
        if self.sales_start and now_date < self.sales_start:
            return False
        if self.sales_end and now_date > self.sales_end:
            return False
        return True

    @property
    def status(self):
        if not self.is_active:
            return "PAUSED"

        if self.is_limited and self.quantity_available is not None:
            if self.tickets_sold >= self.quantity_available:
                return "SOLD_OUT"

        from django.utils import timezone

        now_date = timezone.now().date()

        if self.sales_start and now_date < self.sales_start:
            return "UPCOMING"

        if self.sales_end and now_date > self.sales_end:
            return "ENDED"

        return "ON_SALE"

    class Meta:
        verbose_name = "Ticket Type"
        verbose_name_plural = "Ticket Types"
        ordering = ["event", "-price"]

    def __str__(self):
        return self.name
