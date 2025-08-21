from rest_framework import status
from .serializer import *
from rest_framework.views import APIView
from rest_framework.response import Response
import tempfile
import os

# Import de ta task Celery
from .tasks import analyze_save_file

class TwitchSessionView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = TwitchSessionSerializer(data=request.data)
        if serializer.is_valid():
            twitch_session = serializer.save()
            return Response(
                TwitchSessionSerializer(twitch_session).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GameDataView(APIView):

    def get(self, request, session_code, *args, **kwargs):
        game_data = GameData.objects.filter(
            twitch_id__code=session_code
        )

        if not game_data:
            return Response(
                {"detail": "No game data found for this session."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = GameDataSerializer(game_data)
        return Response(serializer.data)

class UploadSaveView(APIView):
    def post(self, request, session_code, *args, **kwargs):

        if 'file' not in request.FILES:
            return Response({"detail": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        uploaded_file = request.FILES['file']

        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, uploaded_file.name)

        with open(temp_path, 'wb+') as temp_file:
            for chunk in uploaded_file.chunks():
                temp_file.write(chunk)

        analyze_save_file.delay(temp_path, session_code)

        return Response({"detail": "File received and analysis started"}, status=status.HTTP_202_ACCEPTED)
