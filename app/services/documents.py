from dataclasses import dataclass
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.base import utc_now
from app.db.models import AuditLog, Document, DocumentImage, DocumentStatus, ImageSide, Person
from app.imaging.preprocess import prepare_image
from app.ocr.base import OcrEngine, TextBox
from app.parsers.registry import get_parser
from app.storage.encrypted_store import EncryptedFileStore
from app.validators.cpf import normalize_cpf, only_digits
from app.validators.dates import format_brazilian_date, parse_brazilian_date

DOCUMENT_COLUMNS = (
    "full_name", "cpf", "birth_date", "mother_name", "father_name", "birthplace", "rg_number",
    "issuing_authority", "issue_date", "cnh_register", "cnh_category", "valid_until", "first_license_date", "mrz_raw",
)
DATE_COLUMNS = {"birth_date", "issue_date", "valid_until", "first_license_date"}
PERSON_COLUMNS = ("full_name", "birth_date", "mother_name", "father_name", "birthplace")


@dataclass(frozen=True)
class UploadedSide:
    side: ImageSide
    content: bytes


def to_column_value(name: str, value: str | None):
    text = (value or "").strip()
    if not text:
        return None
    if name in DATE_COLUMNS:
        return parse_brazilian_date(text)
    if name == "cpf":
        digits = only_digits(text)
        return digits if len(digits) == 11 else None
    return text


def to_display_value(name: str, value) -> str:
    if value is None:
        return ""
    if isinstance(value, date):
        return format_brazilian_date(value)
    if name == "cpf" and len(value) == 11:
        return f"{value[:3]}.{value[3:6]}.{value[6:9]}-{value[9:]}"
    return str(value)


def apply_values(document: Document, values: dict[str, str]) -> None:
    invalid_raw = {}
    extra = dict(document.extra_fields or {})
    for name, raw in values.items():
        if name in DOCUMENT_COLUMNS:
            converted = to_column_value(name, raw)
            setattr(document, name, converted)
            if raw and converted is None:
                invalid_raw[name] = raw
        else:
            extra[name] = raw
    extra["unparsed_values"] = invalid_raw
    document.extra_fields = extra


def document_values(document: Document) -> dict[str, str]:
    values = {name: to_display_value(name, getattr(document, name)) for name in DOCUMENT_COLUMNS}
    for name, raw in (document.extra_fields or {}).get("unparsed_values", {}).items():
        values[name] = raw
    return values


def process_document(
    session: Session,
    store: EncryptedFileStore,
    engine: OcrEngine,
    doc_type: str,
    sides: list[UploadedSide],
    user_id: int | None = None,
) -> Document:
    document = Document(doc_type=doc_type, ocr_engine=engine.name, created_by=user_id, field_confidence={}, extra_fields={})
    boxes_by_side: dict[ImageSide, list[TextBox]] = {ImageSide.FRONT: [], ImageSide.BACK: []}
    for uploaded in sides:
        prepared = prepare_image(uploaded.content)
        original = store.save("originals", uploaded.content)
        document.images.append(
            DocumentImage(
                side=uploaded.side,
                original_path=original.relative_path,
                processed_path=store.save("processed", prepared.processed_jpeg).relative_path,
                thumbnail_path=store.save("thumbnails", prepared.thumbnail_webp).relative_path,
                original_mime=prepared.original_mime,
                sha256=original.sha256,
                width=prepared.width,
                height=prepared.height,
            )
        )
        boxes_by_side[uploaded.side] = engine.read(prepared.ocr_image)
    apply_extraction(document, engine, boxes_by_side)
    session.add(document)
    session.flush()
    session.add(AuditLog(user_id=user_id, action="create", entity="document", entity_id=document.id))
    session.commit()
    return document


def apply_extraction(document: Document, engine: OcrEngine, boxes_by_side: dict[ImageSide, list[TextBox]]) -> None:
    result = get_parser(document.doc_type).parse(boxes_by_side[ImageSide.FRONT], boxes_by_side[ImageSide.BACK])
    document.extra_fields = {}
    for name in DOCUMENT_COLUMNS:
        setattr(document, name, None)
    apply_values(document, result.values())
    document.field_confidence = {name: field.confidence for name, field in result.fields.items()}
    document.extra_fields = {**document.extra_fields, "extracted": result.values(), "issues": result.issues}
    all_boxes = boxes_by_side[ImageSide.FRONT] + boxes_by_side[ImageSide.BACK]
    document.ocr_confidence_avg = sum(box.confidence for box in all_boxes) / len(all_boxes) if all_boxes else None
    document.raw_text = result.raw_text
    document.ocr_engine = engine.name
    document.processed_at = utc_now()
    document.status = DocumentStatus.PENDING_REVIEW
    document.reviewed_manually = False
    document.reviewed_at = None


def reprocess_document(
    session: Session, store: EncryptedFileStore, engine: OcrEngine, document: Document, user_id: int | None = None
) -> Document:
    boxes_by_side: dict[ImageSide, list[TextBox]] = {ImageSide.FRONT: [], ImageSide.BACK: []}
    for image in document.images:
        prepared = prepare_image(store.load(image.original_path))
        boxes_by_side[ImageSide(image.side)] = engine.read(prepared.ocr_image)
    apply_extraction(document, engine, boxes_by_side)
    session.add(AuditLog(user_id=user_id, action="reprocess", entity="document", entity_id=document.id))
    session.commit()
    return document


def review_document(session: Session, document: Document, values: dict[str, str], user_id: int | None = None) -> Document:
    extracted = (document.extra_fields or {}).get("extracted", {})
    apply_values(document, {name: values.get(name, "") for name in DOCUMENT_COLUMNS if name in values})
    parser = get_parser(document.doc_type)
    current = document_values(document)
    document.extra_fields = {**document.extra_fields, "issues": parser.validate(current)}
    document.reviewed_manually = any((extracted.get(name) or "") != (current.get(name) or "") for name in current)
    document.status = DocumentStatus.REVIEWED
    document.reviewed_at = utc_now()
    document.person = upsert_person(session, document)
    session.add(AuditLog(user_id=user_id, action="review", entity="document", entity_id=document.id))
    session.commit()
    return document


def upsert_person(session: Session, document: Document) -> Person:
    cpf = normalize_cpf(document.cpf or "")
    person = document.person
    if cpf:
        existing = session.scalar(select(Person).where(Person.cpf == cpf))
        if existing is not None:
            person = existing
    if person is None:
        person = Person()
        session.add(person)
    if cpf and person.cpf is None:
        person.cpf = cpf
    for name in PERSON_COLUMNS:
        value = getattr(document, name)
        if value:
            setattr(person, name, value)
    return person


def delete_document(session: Session, store: EncryptedFileStore, document: Document, user_id: int | None = None) -> None:
    for image in document.images:
        for path in (image.original_path, image.processed_path, image.thumbnail_path):
            if path:
                store.delete(path)
    person = document.person
    session.add(AuditLog(user_id=user_id, action="delete", entity="document", entity_id=document.id))
    session.delete(document)
    session.flush()
    if person is not None and not session.scalar(select(func.count()).where(Document.person_id == person.id)):
        session.delete(person)
    session.commit()


def delete_person(session: Session, store: EncryptedFileStore, person: Person, user_id: int | None = None) -> None:
    for document in list(person.documents):
        for image in document.images:
            for path in (image.original_path, image.processed_path, image.thumbnail_path):
                if path:
                    store.delete(path)
    session.add(AuditLog(user_id=user_id, action="delete", entity="person", entity_id=person.id))
    session.delete(person)
    session.commit()
