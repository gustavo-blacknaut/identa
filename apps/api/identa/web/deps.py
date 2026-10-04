from collections.abc import Callable, Iterator
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from identa.auth.permissions import Permission
from identa.auth.tokens import is_session_active
from identa.db.models import User
from identa.ocr.base import OcrEngine
from identa.ocr.factory import get_ocr_engine
from identa.services.settings import RuntimeSettings, load_runtime
from identa.storage.file_store import FileStore


def get_session(request: Request) -> Iterator[Session]:
    with request.app.state.session_factory() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


def get_store(request: Request) -> FileStore:
    return request.app.state.store


def get_runtime(request: Request, session: SessionDep) -> RuntimeSettings:
    return load_runtime(session, request.app.state.settings)


RuntimeDep = Annotated[RuntimeSettings, Depends(get_runtime)]


def engine_for(request: Request, device: str) -> OcrEngine:
    override = getattr(request.app.state, "ocr_engine", None)
    settings = request.app.state.settings
    return override or get_ocr_engine(settings.ocr_engine, device, settings.ocr_model_dir, settings.ocr_languages)


def get_engine(request: Request, runtime: RuntimeDep) -> OcrEngine:
    return engine_for(request, runtime.ocr_device)


def current_user(request: Request, session: SessionDep) -> User:
    user_id = request.session.get("user_id")
    user = session.get(User, user_id) if user_id else None
    if user is None or not user.is_active or not is_session_active(session, user.id, request.session.get("sid")):
        if user_id:
            request.session.clear()
        raise HTTPException(401, "Não autenticado")
    request.state.user = user
    return user


UserDep = Annotated[User, Depends(current_user)]


def require(permission: Permission) -> Callable[..., User]:
    def dependency(user: UserDep, runtime: RuntimeDep) -> User:
        if permission not in runtime.permissions_of(user.role):
            raise HTTPException(403, "Você não tem permissão para esta ação.")
        return user

    return dependency


def permitted(permission: Permission):
    return Annotated[User, Depends(require(permission))]
