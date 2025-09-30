import os
from fastapi import FastAPI, UploadFile, File
from storage.factory import get_storage_provider

app = FastAPI()
storage = get_storage_provider()

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    destination = f"uploads/{file.filename}"
    with open(file.filename, "wb") as buffer:
        buffer.write(await file.read())
    storage.upload(file.filename, destination)
    os.remove(file.filename)
    return {"message": "Uploaded successfully", "path": destination}

@app.get("/download")
def download_file(path: str):
    destination = f"downloaded_{os.path.basename(path)}"
    storage.download(path, destination)
    return {"message": "Downloaded", "saved_as": destination}

@app.delete("/delete")
def delete_file(path: str):
    storage.delete(path)
    return {"message": "Deleted"}

@app.get("/list")
def list_files():
    return storage.list_files()

@app.get("/url")
def presigned_url(path: str):
    return {"url": storage.generate_presigned_url(path)}
