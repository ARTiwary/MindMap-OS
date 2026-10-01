import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.db.redis import cache_delete_pattern
from app.models.activity import Activity
from app.models.enums import ActivityAction
from app.models.node import KnowledgeNode
from app.models.relationship import Relationship
from app.models.user import User
from app.schemas.graph import RelationshipCreate, RelationshipOut, RelationshipUpdate

router = APIRouter(prefix="/relationships", tags=["Relationships"])


async def _assert_owns_node(db: AsyncSession, node_id: uuid.UUID, user_id: uuid.UUID) -> None:
    result = await db.execute(
        select(KnowledgeNode.id).where(KnowledgeNode.id == node_id, KnowledgeNode.user_id == user_id)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NODE_NOT_FOUND", "message": "The requested node does not exist."}},
        )


@router.post("", response_model=RelationshipOut, status_code=status.HTTP_201_CREATED)
async def create_relationship(
    payload: RelationshipCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if payload.source_node_id == payload.target_node_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "SELF_REFERENCE", "message": "A node cannot relate to itself."}},
        )

    await _assert_owns_node(db, payload.source_node_id, current_user.id)
    await _assert_owns_node(db, payload.target_node_id, current_user.id)

    relationship = Relationship(
        source_node_id=payload.source_node_id,
        target_node_id=payload.target_node_id,
        relationship_type=payload.relationship_type,
        label=payload.label,
        strength=payload.strength,
    )
    db.add(relationship)
    db.add(
        Activity(
            user_id=current_user.id,
            action=ActivityAction.RELATIONSHIP_CREATED,
            summary=f"Connected two nodes via {payload.relationship_type.value}",
        )
    )
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "DUPLICATE_RELATIONSHIP",
                    "message": "This relationship already exists between these nodes.",
                }
            },
        )
    await db.refresh(relationship)
    await cache_delete_pattern(f"graph:user:{current_user.id}*")
    await cache_delete_pattern(f"dashboard:user:{current_user.id}*")
    return relationship


@router.patch("/{relationship_id}", response_model=RelationshipOut)
async def update_relationship(
    relationship_id: uuid.UUID,
    payload: RelationshipUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Relationship)
        .join(KnowledgeNode, KnowledgeNode.id == Relationship.source_node_id)
        .where(Relationship.id == relationship_id, KnowledgeNode.user_id == current_user.id)
    )
    relationship = result.scalar_one_or_none()
    if not relationship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "RELATIONSHIP_NOT_FOUND", "message": "The relationship does not exist."}},
        )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(relationship, field, value)
    await db.commit()
    await db.refresh(relationship)
    await cache_delete_pattern(f"graph:user:{current_user.id}*")
    return relationship


@router.delete("/{relationship_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_relationship(
    relationship_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Relationship)
        .join(KnowledgeNode, KnowledgeNode.id == Relationship.source_node_id)
        .where(Relationship.id == relationship_id, KnowledgeNode.user_id == current_user.id)
    )
    relationship = result.scalar_one_or_none()
    if not relationship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "RELATIONSHIP_NOT_FOUND", "message": "The relationship does not exist."}},
        )
    await db.delete(relationship)
    db.add(
        Activity(
            user_id=current_user.id,
            action=ActivityAction.RELATIONSHIP_DELETED,
            summary="Removed a connection between nodes",
        )
    )
    await db.commit()
    await cache_delete_pattern(f"graph:user:{current_user.id}*")
    await cache_delete_pattern(f"dashboard:user:{current_user.id}*")
    return None
