from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "eldenringapi.api"

    def ready(self):
        # Ensure tasks are imported
        from . import tasks  # noqa: F401
