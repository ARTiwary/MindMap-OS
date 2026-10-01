from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.db.redis import cache_get, cache_set, get_popular_nodes, get_recent_nodes
from app.models.enums import NodeType
from app.models.node import KnowledgeNode
from app.models.relationship import Relationship
from app.models.tag import Tag
from app.models.user import User

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("")
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cache_key = f"dashboard:user:{current_user.id}:summary"
    cached = await cache_get(cache_key)
    if cached:
        stats = cached
    else:
        total_nodes = (
            await db.execute(
                select(func.count()).where(KnowledgeNode.user_id == current_user.id)
            )
        ).scalar_one()

        total_connections = (
            await db.execute(
                select(func.count())
                .select_from(Relationship)
                .join(KnowledgeNode, KnowledgeNode.id == Relationship.source_node_id)
                .where(KnowledgeNode.user_id == current_user.id)
            )
        ).scalar_one()

        total_tags = (
            await db.execute(select(func.count()).where(Tag.user_id == current_user.id))
        ).scalar_one()

        total_projects = (
            await db.execute(
                select(func.count()).where(
                    KnowledgeNode.user_id == current_user.id,
                    KnowledgeNode.node_type == NodeType.PROJECT,
                )
            )
        ).scalar_one()

        total_favorites = (
            await db.execute(
                select(func.count()).where(
                    KnowledgeNode.user_id == current_user.id, KnowledgeNode.is_favorite.is_(True)
                )
            )
        ).scalar_one()

        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        growth_rows = (
            await db.execute(
                select(func.date(KnowledgeNode.created_at), func.count())
                .where(
                    KnowledgeNode.user_id == current_user.id,
                    KnowledgeNode.created_at >= thirty_days_ago,
                )
                .group_by(func.date(KnowledgeNode.created_at))
                .order_by(func.date(KnowledgeNode.created_at))
            )
        ).all()

        stats = {
            "total_nodes": total_nodes,
            "total_connections": total_connections,
            "total_tags": total_tags,
            "total_projects": total_projects,
            "total_favorites": total_favorites,
            "knowledge_density": round(total_connections / total_nodes, 2) if total_nodes else 0,
            "growth": [{"date": str(d), "count": c} for d, c in growth_rows],
        }
        await cache_set(cache_key, stats, ttl_seconds=300)

    recently_updated = (
        await db.execute(
            select(KnowledgeNode)
            .where(KnowledgeNode.user_id == current_user.id)
            .order_by(KnowledgeNode.updated_at.desc())
            .limit(5)
        )
    ).scalars().all()

    favorite_nodes = (
        await db.execute(
            select(KnowledgeNode)
            .where(KnowledgeNode.user_id == current_user.id, KnowledgeNode.is_favorite.is_(True))
            .order_by(KnowledgeNode.updated_at.desc())
            .limit(5)
        )
    ).scalars().all()

    recent_ids = await get_recent_nodes(str(current_user.id))
    popular = await get_popular_nodes(str(current_user.id))

    def brief(n: KnowledgeNode) -> dict:
        return {"id": str(n.id), "title": n.title, "node_type": n.node_type.value, "slug": n.slug}

    return {
        **stats,
        "recently_updated": [brief(n) for n in recently_updated],
        "favorites": [brief(n) for n in favorite_nodes],
        "recently_viewed_ids": recent_ids,
        "popular_node_ids": [{"node_id": nid, "views": score} for nid, score in popular],
    }
