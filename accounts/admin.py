from django.contrib import admin

from django.contrib.auth import get_user_model

User = get_user_model()


class UserAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "first_name",
        "last_name",
        "username",
        "is_event_manager",
        "is_staff",
        "is_active",
    )
    search_fields = ("email", "first_name", "last_name", "username")
    list_filter = ("is_staff", "is_active", "is_event_manager")
    ordering = ("-created_at",)


admin.site.register(User, UserAdmin)
