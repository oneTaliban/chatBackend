from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, UserProfile, LoginHistory

class UserProfileSerializer(serializers.ModelSerializer): 
    class Meta:
        model = UserProfile
        fields = '__all__'
        read_only_fields = ('user',)

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name',
                  'avatar', 'bio', 'is_online', 'last_seen', 'profile'
                  )
        read_only_fields = ('id', 'is_online', 'last_seen')

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password_confirm',
                  'first_name', 'last_name', )
        
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']: 
            raise serializers.ValidationError({"password_confirm":  "Passwords did not match"})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        UserProfile.objects.create(user=user)
        return user
    
class LoginHIstorySerializer(serializers.Serializer):
    class Meta:
        model = LoginHistory
        fields = [
            'ip_address', 'user_agent', 'timestamp', 'success',
        ]

class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

class PasswordResetConfirmationSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True, validators=[validate_password])
    token = serializers.CharField(required=True)