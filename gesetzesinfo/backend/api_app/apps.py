from django.apps import AppConfig
from django.db.utils import OperationalError, ProgrammingError
from django.conf import settings

class ApiAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api_app'

    def ready(self):
        try:
            from .models import populate_test_laws
            if getattr(settings, 'USE_TEST_DB', False):
                populate_test_laws()
        except (OperationalError, ProgrammingError):
            # Handle the case where the table doesn't exist yet
            pass
        