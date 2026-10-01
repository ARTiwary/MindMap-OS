from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.activity import Activity
from app.models.user import User

router = APIRouter(prefix="/activity", tags=["Activity"])


@router.get("")
async def list_activity(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=30, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Activity)
        .where(Activity.user_id == current_user.id)
        .order_by(Activity.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    rows = (await db.execute(query)).scalars().all()
    return [
        {
            "id": str(a.id),
            "action": a.action.value,
            "summary": a.summary,
            "node_id": str(a.node_id) if a.node_id else None,
            "created_at": a.created_at.isoformat(),
        }
        for a in rows
    ]
