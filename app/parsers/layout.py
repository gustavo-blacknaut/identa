import re
import unicodedata
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from difflib import SequenceMatcher

from app.ocr.base import TextBox
from app.parsers.base import ExtractedField

LABEL_SIMILARITY = 0.82
MAX_BELOW_GAP_FACTOR = 3.5
SAME_LINE_FACTOR = 0.6

ValueCheck = Callable[[str], bool]


def normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", without_accents.upper()).strip()


def compact(text: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", normalize(text))


@dataclass(frozen=True)
class LabelMatch:
    box: TextBox
    remainder: str
    score: float


def match_label(box: TextBox, variants: Iterable[str]) -> LabelMatch | None:
    box_compact = compact(box.text)
    best: LabelMatch | None = None
    for variant in variants:
        variant_compact = compact(variant)
        if not variant_compact or not box_compact:
            continue
        prefix = box_compact[: len(variant_compact)]
        score = 1.0 if prefix == variant_compact else SequenceMatcher(None, prefix, variant_compact).ratio()
        if score < LABEL_SIMILARITY or (best and best.score >= score):
            continue
        best = LabelMatch(box, strip_label_prefix(box.text, variant_compact), score)
    return best


def strip_label_prefix(text: str, variant_compact: str) -> str:
    consumed = 0
    for index, char in enumerate(normalize(text)):
        if char.isalnum():
            consumed += 1
        if consumed == len(variant_compact):
            return text[index + 1:].strip(" :.-/").strip()
    return ""


def find_label(boxes: list[TextBox], variants: Iterable[str]) -> LabelMatch | None:
    variants = tuple(variants)
    matches = [match for box in boxes if (match := match_label(box, variants))]
    return max(matches, key=lambda match: (match.score, -match.box.y0), default=None)


def is_any_label(box: TextBox, all_labels: Iterable[str]) -> bool:
    match = match_label(box, all_labels)
    return bool(match and not match.remainder)


def boxes_right_of(label: TextBox, boxes: list[TextBox]) -> list[TextBox]:
    tolerance = label.height * SAME_LINE_FACTOR
    candidates = [
        box for box in boxes
        if box is not label and abs(box.center_y - label.center_y) <= tolerance and box.x0 >= label.x1 - label.height
    ]
    return sorted(candidates, key=lambda box: box.x0)


def boxes_below(label: TextBox, boxes: list[TextBox]) -> list[TextBox]:
    max_gap = label.height * MAX_BELOW_GAP_FACTOR
    candidates = [
        box for box in boxes
        if box is not label
        and box.y0 >= label.center_y
        and box.center_y > label.y1 - label.height * 0.2
        and box.x0 <= label.x1 + label.height * 2
        and box.x1 >= label.x0 - label.height
    ]
    candidates.sort(key=lambda box: (box.y0, abs(box.x0 - label.x0)))
    if not candidates or candidates[0].y0 - label.y1 > max_gap:
        return []
    return candidates


def find_value(
    boxes: list[TextBox],
    variants: Iterable[str],
    all_labels: Iterable[str],
    accepts: ValueCheck = bool,
    prefer: str = "below",
) -> ExtractedField | None:
    label = find_label(boxes, variants)
    if label is None:
        return None
    all_labels = tuple(all_labels)
    if label.remainder and accepts(label.remainder):
        return ExtractedField(label.remainder, label.box.confidence)
    directions = (boxes_below, boxes_right_of) if prefer == "below" else (boxes_right_of, boxes_below)
    for direction in directions:
        for candidate in direction(label.box, boxes)[:3]:
            if is_any_label(candidate, all_labels):
                continue
            if accepts(candidate.text):
                return ExtractedField(candidate.text.strip(), candidate.confidence)
    return None


def lines_below(boxes: list[TextBox], variants: Iterable[str], all_labels: Iterable[str], limit: int) -> list[TextBox]:
    label = find_label(boxes, variants)
    if label is None:
        return []
    all_labels = tuple(all_labels)
    lines: list[TextBox] = []
    previous_bottom = label.box.y1
    for candidate in boxes_below(label.box, boxes):
        if candidate.y0 - previous_bottom > label.box.height * MAX_BELOW_GAP_FACTOR:
            break
        if is_any_label(candidate, all_labels):
            break
        if lines and abs(candidate.center_y - lines[-1].center_y) < candidate.height * SAME_LINE_FACTOR:
            continue
        lines.append(candidate)
        previous_bottom = candidate.y1
        if len(lines) == limit:
            break
    return lines


def search_pattern(boxes: list[TextBox], pattern: re.Pattern) -> ExtractedField | None:
    for box in sorted(boxes, key=lambda item: (item.y0, item.x0)):
        match = pattern.search(normalize(box.text))
        if match:
            return ExtractedField(match.group(0), box.confidence)
    return None
