from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.auth.routes import PUBLIC_PATHS
from app.auth.routes import router as auth_router
from app.auth.throttle import LoginThrottle
from app.config import Settings, get_settings
from app.db.session import build_engine, build_session_factory
from app.security.crypto import FileCipher
from app.storage.encrypted_store import EncryptedFileStore
from app.web.routes import router

STATIC_DIR = Path(__file__).resolve().parent / "static"
SESSION_MAX_AGE_SECONDS = 8 * 60 * 60
MINIMUM_SECRET_LENGTH = 32


class MissingSecretKeyError(ValueError):
    pass


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    cipher = FileCipher(settings.encryption_key)
    if len(settings.secret_key) < MINIMUM_SECRET_LENGTH:
        raise MissingSecretKeyError(f"GREEN_OCR_SECRET_KEY precisa ter pelo menos {MINIMUM_SECRET_LENGTH} caracteres")
    application = FastAPI(title="Green OCR", docs_url=None, redoc_url=None, openapi_url=None)
    application.state.settings = settings
    application.state.session_factory = build_session_factory(build_engine(settings.database_url))
    application.state.store = EncryptedFileStore(settings.storage_dir, cipher)
    application.state.login_throttle = LoginThrottle()
    application.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    application.include_router(auth_router)
    application.include_router(router)

    @application.middleware("http")
    async def require_login(request: Request, call_next):
        is_public = request.url.path.startswith(PUBLIC_PATHS)
        if not is_public and not request.session.get("user_id"):
            if request.method == "GET":
                return RedirectResponse("/login", status_code=303)
            return JSONResponse({"detail": "Não autenticado"}, status_code=401)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    application.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
        session_cookie="green_ocr_session",
        max_age=SESSION_MAX_AGE_SECONDS,
        same_site="strict",
        https_only=False,
    )

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return application
