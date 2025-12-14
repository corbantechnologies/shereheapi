from rest_framework import generics
from rest_framework.permissions import AllowAny

from company.models import Company
from company.serializers import CompanySerializer
from company.permissions import IsEventManagerOwnerOrReadOnly


class CompanyListCreateView(generics.ListCreateAPIView):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [
        IsEventManagerOwnerOrReadOnly,
    ]

    def perform_create(self, serializer):
        serializer.save(manager=self.request.user)


class CompanyDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [
        IsEventManagerOwnerOrReadOnly,
    ]
    lookup_field = "reference"
