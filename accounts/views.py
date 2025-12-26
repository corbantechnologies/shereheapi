from rest_framework import generics
from django.contrib.auth import get_user_model, authenticate
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from accounts.serializers import (
    BaseUserSerializer,
    EventManagerSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer,
)

User = get_user_model()

"""
Login View
"""


class TokenView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = BaseUserSerializer

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        user = authenticate(email=email, password=password)
        if user:
            if user.is_active:
                token, created = Token.objects.get_or_create(user=user)
                user_details = {
                    "id": user.id,
                    "reference": user.reference,
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "avatar": user.avatar,
                    "phone_number": user.phone_number,
                    "country": user.country,
                    "is_event_manager": user.is_event_manager,
                    "is_staff": user.is_staff,
                    "is_active": user.is_active,
                    "is_superuser": user.is_superuser,
                    "token": token.key,
                }
                return Response(user_details, status=status.HTTP_200_OK)

            else:
                return Response(
                    {"error": "User is not active"}, status=status.HTTP_401_UNAUTHORIZED
                )
        return Response(
            {"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
        )


"""
Logout View
"""


class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        request.auth.delete()
        return Response(status=status.HTTP_200_OK)


"""
Account Views
"""


class EventManagerCreateView(generics.CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = EventManagerSerializer
    queryset = User.objects.all()


class EventManagerListView(generics.ListAPIView):
    permission_classes = (AllowAny,)
    serializer_class = EventManagerSerializer
    queryset = User.objects.filter(is_event_manager=True)


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = BaseUserSerializer
    queryset = User.objects.all()
    lookup_field = "username"

    def get_queryset(self):
        return self.queryset.filter(
            username=self.request.user.username
        ).prefetch_related("companies")


"""
Password Reset Views
"""


class PasswordResetRequestView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = PasswordResetSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Password reset email sent."}, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Password has been reset successfully."},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
