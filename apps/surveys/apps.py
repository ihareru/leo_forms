from django.apps import AppConfig


class SurveysConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.surveys"
    label = "surveys"
    verbose_name = "Конструктор форм"

    def ready(self):
        from . import signals  # noqa: F401