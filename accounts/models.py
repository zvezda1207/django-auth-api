from django.db import models
from access_control.models import Role


class User(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(unique=True)

    password_hash = models.CharField(max_length=250)
    is_active = models.BooleanField(default=True)

    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='users')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email  
        

class BlacklistedToken(models.Model):
    """
    Токены, которые были "разлогинены" (инвалидированы).
    """
    token = models.TextField(unique=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"BlacklistedToken(expires_at={self.expires_at})"

