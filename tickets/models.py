import qrcode
import cloudinary
from django.db import models
from cloudinary.models import CloudinaryField
from django.conf import settings
from io import BytesIO

from accounts.abstracts import UniversalIdModel, TimeStampedModel, ReferenceModel
from bookings.models import Booking
from tickettypes.models import TicketType
from tickets.utils import generate_ticket_code


class Ticket(UniversalIdModel, TimeStampedModel, ReferenceModel):
    booking = models.ForeignKey(
        Booking, on_delete=models.CASCADE, related_name="tickets"
    )
    ticket_type = models.ForeignKey(
        TicketType,
        on_delete=models.CASCADE,
        related_name="ticket_types",
        blank=True,
        null=True,
    )
    ticket_code = models.CharField(
        max_length=100, unique=True, default=generate_ticket_code, editable=False
    )
    qr_code = CloudinaryField("tickets_qr_code", blank=True, null=True)
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    scanned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="scanned_tickets",
    )
    gate_station = models.CharField(max_length=100, default="Main Gate", blank=True)

    class Meta:
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"Ticket {self.ticket_code} for {self.booking.name} type {self.ticket_type}"
        )

    def save(self, *args, **kwargs):

        if not self.qr_code:
            qr = qrcode.QRCode(
                version=1,
                box_size=10,
                border=4,
            )
            frontend_url = f"{settings.SITE_URL}/tickets/{self.reference}/"
            qr.add_data(frontend_url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")

            # save QR Code to Cloudinary
            buffer = BytesIO()
            img.save(buffer, "PNG")
            buffer.seek(0)

            upload_result = cloudinary.uploader.upload(
                buffer,
                folder="tickets_qr_codes",
                public_id=f"{self.reference}_qr_code",
                resource_type="image",
                format="png",
            )
            self.qr_code = upload_result["secure_url"]

        super().save(*args, **kwargs)


class TicketScanLog(UniversalIdModel, TimeStampedModel):
    STATUS_CHOICES = (
        ("VALID", "Valid Entry"),
        ("ALREADY_USED", "Already Used"),
        ("INVALID_EVENT", "Invalid Event"),
        ("NOT_FOUND", "Ticket Not Found"),
        ("UNPAID", "Unpaid Booking"),
    )
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="scan_logs",
    )
    event_code = models.CharField(max_length=255, blank=True, null=True)
    scanned_code = models.CharField(max_length=500)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    gate_station = models.CharField(max_length=100, default="Main Gate")
    scanned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ticket_scan_logs",
    )
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Ticket Scan Log"
        verbose_name_plural = "Ticket Scan Logs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.status} - {self.scanned_code} ({self.created_at})"

