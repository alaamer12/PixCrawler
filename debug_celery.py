import sys
import os
import importlib

sys.path.append(os.getcwd())

print(f"CWD: {os.getcwd()}")
print(f"Sys Path: {sys.path}")

try:
    import celery_core
    print(f"Imported celery_core: {celery_core}")
    print(f"celery_core file: {celery_core.__file__}")
except ImportError as e:
    print(f"Failed to import celery_core: {e}")

try:
    import celery_core.tasks
    print(f"Imported celery_core.tasks: {celery_core.tasks}")
except ImportError as e:
    print(f"Failed to import celery_core.tasks: {e}")

from celery_core.app import get_celery_app
app = get_celery_app()
print(f"App tasks keys: {list(app.tasks.keys())}")
