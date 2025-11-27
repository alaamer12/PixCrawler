import sys
import os

# Add the current directory to sys.path
sys.path.append(os.getcwd())

try:
    from celery_core.app import get_celery_app
    app = get_celery_app()
    
    print(f"Broker URL: {app.conf.broker_url}")
    print(f"Result Backend: {app.conf.result_backend}")
    
    print("\nRegistered Tasks:")
    tasks = list(app.tasks.keys())
    tasks.sort()
    for task in tasks:
        if not task.startswith('celery.'):
            print(f"- {task}")
            
    # Check for specific tasks
    expected_tasks = [
        'celery_core.health_check',
        'celery_core.cleanup_expired_results'
    ]
    
    missing = [t for t in expected_tasks if t not in tasks]
    
    if missing:
        print(f"\nERROR: Missing expected tasks: {missing}")
        sys.exit(1)
    else:
        print("\nSUCCESS: All expected core tasks found.")
        
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
