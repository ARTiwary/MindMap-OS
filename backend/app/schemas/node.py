import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.enums import Importance, NodeStatus, NodeType


class NodeCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    content: Optional[str] = None
    node_type: NodeType = NodeType.NOTE
    status: NodeStatus = NodeStatus.ACTIVE
    importance: Importance = Importance.MEDIUM
    color: Optional[str] = None
    icon: Optional[str] = None
    is_favorite: bool = False
    tag_ids: list[uuid.UUID] = Field(default_factory=list)


class NodeUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    content: Optional[str] = None
    node_type: Optional[NodeType] = None
    status: Optional[NodeStatus] = None
    importance: Optional[Importance] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    is_favorite: Optional[bool] = None
    tag_ids: Optional[list[uuid.UUID]] = None


class TagOut(BaseModel):
    id: uuid.UUID
    name: str
    color: str

    model_config = {"from_attributes": True}


class NodeOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    slug: str
    description: Optional[str] = None
    content: Optional[str] = None
    node_type: NodeType
    status: NodeStatus
    importance: Importance
    color: Optional[str] = None
    icon: Optional[str] = None
    is_favorite: bool
    created_at: datetime
    updated_at: datetime
    last_accessed_at: Optional[datetime] = None
    tags: list[TagOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class NodeListResponse(BaseModel):
    items: list[NodeOut]
    page: int
    limit: int
    total: int
    pages: int


class NodeDetailOut(NodeOut):
    referenced_by_count: int = 0
    references_count: int = 0
