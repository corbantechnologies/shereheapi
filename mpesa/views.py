import logging
import requests
import base64
import threading
from datetime import datetime
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.conf import settings

from mpesa.utils import get_access_token
from mpesa.models import MpesaBody
from mpesa.serializers import MpesaBodySerializer
from bookings.models import Booking
from bookings.utils import send_booking_confirmation_email
from tickets.models import Ticket

logger = logging.getLogger(__name__)


class MpesaPaymentCreateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            booking_code = request.data.get("booking_code")
            phone_number = request.data.get("phone_number")

            if not booking_code:
                logger.error("Booking code is required")
                return Response(
                    {"error": "Booking code is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not phone_number:
                logger.error("Phone number is required")
                return Response(
                    {"error": "Phone number is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            booking = Booking.objects.get(booking_code=booking_code)

            if booking.payment_status == "Completed":
                logger.error("Booking already paid")
                return Response(
                    {"error": "Booking already paid"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if booking.status != "PENDING" or booking.payment_status != "PENDING":
                logger.error("Booking is not in PENDING state")
                return Response(
                    {"error": "Booking is not in a valid state for payment"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validate M-Pesa credentials
            if not all(
                [
                    settings.MPESA_CONSUMER_KEY,
                    settings.MPESA_CONSUMER_SECRET,
                    settings.MPESA_SHORTCODE,
                    settings.MPESA_PASSKEY,
                ]
            ):
                logger.error("M-Pesa credentials not configured")
                return Response(
                    {"error": "M-Pesa credentials not configured"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get access token
            try:
                access_token = get_access_token(
                    access_token_url=f"{settings.MPESA_API_URL}/oauth/v1/generate?grant_type=client_credentials",
                    consumer_key=settings.MPESA_CONSUMER_KEY,
                    consumer_secret=settings.MPESA_CONSUMER_SECRET,
                )
            except ValueError as e:
                logger.error(f"M-Pesa authentication failed: {str(e)}")
                return Response(
                    {"error": f"Authentication failed: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # Prepare STK Push payload
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            password = base64.b64encode(
                f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}".encode()
            ).decode()

            payload = {
                "BusinessShortCode": settings.MPESA_SHORTCODE,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": int(booking.amount),
                "PartyA": phone_number,
                "PartyB": settings.MPESA_SHORTCODE,
                "PhoneNumber": phone_number,
                "CallBackURL": settings.MPESA_CALLBACK_URL,
                "AccountReference": booking_code,
                "TransactionDesc": "ShereheTickets",
            }

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }

            try:
                response = requests.post(
                    f"{settings.MPESA_API_URL}/mpesa/stkpush/v1/processrequest",
                    json=payload,
                    headers=headers,
                )
                response_data = response.json()
                logger.info(f"M-Pesa STK Push response: {response_data}")

                if response_data.get("ResponseCode") == "0":
                    # FIXED: Save CheckoutRequestID to the correct field
                    booking.checkout_request_id = response_data.get("CheckoutRequestID")
                    booking.callback_url = settings.MPESA_CALLBACK_URL
                    booking.payment_method = "M-Pesa STK Push"
                    booking.mpesa_phone_number = phone_number
                    booking.save()

                    return Response(
                        {
                            "merchant_request_id": response_data.get(
                                "MerchantRequestID"
                            ),
                            "checkout_request_id": response_data.get(
                                "CheckoutRequestID"
                            ),
                            "response_description": response_data.get(
                                "ResponseDescription"
                            ),
                            "customer_message": response_data.get("CustomerMessage"),
                        },
                        status=status.HTTP_200_OK,
                    )
                else:
                    logger.error(f"M-Pesa STK Push failed: {response_data}")
                    return Response(
                        {
                            "error": response_data.get(
                                "errorMessage", "STK Push request failed"
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            except requests.RequestException as e:
                logger.error(f"M-Pesa STK Push request exception: {str(e)}")
                return Response(
                    {"error": f"STK Push request failed: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        except Booking.DoesNotExist:
            logger.error("Booking not found")
            return Response(
                {"error": "Booking not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            logger.error(f"Unexpected error in MpesaPaymentCreateView: {str(e)}")
            return Response(
                {"error": "An unexpected error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class MpesaCallbackView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        body = request.data

        if not body:
            logger.error("Invalid or empty callback data")
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # Save raw callback for debugging
        MpesaBody.objects.create(body=body)

        stk_callback = body.get("Body", {}).get("stkCallback", {})
        checkout_request_id = stk_callback.get("CheckoutRequestID")

        if not checkout_request_id:
            logger.error("Missing CheckoutRequestID in callback")
            return Response(
                {"ResultCode": 1, "ResultDesc": "Invalid callback data"},
                status=status.HTTP_200_OK,
            )

        try:
            booking = Booking.objects.get(checkout_request_id=checkout_request_id)
        except Booking.DoesNotExist:
            logger.error(
                f"Booking not found for CheckoutRequestID: {checkout_request_id}"
            )
            return Response(
                {"ResultCode": 0, "ResultDesc": "Booking not found"},
                status=status.HTTP_200_OK,
            )

        # Prevent duplicate processing
        if booking.payment_status == "Completed":
            logger.info(
                f"Booking {booking.booking_code} already processed, skipping duplicate callback"
            )
            return Response(
                {"ResultCode": 0, "ResultDesc": "Already processed"},
                status=status.HTTP_200_OK,
            )

        # FIXED: Compare ResultCode as integer (M-Pesa sends 0 as int, not string)
        result_code = stk_callback.get("ResultCode")

        if result_code != 0:  # Critical fix: was comparing to "0" (string)
            booking.status = "CANCELLED"
            booking.payment_status = "FAILED"
            booking.payment_status_description = stk_callback.get(
                "ResultDesc", "Payment failed"
            )
            frontend_url = f"{settings.SITE_URL}/payment/{booking.reference}/failure"
            booking.redirect_url = frontend_url
            booking.save()

            logger.warning(
                f"Payment FAILED for booking {booking.reference} | ResultCode: {result_code}"
            )
            return Response(
                {"ResultCode": 0, "ResultDesc": "Payment failed acknowledged"},
                status=status.HTTP_200_OK,
            )

        # SUCCESS PATH
        metadata_items = stk_callback.get("CallbackMetadata", {}).get("Item", [])

        confirmation_code = next(
            (
                item.get("Value")
                for item in metadata_items
                if item.get("Name") == "MpesaReceiptNumber"
            ),
            None,
        )
        payment_account = next(
            (
                item.get("Value")
                for item in metadata_items
                if item.get("Name") == "PhoneNumber"
            ),
            None,
        )

        booking.status = "CONFIRMED"
        booking.payment_status = "Completed"
        booking.payment_date = timezone.now()
        booking.mpesa_receipt_number = confirmation_code
        booking.payment_account = payment_account
        booking.save()

        # Create tickets if not already created
        if not Ticket.objects.filter(booking=booking).exists():
            logger.info(
                f"Creating {booking.quantity} tickets for booking {booking.booking_code}"
            )
            for _ in range(booking.quantity):
                Ticket.objects.create(
                    booking=booking,
                    ticket_type=booking.ticket_type,
                )

            # Update ticket type availability
            ticket_type = booking.ticket_type
            if ticket_type.is_limited and ticket_type.quantity_available is not None:
                ticket_type.quantity_available -= booking.quantity
                ticket_type.save()
                logger.info(
                    f"Reduced availability for {ticket_type.name}: {ticket_type.quantity_available} left"
                )

        frontend_url = f"{settings.SITE_URL}/payment/{booking.reference}/success"
        booking.redirect_url = frontend_url
        booking.save()

        logger.info(
            f"Payment SUCCESSFUL for booking {booking.booking_code} | Receipt: {confirmation_code}"
        )

        # Send confirmation email in background
        if booking.email:
            threading.Thread(
                target=send_booking_confirmation_email,
                args=(booking.email, booking),
            ).start()

        return Response(
            {
                "ResultCode": 0,
                "ResultDesc": "Payment successful",
                "redirect_url": frontend_url,
            },
            status=status.HTTP_200_OK,
        )

    def get(self, request, *args, **kwargs):
        """Endpoint to view all saved callback bodies (for debugging)"""
        bodies = MpesaBody.objects.all().order_by("-id")
        serializer = MpesaBodySerializer(bodies, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
