from rest_framework import serializers
from company.models import Company


class CompanySerializer(serializers.ModelSerializer):
    manager = serializers.CharField(source="manager.username", read_only=True)
    logo = serializers.ImageField(required=False, use_url=True)
    banner = serializers.ImageField(required=False, use_url=True)

    class Meta:
        model = Company
        fields = [
            "name",
            "manager",
            "company_code",
            "logo",
            "banner",
            "country",
            "city",
            "address",
            "phone",
            "email",
            "website",
            "created_at",
            "updated_at",
            "reference",
        ]
