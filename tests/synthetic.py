from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from app.ocr.base import TextBox

FONT_CANDIDATES = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "C:/Windows/Fonts/arial.ttf",
)

FICTITIOUS_RG = {
    "rg_number": "48.217.395-6",
    "issue_date": "12/06/2015",
    "full_name": "MARIANA OLIVEIRA DOS SANTOS",
    "father_name": "CARLOS EDUARDO DOS SANTOS",
    "mother_name": "LUCIA HELENA OLIVEIRA",
    "birthplace": "CAMPINAS-SP",
    "birth_date": "23/09/1991",
    "cpf": "529.982.247-25",
    "issuing_authority": "SSP/SP",
}


def label_value_boxes(layout: list[tuple[str, float, float, float]], height: float = 20) -> list[TextBox]:
    return [TextBox(text, 0.97, x, y, x + width, y + height) for text, x, y, width in layout]


def rg_back_boxes(values: dict[str, str] = FICTITIOUS_RG) -> list[TextBox]:
    return label_value_boxes(
        [
            ("REGISTRO GERAL", 40, 40, 160),
            (values["rg_number"], 220, 40, 150),
            ("DATA DE EXPEDIÇÃO", 520, 40, 170),
            (values["issue_date"], 710, 40, 110),
            ("NOME", 40, 100, 50),
            (values["full_name"], 40, 128, 380),
            ("FILIAÇÃO", 40, 180, 80),
            (values["father_name"], 40, 208, 360),
            (values["mother_name"], 40, 236, 300),
            ("NATURALIDADE", 40, 300, 130),
            (values["birthplace"], 40, 328, 140),
            ("DATA DE NASCIMENTO", 520, 300, 190),
            (values["birth_date"], 520, 328, 110),
            ("DOC. ORIGEM", 40, 390, 110),
            ("CERT. NASC. LV 12 FL 34 N 5678", 40, 418, 320),
            ("CPF", 40, 470, 40),
            (values["cpf"], 40, 498, 150),
            ("ASSINATURA DO DIRETOR", 520, 540, 220),
            (f"LEI Nº 7.116 DE 29/08/83 {values['issuing_authority']}", 40, 580, 360),
        ]
    )


def load_font(size: int) -> ImageFont.FreeTypeFont:
    for candidate in FONT_CANDIDATES:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default(size)


def render_rg_back(values: dict[str, str] = FICTITIOUS_RG) -> np.ndarray:
    width, height = 1400, 960
    card = Image.new("RGB", (width, height), (214, 232, 214))
    draw = ImageDraw.Draw(card)
    label_font, value_font = load_font(22), load_font(34)
    for y in range(0, height, 6):
        draw.line([(0, y), (width, y)], fill=(205, 225, 207))
    draw.rectangle([10, 10, width - 10, height - 10], outline=(90, 120, 95), width=3)
    texts = [
        ("REGISTRO GERAL", (40, 40), label_font), (values["rg_number"], (260, 30), value_font),
        ("DATA DE EXPEDIÇÃO", (820, 40), label_font), (values["issue_date"], (1080, 30), value_font),
        ("NOME", (40, 130), label_font), (values["full_name"], (40, 162), value_font),
        ("FILIAÇÃO", (40, 250), label_font), (values["father_name"], (40, 282), value_font),
        (values["mother_name"], (40, 330), value_font),
        ("NATURALIDADE", (40, 430), label_font), (values["birthplace"], (40, 462), value_font),
        ("DATA DE NASCIMENTO", (820, 430), label_font), (values["birth_date"], (820, 462), value_font),
        ("DOC. ORIGEM", (40, 560), label_font), ("CERT. NASC. LV 12 FL 34 N 5678", (40, 592), value_font),
        ("CPF", (40, 690), label_font), (values["cpf"], (40, 722), value_font),
        ("ASSINATURA DO DIRETOR", (820, 800), label_font),
        (f"LEI Nº 7.116 DE 29/08/83   {values['issuing_authority']}", (40, 870), label_font),
    ]
    for text, position, font in texts:
        draw.text(position, text, fill=(25, 30, 28), font=font)
    return cv2.cvtColor(np.asarray(card), cv2.COLOR_RGB2BGR)


def photograph(card_bgr: np.ndarray, angle_degrees: float = 8, tilt: float = 0.06) -> np.ndarray:
    card_height, card_width = card_bgr.shape[:2]
    canvas_width, canvas_height = int(card_width * 1.6), int(card_height * 1.8)
    offset_x, offset_y = canvas_width * 0.18, canvas_height * 0.2
    source = np.float32([[0, 0], [card_width, 0], [card_width, card_height], [0, card_height]])
    destination = np.float32(
        [
            [offset_x + card_width * tilt, offset_y],
            [offset_x + card_width * (1 - tilt * 0.3), offset_y + card_height * tilt],
            [offset_x + card_width, offset_y + card_height * (1 + tilt)],
            [offset_x - card_width * tilt * 0.5, offset_y + card_height * (1 - tilt * 0.2)],
        ]
    )
    center = destination.mean(axis=0)
    rotation = cv2.getRotationMatrix2D(tuple(center), angle_degrees, 1.0)
    destination = cv2.transform(destination.reshape(-1, 1, 2), rotation).reshape(-1, 2).astype(np.float32)
    matrix = cv2.getPerspectiveTransform(source, destination)
    background = np.full((canvas_height, canvas_width, 3), (48, 42, 38), dtype=np.uint8)
    noise = np.random.default_rng(7).integers(0, 18, background.shape, dtype=np.uint8)
    background = cv2.add(background, noise)
    warped = cv2.warpPerspective(card_bgr, matrix, (canvas_width, canvas_height))
    mask = cv2.warpPerspective(np.full(card_bgr.shape[:2], 255, np.uint8), matrix, (canvas_width, canvas_height))
    background[mask > 0] = warped[mask > 0]
    return cv2.GaussianBlur(background, (3, 3), 0)


def encode_jpeg(image_bgr: np.ndarray) -> bytes:
    return cv2.imencode(".jpg", image_bgr, [cv2.IMWRITE_JPEG_QUALITY, 90])[1].tobytes()
