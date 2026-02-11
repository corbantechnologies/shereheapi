from django.contrib import admin

from coupons.models import Coupon


class CouponAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "discount_value",
        "discount_type",
        "valid_from",
        "valid_to",
        "usage_limit",
        "usage_count",
        "is_active",
    )


admin.site.register(Coupon)
