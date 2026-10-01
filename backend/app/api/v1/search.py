import math

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.db.redis import cache_get, cache_set
from app.models.node import KnowledgeNode
from app.models.resource import Resource
from app.models.tag import NodeTag, Tag
from app.models.user import User
from app.schemas.node import NodeListResponse, NodeOut

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("", response_model=NodeListResponse)
async def search(
    q: str = Query(min_length=1),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cache_key = f"search:{current_user.id}:{q.lower()}:{page}:{limit}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    # PostgreSQL full-text search across title/description/content, plus
    # matches on tag name and resource title/url via EXISTS subqueries.
    tsquery = func.plainto_tsquery("english", q)
    fts_vector = func.to_tsvector(
        "english",
        func.coalesce(KnowledgeNode.title, "")
        + " "
        + func.coalesce(KnowledgeNode.description, "")
        + " "
        + func.coalesce(KnowledgeNode.content, ""),
    )

    tag_match = (
        select(NodeTag.node_id)
        .join(Tag, Tag.id == NodeTag.tag_id)
        .where(Tag.name.ilike(f"%{q}%"))
    )
    resource_match = select(Resource.node_id).where(
        or_(Resource.title.ilike(f"%{q}%"), Resource.url.ilike(f"%{q}%"))
    )

    query = select(KnowledgeNode).where(
        KnowledgeNode.user_id == current_user.id,
        or_(
            fts_vector.op("@@")(tsquery),
            KnowledgeNode.id.in_(tag_match),
            KnowledgeNode.id.in_(resource_match),
        ),
    )

    count_query = select(func.count()).select_from(query.with_only_columns(KnowledgeNode.id).subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = query.order_by(KnowledgeNode.updated_at.desc()).offset((page - 1) * limit).limit(limit)
    query = query.options(selectinload(KnowledgeNode.tag_links).selectinload(NodeTag.tag))
    nodes = (await db.execute(query)).scalars().unique().all()

    result = {
        "items": [NodeOut.model_validate(n).model_dump(mode="json") for n in nodes],
        "page": page,
        "limit": limit,
        "total": total,
        "pages": math.ceil(total / limit) if limit else 0,
    }
    await cache_set(cache_key, result, ttl_seconds=60)
    return result
