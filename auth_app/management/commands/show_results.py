from django.core.management.base import BaseCommand
from auth_app.models import Candidate

class Command(BaseCommand):
    help = 'Show current election results'

    def handle(self, *args, **options):
        candidates = Candidate.objects.select_related('student').all()
        if not candidates:
            self.stdout.write("No candidates found.")
            return
        self.stdout.write("\n=== Election Results ===\n")
        for c in candidates:
            self.stdout.write(f"{c.student.name}: {c.vote_count} vote(s)")