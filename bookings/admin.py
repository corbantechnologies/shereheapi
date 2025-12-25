from django.contrib import admin

from bookings.models import Booking


class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "booking_code",
        "name",
        "email",
        "phone",
        "quantity",
        "amount",
        "status",
        "payment_status",
        "payment_method",
        "confirmation_code",
        "payment_account",
        "currency",
        "payment_date",
        "mpesa_receipt_number",
        "mpesa_phone_number",
    )


admin.site.register(Booking, BookingAdmin)
