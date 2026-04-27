from django.core.management.base import BaseCommand
from django.utils import timezone
from auth_app.models import ElectionSettings
from datetime import datetime

class Command(BaseCommand):
    help = 'Set election start and end times'

    def handle(self, *args, **options):
        start_str = input("Start time (YYYY-MM-DD HH:MM): ")
        end_str = input("End time (YYYY-MM-DD HH:MM): ")
        try:
            start = timezone.make_aware(datetime.strptime(start_str, '%Y-%m-%d %H:%M'))
            end = timezone.make_aware(datetime.strptime(end_str, '%Y-%m-%d %H:%M'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Invalid time format: {e}"))
            return
        if start >= end:
            self.stdout.write(self.style.ERROR("Start time must be before end time"))
            return
        obj, created = ElectionSettings.objects.update_or_create(
            id=1,
            defaults={'start_time': start, 'end_time': end}
        )
        self.stdout.write(self.style.SUCCESS(f"✅ Election times set from {start} to {end}"))