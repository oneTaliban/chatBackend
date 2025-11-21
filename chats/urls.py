from django.urls import path
from . import views

urlpatterns = [
    path('rooms/', views.ChatRoomListCreateView.as_view(), name='room-list') ,
    path('rooms/<uuid:pk>/', views.ChatRoomDetailView.as_view(), name='room-detail') ,
    path('rooms/<uuid:room_id>/messages/', views.MessageListCreateView.as_view(), name='message-list'),
    path('messages/<uuid:message_id>/read/',views.mark_message_read, name='mark-read'),
    path('messages/<uuid:message_id>/like/', views.like_message, name='like-message'),
]