from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog

class AuditService:
    
    async def create_log(self, db:AsyncSession, user_id: UUID|None , ticket_id:UUID|None, action:str, old_value:dict|None, new_value:dict|None, details:dict|None=None)->AuditLog:
        audit_log = AuditLog(
            user_id=user_id,
            ticket_id=ticket_id,
            action=action,
            old_value=old_value,
            new_value=new_value,
            details=details,
        )
        
        db.add(audit_log)
        
        await db.flush()
        
        return audit_log
    
audit_service = AuditService()