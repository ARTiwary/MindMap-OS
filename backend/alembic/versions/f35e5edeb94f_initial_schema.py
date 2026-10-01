"""initial schema

Revision ID: f35e5edeb94f
Revises:
Create Date: 2026-08-13 00:00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "f35e5edeb94f"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

node_type_enum = postgresql.ENUM(
    "IDEA", "NOTE", "CONCEPT", "QUESTION", "RESOURCE", "PROJECT", "BOOK",
    "COURSE", "PERSON", "TOPIC", "REFERENCE", name="node_type_enum", create_type=False,
)
node_status_enum = postgresql.ENUM("DRAFT", "ACTIVE", "ARCHIVED", "COMPLETED", name="node_status_enum", create_type=False)
importance_enum = postgresql.ENUM("LOW", "MEDIUM", "HIGH", "CRITICAL", name="importance_enum", create_type=False)
relationship_type_enum = postgresql.ENUM(
    "RELATED_TO", "PARENT_OF", "CHILD_OF", "REQUIRES", "DEPENDS_ON", "INSPIRES",
    "REFERENCES", "DERIVED_FROM", "PART_OF", "CONTRADICTS", "SUPPORTS",
    name="relationship_type_enum", create_type=False,
)
resource_type_enum = postgresql.ENUM(
    "ARTICLE", "VIDEO", "DOCUMENTATION", "BOOK", "COURSE", "GITHUB",
    "PAPER", "WEBSITE", "OTHER", name="resource_type_enum", create_type=False,
)
activity_action_enum = postgresql.ENUM(
    "NODE_CREATED", "NODE_UPDATED", "NODE_DELETED", "NODE_VIEWED",
    "RELATIONSHIP_CREATED", "RELATIONSHIP_DELETED", "TAG_ADDED", "RESOURCE_ADDED",
    name="activity_action_enum", create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    for enum_type in (
        node_type_enum, node_status_enum, importance_enum,
        relationship_type_enum, resource_type_enum, activity_action_enum,
    ):
        enum_type.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(150)),
        sa.Column("avatar_url", sa.String(500)),
        sa.Column("bio", sa.Text()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.UniqueConstraint("username", name="uq_users_username"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_username", "users", ["username"])

    op.create_table(
        "knowledge_nodes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(220), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("content", sa.Text()),
        sa.Column("node_type", node_type_enum, nullable=False, server_default="NOTE"),
        sa.Column("status", node_status_enum, nullable=False, server_default="ACTIVE"),
        sa.Column("importance", importance_enum, nullable=False, server_default="MEDIUM"),
        sa.Column("color", sa.String(20)),
        sa.Column("icon", sa.String(50)),
        sa.Column("is_favorite", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("last_accessed_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("user_id", "slug", name="uq_node_user_slug"),
    )
    op.create_index("ix_nodes_user_id", "knowledge_nodes", ["user_id"])
    op.create_index("ix_nodes_slug", "knowledge_nodes", ["slug"])
    op.create_index("ix_nodes_created_at", "knowledge_nodes", ["created_at"])
    op.create_index("ix_nodes_updated_at", "knowledge_nodes", ["updated_at"])
    op.create_index("ix_nodes_user_type", "knowledge_nodes", ["user_id", "node_type"])
    op.create_index("ix_nodes_user_status", "knowledge_nodes", ["user_id", "status"])

    op.create_table(
        "tags",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("color", sa.String(20), nullable=False, server_default="#6366F1"),
        sa.UniqueConstraint("user_id", "name", name="uq_tag_user_name"),
    )
    op.create_index("ix_tags_user_id", "tags", ["user_id"])

    op.create_table(
        "node_tags",
        sa.Column("node_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("knowledge_nodes.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "relationships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("source_node_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("knowledge_nodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_node_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("knowledge_nodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relationship_type", relationship_type_enum, nullable=False, server_default="RELATED_TO"),
        sa.Column("label", sa.String(100)),
        sa.Column("strength", sa.Integer(), nullable=False, server_default="5"),
        sa.UniqueConstraint("source_node_id", "target_node_id", "relationship_type", name="uq_relationship_edge"),
        sa.CheckConstraint("source_node_id != target_node_id", name="ck_no_self_reference"),
    )
    op.create_index("ix_rel_source", "relationships", ["source_node_id"])
    op.create_index("ix_rel_target", "relationships", ["target_node_id"])

    op.create_table(
        "resources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("node_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("knowledge_nodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("url", sa.String(1000), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("resource_type", resource_type_enum, nullable=False, server_default="WEBSITE"),
        sa.Column("metadata_fetched", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("thumbnail_url", sa.String(1000)),
    )
    op.create_index("ix_resources_node_id", "resources", ["node_id"])

    op.create_table(
        "activities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action", activity_action_enum, nullable=False),
        sa.Column("node_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("knowledge_nodes.id", ondelete="SET NULL")),
        sa.Column("summary", sa.String(300), nullable=False),
        sa.Column("extra_data", postgresql.JSONB()),
    )
    op.create_index("ix_activities_user_id", "activities", ["user_id"])


def downgrade() -> None:
    op.drop_table("activities")
    op.drop_table("resources")
    op.drop_table("relationships")
    op.drop_table("node_tags")
    op.drop_table("tags")
    op.drop_table("knowledge_nodes")
    op.drop_table("users")

    bind = op.get_bind()
    for enum_type in (
        activity_action_enum, resource_type_enum, relationship_type_enum,
        importance_enum, node_status_enum, node_type_enum,
    ):
        enum_type.drop(bind, checkfirst=True)
