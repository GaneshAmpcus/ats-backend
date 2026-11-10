import hmac

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader

from app.api.v1.health import router as health_router
from app.config import get_settings

settings = get_settings()
api_key_header = APIKeyHeader(name="X-API-Key", scheme_name="ApiKeyAuth", auto_error=False)
app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    dependencies=[Depends(api_key_header)],
)
app.include_router(health_router, prefix=settings.api_v1_prefix)


@app.middleware("http")
async def require_service_api_key(request: Request, call_next):
    """Require a configured service key on every HTTP endpoint."""
    public_docs_paths = {
        "/docs",
        "/docs/oauth2-redirect",
        "/redoc",
        "/openapi.json",
    }
    if request.url.path in public_docs_paths:
        return await call_next(request)

    configured_key = get_settings().ai_service_api_key
    if configured_key is None or not configured_key.get_secret_value():
        return JSONResponse(
            status_code=503,
            content={"detail": "AI service API key is not configured"},
        )

    supplied_key = request.headers.get("X-API-Key", "")
    expected_key = configured_key.get_secret_value()
    if not supplied_key or not hmac.compare_digest(supplied_key, expected_key):
        return JSONResponse(status_code=401, content={"detail": "Invalid or missing API key"})

    return await call_next(request)
