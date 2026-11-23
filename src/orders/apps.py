"""App module for the `orders` app.

Entry-point for Django app introspection and metadata configuration.
"""

from django.apps import AppConfig


class OrdersConfig(AppConfig):
    """Configuration for the `orders` Django app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "orders"

    def ready(self) -> None:
        # Implicitly connect signal handlers decorated with @receiver.
        from orders import signals  # noqa: F401

