import logging
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from events.models import Event, PayoutRequest
from bookings.models import Booking

logger = logging.getLogger(__name__)


def calculate_event_settlement(event):
    """
    Calculates gross sales, platform fee, disbursed payouts, and net withdrawable balance.
    """
    completed_bookings = Booking.objects.filter(
        ticket_type__event=event, payment_status="COMPLETED"
    )

    total_tickets_sold = sum(b.quantity for b in completed_bookings)
    gross_sales = sum((b.amount for b in completed_bookings), Decimal("0.00"))

    platform_fee_percent = Decimal(str(event.platform_fee_percent or 3.50))
    platform_fee_amount = (gross_sales * platform_fee_percent) / Decimal("100.00")
    net_event_revenue = gross_sales - platform_fee_amount

    all_payouts = PayoutRequest.objects.filter(event=event).order_by("-created_at")

    disbursed_amount = sum(
        (p.amount_requested for p in all_payouts if p.status in ["APPROVED", "DISBURSED"]),
        Decimal("0.00"),
    )
    pending_amount = sum(
        (p.amount_requested for p in all_payouts if p.status == "PENDING"),
        Decimal("0.00"),
    )

    withdrawable_balance = max(
        Decimal("0.00"), net_event_revenue - disbursed_amount - pending_amount
    )

    # 14-day sales velocity timeline for charts
    today = timezone.now().date()
    sales_velocity = []
    for i in range(13, -1, -1):
        day = today - timedelta(days=i)
        day_bookings = [
            b for b in completed_bookings if b.created_at.date() == day
        ]
        day_rev = sum((b.amount for b in day_bookings), Decimal("0.00"))
        day_tickets = sum(b.quantity for b in day_bookings)
        sales_velocity.append(
            {
                "date": day.strftime("%b %d"),
                "revenue": float(day_rev),
                "tickets": day_tickets,
            }
        )

    payouts_serialized = [
        {
            "reference": p.reference,
            "amount_requested": float(p.amount_requested),
            "platform_fee_deducted": float(p.platform_fee_deducted),
            "net_payout_amount": float(p.net_payout_amount),
            "payout_phone": p.payout_phone,
            "status": p.status,
            "mpesa_transaction_id": p.mpesa_transaction_id,
            "notes": p.notes,
            "created_at": p.created_at.isoformat(),
            "disbursed_at": p.disbursed_at.isoformat() if p.disbursed_at else None,
        }
        for p in all_payouts[:10]
    ]

    return {
        "event_code": event.event_code,
        "event_name": event.name,
        "gate_passcode": event.gate_passcode,
        "total_tickets_sold": total_tickets_sold,
        "gross_sales": float(gross_sales),
        "platform_fee_percent": float(platform_fee_percent),
        "platform_fee_amount": float(platform_fee_amount),
        "net_event_revenue": float(net_event_revenue),
        "disbursed_amount": float(disbursed_amount),
        "pending_amount": float(pending_amount),
        "withdrawable_balance": float(withdrawable_balance),
        "sales_velocity": sales_velocity,
        "recent_payouts": payouts_serialized,
    }


class EventSettlementView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, event_code, *args, **kwargs):
        try:
            event = Event.objects.get(event_code=event_code)
        except Event.DoesNotExist:
            return Response(
                {"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND
            )

        if not (request.user.is_superuser or event.manager == request.user):
            return Response(
                {"error": "You do not have permission to view settlement details."},
                status=status.HTTP_403_FORBIDDEN,
            )

        data = calculate_event_settlement(event)
        return Response(data, status=status.HTTP_200_OK)


class EventPayoutRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, event_code, *args, **kwargs):
        try:
            event = Event.objects.get(event_code=event_code)
        except Event.DoesNotExist:
            return Response(
                {"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND
            )

        if not (request.user.is_superuser or event.manager == request.user):
            return Response(
                {"error": "You do not have permission to request payouts."},
                status=status.HTTP_403_FORBIDDEN,
            )

        amount_raw = request.data.get("amount")
        payout_phone = (request.data.get("phone_number") or "").strip()

        if not amount_raw:
            return Response(
                {"error": "Amount is required."}, status=status.HTTP_400_BAD_REQUEST
            )
        if not payout_phone:
            return Response(
                {"error": "M-Pesa phone number is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            requested_amount = Decimal(str(amount_raw))
        except Exception:
            return Response(
                {"error": "Invalid amount format."}, status=status.HTTP_400_BAD_REQUEST
            )

        if requested_amount <= 0:
            return Response(
                {"error": "Requested amount must be greater than zero."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        settlement = calculate_event_settlement(event)
        withdrawable = Decimal(str(settlement["withdrawable_balance"]))

        if requested_amount > withdrawable:
            return Response(
                {
                    "error": f"Requested amount (KES {requested_amount:,.2f}) exceeds available withdrawable balance (KES {withdrawable:,.2f})."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create Payout Request
        payout = PayoutRequest.objects.create(
            event=event,
            company=event.company,
            requested_by=request.user,
            amount_requested=requested_amount,
            platform_fee_deducted=Decimal("0.00"),
            net_payout_amount=requested_amount,
            payout_phone=payout_phone,
            status="PENDING",
            notes=request.data.get("notes", ""),
        )

        logger.info(
            f"[PAYOUT REQUEST] Organizer {request.user.email} requested KES {requested_amount} for event {event.name} ({event.event_code})"
        )

        return Response(
            {
                "success": True,
                "message": f"Payout request of KES {requested_amount:,.2f} submitted for review.",
                "payout": {
                    "reference": payout.reference,
                    "amount_requested": float(payout.amount_requested),
                    "status": payout.status,
                    "payout_phone": payout.payout_phone,
                    "created_at": payout.created_at.isoformat(),
                },
                "updated_balance": float(withdrawable - requested_amount),
            },
            status=status.HTTP_201_CREATED,
        )
