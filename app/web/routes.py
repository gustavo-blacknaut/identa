import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import RedirectResponse, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Document, DocumentImage, DocumentStatus, ImageKind, ImageSide, Person
from app.imaging.preprocess import InvalidImageError
from app.ocr.base import OcrEngine
from app.parsers.registry import available_parsers, get_parser
from app.services.documents import (
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
logger = logging.getLogger(__name__)

SessionDep = Annotated[Session, Depends(get_session)]
StoreDep = Annotated[EncryptedFileStore, Depends(get_store)]
EngineDep = Annotated[OcrEngine, Depends(get_engine)]
SIDE_LABELS = {"front": "Frente", "back": "Verso", "open": "Documento aberto"}
KIND_LABELS = {"portrait": "Foto", "fingerprint": "Polegar", "signature": "Assinatura"}
NO_IMAGE_MESSAGE = "Envie pelo menos uma foto do documento."
PROCESSING_FAILED_MESSAGE = "Não foi possível processar a imagem. Tente novamente ou envie outra foto."


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
    front: Annotated[UploadFile | None, File()] = None,
    back: Annotated[UploadFile | None, File()] = None,
    open_document: Annotated[UploadFile | None, File()] = None,
):
    max_bytes = request.app.state.settings.max_upload_mb * 1024 * 1024
    sides = []
    uploads = ((ImageSide.FRONT, front), (ImageSide.BACK, back))
    if open_document and open_document.filename:
        uploads = ((ImageSide.OPEN, open_document),)
    for side, upload in uploads:
        if upload is None or not upload.filename:
            continue
        content = await upload.read(max_bytes + 1)
        if len(content) > max_bytes:
            raise HTTPException(413, "Imagem maior que o limite permitido")
        sides.append(UploadedSide(side, content))
    if not sides:
        return templates.TemplateResponse(
            request, "new.html", {"parsers": available_parsers(), "error": NO_IMAGE_MESSAGE}, status_code=400
        )
    try:
        get_parser(doc_type)
        document = await run_in_threadpool(process_document, session, store, engine, doc_type, sides, current_user_id(request))
    except KeyError as error:
        raise HTTPException(400, str(error)) from error
    except InvalidImageError as error:
        return templates.TemplateResponse(
            request, "new.html", {"parsers": available_parsers(), "error": str(error)}, status_code=400
        )
    except Exception:
        logger.exception("Falha ao processar documento")
        return templates.TemplateResponse(
            request,
            "new.html",
            {"parsers": available_parsers(), "error": PROCESSING_FAILED_MESSAGE},
            status_code=500,
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
    values = document_values(document)
    extra_fields = [definition for definition in parser.field_definitions if definition.kind == "extra"]
    return templates.TemplateResponse(
        request,
        "document.html",
        {
            "document": document,
            "parser": parser,
            "values": values,
            "confidence": document.field_confidence or {},
            "issues": issues_by_field,
            "notes": extra.get("notes", []),
            "saved": request.query_params.get("salvo") == "1",
            "failed": request.query_params.get("erro") == "1",
            "main_fields": [definition for definition in parser.field_definitions if definition.kind != "extra"],
            "extra_fields": extra_fields,
            "extra_found": sum(1 for definition in extra_fields if values.get(definition.name)),
            "pages": [image for image in document.images if image.kind == ImageKind.PAGE],
            "crops": [image for image in document.images if image.kind != ImageKind.PAGE],
            "side_labels": SIDE_LABELS,
            "kind_labels": KIND_LABELS,
        },
    )


@router.post("/documentos/{document_id}")
async def save_document(request: Request, document_id: int, session: SessionDep):
    document = load_document(session, document_id)
    form = await request.form()
    values = {name: str(form[name]) for name in get_parser(document.doc_type).field_names if name in form}
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
    try:
        await run_in_threadpool(reprocess_document, session, store, engine, document, current_user_id(request))
    except Exception:
        logger.exception("Falha ao reprocessar documento %s", document_id)
        session.rollback()
        return RedirectResponse(f"/documentos/{document_id}?erro=1", status_code=303)
    return RedirectResponse(f"/documentos/{document.id}", status_code=303)
