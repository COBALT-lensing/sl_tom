from django.apps import AppConfig


class ZooniverseConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "zooniverse"

    def nav_items(self):
        return [{"partial": "zooniverse/partials/navbar_link.html"}]
