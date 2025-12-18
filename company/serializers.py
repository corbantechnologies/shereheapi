from rest_framework import serializers

from company.models import Company
from company.utils import send_company_created_email


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

    def create(self, validated_data):
        company = super().create(validated_data)
        send_company_created_email(company.manager, company)
        return company
