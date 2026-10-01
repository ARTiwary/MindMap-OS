import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.enums import Importance, NodeStatus, NodeType
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class KnowledgeNode(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "knowledge_nodes"
    __table_args__ = (
        UniqueConstraint("user_id", "slug", name="uq_node_user_slug"),
        Index("ix_nodes_user_type", "user_id", "node_type"),
        Index("ix_nodes_user_status", "user_id", "status"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    content: Mapped[Optional[str]] = mapped_column(Text)
    node_type: Mapped[NodeType] = mapped_column(
        Enum(NodeType, name="node_type_enum"), default=NodeType.NOTE, nullable=False
    )
    status: Mapped[NodeStatus] = mapped_column(
        Enum(NodeStatus, name="node_status_enum"), default=NodeStatus.ACTIVE, nullable=False
    )
    importance: Mapped[Importance] = mapped_column(
        Enum(Importance, name="importance_enum"), default=Importance.MEDIUM, nullable=False
    )
    color: Mapped[Optional[str]] = mapped_column(String(20))
    icon: Mapped[Optional[str]] = mapped_column(String(50))
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # User-arranged graph coordinates. NULL until the user drags the node at
    # least once - the frontend falls back to a computed radial layout for
    # any node where these are unset, then persists the computed position
    # back so the layout is stable on the next visit.
    position_x: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    position_y: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    user: Mapped["User"] = relationship(back_populates="nodes")
    tag_links: Mapped[list["NodeTag"]] = relationship(
        back_populates="node", cascade="all, delete-orphan"
    )
    resources: Mapped[list["Resource"]] = relationship(
        back_populates="node", cascade="all, delete-orphan"
    )
    outgoing_relationships: Mapped[list["Relationship"]] = relationship(
        back_populates="source_node",
        foreign_keys="Relationship.source_node_id",
        cascade="all, delete-orphan",
    )
    incoming_relationships: Mapped[list["Relationship"]] = relationship(
        back_populates="target_node",
        foreign_keys="Relationship.target_node_id",
        cascade="all, delete-orphan",
    )

    @property
    def tags(self) -> list["Tag"]:
        """Convenience accessor so Pydantic (NodeOut.tags) can read tags
        directly without callers needing to know about the association table."""
        return [link.tag for link in self.tag_links]
