from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.db.redis import cache_get, cache_set, cache_delete_pattern
from app.models.node import KnowledgeNode
from app.models.relationship import Relationship
from app.models.user import User
from app.schemas.graph import GraphResponse

router = APIRouter(prefix="/graph", tags=["Nodes"])


class NodePosition(BaseModel):
    node_id: str
    x: float
    y: float


class SavePositionsRequest(BaseModel):
    positions: list[NodePosition] = Field(min_length=1, max_length=500)


@router.get("", response_model=GraphResponse)
async def get_graph(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cache_key = f"graph:user:{current_user.id}:full"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    node_rows = (
        await db.execute(select(KnowledgeNode).where(KnowledgeNode.user_id == current_user.id))
    ).scalars().all()

    node_ids = [n.id for n in node_rows]
    edge_rows = (
        await db.execute(
            select(Relationship).where(Relationship.source_node_id.in_(node_ids))
        )
    ).scalars().all()

    payload = {
        "nodes": [
            {
                "id": str(n.id),
                "type": "knowledgeNode",
                "data": {
                    "label": n.title,
                    "nodeType": n.node_type.value,
                    "importance": n.importance.value,
                    "color": n.color,
                    "icon": n.icon,
                    "isFavorite": n.is_favorite,
                },
                # null means "the user hasn't placed this node yet" - the
                # frontend computes a fallback layout only for these nodes,
                # then immediately persists that computed position via
                # POST /graph/positions so the layout is stable from then on.
                "position": (
                    {"x": n.position_x, "y": n.position_y}
                    if n.position_x is not None and n.position_y is not None
                    else None
                ),
            }
            for n in node_rows
        ],
        "edges": [
            {
                "id": str(e.id),
                "source": str(e.source_node_id),
                "target": str(e.target_node_id),
                "label": e.label or e.relationship_type.value,
                "data": {"relationshipType": e.relationship_type.value, "strength": e.strength},
            }
            for e in edge_rows
        ],
    }
    await cache_set(cache_key, payload, ttl_seconds=120)
    return payload


@router.post("/positions", status_code=status.HTTP_204_NO_CONTENT)
async def save_positions(
    payload: SavePositionsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Persist user-arranged (or first-computed) node coordinates so the
    graph layout survives navigation and refreshes. Called by the frontend
    after a drag ends, and once after computing a fallback layout for any
    newly-created nodes that don't have a saved position yet."""
    node_ids = [p.node_id for p in payload.positions]
    owned = (
        await db.execute(
            select(KnowledgeNode.id).where(
                KnowledgeNode.id.in_(node_ids), KnowledgeNode.user_id == current_user.id
            )
        )
    ).scalars().all()
    owned_set = {str(nid) for nid in owned}

    missing = [p.node_id for p in payload.positions if p.node_id not in owned_set]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NODE_NOT_FOUND",
                    "message": "One or more nodes do not exist or are not yours.",
                }
            },
        )

    position_by_id = {p.node_id: p for p in payload.positions}
    nodes = (
        await db.execute(
            select(KnowledgeNode).where(KnowledgeNode.id.in_(node_ids))
        )
    ).scalars().all()
    for node in nodes:
        pos = position_by_id[str(node.id)]
        node.position_x = pos.x
        node.position_y = pos.y

    await db.commit()
    await cache_delete_pattern(f"graph:user:{current_user.id}*")
    return None
