import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("mindmap.errors")


def _sanitize_validation_errors(errors: list[dict]) -> list[dict]:
    """Pydantic v2 puts the raw exception object (e.g. a ValueError raised by
    a field_validator) in errors()[i]['ctx']['error'], which json.dumps can't
    serialize on its own. Stringify it before it goes anywhere near a response."""
    sanitized = []
    for err in errors:
        err = dict(err)
        ctx = err.get("ctx")
        if isinstance(ctx, dict) and "error" in ctx:
            ctx = dict(ctx)
            ctx["error"] = str(ctx["error"])
            err["ctx"] = ctx
        sanitized.append(err)
    return sanitized


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        detail = exc.detail
        if isinstance(detail, dict) and "error" in detail:
            body = detail
        else:
            body = {"error": {"code": "HTTP_ERROR", "message": str(detail)}}
        return JSONResponse(status_code=exc.status_code, content=body, headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        details = jsonable_encoder(_sanitize_validation_errors(exc.errors()))
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "The request payload is invalid.",
                    "details": details,
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Something went wrong on our end. Please try again.",
                }
            },
        )
