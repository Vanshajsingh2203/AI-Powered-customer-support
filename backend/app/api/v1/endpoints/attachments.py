
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies import get_current_user
from app.models.ticket import Ticket
from app.models.user import User
from app.services.attachment_service import AttachmentService


router = APIRouter(tags=["Attachments"])

attachment_service = AttachmentService()


# --------------------------------------------------
# Helper: Check whether the user can access the ticket
# --------------------------------------------------

async def get_accessible_ticket(
    ticket_id: UUID,
    current_user: User,
    db: AsyncSession
) -> Ticket:

    result = await db.execute(
        select(Ticket).where(Ticket.id == ticket_id)
    )

    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    # Customer can access only their own tickets
    if current_user.role == "CUSTOMER":

        if ticket.customer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found"
            )

    # Agent can access only tickets assigned to them
    elif current_user.role == "AGENT":

        if ticket.assigned_agent_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found"
            )

    # Admin can access all tickets
    elif current_user.role != "ADMIN":

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return ticket


# --------------------------------------------------
# Route: Upload attachment
# --------------------------------------------------

@router.post(
    "/tickets/{ticket_id}/attachments",
    status_code=status.HTTP_201_CREATED
)
async def upload_attachment(
    ticket_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    file_path = None

    try:

        # 1. Verify ticket access
        await get_accessible_ticket(
            ticket_id=ticket_id,
            current_user=current_user,
            db=db
        )

        # 2. Validate file extension
        extension = attachment_service.validate_file_extension(
            file.filename or ""
        )

        # 3. Validate actual file size
        file_size = await attachment_service.validate_file_size(file)

        # 4. Save physical file to disk
        file_metadata = await attachment_service.save_file(
            file=file,
            ticket_id=ticket_id,
            extension=extension,
            file_size=file_size
        )

        file_path = file_metadata["file_path"]

        # 5. Create attachment record in PostgreSQL
        attachment = await attachment_service.create_attachment_record(
            db=db,
            ticket_id=ticket_id,
            uploaded_by=current_user.id,
            file_metadata=file_metadata
        )

        # 6. Commit database transaction
        await db.commit()

        await db.refresh(attachment)

        # 7. Return attachment metadata
        return {
            "id": attachment.id,
            "ticket_id": attachment.ticket_id,
            "file_name": attachment.file_name,
            "content_type": attachment.content_type,
            "file_size": attachment.file_size,
            "uploaded_by": attachment.uploaded_by,
            "created_at": attachment.created_at,
        }

    except Exception:

        await db.rollback()

        # Clean up physical file if database operation fails
        if file_path:
            attachment_service.delete_file(file_path)

        raise

    finally:
        await file.close()

