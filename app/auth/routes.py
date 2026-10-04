from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.auth.users import authenticate
from app.db.models import User
from app.web.deps import get_session
from app.web.schemas import Credentials, UserOut

router = APIRouter(prefix="/api/auth")
PUBLIC_API_PATHS = ("/api/auth/login", "/api/auth/me", "/health")


def client_key(request: Request, username: str) -> str:
    host = request.client.host if request.client else "unknown"
    return f"{host}:{username.lower()}"


@router.post("/login")
def login(request: Request, credentials: Credentials, session: Annotated[Session, Depends(get_session)]) -> UserOut:
    throttle = request.app.state.login_throttle
    key = client_key(request, credentials.username)
    if throttle.is_blocked(key):
        raise HTTPException(429, "Muitas tentativas. Aguarde alguns minutos.")
    user = authenticate(session, credentials.username.strip(), credentials.password)
    if user is None:
        throttle.record_failure(key)
        raise HTTPException(401, "Usuário ou senha inválidos.")
    throttle.reset(key)
    request.session.clear()
    request.session["user_id"] = user.id
    return UserOut(id=user.id, username=user.username)


@router.get("/me")
def me(request: Request, session: Annotated[Session, Depends(get_session)]) -> UserOut:
    user_id = request.session.get("user_id")
    user = session.get(User, user_id) if user_id else None
    if user is None or not user.is_active:
        request.session.clear()
        raise HTTPException(401, "Não autenticado")
    return UserOut(id=user.id, username=user.username)


@router.post("/logout", status_code=204)
def logout(request: Request) -> Response:
    request.session.clear()
    return Response(status_code=204)
