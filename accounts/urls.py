from django.urls import path

from accounts.views import (
    TokenView,
    LogoutView,
    EventManagerCreateView,
    EventManagerListView,
    UserDetailView,
)

app_name = "accounts"

urlpatterns = [
    path("token/", TokenView.as_view(), name="token"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path(
        "signup/event-manager/",
        EventManagerCreateView.as_view(),
        name="event-manager",
    ),
    path(
        "event-manager/list/", EventManagerListView.as_view(), name="event-manager-list"
    ),
    path("<str:username>/", UserDetailView.as_view(), name="user-detail"),
]
