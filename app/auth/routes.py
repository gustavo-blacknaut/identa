from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth.users import authenticate
from app.web.deps import get_session
from app.web.templating import templates

router = APIRouter()
PUBLIC_PATHS = ("/login", "/health", "/static/")


def client_key(request: Request, username: str) -> str:
    host = request.client.host if request.client else "unknown"
    return f"{host}:{username.lower()}"


@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {})


@router.post("/login")
def login(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
):
    throttle = request.app.state.login_throttle
    key = client_key(request, username)
    if throttle.is_blocked(key):
        return templates.TemplateResponse(
            request, "login.html", {"error": "Muitas tentativas. Aguarde alguns minutos."}, status_code=429
        )
    user = authenticate(session, username.strip(), password)
    if user is None:
        throttle.record_failure(key)
        return templates.TemplateResponse(request, "login.html", {"error": "Usuário ou senha inválidos."}, status_code=401)
    throttle.reset(key)
    request.session.clear()
    request.session["user_id"] = user.id
    request.session["username"] = user.username
    return RedirectResponse("/", status_code=303)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)
