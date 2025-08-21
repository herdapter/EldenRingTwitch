import os
import json
import subprocess
from celery import shared_task
from django.db import transaction
from api.models import GameData

@shared_task
def analyze_save_file(file_path, session_code):
    try:
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}

        result = subprocess.run(
            ["erdb", "generate", "--file", file_path],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return {"error": f"ERDB failed: {result.stderr}"}

        data = json.loads(result.stdout)

        with transaction.atomic():
            GameData.objects.update_or_create(
                twitch_id=session_code,
                defaults=data
            )

        return {"success": True, "data": data}

    except Exception as e:
        return {"error": str(e)}

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
