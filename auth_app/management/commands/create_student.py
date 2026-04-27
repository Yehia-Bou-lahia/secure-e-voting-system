import getpass
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from auth_app.models import Student
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a new student with RSA key pair (private key saved to file)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Create New Student Account ==='))
        name = input("Full name: ")
        email = input("Email address: ")
        username = input("Username (or press Enter to use email): ")
        if not username:
            username = email
        password = getpass.getpass("Password: ")
        password2 = getpass.getpass("Confirm password: ")
        if password != password2:
            self.stdout.write(self.style.ERROR("Passwords do not match"))
            return

        try:
            user = User.objects.create_user(username=username, email=email, password=password)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error creating user: {e}"))
            return

        # Generate RSA key pair
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()
        pem_public = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')

        student = Student.objects.create(user=user, name=name, public_key=pem_public, has_voted=False)

        pem_private = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')

        filename = f"student_{student.id}_private.pem"
        with open(filename, 'w') as f:
            f.write(pem_private)

        self.stdout.write(self.style.SUCCESS(f"\n✅ Student created successfully!"))
        self.stdout.write(f"Student ID: {student.id}")
        self.stdout.write(f"Private key saved to file: {filename}")
        self.stdout.write(self.style.WARNING("⚠ Keep this file, you will need it to sign votes."))