from rest_framework import serializers
from .models import *

class TwitchSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TwitchSession
        fields = '__all__'


class GameDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameData
        fields = ['map_discovered', 'bosses_defeated']
