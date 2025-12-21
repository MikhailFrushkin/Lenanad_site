# models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from urllib.parse import urlparse, urlunparse


class PageVisit(models.Model):
    user = models.ForeignKey(
        "users.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    session_key = models.CharField(max_length=40, db_index=True)
    url = models.URLField(max_length=500)  # URL без параметров
    full_url = models.URLField(max_length=1000)  # Полный URL с параметрами
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    referer = models.URLField(max_length=500, null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    method = models.CharField(max_length=10, default='GET')
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=['url', 'timestamp']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['session_key', 'timestamp']),
        ]
        verbose_name = 'Посещение страницы'
        verbose_name_plural = 'Посещения страниц'

    def __str__(self):
        return f"{self.url} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"