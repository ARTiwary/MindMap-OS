import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.enums import RelationshipType, ResourceType


class RelationshipCreate(BaseModel):
    source_node_id: uuid.UUID
    target_node_id: uuid.UUID
    relationship_type: RelationshipType = RelationshipType.RELATED_TO
    label: Optional[str] = Field(default=None, max_length=100)
    strength: int = Field(default=5, ge=1, le=10)


class RelationshipUpdate(BaseModel):
    relationship_type: Optional[RelationshipType] = None
    label: Optional[str] = Field(default=None, max_length=100)
    strength: Optional[int] = Field(default=None, ge=1, le=10)


class RelationshipOut(BaseModel):
    id: uuid.UUID
    source_node_id: uuid.UUID
    target_node_id: uuid.UUID
    relationship_type: RelationshipType
    label: Optional[str] = None
    strength: int
    created_at: datetime

    model_config = {"from_attributes": True}


class GraphResponse(BaseModel):
    """Payload shaped for direct consumption by React Flow."""

    nodes: list[dict]
    edges: list[dict]


class TagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    color: str = Field(default="#6366F1", max_length=20)


class TagUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    color: Optional[str] = Field(default=None, max_length=20)


class ResourceCreate(BaseModel):
    node_id: uuid.UUID
    title: str = Field(min_length=1, max_length=300)
    url: str = Field(min_length=1, max_length=1000)
    description: Optional[str] = None
    resource_type: ResourceType = ResourceType.WEBSITE


class ResourceOut(BaseModel):
    id: uuid.UUID
    node_id: uuid.UUID
    title: str
    url: str
    description: Optional[str] = None
    resource_type: ResourceType
    thumbnail_url: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
