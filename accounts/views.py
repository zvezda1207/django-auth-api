import json
import bcrypt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import User
from .serializers import RegisterSerializer, UserSerializer, LoginSerializer
from config.jwt_utils import create_access_token
from config.jwt_utils import decode_access_token
from jwt import InvalidTokenError
from .models import BlacklistedToken
from datetime import datetime, timezone


def _get_login_data(request):
    """Достаём email и password из тела (JSON) или из form-data."""
    # 1) Уже распарсенные данные (DRF request.data при application/json)
    data = getattr(request, 'data', None) or {}
    if isinstance(data, dict) and data.get('email') is not None and data.get('password') is not None:
        return data
    # 2) Сырое тело (JSON)
    body = getattr(request, 'body', None)
    if body:
        try:
            parsed = json.loads(body.decode('utf-8'))
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass
    # 3) Form-data / x-www-form-urlencoded (request.POST)
    post = getattr(request, 'POST', None)
    if post and post.get('email') and post.get('password'):
        return {'email': post['email'], 'password': post['password']}
    return data if isinstance(data, dict) else {}

class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    def post(self, request):
        data = _get_login_data(request)
        serialiser = LoginSerializer(data=data)
        if not serialiser.is_valid():
            return Response(
                serialiser.errors,
                status=status.HTTP_400_BAD_REQUEST,
                content_type='application/json',
            )

        email = serialiser.validated_data['email']
        password = serialiser.validated_data['password']

        try:
            user = User.objects.get(email=email, is_active=True)
        except User.DoesNotExist:
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        token = create_access_token(user.id)
        return Response({'access_token': token})

class LogoutView(APIView):
    """
    Logout для JWT:
    - добавляем текущий access token в blacklist
    - после этого запросы с этим токеном будут получать 401
    """
    def post(self, request):
        if not _is_authenticated_user(request):
            return Response({'detail': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

        token = getattr(request, "auth", None)
        if not token:
            return Response({'detail': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            payload = decode_access_token(token)
        except InvalidTokenError:
            return Response({'detail': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

        exp = payload.get("exp")
        # exp может быть datetime (PyJWT умеет такое), но чаще это timestamp
        if isinstance(exp, (int, float)):
            expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
        elif isinstance(exp, datetime):
            expires_at = exp
        else:
            # на всякий случай: если exp нет, ставим "сейчас"
            expires_at = datetime.now(timezone.utc)

        BlacklistedToken.objects.get_or_create(
            token=token,
            defaults={"expires_at": expires_at},
        )
        return Response({'detail': 'Logged out'}, status=status.HTTP_200_OK)


def _is_authenticated_user(request):
    """Пользователь залогинен только если это наша модель User (не AnonymousUser)."""
    return isinstance(getattr(request, 'user', None), User)


class MeView(APIView):
    def get(self, request):
        if not _is_authenticated_user(request):
            return Response({'detail': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(UserSerializer(request.user).data)

    def put(self, request):
        if not _is_authenticated_user(request):
            return Response({'detail': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        serializer = UserSerializer(request.user, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        if not _is_authenticated_user(request):
            return Response({'detail': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteMeView(APIView):
    def delete(self, request):
        if not _is_authenticated_user(request):
            return Response({'detail': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        user = request.user
        user.is_active = False
        user.save()
        return Response({'detail': 'Account deactivated'}, status=status.HTTP_200_OK)


        

