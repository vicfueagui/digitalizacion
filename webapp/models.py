from django.conf import settings
from django.db import models


class DeskPreferences(models.Model):
    """Preferencias personales en acceso.sqlite3; sin FK hacia los expedientes."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    favorites = models.JSONField(default=list)
    layout = models.JSONField(default=dict)
    updated = models.DateTimeField(auto_now=True)
