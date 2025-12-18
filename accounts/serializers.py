from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.validators import UniqueValidator
import secrets
import string
from django.utils import timezone
from accounts.utils import (
    send_password_reset_email,
    send_event_manager_account_created_email,
)

from accounts.validators import (
    validate_password_digit,
    validate_password_lowercase,
    validate_password_symbol,
    validate_password_uppercase,
)
from company.models import Company

User = get_user_model()


class BaseUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())],
    )
    password = serializers.CharField(
        max_length=128,
        min_length=5,
        write_only=True,
        validators=[
            validate_password_digit,
            validate_password_uppercase,
            validate_password_symbol,
            validate_password_lowercase,
        ],
    )
    avatar = serializers.ImageField(required=False, use_url=True)

    class Meta:
        model = User
        fields = [
            "email",
            "password",
            "first_name",
            "last_name",
            "username",
            "avatar",
            "phone_number",
            "country",
            "is_event_manager",
            "is_staff",
            "is_active",
            "is_superuser",
        ]

    def create_user(self, validated_data, role_field):
        user = User.objects.create_user(**validated_data)
        setattr(user, role_field, True)
        user.is_active = True
        user.save()
        return user


# Accounts
class EventManagerSerializer(BaseUserSerializer):
    def create(self, validated_data):
        user = self.create_user(validated_data, "is_event_manager")
        send_event_manager_account_created_email(user)

        Company.objects.create(manager=user, name=f"{user.username}'s Company")
        return user


# Password Reset


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value

    def save(self):
        email = self.validated_data["email"]
        user = User.objects.get(email=email)

        # Generate 6-digit code
        alphabet = string.digits
        code = "".join(secrets.choice(alphabet) for _ in range(6))

        user.password_reset_code = code
        user.password_reset_code_created_at = timezone.now()
        user.save()

        send_password_reset_email(user, code)


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    password = serializers.CharField(
        max_length=128,
        min_length=5,
        write_only=True,
        validators=[
            validate_password_digit,
            validate_password_uppercase,
            validate_password_symbol,
            validate_password_lowercase,
        ],
    )

    def validate(self, attrs):
        email = attrs.get("email")
        code = attrs.get("code")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"email": "User with this email does not exist."}
            )

        if user.password_reset_code != code:
            raise serializers.ValidationError({"code": "Invalid reset code."})

        # Check expiration (15 minutes)
        if user.password_reset_code_created_at:
            created_at = user.password_reset_code_created_at
            if timezone.now() > created_at + timezone.timedelta(minutes=15):
                raise serializers.ValidationError({"code": "Reset code has expired."})
        else:
            raise serializers.ValidationError({"code": "Invalid reset code."})

        attrs["user"] = user
        return attrs

    def save(self):
        user = self.validated_data["user"]
        password = self.validated_data["password"]

        user.set_password(password)
        user.password_reset_code = None
        user.password_reset_code_created_at = None
        user.save()
        return user
