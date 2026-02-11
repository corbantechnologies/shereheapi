from django.urls import path

from coupons.views import CouponListCreateView, CouponRetrieveUpdateDestroyView

app_name = "coupons"

urlpatterns = [
    path("", CouponListCreateView.as_view(), name="coupon-list-create"),
    path(
        "<str:reference>",
        CouponRetrieveUpdateDestroyView.as_view(),
        name="coupon-retrieve-update-destroy",
    ),
]
