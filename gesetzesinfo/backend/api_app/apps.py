from django.apps import AppConfig
from dotenv import load_dotenv

class ApiAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api_app'

    def ready(self) -> None:
        load_dotenv(override=True)
        return super().ready()
    
