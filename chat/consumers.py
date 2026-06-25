import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from rest_framework.authtoken.models import Token
from .models import Chat, Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.room_group_name = f'chat_{self.chat_id}'

        # Obter token dos parâmetros da query string
        query_string = self.scope.get('query_string', b'').decode()
        token_key = None
        for param in query_string.split('&'):
            if param.startswith('token='):
                token_key = param.split('=')[1]
                break

        self.user = await self.get_user(token_key)
        if self.user is None or not await self.is_participant(self.user, self.chat_id):
            await self.close()
            return

        # Entrar no grupo da conversa
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Sair do grupo da conversa
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        content = data.get('content', '').strip()
        if not content:
            return

        # Salvar mensagem no banco de dados e serializá-la
        message = await self.save_message(self.user, self.chat_id, content)

        # Enviar mensagem para todos no grupo da conversa
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )

    async def chat_message(self, event):
        message = event['message']

        # Enviar a mensagem recebida no grupo para o cliente WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': message
        }))

    @database_sync_to_async
    def get_user(self, token_key):
        if not token_key:
            return None
        try:
            token = Token.objects.select_related('user').get(key=token_key)
            return token.user
        except Token.DoesNotExist:
            return None

    @database_sync_to_async
    def is_participant(self, user, chat_id):
        try:
            chat = Chat.objects.get(id=chat_id)
            return chat.Participants.filter(id=user.id).exists()
        except Chat.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, user, chat_id, content):
        chat = Chat.objects.get(id=chat_id)
        msg = Message.objects.create(Chat=chat, Sender=user, Content=content)
        return {
            "id": msg.id,
            "chatId": msg.Chat_id,
            "senderId": msg.Sender_id,
            "senderUsername": msg.Sender.username,
            "content": msg.Content,
            "createdAt": msg.CreatedAt.isoformat(),
        }
