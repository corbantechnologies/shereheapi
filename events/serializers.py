from rest_framework import serializers
from django.contrib.auth import get_user_model

from events.models import Event

User = get_user_model()


class EventSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(source="created_by.username", read_only=True)
    image = serializers.ImageField(use_url=True, required=False, allow_null=True)
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=False, allow_null=True)
    start_time = serializers.TimeField(required=False, allow_null=True)
    end_time = serializers.TimeField(required=False, allow_null=True)
