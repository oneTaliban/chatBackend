from django.shortcuts import render
from django.db.models import Q

from rest_framework import generics, status, permissions
from rest_framework.decorators import permission_classes, api_view
from rest_framework.response import Response

from .models import ChatRoom, Message 
from .serializers import ChatRoomSerializer, MessageSerializer, RoomParticipantsSerializer

class ChatRoomListCreateView(generics.ListCreateAPIView):
    serializer_class= ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # return ChatRoom.objects.all()
        return ChatRoom.objects.filter(
            Q(participants=self.request.user) |
            Q(room_type='channel',is_private=False)
        ).distinct()
    
    def perform_create(self, serializer):
        room = serializer.save(created_by=self.request.user) 
        room.participants.add(self.request.user)

class ChatRoomDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ChatRoom.objects.filter(participants=self.request.user)

class MessageListCreateView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        room_id = self.kwargs['room_id']
        print(room_id)
        return Message.objects.filter(room_id=room_id, room__participants = self.request.user) 
    
    def perform_create(self, serializer):
        print("creating message")
        room = ChatRoom.objects.get(id=self.kwargs['room_id'])
        print(room)
        message = serializer.save(sender=self.request.user, room=room)
        print(message)
        # mark message as read by sender
        message.read_by.add(self.request.user)

@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def mark_message_read(request, message_id):
    try:
        message = Message.objects.get(id=message_id, room__participants = request.user)
        message.read_by.add(request.user)
        return Response({'status': 'success'})
    except Message.DoesNotExist:
        return Response({'error': 'Message not found'}, status=status.HTTP_404_NOT_FOUND)
    
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def like_message(request, message_id):
    try:
        message = Message.objects.get(id=message_id, room__participants=request.user)
        if message.likes.filter(id=request.user.id).exists():
            message.likes.remove(request.user)
            liked = False
        else:
            message.likes.add(request.user)
            liked = True

        return Response({'liked': liked, 'likes_count': message.likes.count()})    
    except Message.DoesNotExist:
        return Response({'error': 'Message not found'}, status=status.HTTP_404_NOT_FOUND)
    
    