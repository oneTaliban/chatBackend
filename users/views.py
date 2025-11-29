from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout

from .models import User , UserProfile, LoginHistory
from .serializers import UserSerializer, UserRegistrationSerializer, LoginHIstorySerializer

from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        print(request.data)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)

#         UserProfile.objects.create(user=user)

        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'payload': 'user registration successful'
        }, status=status.HTTP_201_CREATED)

class LoginHistoryView(generics.ListAPIView):
    serializer_class = LoginHIstorySerializer

    def get_queryset(self):
        return LoginHistory.objects.filter(user=self.request.user)[:10]

@api_view(["post"])
@permission_classes([permissions.AllowAny])
def login_view(request):
    username = request.data.get('username', '')
    password = request.data.get('password', '')

    user = authenticate(username=username, password=password)

    if user is not None:
        refresh =  RefreshToken.for_user(user)
        user.is_online=True
        user.save()

        LoginHistory.objects.create(
            user=user,
            ip_address = get_client_ip(request),
            user_agent = request.META.get('HTTP_USER_AGENT', ''),
            success =True
        )

        login(request, user)

        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })
    
    else:
        #tracking failed login attempt
        try:
            user = User.objects.get(username=username)
            LoginHistory.objects.create(
                user=user,
                ip_address = get_client_ip(request),
                user_agent = request.META.get('HTTP_USER_AGENT', ''),
                success = False
            )
        except User.DoesNotExist:
            pass
    
    return Response({'error': "Invalid Credentials", }, status=status.HTTP_401_UNAUTHORIZED)

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class=UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
    
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    logout(request)
    request.user.is_online = False
    request.user.save()
    return Response({"message": "Successfully logged out"})

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip