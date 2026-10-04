from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import RedirectResponse, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Document, DocumentImage, DocumentStatus, ImageSide, Person
from app.imaging.preprocess import InvalidImageError
from app.ocr.base import OcrEngine
from app.parsers.registry import available_parsers, get_parser
from app.services.documents import (
    DOCUMENT_COLUMNS,
    UploadedSide,
    delete_document,
    delete_person,
    document_values,
    process_document,
    reprocess_document,
    review_document,
)
from app.storage.encrypted_store import EncryptedFileStore
from app.web.deps import get_engine, get_session, get_store
from app.web.templating import templates

router = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]
StoreDep = Annotated[EncryptedFileStore, Depends(get_store)]
EngineDep = Annotated[OcrEngine, Depends(get_engine)]


def current_user_id(request: Request) -> int | None:
    return request.session.get("user_id")


def load_document(session: Session, document_id: int) -> Document:
    document = session.get(Document, document_id)
    if document is None:
        raise HTTPException(404, "Documento não encontrado")
    return document


@router.get("/")
def dashboard(request: Request, session: SessionDep):
    documents = session.scalars(select(Document).order_by(Document.processed_at.desc()).limit(100)).all()
    people = session.scalars(select(Person).order_by(Person.updated_at.desc()).limit(100)).all()
    stats = {
        "documents": session.scalar(select(func.count(Document.id))),
        "pending": session.scalar(select(func.count(Document.id)).where(Document.status == DocumentStatus.PENDING_REVIEW)),
        "people": session.scalar(select(func.count(Person.id))),
    }
    parsers = {parser.doc_type: parser.display_name for parser in available_parsers()}
    return templates.TemplateResponse(
        request, "dashboard.html", {"documents": documents, "people": people, "stats": stats, "parsers": parsers}
    )


@router.get("/novo")
def new_document(request: Request):
    return templates.TemplateResponse(request, "new.html", {"parsers": available_parsers()})


@router.post("/documentos")
async def upload_document(
    request: Request,
    session: SessionDep,
    store: StoreDep,
    engine: EngineDep,
    doc_type: Annotated[str, Form()],
    front: Annotated[UploadFile, File()],
    back: Annotated[UploadFile | None, File()] = None,
):
    max_bytes = request.app.state.settings.max_upload_mb * 1024 * 1024
    sides = []
    for side, upload in ((ImageSide.FRONT, front), (ImageSide.BACK, back)):
        if upload is None or not upload.filename:
            continue
        content = await upload.read(max_bytes + 1)
        if len(content) > max_bytes:
            raise HTTPException(413, "Imagem maior que o limite permitido")
        sides.append(UploadedSide(side, content))
    try:
        get_parser(doc_type)
        document = await run_in_threadpool(process_document, session, store, engine, doc_type, sides, current_user_id(request))
    except KeyError as error:
        raise HTTPException(400, str(error)) from error
    except InvalidImageError as error:
        return templates.TemplateResponse(
            request, "new.html", {"parsers": available_parsers(), "error": str(error)}, status_code=400
        )
    return RedirectResponse(f"/documentos/{document.id}", status_code=303)


@router.get("/documentos/{document_id}")
def show_document(request: Request, document_id: int, session: SessionDep):
    document = load_document(session, document_id)
    parser = get_parser(document.doc_type)
    extra = document.extra_fields or {}
    issues_by_field: dict[str, list[str]] = {}
    for issue in extra.get("issues", []):
        issues_by_field.setdefault(issue["field"], []).append(issue["message"])
    return templates.TemplateResponse(
        request,
        "document.html",
        {
            "document": document,
            "parser": parser,
            "values": document_values(document),
            "confidence": document.field_confidence or {},
            "issues": issues_by_field,
            "saved": request.query_params.get("salvo") == "1",
        },
    )


@router.post("/documentos/{document_id}")
async def save_document(request: Request, document_id: int, session: SessionDep):
    document = load_document(session, document_id)
    form = await request.form()
    values = {name: str(form[name]) for name in DOCUMENT_COLUMNS if name in form}
    review_document(session, document, values, current_user_id(request))
    return RedirectResponse(f"/documentos/{document.id}?salvo=1", status_code=303)


@router.post("/documentos/{document_id}/excluir")
def remove_document(request: Request, document_id: int, session: SessionDep, store: StoreDep):
    delete_document(session, store, load_document(session, document_id), current_user_id(request))
    return RedirectResponse("/", status_code=303)


@router.post("/pessoas/{person_id}/excluir")
def remove_person(request: Request, person_id: int, session: SessionDep, store: StoreDep):
    person = session.get(Person, person_id)
    if person is None:
        raise HTTPException(404, "Pessoa não encontrada")
    delete_person(session, store, person, current_user_id(request))
    return RedirectResponse("/", status_code=303)


@router.get("/imagens/{image_id}/{variant}")
def image(image_id: int, variant: str, session: SessionDep, store: StoreDep):
    record = session.get(DocumentImage, image_id)
    paths = {
        "miniatura": (record.thumbnail_path, "image/webp") if record else None,
        "processada": (record.processed_path, "image/jpeg") if record else None,
        "original": (record.original_path, record.original_mime) if record else None,
    }
    selected = paths.get(variant)
    if not selected or not selected[0]:
        raise HTTPException(404, "Imagem não encontrada")
    return Response(store.load(selected[0]), media_type=selected[1], headers={"Cache-Control": "private, no-store"})


@router.post("/documentos/{document_id}/reprocessar")
async def reprocess(request: Request, document_id: int, session: SessionDep, store: StoreDep, engine: EngineDep):
    document = load_document(session, document_id)
    await run_in_threadpool(reprocess_document, session, store, engine, document, current_user_id(request))
    return RedirectResponse(f"/documentos/{document.id}", status_code=303)
