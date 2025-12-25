import qrcode
import cloudinary
from django.db import models
from cloudinary.models import CloudinaryField
from django.conf import settings
from io import BytesIO

from accounts.abstracts import UniversalIdModel, TimeStampedModel, ReferenceModel
from bookings.models import Booking
from tickets.utils import generate_ticket_code


class Ticket(UniversalIdModel, TimeStampedModel, ReferenceModel):
    booking = models.ForeignKey(
        Booking, on_delete=models.CASCADE, related_name="tickets"
    )
    ticket_type = models.CharField(max_length=1000, blank=True, null=True)
    ticket_code = models.CharField(
        max_length=100, unique=True, default=generate_ticket_code, editable=False
    )
    qr_code = CloudinaryField("tickets_qr_code", blank=True, null=True)
    is_used = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"Ticket {self.ticket_code} for {self.booking.name} type {self.ticket_type}"
        )

    def save(self, *args, **kwargs):
        if not self.ticket_type:
            self.ticket_type = (
                f"{self.booking.ticket_type.name} - {self.booking.ticket_type.price}"
            )

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
            self.qr_code = upload_result["url"]

        super().save(*args, **kwargs)
