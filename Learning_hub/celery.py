import os
from pathlib import Path
from celery import Celery

# Load .env file BEFORE Django settings
from dotenv import load_dotenv
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(env_path, override=True)

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Learning_hub.settings')

app = Celery('Learning_hub')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Import tasks from core modules (not in Django apps)
from core import cdn_helper  # This will register the BunnyService tasks

# Ensure shared_task uses this app
from celery import current_app
current_app.set_default()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')