from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings

import uuid



class ChatRoom(models.Model):
    ROOM_TYPES = (
        ('direct', 'Direct Message'),
        ('group', 'Group Chat'),
        ('channel', 'Channel'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description  = models.TextField(blank=True)
    room_type = models.CharField(max_length=10, choices=ROOM_TYPES, default='direct')
    created_by  = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='created_rooms', blank=True)
    participants = models.ManyToManyField('users.User', related_name='chat_rooms', blank=True)
    is_private = models.BooleanField(default=False)
    max_participants  = models.IntegerField(default=100)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f'{self.name} {self.room_type}'


class Message(models.Model):
    MESSAGE_TYPES = (
        ('text', 'Text'),
        ('image', 'Image'),
        ('file', 'File'),
        ('system', 'System'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    file = models.FileField(upload_to='chat_files/', blank=True, null=True)

    # Reactions
    likes = models.ManyToManyField('users.User', related_name='liked_messages', blank=True )
    reactions = models.JSONField(default=dict) #stores emoji reactions

    # read receipts
    read_by = models.ManyToManyField('users.User', related_name='read_messages', blank=True)

    # edit history
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(auto_now=True)

    # reply functonality
    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True, related_name='replies')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.sender.username}: {self.content[:50]}'
    


class RoomParticipant(models.Model):
    
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('moderator', 'Moderator'),
        ('member', 'Member'),
    )
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)
    is_banned = models.BooleanField(default=False)

    class Meta: 
        unique_together  = ['user', 'room']

    def __str__(self):
        return f'{self.user.username} in {self.room.name}'
