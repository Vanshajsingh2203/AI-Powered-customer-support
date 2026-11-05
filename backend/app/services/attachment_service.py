import uuid
import shutil
from pathlib import Path

from fastapi import UploadFile, HTTPException, status
import aiofiles
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.attachment import Attachment
from app.services.notification_service import notification_service

BACKEND_DIR = Path(__file__).resolve().parents[2]

UPLOAD_DIR = BACKEND_DIR / "uploads" / "tickets"

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".txt",
}

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

class AttachmentService:
    
    def validate_file_extension(self, filename:str)->str:
        extension = Path(filename).suffix.lower()
        
        if extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File type not allowed"
            )
            
        return extension 
    
    async def validate_file_size(self, file: UploadFile) -> int:
        total_size = 0

        while chunk := await file.read(1024 * 1024):
            total_size += len(chunk)

            if total_size > MAX_FILE_SIZE:
                await file.seek(0)

                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="File size exceeds the 5 MB limit"
                )

        await file.seek(0)

        return total_size
    
    async def save_file(
        self,
        file: UploadFile,
        ticket_id: uuid.UUID,
        extension: str,
        file_size: int
) -> dict:
        ticket_dir = UPLOAD_DIR / str(ticket_id)
        ticket_dir.mkdir(parents=True, exist_ok=True)

        stored_filename = f"{uuid.uuid4()}{extension}"
        file_path = ticket_dir / stored_filename

        try:
            async with aiofiles.open(file_path, "wb") as buffer:
                while chunk := await file.read(1024 * 1024):
                    await buffer.write(chunk)

        except Exception:
            if file_path.exists():
                file_path.unlink()
            raise

        finally:
            await file.seek(0)

        return {
            "file_name": Path(file.filename).name,
            "stored_filename": stored_filename,
            "file_path": str(file_path),
            "content_type": file.content_type or "application/octet-stream",
            "file_size": file_size,
        }
        
    async def create_attachment_record(
        self,
        db: AsyncSession,
        ticket_id: uuid.UUID,
        uploaded_by: uuid.UUID,
        file_metadata: dict,
        message_id: uuid.UUID | None = None,
) -> Attachment:

        attachment = Attachment(
        ticket_id=ticket_id,
        message_id=message_id,
        uploaded_by=uploaded_by,
        file_name=file_metadata["file_name"],
        stored_filename=file_metadata["stored_filename"],
        file_path=file_metadata["file_path"],
        content_type=file_metadata["content_type"],
        file_size=file_metadata["file_size"],
    )

        db.add(attachment)

        await db.flush()

        return attachment
    
    def delete_file(self, file_path: str) -> None:
        path = Path(file_path)

        if path.exists() and path.is_file():
            path.unlink()