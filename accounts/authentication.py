from jwt import InvalidTokenError, ExpiredSignatureError
from rest_framework import authentication

from .models import User, BlacklistedToken
from config.jwt_utils import decode_access_token


class JWTAuthentication(authentication.BaseAuthentication):
    """
    DRF-аутентификация по заголовку Authorization: Bearer <token>.
    Без этого класса DRF перезаписывает request.user в AnonymousUser.
    """
    keyword = 'Bearer'

    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION') or ''
        if not auth_header.strip():
            return None

        parts = auth_header.split(None, 1)
        if len(parts) != 2 or parts[0] != self.keyword:
            return None

        token = parts[1].strip()
        if not token:
            return None

        try:
            payload = decode_access_token(token)
        except (ExpiredSignatureError, InvalidTokenError):
            return None

        # Logout для JWT: если токен в blacklist — считаем пользователя неаутентифицированным
        if BlacklistedToken.objects.filter(token=token).exists():
            return None

        user_id = payload.get('user_id')
        if user_id is None:
            return None

        try:
            user = User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            return None

        return (user, token)
