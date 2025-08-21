from django.db import models

class TwitchSession(models.Model):
    code = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

class GameData(models.Model):
    twitch_id = models.ForeignKey(TwitchSession, on_delete=models.CASCADE)
    map_discovered= models.JSONField(encoder=None, decoder=None)
    bosses_defeated = models.JSONField(encoder=None, decoder=None)
    last_updated = models.DateTimeField(auto_now_add=True)
