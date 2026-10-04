from pathlib import Path

from fastapi.templating import Jinja2Templates

HIGH_CONFIDENCE = 0.9
MEDIUM_CONFIDENCE = 0.75

templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")


def confidence_level(confidence: float | None) -> str:
    if confidence is None:
        return "unknown"
    if confidence >= HIGH_CONFIDENCE:
        return "high"
    return "medium" if confidence >= MEDIUM_CONFIDENCE else "low"


templates.env.globals["confidence_level"] = confidence_level
