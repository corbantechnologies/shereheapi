from django.db import models
from django.contrib.auth import get_user_model
from cloudinary.models import CloudinaryField
from django.core.validators import MinValueValidator
from django.utils.text import slugify

from accounts.abstracts import UniversalIdModel, TimeStampedModel, ReferenceModel

User = get_user_model()


class Event(UniversalIdModel, TimeStampedModel, ReferenceModel):
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="events"
    )
    name = models.CharField(max_length=255)
    description = models.TextField()
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
    is_closed = models.BooleanField(default=False, help_text="Is the event closed?")
    identity = models.CharField(max_length=2000, unique=True, blank=True)
    cancellation_policy = models.TextField(
        blank=True, null=True, help_text="Cancellation policy for the event"
    )

    class Meta:
        verbose_name = "Event"
        verbose_name_plural = "Events"
        ordering = ["start_date"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.identity:
            base_identity = slugify(self.name)
            identity = base_identity
            counter = 1
            while Event.objects.filter(identity=identity).exists():
                identity = f"{base_identity}-{counter}"
                counter += 1
            self.identity = identity
        super().save(*args, **kwargs)
