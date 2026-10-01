from fastapi import APIRouter, Depends

from app.api.v1 import (
    activity,
    analytics,
    auth,
    dashboard,
    graph,
    nodes,
    relationships,
    resources,
    search,
    suggestions,
    tags,
)
from app.core.dependencies import rate_limit

# Every route under /api/v1 goes through the general rate limit by default.
# Auth endpoints additionally apply a stricter, lower-ceiling limit directly
# on their own router (see api/v1/auth.py) since they need tighter
# protection against brute-force/credential-stuffing than normal API traffic.
api_router = APIRouter(dependencies=[Depends(rate_limit)])
api_router.include_router(auth.router)
api_router.include_router(nodes.router)
api_router.include_router(tags.router)
api_router.include_router(relationships.router)
api_router.include_router(resources.router)
api_router.include_router(graph.router)
api_router.include_router(search.router)
api_router.include_router(dashboard.router)
api_router.include_router(analytics.router)
api_router.include_router(suggestions.router)
api_router.include_router(activity.router)
