from django.apps import AppConfig


class LogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "systems.log"
    verbose_name = "日志管理"
