import logging
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from events.models import Event
from tickets.models import Ticket, TicketScanLog
from tickettypes.models import TicketType

logger = logging.getLogger(__name__)


def check_gate_authorization(request, event):
    """
    Check if request is authorized to perform gate operations:
    1. Authenticated user who is event manager or superuser.
    2. Or request provides valid 'gate_passcode' matching event.gate_passcode.
    """
    if request.user and request.user.is_authenticated:
        if request.user.is_superuser or event.manager == request.user:
            return True, "Authenticated Organizer"

    passcode = (
        request.data.get("gate_passcode")
        or request.query_params.get("gate_passcode")
        or request.headers.get("X-Gate-Passcode")
    )
    if passcode and event.gate_passcode:
        if passcode.strip().upper() == event.gate_passcode.strip().upper():
            return True, "Authorized via Passcode"

    return False, "Invalid gate authorization"


class TicketScanView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, event_code, *args, **kwargs):
        try:
            event = Event.objects.get(event_code=event_code)
        except Event.DoesNotExist:
            return Response(
                {"status": "INVALID_EVENT", "error": "Event not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        is_auth, auth_msg = check_gate_authorization(request, event)
        if not is_auth:
            return Response(
                {"status": "UNAUTHORIZED", "error": "Invalid gate authorization or passcode."},
                status=status.HTTP_403_FORBIDDEN,
            )

        raw_code = request.data.get("ticket_code") or request.data.get("qr_data")
        gate_station = request.data.get("gate_station", "Main Gate")

        if not raw_code:
            return Response(
                {"status": "BAD_REQUEST", "error": "ticket_code or qr_data is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Normalize raw_code: if full URL like https://sherehe.co.ke/tickets/<ref>/, extract <ref>
        clean_code = str(raw_code).strip()
        if "/tickets/" in clean_code:
            clean_code = clean_code.split("/tickets/")[-1].strip("/").strip()

        # Find ticket by reference or ticket_code
        ticket = (
            Ticket.objects.select_related("booking", "ticket_type")
            .filter(reference=clean_code)
            .first()
        )
        if not ticket:
            ticket = (
                Ticket.objects.select_related("booking", "ticket_type")
                .filter(ticket_code=clean_code)
                .first()
            )

        if not ticket:
            TicketScanLog.objects.create(
                event_code=event_code,
                scanned_code=clean_code,
                status="NOT_FOUND",
                gate_station=gate_station,
                scanned_by=request.user if request.user.is_authenticated else None,
                notes="Ticket not found in system",
            )
            return Response(
                {
                    "status": "NOT_FOUND",
                    "error": "Ticket not found. Invalid barcode or QR code.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Validate ticket belongs to this event
        ticket_event = getattr(ticket.ticket_type, "event", None)
        if not ticket_event or ticket_event.event_code != event_code:
            TicketScanLog.objects.create(
                ticket=ticket,
                event_code=event_code,
                scanned_code=clean_code,
                status="INVALID_EVENT",
                gate_station=gate_station,
                scanned_by=request.user if request.user.is_authenticated else None,
                notes=f"Ticket belongs to different event ({ticket_event.name if ticket_event else 'Unknown'})",
            )
            return Response(
                {
                    "status": "INVALID_EVENT",
                    "error": f"Ticket belongs to a different event: {ticket_event.name if ticket_event else 'Unknown'}",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check booking payment status
        if ticket.booking.payment_status != "COMPLETED":
            TicketScanLog.objects.create(
                ticket=ticket,
                event_code=event_code,
                scanned_code=clean_code,
                status="UNPAID",
                gate_station=gate_station,
                scanned_by=request.user if request.user.is_authenticated else None,
                notes=f"Booking payment status is {ticket.booking.payment_status}",
            )
            return Response(
                {
                    "status": "UNPAID",
                    "error": f"Ticket is unpaid. Payment status: {ticket.booking.payment_status}",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check duplicate scan
        if ticket.is_used:
            TicketScanLog.objects.create(
                ticket=ticket,
                event_code=event_code,
                scanned_code=clean_code,
                status="ALREADY_USED",
                gate_station=gate_station,
                scanned_by=request.user if request.user.is_authenticated else None,
                notes=f"Duplicate entry attempt. First scanned at {ticket.used_at} at {ticket.gate_station}",
            )
            return Response(
                {
                    "status": "ALREADY_USED",
                    "error": "⚠️ TICKET ALREADY SCANNED!",
                    "attendee_name": ticket.booking.name,
                    "ticket_type": ticket.ticket_type.name if ticket.ticket_type else "General",
                    "first_used_at": ticket.used_at,
                    "first_gate_station": ticket.gate_station,
                    "ticket_code": ticket.ticket_code,
                    "reference": ticket.reference,
                },
                status=status.HTTP_409_CONFLICT,
            )

        # Valid scan - mark used
        now = timezone.now()
        ticket.is_used = True
        ticket.used_at = now
        ticket.gate_station = gate_station
        if request.user.is_authenticated:
            ticket.scanned_by = request.user
        ticket.save(update_fields=["is_used", "used_at", "gate_station", "scanned_by"])

        TicketScanLog.objects.create(
            ticket=ticket,
            event_code=event_code,
            scanned_code=clean_code,
            status="VALID",
            gate_station=gate_station,
            scanned_by=request.user if request.user.is_authenticated else None,
            notes="Successful check-in",
        )

        return Response(
            {
                "status": "VALID",
                "message": "Entry Approved",
                "attendee_name": ticket.booking.name,
                "phone": ticket.booking.phone,
                "email": ticket.booking.email,
                "ticket_type": ticket.ticket_type.name if ticket.ticket_type else "General",
                "price": str(ticket.ticket_type.price) if ticket.ticket_type else "0.00",
                "booking_code": ticket.booking.booking_code,
                "ticket_code": ticket.ticket_code,
                "reference": ticket.reference,
                "checked_in_at": now,
                "gate_station": gate_station,
            },
            status=status.HTTP_200_OK,
        )


class GateStatsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, event_code, *args, **kwargs):
        try:
            event = Event.objects.get(event_code=event_code)
        except Event.DoesNotExist:
            return Response({"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND)

        is_auth, _ = check_gate_authorization(request, event)
        if not is_auth:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        # Tickets stats
        all_tickets = Ticket.objects.filter(
            booking__ticket_type__event=event,
            booking__payment_status="COMPLETED",
        )
        total_sold = all_tickets.count()
        total_checked_in = all_tickets.filter(is_used=True).count()
        remaining = total_sold - total_checked_in
        check_in_rate = round((total_checked_in / total_sold * 100), 1) if total_sold > 0 else 0.0

        # Breakdown by ticket tier
        tier_breakdown = []
        for tt in event.ticket_types.all():
            tt_tickets = all_tickets.filter(ticket_type=tt)
            tt_sold = tt_tickets.count()
            tt_checked = tt_tickets.filter(is_used=True).count()
            tier_breakdown.append(
                {
                    "ticket_type_code": tt.ticket_type_code,
                    "name": tt.name,
                    "price": str(tt.price),
                    "sold": tt_sold,
                    "checked_in": tt_checked,
                    "remaining": tt_sold - tt_checked,
                }
            )

        # Last 10 scan logs
        recent_logs = []
        for log in TicketScanLog.objects.filter(event_code=event_code).order_by("-created_at")[:10]:
            recent_logs.append(
                {
                    "status": log.status,
                    "scanned_code": log.scanned_code,
                    "gate_station": log.gate_station,
                    "created_at": log.created_at,
                    "attendee_name": log.ticket.booking.name if log.ticket and log.ticket.booking else None,
                    "ticket_type": log.ticket.ticket_type.name if log.ticket and log.ticket.ticket_type else None,
                }
            )

        return Response(
            {
                "event_name": event.name,
                "event_code": event.event_code,
                "gate_passcode": event.gate_passcode,
                "total_sold": total_sold,
                "total_checked_in": total_checked_in,
                "remaining": remaining,
                "check_in_rate_percent": check_in_rate,
                "tier_breakdown": tier_breakdown,
                "recent_logs": recent_logs,
            },
            status=status.HTTP_200_OK,
        )


class GateAttendeeSearchView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, event_code, *args, **kwargs):
        try:
            event = Event.objects.get(event_code=event_code)
        except Event.DoesNotExist:
            return Response({"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND)

        is_auth, _ = check_gate_authorization(request, event)
        if not is_auth:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        q = request.query_params.get("q", "").strip()
        tickets = Ticket.objects.filter(
            booking__ticket_type__event=event,
            booking__payment_status="COMPLETED",
        ).select_related("booking", "ticket_type")

        if q:
            from django.db.models import Q
            tickets = tickets.filter(
                Q(booking__name__icontains=q)
                | Q(booking__phone__icontains=q)
                | Q(booking__email__icontains=q)
                | Q(booking__booking_code__icontains=q)
                | Q(booking__mpesa_receipt_number__icontains=q)
                | Q(ticket_code__icontains=q)
                | Q(reference__icontains=q)
            )

        results = []
        for t in tickets[:50]:
            results.append(
                {
                    "reference": t.reference,
                    "ticket_code": t.ticket_code,
                    "is_used": t.is_used,
                    "used_at": t.used_at,
                    "gate_station": t.gate_station,
                    "attendee_name": t.booking.name,
                    "phone": t.booking.phone,
                    "email": t.booking.email,
                    "ticket_type": t.ticket_type.name if t.ticket_type else "General",
                    "booking_code": t.booking.booking_code,
                    "mpesa_receipt": t.booking.mpesa_receipt_number,
                }
            )

        return Response({"results": results, "count": len(results)}, status=status.HTTP_200_OK)


class GateManualCheckInView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, event_code, *args, **kwargs):
        try:
            event = Event.objects.get(event_code=event_code)
        except Event.DoesNotExist:
            return Response({"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND)

        is_auth, _ = check_gate_authorization(request, event)
        if not is_auth:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        ticket_reference = request.data.get("ticket_reference")
        gate_station = request.data.get("gate_station", "Manual Desk")

        if not ticket_reference:
            return Response(
                {"error": "ticket_reference is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ticket = Ticket.objects.select_related("booking", "ticket_type").filter(
            reference=ticket_reference,
            booking__ticket_type__event=event,
        ).first()

        if not ticket:
            return Response({"error": "Ticket not found"}, status=status.HTTP_404_NOT_FOUND)

        if ticket.is_used:
            return Response(
                {
                    "status": "ALREADY_USED",
                    "error": f"Ticket already used at {ticket.used_at} by {ticket.gate_station}",
                    "attendee_name": ticket.booking.name,
                },
                status=status.HTTP_409_CONFLICT,
            )

        now = timezone.now()
        ticket.is_used = True
        ticket.used_at = now
        ticket.gate_station = gate_station
        if request.user.is_authenticated:
            ticket.scanned_by = request.user
        ticket.save(update_fields=["is_used", "used_at", "gate_station", "scanned_by"])

        TicketScanLog.objects.create(
            ticket=ticket,
            event_code=event_code,
            scanned_code=ticket.ticket_code,
            status="VALID",
            gate_station=gate_station,
            scanned_by=request.user if request.user.is_authenticated else None,
            notes="Manual check-in by operator",
        )

        return Response(
            {
                "status": "VALID",
                "message": "Manual check-in successful",
                "attendee_name": ticket.booking.name,
                "ticket_type": ticket.ticket_type.name if ticket.ticket_type else "General",
                "checked_in_at": now,
            },
            status=status.HTTP_200_OK,
        )
