from django.core.management.base import BaseCommand
from auth_app.models import ServerKey
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

class Command(BaseCommand):
    help = 'Generate RSA keys for the server and save to database'

    def handle(self, *args, **options):
        if ServerKey.objects.exists():
            overwrite = input("Server keys already exist. Overwrite? (y/n): ")
            if overwrite.lower() != 'y':
                self.stdout.write("Operation cancelled.")
                return
            ServerKey.objects.all().delete()

        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()
        pem_private = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        pem_public = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')

        ServerKey.objects.create(private_key=pem_private, public_key=pem_public)
        self.stdout.write(self.style.SUCCESS("✅ Server RSA keys generated and saved successfully."))