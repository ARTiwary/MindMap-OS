from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds baseline security headers to every response. CORS is handled
    separately by CORSMiddleware in main.py - this covers the headers CORS
    doesn't touch: clickjacking, MIME-sniffing, referrer leakage, and
    (in production, where we're not serving the Swagger UI's CDN assets
    from arbitrary origins) a real Content-Security-Policy."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        if settings.ENV == "production":
            # HSTS only makes sense once you're actually serving over HTTPS,
            # which is the deploy target this header assumes.
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
            # /docs and /redoc pull Swagger UI assets from a CDN - excluding
            # them keeps the API's own CSP strict without breaking the docs.
            if not request.url.path.startswith(("/docs", "/redoc")):
                response.headers["Content-Security-Policy"] = (
                    "default-src 'none'; frame-ancestors 'none'"
                )

        return response
