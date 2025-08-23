import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send(text_data=json.dumps({
            "message": "Bienvenue dans le WS Django!"
        }))

    async def receive(self, text_data):
        data = json.loads(text_data)
        print("Message reçu:", data)
        await self.send(text_data=json.dumps({
            "message": f"Reçu: {data['message']}"
        }))
