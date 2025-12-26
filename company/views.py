from rest_framework import generics

from company.models import Company
from company.serializers import CompanySerializer
from company.permissions import IsEventManagerOwnerOrReadOnly
from company.mixins import EventManagerOwnedFilterMixin


class CompanyListCreateView(EventManagerOwnedFilterMixin, generics.ListCreateAPIView):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [
        IsEventManagerOwnerOrReadOnly,
    ]

    def perform_create(self, serializer):
        serializer.save(manager=self.request.user)


class CompanyDetailView(
    EventManagerOwnedFilterMixin, generics.RetrieveUpdateDestroyAPIView
):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [
        IsEventManagerOwnerOrReadOnly,
    ]
    lookup_field = "reference"
