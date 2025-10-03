import os
from dotenv import load_dotenv

from storage_abstraction import StorageManager, Tier


if __name__ == "__main__":
    load_dotenv()  # optional

    # Configure via env; defaults to LOCAL under ./storage_data in dev
    # Example overrides:
    # os.environ["STORAGE_ENV"] = "dev"
    # os.environ["STORAGE_HOT_PROVIDER"] = "local"  # memory | local | s3
    # os.environ["LOCAL_BASE_PATH"] = "./storage_data"

    mgr = StorageManager.from_env()

    key = "hello/demo.txt"
    data = b"Hello storage layers!"

    # Put in HOT tier
    mgr.put(Tier.HOT, key, data, content_type="text/plain")

    # Read back
    got = mgr.get(Tier.HOT, key)
    print("Read:", got)

    # List
    print("List HOT:", list(mgr.list(Tier.HOT, prefix="hello/")))

    # URL (may be None for local without public URL)
    print("URL:", mgr.url(Tier.HOT, key))

    # Cleanup
    mgr.delete(Tier.HOT, key)
    print("Exists after delete:", mgr.exists(Tier.HOT, key))
