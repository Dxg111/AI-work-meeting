from pathlib import Path
from fastapi import UploadFile
from config import settings

class StorageService:
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.public_base_url = settings.PUBLIC_BASE_URL
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    async def save_upload_file(self, file: UploadFile, meeting_id: int):
        unique_filename = f"{meeting_id}_{file.filename}"
        file_path = self.upload_dir / unique_filename
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        file_url = f"{self.public_base_url}/uploads/{unique_filename}"
        return str(file_path), file_url
    
    def check_public_url_accessibility(self):
        if "127.0.0.1" in self.public_base_url or "localhost" in self.public_base_url:
            return False, "localhost"
        return True, "OK"

storage_service = StorageService()
