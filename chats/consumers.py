import json
import jwt

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatRoom, Message


User = get_user_model()

class chatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'

        #Authenticate user before accepting connection
        user = await self.authenticate_user()
        if user is None or user.is_anonymous:
            await self.close(code=4001)
            return
        
        # join room group 
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # send online status
        if self.scope['user'].is_authenticated:
            await self.update_user_online_status(True)

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        # update offline status
        if self.scope['user'].is_authenticated:
            await self.update_user_online_status(False)

    async def authenticate_user(self):
        #Authenticating user from token in query string or cookie
        #Trying to get token from query string 
        query_string = self.scope.get('query_string', b'').decode()
        token = None

        
        #Extracting token from query parameters
        if  'token=' in query_string:
            #handling case for multiple parameters
            params = query_string.split('&')
            for param in params:
                if param.startswith('token='):
                    token = param[6:]
                    break
        print("jwt : ", token)
        
        #If no token in query, try to get from cookies
        if not token:
            headers = dict(self.scope.get('headers', {}))
            if b'authorization' in headers:
                auth_header = headers[b'authorization'].decode()
                if auth_header.startswith('Bearer'):
                    token = auth_header[7:]
        
        if not token:
            return AnonymousUser()
        
        return await self.get_user_from_token(token)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type  = text_data_json.get('type')
        print("websocket message type: ",message_type)

        if message_type == "chat_message":
            await self.handle_chat_message(text_data_json)
        elif message_type == "typing":
            await self.handle_typing_indicator(text_data_json)
        elif message_type == "message_read":
            await self.handle_message_read(text_data_json)
        elif message_type  == 'typing_start':
            await self.handle_typing_indicator(True)
        elif message_type == 'typing_stop':
            await self.handle_typing_indicator(False)

        
    async def handle_chat_message(self, data):
        message_content = data['message']
        user = self.scope["user"]
        print("Message content and user: ",message_content, user)

        if user.is_authenticated:
            # save message to database
            print("started saving message")
            message = await self.save_message(user, message_content)
            
            print("message saved and broadcasting")
            # send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': await self.message_to_dict(message),
                    'sender_username': user.username,
                }
            )

    async def handle_typing_indicator(self, data):
        user = self.scope['user']
        if user.is_authenticated:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_indicator',
                    'user_id': str(user.id),
                    'username': user.username,
                    'is_typing': data['is_typing']
                }
            )

    async def handle_message_read(self, data):
        user = self.scope['user']
        message_id = data['message_id']

        if user.is_authenticated:
            await self.mark_message_as_read(user, message_id)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'message_read',
                    'message_id': message_id,
                    'user_id': str(user.id),
                    'username': user.username,
                }
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'sender_username': event['sender_username'],
        }))
        
    async def typing_indicator(self, event):
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user_id': event['user_id'],
            'username': event['username'],
            'is_typing': event['is_typing'],
        }))

    async def message_read(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message_read',
            'message_id': event['message_id'],
            'user_id': event['user_id'],
            'username': event['username'],
        }))

    @database_sync_to_async
    def get_user_from_token(self, token):
        #validating token and returning user object
        try:
            # print("token length: ", len(token))
            print("token type:", type(token))

            from django.conf import settings
            if isinstance(token, bytes):
                token = token.decode('utf-8')
            
            token.strip()
            if token.startswith('"') and token.endswith('"'):
                token = token[1:-1]

            print(f'Cleaned token: {token}')

            payload = jwt.decode(
                token,
                settings.SECRET_KEY, 
                algorithms=['HS256'],
                options={"verify_exp": True},
            )
            user_id = payload.get('user_id')
            print("Decoded user_id: ", user_id)
            if user_id:
                user = User.objects.get(id=user_id)
                print("Found user : ", user.username)
                return user

        except jwt.ExpiredSignatureError:
            print("Token expired")
        except jwt.DecodeError as e:
            print("Token decode error: ", e)
        except User.DoesNotExist:
            print("user does not exist")
        except Exception as e:
            print("Token validation error: ", e)
            #fallback for simple token validation ---> if simple token implementation
            try: 
                return
                return User.objects.get(auth_token=token)
            except User.DoesNotExist:
                pass #silent fail without screem

        return  AnonymousUser()

    @database_sync_to_async
    def update_user_online_status(self, is_online):
        user = User.objects.get(id=self.scope['user'].id)
        user.is_online = is_online
        user.save()

    @database_sync_to_async
    def mark_message_as_read(self, user, message_id):
        try:
            message = Message.objects.get(id=message_id)
            message.read_by.add(user)
        except Message.DoesNotExist:
            pass
    @database_sync_to_async
    def message_to_dict(self, message):
        return {
            'id': str(message.id),
            'content': message.content,
            'sender': {
                'id': str(message.sender.id),
                'username': message.sender.username,
                'avatar': message.sender.avatar.url if message.sender.avatar else None,

            },
            'created_at': message.created_at.isoformat(),
            'message_type': message.message_type,
        }

    @database_sync_to_async
    def save_message(self, user, content):
        room = ChatRoom.objects.get(id=self.room_id)
        print("Room for message: ", room)
        message = Message.objects.create(
            room=room,
            sender=user,
            content=content,
        )
        print("message created successfully: ", message)
        return message