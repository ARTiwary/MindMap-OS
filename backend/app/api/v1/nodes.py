import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.enums import Importance, NodeStatus, NodeType
from app.models.user import User
from app.repositories.node_repository import count_relationships
from app.schemas.node import NodeCreate, NodeDetailOut, NodeListResponse, NodeOut, NodeUpdate
from app.services import node_service

router = APIRouter(prefix="/nodes", tags=["Nodes"])


@router.get("", response_model=NodeListResponse)
async def list_nodes(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    type: Optional[NodeType] = None,
    status_filter: Optional[NodeStatus] = Query(default=None, alias="status"),
    importance: Optional[Importance] = None,
    tag: Optional[str] = None,
    favorite: Optional[bool] = None,
    sort: str = Query(default="-updated_at"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await node_service.paginated_nodes(
        db,
        current_user.id,
        page,
        limit,
        node_type=type,
        status_filter=status_filter,
        importance=importance,
        favorite=favorite,
        tag_name=tag,
        sort=sort,
    )
    return result


@router.post("", response_model=NodeOut, status_code=status.HTTP_201_CREATED)
async def create_node(
    payload: NodeCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await node_service.create_node(db, current_user.id, payload)


@router.get("/{node_id}", response_model=NodeDetailOut)
async def get_node(
    node_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    node = await node_service.get_node_detail(db, current_user.id, node_id)
    references_count, referenced_by_count = await count_relationships(db, node_id)
    return NodeDetailOut(
        **NodeOut.model_validate(node).model_dump(),
        references_count=references_count,
        referenced_by_count=referenced_by_count,
    )


@router.patch("/{node_id}", response_model=NodeOut)
async def update_node(
    node_id: uuid.UUID,
    payload: NodeUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await node_service.update_node(db, current_user.id, node_id, payload)


@router.delete("/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_node(
    node_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await node_service.delete_node(db, current_user.id, node_id)
    return None
