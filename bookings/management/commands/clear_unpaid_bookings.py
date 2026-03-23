from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from bookings.models import Booking

class Command(BaseCommand):
    help = 'Deletes PENDING bookings that are older than 30 minutes'

    def handle(self, *args, **options):
        # Calculate the threshold time (30 minutes ago)
        threshold_time = timezone.now() - timedelta(minutes=30)
        
        # Find bookings to delete: status=PENDING and created_at < threshold_time
        expired_bookings = Booking.objects.filter(
            status='PENDING',
            created_at__lt=threshold_time
        )
        
        count = expired_bookings.count()
        if count > 0:
            expired_bookings.delete()
            self.stdout.write(self.style.SUCCESS(f'Successfully deleted {count} expired pending bookings'))
        else:
            self.stdout.write(self.style.SUCCESS('No expired pending bookings found'))
