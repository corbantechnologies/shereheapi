from django.urls import path

from company.views import CompanyListCreateView, CompanyDetailView

app_name = "company"

urlpatterns = [
    path("", CompanyListCreateView.as_view(), name="company-list-create"),
    path("<str:reference>", CompanyDetailView.as_view(), name="company-detail"),
]
