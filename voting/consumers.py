import json
from channels.generic.websocket import AsyncWebsocketConsumer

class VotingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send(text_data=json.dumps({
            "status": "connected",
            "message": "E-Voting System Ready"
        }))

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        data = json.loads(text_data)
        await self.send(text_data=json.dumps({
            "status": "received",
            "data": data
        }))