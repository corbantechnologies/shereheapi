from rest_framework.routers import DefaultRouter
from coupons.views import CouponViewSet

app_name = "coupons"

router = DefaultRouter()
router.register("", CouponViewSet, basename="coupons")

urlpatterns = router.urls
