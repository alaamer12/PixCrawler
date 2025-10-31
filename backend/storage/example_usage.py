"""Example usage of the DataLakeBlobProvider.

Demonstrates basic upload, list, download, and delete operations.
"""
from dotenv import load_dotenv
from storage_settings import StorageSettings
from datalake_blob_provider import DataLakeBlobProvider


def main() -> None:
    """Run a simple end-to-end demonstration."""
    load_dotenv()
    settings = StorageSettings.from_env()
    provider = DataLakeBlobProvider(settings)

    # Upload bytes
    r1 = provider.upload_blob("example.txt", b"hello from provider", overwrite=True)
    print("upload:", r1)

    # List blobs
    blobs = provider.list_blobs(prefix="example")
    print("list:", blobs)

    # Download
    content = provider.download_blob("example.txt")
    print("download:", content)

    # Download to file
    provider.download_to_file("example.txt", "./out/example.txt")

    # Delete
    ok = provider.delete_blob("example.txt")
    print("delete:", ok)


if __name__ == "__main__":
    main()
