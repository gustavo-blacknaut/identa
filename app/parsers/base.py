from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.ocr.base import TextBox
from app.validators.rules import DocumentRules, validate_fields


@dataclass
class ExtractedField:
    value: str
    confidence: float | None


@dataclass
class ExtractionResult:
    doc_type: str
    fields: dict[str, ExtractedField] = field(default_factory=dict)
    issues: list[dict[str, str]] = field(default_factory=list)
    raw_text: str = ""

    def values(self) -> dict[str, str]:
        return {name: extracted.value for name, extracted in self.fields.items()}


@dataclass(frozen=True)
class FieldDefinition:
    name: str
    label: str
    kind: str = "text"


class DocumentParser(ABC):
    doc_type: str
    display_name: str
    field_definitions: tuple[FieldDefinition, ...]
    rules: DocumentRules

    @abstractmethod
    def extract(self, front: list[TextBox], back: list[TextBox]) -> dict[str, ExtractedField]: ...

    def parse(self, front: list[TextBox], back: list[TextBox]) -> ExtractionResult:
        fields = {name: value for name, value in self.extract(front, back).items() if value.value}
        result = ExtractionResult(self.doc_type, fields, raw_text=build_raw_text(front, back))
        result.issues = self.validate(result.values())
        return result

    def validate(self, values: dict[str, str]) -> list[dict[str, str]]:
        return [
            {"field": issue.field_name, "code": issue.code.value, "message": issue.message}
            for issue in validate_fields(values, self.rules)
        ]


def build_raw_text(*sides: list[TextBox]) -> str:
    blocks = []
    for boxes in sides:
        ordered = sorted(boxes, key=lambda box: (round(box.center_y / max(box.height, 1)), box.x0))
        blocks.append("\n".join(box.text for box in ordered))
    return "\n\n".join(block for block in blocks if block)
