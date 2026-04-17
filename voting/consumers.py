import json
from channels.generic.websocket import AsyncWebsocketConsumer


class VotingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Accept the WebSocket connection
        await self.accept()
        # Optional: send a welcome message
        await self.send(text_data=json.dumps({
            "status": "connected",
            "message": "Welcome to the Secure E-Voting System"
        }))

    async def disconnect(self, close_code):
        # Called when the client disconnects
        pass

    async def receive(self, text_data):
        # This will handle incoming vote messages later
        # For now, just echo back a test response
        data = json.loads(text_data)

        # Simple test response (will be replaced with full voting logic)
        await self.send(text_data=json.dumps({
            "status": "received",
            "your_message": data
        }))