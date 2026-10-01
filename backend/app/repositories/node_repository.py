import uuid
from typing import Optional

from slugify import slugify
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.node import KnowledgeNode
from app.models.tag import NodeTag


async def generate_unique_slug(db: AsyncSession, user_id: uuid.UUID, title: str) -> str:
    base = slugify(title)[:200] or "node"
    slug = base
    counter = 1
    while True:
        result = await db.execute(
            select(KnowledgeNode.id).where(
                KnowledgeNode.user_id == user_id, KnowledgeNode.slug == slug
            )
        )
        if result.scalar_one_or_none() is None:
            return slug
        counter += 1
        slug = f"{base}-{counter}"


async def get_node_by_id(
    db: AsyncSession, node_id: uuid.UUID, user_id: uuid.UUID
) -> Optional[KnowledgeNode]:
    result = await db.execute(
        select(KnowledgeNode)
        .options(selectinload(KnowledgeNode.tag_links).selectinload(NodeTag.tag))
        .where(KnowledgeNode.id == node_id, KnowledgeNode.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def list_nodes(
    db: AsyncSession,
    user_id: uuid.UUID,
    page: int,
    limit: int,
    node_type: Optional[str] = None,
    status_filter: Optional[str] = None,
    importance: Optional[str] = None,
    favorite: Optional[bool] = None,
    tag_name: Optional[str] = None,
    sort: str = "-updated_at",
) -> tuple[list[KnowledgeNode], int]:
    query = select(KnowledgeNode).where(KnowledgeNode.user_id == user_id)

    if node_type:
        query = query.where(KnowledgeNode.node_type == node_type)
    if status_filter:
        query = query.where(KnowledgeNode.status == status_filter)
    if importance:
        query = query.where(KnowledgeNode.importance == importance)
    if favorite is not None:
        query = query.where(KnowledgeNode.is_favorite == favorite)
    if tag_name:
        from app.models.tag import Tag

        query = (
            query.join(NodeTag, NodeTag.node_id == KnowledgeNode.id)
            .join(Tag, Tag.id == NodeTag.tag_id)
            .where(func.lower(Tag.name) == tag_name.lower())
        )

    # Sorting: prefix '-' means descending
    sort_field = sort.lstrip("-")
    sort_column = getattr(KnowledgeNode, sort_field, KnowledgeNode.updated_at)
    query = query.order_by(sort_column.desc() if sort.startswith("-") else sort_column.asc())

    query = query.options(selectinload(KnowledgeNode.tag_links).selectinload(NodeTag.tag))

    count_query = select(func.count()).select_from(query.with_only_columns(KnowledgeNode.id).subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    nodes = list(result.scalars().unique().all())
    return nodes, total


async def count_relationships(db: AsyncSession, node_id: uuid.UUID) -> tuple[int, int]:
    """Returns (references_count, referenced_by_count)."""
    from app.models.relationship import Relationship

    out_count = (
        await db.execute(
            select(func.count()).where(Relationship.source_node_id == node_id)
        )
    ).scalar_one()
    in_count = (
        await db.execute(
            select(func.count()).where(Relationship.target_node_id == node_id)
        )
    ).scalar_one()
    return out_count, in_count
