import uuid
from typing import Optional

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.enums import ActivityAction
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Activity(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Permanent, queryable activity history. High-churn ephemeral activity
    (e.g. live cursor movement) belongs in Redis, not here."""

    __tablename__ = "activities"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    action: Mapped[ActivityAction] = mapped_column(
        Enum(ActivityAction, name="activity_action_enum"), nullable=False
    )
    node_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("knowledge_nodes.id", ondelete="SET NULL"), nullable=True
    )
    summary: Mapped[str] = mapped_column(String(300), nullable=False)
    extra_data: Mapped[Optional[dict]] = mapped_column(JSONB)
