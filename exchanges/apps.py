from django.apps import AppConfig


class ExchangesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "exchanges"

    def ready(self) -> None:
        from exchanges import signals  # noqa: F401
