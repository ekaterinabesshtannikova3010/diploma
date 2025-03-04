from rest_framework import serializers
from .models import User, InviteCode
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'phone_number', 'invite_code']

class InviteCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = InviteCode
        fields = ['id', 'code', 'is_active', 'users']



class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Добавление пользовательских полей в токен
        token['username'] = user.username
        token['phone_number'] = user.phone_number

        return token

class AuthSerializer(serializers.Serializer):
    phone_number = serializers.CharField(required=True)
    name = serializers.CharField(required=True)