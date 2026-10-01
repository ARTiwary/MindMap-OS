import uuid
from typing import Optional

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.enums import ResourceType
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Resource(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "resources"

    node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_nodes.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    resource_type: Mapped[ResourceType] = mapped_column(
        Enum(ResourceType, name="resource_type_enum"), default=ResourceType.WEBSITE, nullable=False
    )
    # Populated asynchronously by a background job (see services/metadata.py)
    metadata_fetched: Mapped[bool] = mapped_column(default=False)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(1000))

    node: Mapped["KnowledgeNode"] = relationship(back_populates="resources")
