"""
Deterministic (non-AI) suggestion engine.

Phase 7 of the spec calls for rule-based suggestions first, with the
architecture left extensible for a future ML/LLM-backed engine. Every
suggestion here is explainable: it always states *why* it was made.
"""
import uuid
from itertools import combinations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.node import KnowledgeNode
from app.models.relationship import Relationship
from app.models.tag import NodeTag


async def _existing_edge_pairs(db: AsyncSession, user_id: uuid.UUID) -> set[frozenset]:
    rows = (
        await db.execute(
            select(Relationship.source_node_id, Relationship.target_node_id)
            .join(KnowledgeNode, KnowledgeNode.id == Relationship.source_node_id)
            .where(KnowledgeNode.user_id == user_id)
        )
    ).all()
    return {frozenset((a, b)) for a, b in rows}


async def suggest_connections(db: AsyncSession, user_id: uuid.UUID, limit: int = 10) -> list[dict]:
    """Suggest new relationships between nodes that share a tag but aren't
    yet connected. This is the 'shared tags' factor from the spec; same_type,
    same_project, and recency factors can be layered on the same shape later."""
    existing_edges = await _existing_edge_pairs(db, user_id)

    rows = (
        await db.execute(
            select(NodeTag.tag_id, KnowledgeNode.id, KnowledgeNode.title)
            .join(KnowledgeNode, KnowledgeNode.id == NodeTag.node_id)
            .where(KnowledgeNode.user_id == user_id)
        )
    ).all()

    by_tag: dict[uuid.UUID, list[tuple[uuid.UUID, str]]] = {}
    for tag_id, node_id, title in rows:
        by_tag.setdefault(tag_id, []).append((node_id, title))

    suggestions = []
    seen_pairs: set[frozenset] = set()
    for tag_id, nodes in by_tag.items():
        for (id_a, title_a), (id_b, title_b) in combinations(nodes, 2):
            pair = frozenset((id_a, id_b))
            if pair in existing_edges or pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            suggestions.append(
                {
                    "node_a_id": str(id_a),
                    "node_a_title": title_a,
                    "node_b_id": str(id_b),
                    "node_b_title": title_b,
                    "reason": "Both nodes share a tag but aren't connected yet.",
                    "factor": "SHARED_TAG",
                }
            )
            if len(suggestions) >= limit:
                return suggestions
    return suggestions
