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
    ticket_type_code = models.CharField(
        max_length=255, unique=True, default=generate_ticket_type_code, editable=False
    )

    class Meta:
        verbose_name = "Ticket Type"
        verbose_name_plural = "Ticket Types"
        ordering = ["event", "-price"]

    def __str__(self):
        return self.name
