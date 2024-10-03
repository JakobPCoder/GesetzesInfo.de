from django.apps import AppConfig
from django.db.utils import OperationalError, ProgrammingError
from django.conf import settings

from dotenv import load_dotenv


class ApiAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api_app'
    load_dotenv()

    def ready(self):
        try:
 
            if getattr(settings, 'USE_TEST_DB', False):
                from .processing import populate_law_db
                populate_law_db()

        except (OperationalError, ProgrammingError):
            # Handle the case where the table doesn't exist yet
            pass
        