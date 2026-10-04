import re

from app.ocr.base import TextBox
from app.parsers.base import DocumentParser, ExtractedField, FieldDefinition
from app.parsers.common import (
    CPF_PATTERN,
    as_cpf,
    as_date,
    as_name,
    clean_name,
    find_issuing_authority,
    first_present,
    has_cpf,
    has_date,
    looks_like_name,
)
from app.parsers.layout import find_value, lines_below, normalize, search_pattern
from app.parsers.registry import register
from app.validators.rules import DocumentRules

RG_NUMBER_PATTERN = re.compile(r"\d{1,3}\.?\d{3}\.?\d{3}\s?-?\s?[\dX]|\d{5,14}")

LABELS = {
    "rg_number": ("REGISTRO GERAL", "REG. GERAL", "RG"),
    "issue_date": ("DATA DE EXPEDICAO", "DATA EXPEDICAO", "EXPEDICAO", "DATA DE EMISSAO"),
    "full_name": ("NOME", "NOME SOCIAL"),
    "filiation": ("FILIACAO",),
    "birthplace": ("NATURALIDADE", "LOCAL DE NASCIMENTO"),
    "birth_date": ("DATA DE NASCIMENTO", "DATA NASCIMENTO", "NASCIMENTO"),
    "cpf": ("CPF", "C.P.F."),
    "origin_document": ("DOC. ORIGEM", "DOC ORIGEM", "DOCUMENTO DE ORIGEM"),
}
ALL_LABELS = tuple(variant for variants in LABELS.values() for variant in variants) + (
    "ASSINATURA DO DIRETOR",
    "ASSINATURA DO TITULAR",
    "VALIDA EM TODO O TERRITORIO NACIONAL",
    "LEI",
    "POLEGAR DIREITO",
    "SEXO",
    "NACIONALIDADE",
)


def accepts_rg_number(text: str) -> bool:
    return RG_NUMBER_PATTERN.search(normalize(text)) is not None and not has_cpf(text) and not has_date(text)


def extract_rg_number(field: ExtractedField | None) -> ExtractedField | None:
    if field is None:
        return None
    match = RG_NUMBER_PATTERN.search(normalize(field.value))
    return ExtractedField(re.sub(r"\s", "", match.group(0)), field.confidence) if match else None


def accepts_birthplace(text: str) -> bool:
    return len(text.strip()) >= 3 and not has_date(text) and not any(char.isdigit() for char in text)


@register
class RgParser(DocumentParser):
    doc_type = "rg"
    display_name = "RG (Carteira de Identidade)"
    field_definitions = (
        FieldDefinition("full_name", "Nome completo"),
        FieldDefinition("rg_number", "Número do RG"),
        FieldDefinition("issuing_authority", "Órgão expedidor"),
        FieldDefinition("issue_date", "Data de expedição", "date"),
        FieldDefinition("birth_date", "Data de nascimento", "date"),
        FieldDefinition("birthplace", "Naturalidade"),
        FieldDefinition("father_name", "Nome do pai"),
        FieldDefinition("mother_name", "Nome da mãe"),
        FieldDefinition("cpf", "CPF", "cpf"),
    )
    rules = DocumentRules(
        required_fields=("full_name", "rg_number", "birth_date"),
        cpf_fields=("cpf",),
        past_date_fields=("birth_date", "issue_date"),
        ordered_dates=(("birth_date", "issue_date"),),
    )

    def extract(self, front: list[TextBox], back: list[TextBox]) -> dict[str, ExtractedField]:
        boxes = back + front
        fields: dict[str, ExtractedField | None] = {
            "full_name": as_name(find_value(boxes, LABELS["full_name"], ALL_LABELS, looks_like_name)),
            "rg_number": extract_rg_number(
                find_value(boxes, LABELS["rg_number"], ALL_LABELS, accepts_rg_number, prefer="right")
            ),
            "issue_date": as_date(find_value(boxes, LABELS["issue_date"], ALL_LABELS, has_date, prefer="right")),
            "birth_date": as_date(find_value(boxes, LABELS["birth_date"], ALL_LABELS, has_date)),
            "birthplace": find_value(boxes, LABELS["birthplace"], ALL_LABELS, accepts_birthplace),
            "cpf": as_cpf(
                first_present(
                    find_value(boxes, LABELS["cpf"], ALL_LABELS, has_cpf, prefer="right"),
                    search_pattern(boxes, CPF_PATTERN),
                )
            ),
        }
        fields.update(self.extract_filiation(boxes))
        authority = next(
            (
                ExtractedField(found, box.confidence)
                for box in boxes
                if (found := find_issuing_authority(box.text))
            ),
            None,
        )
        fields["issuing_authority"] = authority
        return {name: value for name, value in fields.items() if value}

    def extract_filiation(self, boxes: list[TextBox]) -> dict[str, ExtractedField | None]:
        parents = [box for box in lines_below(boxes, LABELS["filiation"], ALL_LABELS, limit=4) if looks_like_name(box.text)]
        parents = [ExtractedField(clean_name(box.text), box.confidence) for box in parents[:2]]
        if len(parents) == 2:
            return {"father_name": parents[0], "mother_name": parents[1]}
        if len(parents) == 1:
            return {"mother_name": parents[0]}
        return {}
