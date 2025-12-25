from django.db import models

from accounts.abstracts import UniversalIdModel, TimeStampedModel, ReferenceModel


class Lead(UniversalIdModel, TimeStampedModel, ReferenceModel):
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=255)
    message = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Lead"
        verbose_name_plural = "Leads"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.name} - {self.email}"
