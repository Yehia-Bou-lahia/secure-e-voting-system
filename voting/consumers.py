import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from datetime import datetime
from django.conf import settings
from auth_app.models import Student, Candidate, UsedNonce, Vote
from voting.crypto import (
    decrypt_long_text,   # نستخدم فك التشفير للنص الطويل
    verify,              # التحقق من التوقيع
    hash_message         # لتوليد التجزئة (اختياري، لكن verify تستخدمه داخلياً)
)

class VotingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # هنا يمكن إضافة التحقق من JWT لاحقاً
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
            # نتوقع رسالة من النوع "vote"
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
        if not self.is_within_election_time():
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

        # 4. التحقق من التوقيع
        #    يجب أن يكون التوقيع على (cipher_vote + nonce)
        message_to_verify = cipher_vote + nonce
        if not verify(message_to_verify, signature, student.public_key):
            await self.send(json.dumps({"status": "rejected", "reason": "Invalid signature"}))
            return

        # 5. التحقق من عدم التصويت المزدوج
        if student.has_voted:
            await self.send(json.dumps({"status": "rejected", "reason": "You have already voted"}))
            return

        # 6. فك تشفير التصويت (باستخدام المفتاح الخاص للخادم)
        #    نحتاج إلى تحميل المفتاح الخاص للخادم من قاعدة البيانات (سنضيف نموذج ServerKey)
        server_private_key = await self.get_server_private_key()
        if not server_private_key:
            await self.send(json.dumps({"status": "error", "reason": "Server key not configured"}))
            return

        try:
            candidate_name = decrypt_long_text(cipher_vote, server_private_key)
        except Exception as e:
            await self.send(json.dumps({"status": "rejected", "reason": f"Decryption failed: {str(e)}"}))
            return

        # 7. البحث عن المرشح باسمه
        candidate = await self.get_candidate_by_name(candidate_name)
        if not candidate:
            await self.send(json.dumps({"status": "rejected", "reason": "Candidate not found"}))
            return

        # 8. تسجيل التصويت (استخدام معاملة ذرية)
        success = await self.record_vote(student, candidate, cipher_vote, nonce, signature)
        if not success:
            await self.send(json.dumps({"status": "rejected", "reason": "Could not record vote (maybe already voted)"}))
            return

        # 9. إرسال القبول
        await self.send(json.dumps({"status": "accepted", "message": "Your vote has been counted"}))

    # -------------------- الدوال المساعدة (async مع database_sync_to_async) --------------------
    @database_sync_to_async
    def is_within_election_time(self):
        # يمكن قراءة الوقت من settings أو من نموذج Election
        now = timezone.now()
        start = datetime.fromisoformat(settings.ELECTION_START_TIME)
        end = datetime.fromisoformat(settings.ELECTION_END_TIME)
        # تأكد من جعل الوقت aware إذا لزم الأمر
        return start <= now <= end

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
    def get_server_private_key(self):
        # سننشئ نموذج ServerKey يحوي المفتاح الخاص للخادم
        from auth_app.models import ServerKey
        try:
            return ServerKey.objects.get(id=1).private_key
        except ServerKey.DoesNotExist:
            return None

    @database_sync_to_async
    def get_candidate_by_name(self, name):
        # نفرض أن اسم المرشح مخزّن في student.name (لأن Candidate مرتبط بـ Student)
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
                # منع التصويت المزدوج مجدداً (للتأكد)
                if student.has_voted:
                    return False
                # زيادة عداد المرشح
                candidate.vote_count += 1
                candidate.save()
                # تسجيل nonce كمستخدم
                UsedNonce.objects.create(nonce=nonce)
                # تسجيل عملية التصويت
                Vote.objects.create(
                    voter=student,
                    candidate=candidate,
                    cipher_vote=cipher_vote,
                    nonce=nonce,
                    signature=signature
                )
                # تعليم الطالب بأنه صوّت
                student.has_voted = True
                student.save()
            return True
        except Exception:
            return False