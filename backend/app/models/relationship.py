import uuid

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.enums import RelationshipType
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Relationship(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "relationships"
    __table_args__ = (
        UniqueConstraint(
            "source_node_id", "target_node_id", "relationship_type", name="uq_relationship_edge"
        ),
        CheckConstraint("source_node_id != target_node_id", name="ck_no_self_reference"),
    )

    source_node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_nodes.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    target_node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_nodes.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    relationship_type: Mapped[RelationshipType] = mapped_column(
        Enum(RelationshipType, name="relationship_type_enum"),
        default=RelationshipType.RELATED_TO,
        nullable=False,
    )
    label: Mapped[str | None] = mapped_column(String(100))
    strength: Mapped[int] = mapped_column(Integer, default=5, nullable=False)

    source_node: Mapped["KnowledgeNode"] = relationship(
        back_populates="outgoing_relationships", foreign_keys=[source_node_id]
    )
    target_node: Mapped["KnowledgeNode"] = relationship(
        back_populates="incoming_relationships", foreign_keys=[target_node_id]
    )
