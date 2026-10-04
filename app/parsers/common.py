import re

from app.parsers.base import ExtractedField
from app.parsers.layout import normalize
from app.validators.cpf import format_cpf, only_digits
from app.validators.dates import format_brazilian_date, parse_brazilian_date

CPF_PATTERN = re.compile(r"\d{3}\s?[.,]?\s?\d{3}\s?[.,]?\s?\d{3}\s?[-.]?\s?\d{2}")
DATE_PATTERN = re.compile(r"\d{1,2}\s?[/.\-]\s?\d{1,2}\s?[/.\-]\s?\d{2,4}")
ISSUING_AUTHORITY_PATTERN = re.compile(
    r"\b(SSP|SESP|SSPDS|SDS|SEJUSP|SESDEC|SSPCE|SJS|PC|PCII|IIRGD|IGP|IFP|DETRAN|DGPC|ITEP|IIPM|DIC|SEDS|POLITEC)"
    r"\s*[-/ ]?\s*(AC|AL|AP|AM|BA|CE|DF|ES|GO|MA|MT|MS|MG|PA|PB|PR|PE|PI|RJ|RN|RS|RO|RR|SC|SP|SE|TO)\b"
)
NAME_NOISE = re.compile(r"[^A-ZÀ-Ü' ]")


def looks_like_name(text: str) -> bool:
    cleaned = clean_name(text)
    return len(cleaned) >= 5 and " " in cleaned and not any(char.isdigit() for char in text)


def clean_name(text: str) -> str:
    return re.sub(r"\s+", " ", NAME_NOISE.sub(" ", text.upper())).strip()


def has_date(text: str) -> bool:
    return parse_brazilian_date(text) is not None


def has_cpf(text: str) -> bool:
    return CPF_PATTERN.search(normalize(text)) is not None


def as_name(field: ExtractedField | None) -> ExtractedField | None:
    return ExtractedField(clean_name(field.value), field.confidence) if field else None


def as_date(field: ExtractedField | None) -> ExtractedField | None:
    if field is None:
        return None
    parsed = parse_brazilian_date(field.value)
    return ExtractedField(format_brazilian_date(parsed) if parsed else field.value, field.confidence)


def as_cpf(field: ExtractedField | None) -> ExtractedField | None:
    if field is None:
        return None
    match = CPF_PATTERN.search(normalize(field.value))
    digits = only_digits(match.group(0) if match else field.value)
    return ExtractedField(format_cpf(digits), field.confidence)


def find_issuing_authority(text: str) -> str | None:
    match = ISSUING_AUTHORITY_PATTERN.search(normalize(text))
    return f"{match.group(1)}/{match.group(2)}" if match else None


def first_present(*candidates: ExtractedField | None) -> ExtractedField | None:
    return next((candidate for candidate in candidates if candidate and candidate.value), None)
