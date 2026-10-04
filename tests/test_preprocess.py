import io

import cv2
import numpy as np
import pytest
from PIL import Image

from app.imaging.preprocess import InvalidImageError, find_document_corners, prepare_image
from tests.synthetic import encode_jpeg, photograph, render_rg_back


def test_detects_and_rectifies_photographed_document():
    card = render_rg_back()
    prepared = prepare_image(encode_jpeg(photograph(card)))
    assert prepared.document_detected
    height, width = prepared.ocr_image.shape[:2]
    expected_ratio = card.shape[1] / card.shape[0]
    assert width / height == pytest.approx(expected_ratio, rel=0.12)


def test_corners_are_close_to_real_document_area():
    corners = find_document_corners(photograph(render_rg_back()))
    assert corners is not None
    area = cv2.contourArea(corners.astype(np.float32))
    assert area > 1400 * 960 * 0.8


def test_outputs_are_compressed_and_original_is_untouched():
    original = encode_jpeg(photograph(render_rg_back()))
    prepared = prepare_image(original)
    assert prepared.thumbnail_webp[:4] == b"RIFF"
    assert prepared.processed_jpeg[:2] == b"\xff\xd8"
    assert len(prepared.thumbnail_webp) < len(original)
    assert prepared.original_mime == "image/jpeg"


def test_applies_exif_orientation():
    image = Image.new("RGB", (400, 200), "white")
    exif = Image.Exif()
    exif[0x0112] = 6
    buffer = io.BytesIO()
    image.save(buffer, "JPEG", exif=exif)
    prepared = prepare_image(buffer.getvalue())
    assert (prepared.width, prepared.height) == (200, 400)


def test_rejects_non_image():
    with pytest.raises(InvalidImageError):
        prepare_image(b"not an image")
