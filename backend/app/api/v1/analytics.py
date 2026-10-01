from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.node import KnowledgeNode
from app.models.relationship import Relationship
from app.models.tag import NodeTag, Tag
from app.models.user import User

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/most-connected")
async def most_connected_nodes(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Nodes ranked by total degree (incoming + outgoing relationships)."""
    src = select(
        Relationship.source_node_id.label("node_id"), func.count().label("cnt")
    ).group_by(Relationship.source_node_id).subquery()
    tgt = select(
        Relationship.target_node_id.label("node_id"), func.count().label("cnt")
    ).group_by(Relationship.target_node_id).subquery()

    combined = select(
        KnowledgeNode.id,
        KnowledgeNode.title,
        (func.coalesce(src.c.cnt, 0) + func.coalesce(tgt.c.cnt, 0)).label("degree"),
    ).select_from(KnowledgeNode).outerjoin(src, src.c.node_id == KnowledgeNode.id).outerjoin(
        tgt, tgt.c.node_id == KnowledgeNode.id
    ).where(KnowledgeNode.user_id == current_user.id).order_by(
        (func.coalesce(src.c.cnt, 0) + func.coalesce(tgt.c.cnt, 0)).desc()
    ).limit(limit)

    rows = (await db.execute(combined)).all()
    return [
        {"node_id": str(node_id), "title": title, "connections": int(degree)}
        for node_id, title, degree in rows
        if degree
    ]


@router.get("/tags")
async def tag_statistics(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    query = (
        select(Tag.name, Tag.color, func.count(NodeTag.node_id).label("usage"))
        .join(NodeTag, NodeTag.tag_id == Tag.id, isouter=True)
        .where(Tag.user_id == current_user.id)
        .group_by(Tag.id)
        .order_by(func.count(NodeTag.node_id).desc())
    )
    rows = (await db.execute(query)).all()
    return [{"name": n, "color": c, "usage": u} for n, c, u in rows]


@router.get("/growth")
async def growth_over_time(
    interval: str = "day",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    trunc = func.date_trunc(interval, KnowledgeNode.created_at)
    query = (
        select(trunc.label("bucket"), func.count())
        .where(KnowledgeNode.user_id == current_user.id)
        .group_by(trunc)
        .order_by(trunc)
    )
    rows = (await db.execute(query)).all()
    return [{"period": bucket.isoformat(), "count": count} for bucket, count in rows]
