from django.urls import path

from coupons.views import (
    CouponListCreateView,
    CouponRetrieveUpdateDestroyView,
    CouponValidateView,
)

app_name = "coupons"

urlpatterns = [
    path("", CouponListCreateView.as_view(), name="coupon-list-create"),
    path("validate/", CouponValidateView.as_view(), name="coupon-validate"),
    path(
        "<str:reference>/",
        CouponRetrieveUpdateDestroyView.as_view(),
        name="coupon-retrieve-update-destroy",
    ),
]
