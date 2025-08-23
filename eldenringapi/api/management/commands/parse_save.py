import os
import json
from django.core.management.base import BaseCommand, CommandError
from eldenringapi.api.tasks import analyze_save_file
from eldenringapi.api.models import GameData, TwitchSession


class Command(BaseCommand):
    help = "Parse an Elden Ring save file via Celery task and print result"

    def add_arguments(self, parser):
        parser.add_argument("file_path", type=str, help="Path to ER save file (.sl2)")
        parser.add_argument(
            "--session",
            dest="session_code",
            default="local-test",
            help="Twitch session code to attach parsed data",
        )
        parser.add_argument(
            "--sync",
            action="store_true",
            help="Run synchronously (call task directly) instead of queueing",
        )
        parser.add_argument(
            "--json",
            action="store_true",
            help="Print JSON output (sync: parsed GameData; async: task id only)",
        )

    def handle(self, *args, **options):
        file_path = options["file_path"]
        session_code = options["session_code"]
        run_sync = options.get("sync", False)
        want_json = options.get("json", False)

        if not os.path.exists(file_path):
            raise CommandError(f"File not found: {file_path}")

        if run_sync:
            result = analyze_save_file.apply(args=[file_path, session_code]).get()
            if isinstance(result, dict) and result.get("error"):
                raise CommandError(result["error"])

            if want_json:
                try:
                    session = TwitchSession.objects.get(code=session_code)
                    gd = GameData.objects.filter(twitch_id=session).order_by("-last_updated").first()
                    payload = {
                        "session": session_code,
                        "map_discovered": gd.map_discovered if gd else {},
                        "bosses_defeated": gd.bosses_defeated if gd else {},
                    }
                    self.stdout.write(json.dumps(payload))
                except Exception as e:
                    raise CommandError(str(e))
            else:
                self.stdout.write(self.style.SUCCESS("Parsed successfully (sync)"))
        else:
            async_result = analyze_save_file.delay(file_path, session_code)
            if want_json:
                self.stdout.write(json.dumps({"task_id": async_result.id, "session": session_code}))
            else:
                self.stdout.write(
                    self.style.SUCCESS(f"Task queued: {async_result.id}. Check worker logs for output.")
                )
