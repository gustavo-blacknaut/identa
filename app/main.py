from fastapi import FastAPI

from app.config import get_settings
from app.security.crypto import decode_key


def create_app() -> FastAPI:
    settings = get_settings()
    decode_key(settings.encryption_key)
    application = FastAPI(title="Green OCR")

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return application
