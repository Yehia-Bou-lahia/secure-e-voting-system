from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from auth_app.models import Student, Candidate

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a new candidate'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Add New Candidate ==='))
        name = input("Candidate name: ")
        email = input("Candidate email address: ")
        username = input("Username (or press Enter to use email): ")
        if not username:
            username = email
        password = input("Password (optional, press Enter to set default): ")
        if not password:
            password = "candidate123"

        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            candidate_student = Student.objects.create(user=user, name=name, public_key='', has_voted=False)
            candidate = Candidate.objects.create(user=user, student=candidate_student, vote_count=0)
            self.stdout.write(self.style.SUCCESS(f"\n✅ Candidate '{name}' created successfully"))
            self.stdout.write(f"Candidate ID: {candidate.id}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))