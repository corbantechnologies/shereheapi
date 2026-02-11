from rest_framework import generics

from coupons.models import Coupon
from coupons.serializers import CouponSerializer
from company.permissions import IsEventManagerOwnerOrReadOnly


class CouponListCreateView(generics.ListCreateAPIView):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [IsEventManagerOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(manager=self.request.user)


class CouponRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [IsEventManagerOwnerOrReadOnly]
    lookup_field = "reference"
