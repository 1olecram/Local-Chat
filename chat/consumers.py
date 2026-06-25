import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from rest_framework.authtoken.models import Token
from .models import Chat, Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Obter token dos parâmetros da query string
        query_string = self.scope.get('query_string', b'').decode()
        token_key = None
        for param in query_string.split('&'):
            if param.startswith('token='):
                token_key = param.split('=')[1]
                break

        self.user = await self.get_user(token_key)
        if self.user is None:
            await self.close()
            return

        self.user_group_name = f'user_{self.user.id}'
        self.joined_groups = [self.user_group_name]

        # Entrar no grupo pessoal do usuário
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )

        # Entrar no grupo de todas as conversas do usuário
        chat_ids = await self.get_user_chat_ids(self.user)
        for chat_id in chat_ids:
            group_name = f'chat_{chat_id}'
            await self.channel_layer.group_add(group_name, self.channel_name)
            self.joined_groups.append(group_name)

        await self.accept()

    async def disconnect(self, close_code):
        # Sair de todos os grupos
        if hasattr(self, 'joined_groups'):
            for group_name in self.joined_groups:
                await self.channel_layer.group_discard(
                    group_name,
                    self.channel_name
                )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        chat_id = data.get('chatId')
        content = data.get('content', '').strip()
        
        if not chat_id or not content:
            return

        # Verificar se o usuário é participante do chat informado
        if not await self.is_participant(self.user, chat_id):
            return

        # Salvar mensagem no banco de dados e serializá-la
        message = await self.save_message(self.user, chat_id, content)

        # Enviar mensagem para todos no grupo da conversa
        await self.channel_layer.group_send(
            f'chat_{chat_id}',
            {
                'type': 'chat_message',
                'message': message
            }
        )

    async def chat_message(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': message
        }))

    async def chat_created(self, event):
        chat_data = event['chat']
        
        # Entrar dinamicamente no grupo da nova conversa
        new_group_name = f'chat_{chat_data["id"]}'
        await self.channel_layer.group_add(new_group_name, self.channel_name)
        if hasattr(self, 'joined_groups'):
            self.joined_groups.append(new_group_name)
            
        # Notificar o cliente sobre a nova conversa
        await self.send(text_data=json.dumps({
            'type': 'chat_created',
            'chat': chat_data
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
    def get_user_chat_ids(self, user):
        return list(Chat.objects.filter(Participants=user).values_list('id', flat=True))

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
