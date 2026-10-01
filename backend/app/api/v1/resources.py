import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.models.activity import Activity
from app.models.enums import ActivityAction
from app.models.node import KnowledgeNode
from app.models.resource import Resource
from app.models.user import User
from app.db.database import get_db
from app.schemas.graph import ResourceCreate, ResourceOut

router = APIRouter(prefix="/resources", tags=["Resources"])


@router.post("", response_model=ResourceOut, status_code=status.HTTP_201_CREATED)
async def create_resource(
    payload: ResourceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    owns = await db.execute(
        select(KnowledgeNode.id).where(
            KnowledgeNode.id == payload.node_id, KnowledgeNode.user_id == current_user.id
        )
    )
    if owns.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NODE_NOT_FOUND", "message": "The requested node does not exist."}},
        )

    resource = Resource(
        node_id=payload.node_id,
        title=payload.title,
        url=payload.url,
        description=payload.description,
        resource_type=payload.resource_type,
    )
    db.add(resource)
    db.add(
        Activity(
            user_id=current_user.id,
            action=ActivityAction.RESOURCE_ADDED,
            summary=f'Added resource "{payload.title}"',
            node_id=payload.node_id,
        )
    )
    await db.commit()
    await db.refresh(resource)

    # In a full implementation, a background job (see services/metadata.py)
    # would fetch OpenGraph metadata for `resource.url` here without blocking
    # this request, then PATCH resource.thumbnail_url once fetched.
    return resource


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resource(
    resource_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Resource)
        .join(KnowledgeNode, KnowledgeNode.id == Resource.node_id)
        .where(Resource.id == resource_id, KnowledgeNode.user_id == current_user.id)
    )
    resource = result.scalar_one_or_none()
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "RESOURCE_NOT_FOUND", "message": "The requested resource does not exist."}},
        )
    await db.delete(resource)
    await db.commit()
    return None
