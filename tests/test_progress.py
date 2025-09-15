import threading
import time
from threading import Lock

# Counter without locks (unsafe)
class Counter:
    def __init__(self):
        self.count = 0

    def increment(self, offset):
        # Artificial delay to trigger race condition
        temp = self.count
        time.sleep(0.0001)   # force thread switch
        self.count = temp + offset


# Counter with locks (safe)
class LockingCounter:
    def __init__(self):
        self.count = 0
        self.lock = Lock()

    def increment(self, offset):
        with self.lock:  # protect critical section
            temp = self.count
            time.sleep(0.0001)  # same delay, but safe
            self.count = temp + offset


def run_threads(counter, num_threads=10, iterations=1000):
    threads = []

    def worker():
        for _ in range(iterations):
            counter.increment(1)

    for _ in range(num_threads):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()


if __name__ == "__main__":
    NUM_THREADS = 10
    ITERATIONS = 1000
    EXPECTED = NUM_THREADS * ITERATIONS

    print("\n--- Demonstrating Race Condition (No Lock) ---")
    counter = Counter()
    run_threads(counter, NUM_THREADS, ITERATIONS)
    print(f"Expected count: {EXPECTED}")
    print(f"Final count without lock: {counter.count}\n")

    print("--- Fixing with Lock ---")
    safe_counter = LockingCounter()
    run_threads(safe_counter, NUM_THREADS, ITERATIONS)
    print(f"Expected count: {EXPECTED}")
    print(f"Final count with lock: {safe_counter.count}\n")

    print("Observation:")
    print(" - Without lock: The final result is often smaller than expected due to lost updates.")
    print(" - With lock: The result always matches the expected value.")
