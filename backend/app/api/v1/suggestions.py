from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.services.suggestion_service import suggest_connections

router = APIRouter(prefix="/suggestions", tags=["Suggestions"])


@router.get("/connections")
async def get_connection_suggestions(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await suggest_connections(db, current_user.id, limit)
