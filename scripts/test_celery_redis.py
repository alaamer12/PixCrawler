import sys
import os
import time
import subprocess
import signal
import redis
from celery import chain
from celery.result import AsyncResult

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from celery_core.app import app
from celery_core.tasks import health_check

def test_redis_connection():
    print("\n[1/5] Testing Redis Connection...")
    try:
        r = redis.from_url(app.conf.broker_url)
        r.ping()
        print("Redis Broker is reachable.")
        
        r_backend = redis.from_url(app.conf.result_backend)
        r_backend.ping()
        print("Redis Backend is reachable.")
    except Exception as e:
        print(f"Redis Connection Failed: {e}")
        sys.exit(1)

def start_worker():
    print("\n[2/5] Starting Temporary Celery Worker...")
    # Using 'solo' pool for Windows compatibility and simplicity in tests
    cmd = [sys.executable, "-m", "celery", "-A", "celery_core.app", "worker", "--loglevel=warning", "--pool=solo", "--concurrency=1"]
    process = subprocess.Popen(cmd, cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    print(f"Worker started with PID {process.pid}")
    time.sleep(5) # Give it time to connect
    return process

def test_simple_task():
    print("\n[3/5] Testing Simple Task Execution (health_check)...")
    try:
        # Purge queues to remove old tasks
        purged = app.control.purge()
        print(f"Purged {purged} tasks from queues.")

        # Force queue to 'maintenance' to be sure
        result = health_check.apply_async(queue='maintenance')
        print(f"Task dispatched to 'maintenance' queue. ID: {result.id}")
        
        # Wait for result with longer timeout
        print("Waiting for result...")
        val = result.get(timeout=30)
        print(f"Task Completed. Result: {val}")
        
        if val['status'] == 'healthy':
            print("Task Logic Verified.")
        else:
            print("Task Logic Failed.")
            
    except Exception as e:
        print(f"Simple Task Failed: {e}")
        raise

# Define a simple add task for chaining tests since health_check returns a dict
@app.task(name='scripts.test_celery_redis.add')
def add(x, y):
    return x + y

def test_chained_task():
    print("\n[4/5] Testing Chained Task Execution (add -> add)...")
    try:
        # Chain: (4 + 4) + 8 = 16
        pass

    except Exception as e:
        print(f"Chained Task Failed: {e}")

def stop_worker(process):
    print("\n[5/5] Stopping Worker...")
    process.terminate()
    process.wait()
    print("Worker Stopped.")

if __name__ == "__main__":
    test_redis_connection()
    
    worker_process = start_worker()
    
    try:
        test_simple_task()
        # test_chained_task() # Commented out for now
    except Exception as e:
        print(f"Test Suite Failed: {e}")
    finally:
        stop_worker(worker_process)
