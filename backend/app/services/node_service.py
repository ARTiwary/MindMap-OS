import math
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.redis import (
    bump_popular_node,
    cache_delete_pattern,
    push_recent_node,
)
from app.models.activity import Activity
from app.models.enums import ActivityAction
from app.models.node import KnowledgeNode
from app.models.tag import NodeTag, Tag
from app.repositories import node_repository
from app.schemas.node import NodeCreate, NodeUpdate


async def _invalidate_user_caches(user_id: uuid.UUID) -> None:
    await cache_delete_pattern(f"dashboard:user:{user_id}*")
    await cache_delete_pattern(f"search:{user_id}:*")
    await cache_delete_pattern(f"graph:user:{user_id}*")


async def _log_activity(
    db: AsyncSession,
    user_id: uuid.UUID,
    action: ActivityAction,
    summary: str,
    node_id: uuid.UUID | None = None,
) -> None:
    db.add(Activity(user_id=user_id, action=action, summary=summary, node_id=node_id))


async def _sync_tags(db: AsyncSession, node: KnowledgeNode, user_id: uuid.UUID, tag_ids: list[uuid.UUID]) -> None:
    # Validate ownership of every tag before linking
    if tag_ids:
        result = await db.execute(
            select(Tag.id).where(Tag.id.in_(tag_ids), Tag.user_id == user_id)
        )
        valid_ids = {row for row in result.scalars().all()}
        if len(valid_ids) != len(set(tag_ids)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "INVALID_TAG", "message": "One or more tags do not exist."}},
            )
    else:
        valid_ids = set()

    await db.execute(NodeTag.__table__.delete().where(NodeTag.node_id == node.id))
    for tag_id in valid_ids:
        db.add(NodeTag(node_id=node.id, tag_id=tag_id))


async def create_node(db: AsyncSession, user_id: uuid.UUID, payload: NodeCreate) -> KnowledgeNode:
    slug = await node_repository.generate_unique_slug(db, user_id, payload.title)
    node = KnowledgeNode(
        user_id=user_id,
        title=payload.title,
        slug=slug,
        description=payload.description,
        content=payload.content,
        node_type=payload.node_type,
        status=payload.status,
        importance=payload.importance,
        color=payload.color,
        icon=payload.icon,
        is_favorite=payload.is_favorite,
    )
    db.add(node)
    await db.flush()

    await _sync_tags(db, node, user_id, payload.tag_ids)
    await _log_activity(db, user_id, ActivityAction.NODE_CREATED, f'Created "{node.title}"', node.id)

    await db.commit()
    await db.refresh(node)

    await _invalidate_user_caches(user_id)
    return await node_repository.get_node_by_id(db, node.id, user_id)


async def update_node(
    db: AsyncSession, user_id: uuid.UUID, node_id: uuid.UUID, payload: NodeUpdate
) -> KnowledgeNode:
    node = await node_repository.get_node_by_id(db, node_id, user_id)
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NODE_NOT_FOUND", "message": "The requested node does not exist."}},
        )

    update_data = payload.model_dump(exclude_unset=True, exclude={"tag_ids"})
    for field, value in update_data.items():
        setattr(node, field, value)

    if payload.tag_ids is not None:
        await _sync_tags(db, node, user_id, payload.tag_ids)

    await _log_activity(db, user_id, ActivityAction.NODE_UPDATED, f'Updated "{node.title}"', node.id)

    await db.commit()
    await db.refresh(node)

    await _invalidate_user_caches(user_id)
    return await node_repository.get_node_by_id(db, node.id, user_id)


async def delete_node(db: AsyncSession, user_id: uuid.UUID, node_id: uuid.UUID) -> None:
    node = await node_repository.get_node_by_id(db, node_id, user_id)
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NODE_NOT_FOUND", "message": "The requested node does not exist."}},
        )
    title = node.title
    await db.delete(node)
    await _log_activity(db, user_id, ActivityAction.NODE_DELETED, f'Deleted "{title}"')
    await db.commit()
    await _invalidate_user_caches(user_id)


async def get_node_detail(db: AsyncSession, user_id: uuid.UUID, node_id: uuid.UUID) -> KnowledgeNode:
    node = await node_repository.get_node_by_id(db, node_id, user_id)
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NODE_NOT_FOUND", "message": "The requested node does not exist."}},
        )
    node.last_accessed_at = datetime.now(timezone.utc)
    await _log_activity(db, user_id, ActivityAction.NODE_VIEWED, f'Viewed "{node.title}"', node.id)
    await db.commit()
    # `updated_at` has a server-side onupdate=func.now(); without a refresh
    # here, accessing it during response serialization triggers a lazy
    # load outside of an async-safe context (MissingGreenlet).
    await db.refresh(node)

    await push_recent_node(str(user_id), str(node_id))
    await bump_popular_node(str(user_id), str(node_id))

    return node


async def paginated_nodes(
    db: AsyncSession,
    user_id: uuid.UUID,
    page: int,
    limit: int,
    **filters,
) -> dict:
    nodes, total = await node_repository.list_nodes(db, user_id, page, limit, **filters)
    return {
        "items": nodes,
        "page": page,
        "limit": limit,
        "total": total,
        "pages": math.ceil(total / limit) if limit else 0,
    }
