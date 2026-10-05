import logging
import threading

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware

from identa import __version__
from identa.auth.routes import PUBLIC_API_PATHS, setup_router, users_router
from identa.auth.routes import router as auth_router
from identa.auth.throttle import LoginThrottle
from identa.config import Settings, get_settings
from identa.db.session import build_engine, build_session_factory
from identa.mail.sender import Mailer
from identa.ocr.factory import get_ocr_engine
from identa.security.crypto import FileCipher
from identa.services.audit import current_ip
from identa.services.retention import start_retention_worker
from identa.services.settings import load_runtime
from identa.storage.file_store import FileStore
from identa.web.limits import BodySizeLimit
from identa.web.routes import public_router, router

CSRF_HEADER = "x-requested-with"
CSRF_HEADER_VALUE = "identa"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
IP_ATTEMPTS = 20
SESSION_COOKIE = "identa_session"


def configure_logging() -> None:
    logger = logging.getLogger("identa")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)


def warm_up_ocr(application: FastAPI) -> None:
    settings = application.state.settings
    try:
        with application.state.session_factory() as session:
            device = load_runtime(session, settings).ocr_device
        get_ocr_engine(settings.ocr_engine, device, settings.ocr_model_dir, settings.ocr_languages)
    except Exception:
        logging.getLogger("identa.ocr").exception("Falha ao preparar o motor de OCR")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging()
    cipher = FileCipher(settings.encryption_key) if settings.encryption_enabled else None
    application = FastAPI(title="Identa", version=__version__, docs_url=None, redoc_url=None, openapi_url=None)
    application.state.settings = settings
    application.state.session_factory = build_session_factory(build_engine(settings.database_url))
    application.state.store = FileStore(settings.storage_dir, cipher)
    application.state.login_throttle = LoginThrottle(max_attempts=IP_ATTEMPTS)
    application.state.mailer = Mailer(settings)
    application.include_router(setup_router)
    application.include_router(auth_router)
    application.include_router(users_router)
    application.include_router(router)
    application.include_router(public_router)

    @application.get("/health", include_in_schema=False)
    def health() -> dict[str, str]:
        return {"status": "ok"}

    if settings.background_jobs:
        start_retention_worker(application.state.session_factory, application.state.store, settings)
        if settings.ocr_warmup:
            threading.Thread(target=warm_up_ocr, args=(application,), daemon=True, name="ocr-warmup").start()

    @application.middleware("http")
    async def protect_api(request: Request, call_next):
        path = request.url.path
        current_ip.set(request.client.host if request.client else None)
        if path.startswith("/api/"):
            if request.method not in SAFE_METHODS and request.headers.get(CSRF_HEADER) != CSRF_HEADER_VALUE:
                return JSONResponse({"detail": "Requisição recusada"}, status_code=403)
            if not path.startswith(PUBLIC_API_PATHS) and not request.session.get("user_id"):
                return JSONResponse({"detail": "Não autenticado"}, status_code=401)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        if path.startswith("/api/") and "Cache-Control" not in response.headers:
            response.headers["Cache-Control"] = "no-store"
        return response

    application.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
        session_cookie=SESSION_COOKIE,
        max_age=settings.access_minutes * 60,
        same_site="strict",
        https_only=settings.secure_cookies,
    )
    application.add_middleware(BodySizeLimit)
    return application


def openapi_document() -> dict:
    from fastapi.openapi.utils import get_openapi

    application = FastAPI(title="Identa", version=__version__)
    for item in (setup_router, auth_router, users_router, router, public_router):
        application.include_router(item)
    return get_openapi(title="Identa", version=__version__, routes=application.routes)
