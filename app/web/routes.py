import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Document, DocumentImage, DocumentStatus, ImageSide, Person
from app.imaging.preprocess import InvalidImageError
from app.ocr.base import OcrEngine
from app.parsers.registry import available_parsers, get_parser
from app.services.documents import (
    UploadedSide,
    delete_document,
    delete_person,
    process_document,
    reprocess_document,
    review_document,
)
from app.storage.encrypted_store import EncryptedFileStore
from app.web.deps import get_engine, get_session, get_store
from app.web.schemas import (
    DocumentDetail,
    DocumentTypeOut,
    OverviewOut,
    PersonOut,
    ReprocessIn,
    ReviewIn,
    StatsOut,
    document_detail,
    document_summary,
    person_out,
)

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)

SessionDep = Annotated[Session, Depends(get_session)]
StoreDep = Annotated[EncryptedFileStore, Depends(get_store)]
EngineDep = Annotated[OcrEngine, Depends(get_engine)]
RECENT_LIMIT = 200
NO_IMAGE_MESSAGE = "Envie pelo menos uma foto do documento."
PROCESSING_FAILED_MESSAGE = "Não foi possível processar a imagem. Tente novamente ou envie outra foto."


def current_user_id(request: Request) -> int | None:
    return request.session.get("user_id")


def load_document(session: Session, document_id: int) -> Document:
    document = session.get(Document, document_id)
    if document is None:
        raise HTTPException(404, "Documento não encontrado")
    return document


def detail(document: Document) -> DocumentDetail:
    return document_detail(document, get_parser(document.doc_type))


@router.get("/document-types")
def document_types() -> list[DocumentTypeOut]:
    return [DocumentTypeOut(doc_type=parser.doc_type, display_name=parser.display_name) for parser in available_parsers()]


@router.get("/overview")
def overview(session: SessionDep) -> OverviewOut:
    documents = session.scalars(select(Document).order_by(Document.processed_at.desc()).limit(RECENT_LIMIT)).all()
    stats = StatsOut(
        documents=session.scalar(select(func.count(Document.id))),
        pending=session.scalar(select(func.count(Document.id)).where(Document.status == DocumentStatus.PENDING_REVIEW)),
        people=session.scalar(select(func.count(Person.id))),
    )
    return OverviewOut(
        stats=stats,
        documents=[document_summary(document, get_parser(document.doc_type)) for document in documents],
    )


@router.post("/documents", status_code=201)
async def upload_document(
    request: Request,
    session: SessionDep,
    store: StoreDep,
    engine: EngineDep,
    doc_type: Annotated[str, Form()] = "",
    front: Annotated[UploadFile | None, File()] = None,
    back: Annotated[UploadFile | None, File()] = None,
) -> DocumentDetail:
    max_bytes = request.app.state.settings.max_upload_mb * 1024 * 1024
    sides = []
    for side, upload in ((ImageSide.FRONT, front), (ImageSide.BACK, back)):
        if upload is None or not upload.filename:
            continue
        content = await upload.read(max_bytes + 1)
        if len(content) > max_bytes:
            raise HTTPException(413, "Imagem maior que o limite permitido")
        sides.append(UploadedSide(side, content))
    if not sides:
        raise HTTPException(400, NO_IMAGE_MESSAGE)
    try:
        requested_type = doc_type or None
        if requested_type:
            get_parser(requested_type)
        document = await run_in_threadpool(
            process_document, session, store, engine, requested_type, sides, current_user_id(request)
        )
    except KeyError as error:
        raise HTTPException(400, str(error)) from error
    except InvalidImageError as error:
        raise HTTPException(400, str(error)) from error
    except Exception as error:
        logger.exception("Falha ao processar documento")
        raise HTTPException(500, PROCESSING_FAILED_MESSAGE) from error
    return detail(document)


@router.get("/documents/{document_id}")
def show_document(document_id: int, session: SessionDep) -> DocumentDetail:
    return detail(load_document(session, document_id))


@router.put("/documents/{document_id}")
def save_document(request: Request, document_id: int, payload: ReviewIn, session: SessionDep) -> DocumentDetail:
    document = load_document(session, document_id)
    allowed = get_parser(document.doc_type).field_names
    values = {name: value for name, value in payload.values.items() if name in allowed}
    review_document(session, document, values, current_user_id(request))
    return detail(document)


@router.post("/documents/{document_id}/reprocess")
async def reprocess(
    request: Request, document_id: int, payload: ReprocessIn, session: SessionDep, store: StoreDep, engine: EngineDep
) -> DocumentDetail:
    document = load_document(session, document_id)
    if payload.doc_type:
        try:
            get_parser(payload.doc_type)
        except KeyError as error:
            raise HTTPException(400, str(error)) from error
    try:
        await run_in_threadpool(
            reprocess_document, session, store, engine, document, current_user_id(request), payload.doc_type or None
        )
    except Exception as error:
        logger.exception("Falha ao reprocessar documento %s", document_id)
        session.rollback()
        raise HTTPException(500, PROCESSING_FAILED_MESSAGE) from error
    return detail(document)


@router.delete("/documents/{document_id}", status_code=204)
def remove_document(request: Request, document_id: int, session: SessionDep, store: StoreDep) -> Response:
    delete_document(session, store, load_document(session, document_id), current_user_id(request))
    return Response(status_code=204)


@router.get("/people")
def list_people(session: SessionDep) -> list[PersonOut]:
    people = session.scalars(select(Person).order_by(Person.updated_at.desc()).limit(RECENT_LIMIT)).all()
    return [person_out(person) for person in people]


@router.delete("/people/{person_id}", status_code=204)
def remove_person(request: Request, person_id: int, session: SessionDep, store: StoreDep) -> Response:
    person = session.get(Person, person_id)
    if person is None:
        raise HTTPException(404, "Pessoa não encontrada")
    delete_person(session, store, person, current_user_id(request))
    return Response(status_code=204)


@router.get("/images/{image_id}/{variant}")
def image(image_id: int, variant: str, session: SessionDep, store: StoreDep) -> Response:
    record = session.get(DocumentImage, image_id)
    if record is None:
        raise HTTPException(404, "Imagem não encontrada")
    variants = {
        "thumbnail": (record.thumbnail_path, "image/webp"),
        "processed": (record.processed_path, "image/jpeg"),
        "original": (record.original_path, record.original_mime),
    }
    path, media_type = variants.get(variant, (None, None))
    if not path:
        raise HTTPException(404, "Imagem não encontrada")
    return Response(store.load(path), media_type=media_type, headers={"Cache-Control": "private, max-age=300"})
