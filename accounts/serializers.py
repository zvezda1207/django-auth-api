import bcrypt
from rest_framework import serializers
from .models import User
from access_control.models import Role

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_repeat = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'middle_name', 'email', 'password', 'password_repeat']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_repeat']:
            raise serializers.ValidationError('Passwords do not match')
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data.pop('password_repeat')

        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        role = Role.objects.filter(name='user').first()
        if not role:
            raise serializers.ValidationError(
                'Role "user" not found. Please run: python manage.py init_test_data'
            )

        user = User.objects.create(
            password_hash=password_hash,
            role=role,
            **validated_data
        )
        return user

class UserSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'middle_name', 'email', 'is_active', 'role', 'role_name']
        read_only_fields = ['id', 'role', 'role_name']

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

