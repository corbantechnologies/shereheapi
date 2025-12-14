from django.contrib import admin

from company.models import Company


class CompanyAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "manager",
        "company_code",
        "created_at",
        "updated_at",
        "reference",
    )
    search_fields = ("name", "manager__username", "reference")
    list_filter = ("manager", "reference")
    ordering = ("-created_at",)


admin.site.register(Company, CompanyAdmin)
