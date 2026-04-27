import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from auth_app.models import Student, Candidate, UsedNonce, Vote, ServerKey, ElectionSettings
from voting.crypto import (
    pem_to_public_numbers, pem_to_private_numbers,
    decrypt_long_text, verify, generate_rsa_keypair
)
import base64

class VotingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send(text_data=json.dumps({
            "status": "connected",
            "message": "Secure E-Voting System WebSocket ready"
        }))

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            if data.get('type') == 'vote':
                await self.handle_vote(data)
            else:
                await self.send(json.dumps({"status": "error", "message": "Unknown message type"}))
        except Exception as e:
            await self.send(json.dumps({"status": "error", "message": str(e)}))

    async def handle_vote(self, data):
        voter_id = data.get('voter_id')
        cipher_vote = data.get('cipher_vote')
        nonce = data.get('nonce')
        signature = data.get('signature')

        # 1. التحقق من وقت التصويت
        if not await self.is_within_election_time():
            await self.send(json.dumps({"status": "rejected", "reason": "Voting is not open at this time"}))
            return

        # 2. التحقق من عدم تكرار nonce
        if await self.is_nonce_used(nonce):
            await self.send(json.dumps({"status": "rejected", "reason": "Replay attack detected (nonce already used)"}))
            return

        # 3. استرجاع الطالب (الناخب) ومفتاحه العمومي
        student = await self.get_student(voter_id)
        if not student:
            await self.send(json.dumps({"status": "rejected", "reason": "Invalid voter ID"}))
            return

        # 4. التحقق من التوقيع (يجب أن يكون على cipher_vote + nonce)
        message_to_verify = cipher_vote + nonce
        # نحول المفتاح العمومي المخزن كنص إلى (e,n)
        try:
            public_numbers = pem_to_public_numbers(student.public_key)
        except Exception:
            await self.send(json.dumps({"status": "rejected", "reason": "Invalid public key format"}))
            return

        if not verify(message_to_verify, signature, public_numbers):
            await self.send(json.dumps({"status": "rejected", "reason": "Invalid signature"}))
            return

        # 5. التحقق من عدم التصويت المزدوج
        if student.has_voted:
            await self.send(json.dumps({"status": "rejected", "reason": "You have already voted"}))
            return

        # 6. تحميل المفتاح الخاص للخادم وتحويله إلى (d,n)
        server_key_obj = await self.get_server_key()
        if not server_key_obj:
            await self.send(json.dumps({"status": "rejected", "reason": "Server key not configured"}))
            return

        try:
            private_numbers = pem_to_private_numbers(server_key_obj.private_key)
            decrypted_candidate = decrypt_long_text(cipher_vote, private_numbers)
        except Exception as e:
            await self.send(json.dumps({"status": "rejected", "reason": f"Decryption failed: {str(e)}"}))
            return

        # 7. البحث عن المرشح باسمه
        candidate = await self.get_candidate_by_name(decrypted_candidate)
        if not candidate:
            await self.send(json.dumps({"status": "rejected", "reason": "Candidate not found"}))
            return

        # 8. تسجيل التصويت
        success = await self.record_vote(student, candidate, cipher_vote, nonce, signature)
        if not success:
            await self.send(json.dumps({"status": "rejected", "reason": "Could not record vote (maybe already voted)"}))
            return

        # 9. القبول
        await self.send(json.dumps({"status": "accepted", "message": "Your vote has been counted"}))

    # ---------- دوال مساعدة async مع database_sync_to_async ----------
    @database_sync_to_async
    def is_within_election_time(self):
        settings = ElectionSettings.objects.first()
        if not settings:
            return False
        now = timezone.now()
        return settings.start_time <= now <= settings.end_time

    @database_sync_to_async
    def is_nonce_used(self, nonce):
        return UsedNonce.objects.filter(nonce=nonce).exists()

    @database_sync_to_async
    def get_student(self, voter_id):
        try:
            return Student.objects.get(id=voter_id)
        except Student.DoesNotExist:
            return None

    @database_sync_to_async
    def get_server_key(self):
        try:
            return ServerKey.objects.first()
        except ServerKey.DoesNotExist:
            return None

    @database_sync_to_async
    def get_candidate_by_name(self, name):
        try:
            student = Student.objects.get(name=name)
            return Candidate.objects.get(student=student)
        except (Student.DoesNotExist, Candidate.DoesNotExist):
            return None

    @database_sync_to_async
    def record_vote(self, student, candidate, cipher_vote, nonce, signature):
        from django.db import transaction
        try:
            with transaction.atomic():
                if student.has_voted:
                    return False
                candidate.vote_count += 1
                candidate.save()
                UsedNonce.objects.create(nonce=nonce)
                Vote.objects.create(
                    voter=student,
                    candidate=candidate,
                    cipher_vote=cipher_vote,
                    nonce=nonce,
                    signature=signature
                )
                student.has_voted = True
                student.save()
            return True
        except Exception:
            return False