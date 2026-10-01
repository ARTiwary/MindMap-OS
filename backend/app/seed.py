"""
Development seed script.

Creates a demo account with a realistic, visually interesting knowledge
graph (50+ nodes, 100+ relationships, 20+ tags, resources included) so the
graph view and analytics have something meaningful to show immediately.

Run inside the backend container:
    python -m app.seed
"""
import asyncio
import random

from app.core.security import hash_password
from app.db.database import AsyncSessionLocal
from app.models.enums import Importance, NodeStatus, NodeType, RelationshipType, ResourceType
from app.models.node import KnowledgeNode
from app.models.relationship import Relationship
from app.models.resource import Resource
from app.models.tag import NodeTag, Tag
from app.models.user import User
from app.repositories.node_repository import generate_unique_slug

DEMO_EMAIL = "demo@mindmapos.app"
DEMO_USERNAME = "demo"
DEMO_PASSWORD = "DemoPassword123!"  # noqa: S105 - clearly-labeled dev/demo-only credential

TOPIC_TREE = {
    "Python": ["FastAPI", "AsyncIO", "Testing", "Pydantic", "Type Hints", "Packaging"],
    "FastAPI": ["Pydantic", "SQLAlchemy", "JWT", "Dependency Injection", "OpenAPI", "Middleware"],
    "Databases": ["PostgreSQL", "Redis", "SQL", "Indexing", "Transactions", "Normalization"],
    "AI": ["LLM", "RAG", "Embeddings", "Prompt Engineering", "Fine-Tuning", "Vector Search"],
    "Frontend": ["React", "TypeScript", "React Flow", "State Management", "Tailwind CSS", "Vite"],
    "Architecture": ["Microservices", "Caching", "Rate Limiting", "Event-Driven Design", "REST", "Scalability"],
    "Projects": ["MindMap OS", "Portfolio Site", "Side Project Ideas"],
    "DevOps": ["Docker", "Docker Compose", "CI/CD", "Observability", "Logging", "Health Checks"],
    "Career": ["System Design Interviews", "Portfolio Building", "Open Source Contributions"],
}

TAG_NAMES = [
    "Python", "Backend", "AI", "Programming", "Research", "Project", "Learning",
    "Frontend", "Database", "DevOps", "Architecture", "Security", "Testing",
    "Performance", "Design", "Career", "Tools", "Reading", "Interview-Prep", "Open-Source",
]

RESOURCE_SEEDS = [
    ("FastAPI Documentation", "https://fastapi.tiangolo.com", ResourceType.DOCUMENTATION),
    ("SQLAlchemy 2.0 Docs", "https://docs.sqlalchemy.org", ResourceType.DOCUMENTATION),
    ("Redis Docs", "https://redis.io/docs/", ResourceType.DOCUMENTATION),
    ("React Flow", "https://reactflow.dev", ResourceType.DOCUMENTATION),
    ("Designing Data-Intensive Applications", "https://dataintensive.net", ResourceType.BOOK),
    ("PostgreSQL Full-Text Search", "https://www.postgresql.org/docs/current/textsearch.html", ResourceType.ARTICLE),
    ("JWT.io", "https://jwt.io", ResourceType.WEBSITE),
    ("Tailwind CSS Docs", "https://tailwindcss.com/docs", ResourceType.DOCUMENTATION),
    ("Awesome FastAPI (GitHub)", "https://github.com/mjhea0/awesome-fastapi", ResourceType.GITHUB),
    ("The RAG Paper", "https://arxiv.org/abs/2005.11401", ResourceType.PAPER),
]

NODE_TYPES = list(NodeType)
IMPORTANCE_LEVELS = list(Importance)
REL_TYPES = list(RelationshipType)


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        existing = await db.execute(User.__table__.select().where(User.email == DEMO_EMAIL))
        if existing.first():
            print(f"Demo user '{DEMO_EMAIL}' already exists - skipping seed.")
            return

        user = User(
            email=DEMO_EMAIL,
            username=DEMO_USERNAME,
            password_hash=hash_password(DEMO_PASSWORD),
            full_name="Demo User",
            bio="Exploring MindMap OS.",
            is_verified=True,
        )
        db.add(user)
        await db.flush()

        tags = {}
        for name in TAG_NAMES:
            tag = Tag(user_id=user.id, name=name, color=f"#{random.randint(0, 0xFFFFFF):06x}")
            db.add(tag)
            tags[name] = tag
        await db.flush()

        nodes: dict[str, KnowledgeNode] = {}
        all_titles = list(TOPIC_TREE.keys()) + [c for children in TOPIC_TREE.values() for c in children]
        all_titles = list(dict.fromkeys(all_titles))  # dedupe, preserve order

        for title in all_titles:
            slug = await generate_unique_slug(db, user.id, title)
            node = KnowledgeNode(
                user_id=user.id,
                title=title,
                slug=slug,
                description=f"Notes and resources about {title}.",
                content=f"# {title}\n\nKey ideas, references, and open questions about **{title}**.",
                node_type=random.choice(NODE_TYPES),
                status=random.choice(list(NodeStatus)),
                importance=random.choice(IMPORTANCE_LEVELS),
                is_favorite=random.random() < 0.15,
            )
            db.add(node)
            nodes[title] = node
        await db.flush()

        # Attach 1-3 random tags to every node
        for node in nodes.values():
            for tag in random.sample(list(tags.values()), k=random.randint(1, 3)):
                db.add(NodeTag(node_id=node.id, tag_id=tag.id))

        # Parent -> child relationships from the topic tree
        relationship_pairs: set[tuple[str, str]] = set()
        for parent, children in TOPIC_TREE.items():
            for child in children:
                if parent == child:
                    continue
                relationship_pairs.add((parent, child))

        # Extra cross-links for a visually rich graph (100+ edges target)
        title_list = list(nodes.keys())
        while len(relationship_pairs) < 110:
            a, b = random.sample(title_list, 2)
            if a != b:
                relationship_pairs.add((a, b))

        for source_title, target_title in relationship_pairs:
            db.add(
                Relationship(
                    source_node_id=nodes[source_title].id,
                    target_node_id=nodes[target_title].id,
                    relationship_type=random.choice(REL_TYPES),
                    strength=random.randint(1, 10),
                )
            )

        # Resources attached to a handful of relevant nodes
        for title, url, rtype in RESOURCE_SEEDS:
            target_node = random.choice(list(nodes.values()))
            db.add(
                Resource(
                    node_id=target_node.id,
                    title=title,
                    url=url,
                    resource_type=rtype,
                    description=f"Reference material linked from {target_node.title}.",
                )
            )

        await db.commit()
        print(f"Seeded {len(nodes)} nodes, {len(relationship_pairs)} relationships, {len(tags)} tags.")
        print(f"Demo login -> email: {DEMO_EMAIL}  password: {DEMO_PASSWORD}")
        print("This account and password are for local development only.")


if __name__ == "__main__":
    asyncio.run(seed())
