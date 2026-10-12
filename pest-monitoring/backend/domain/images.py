"""Checks and cleans an uploaded sighting photo (US-03).

Only JPG and PNG up to 10 MB are accepted; video and audio are out of scope.
The photo is re-saved without its metadata so the reporter's GPS position and
phone details (EXIF) are never stored.
"""
from __future__ import annotations

import io
from dataclasses import dataclass

from PIL import Image, UnidentifiedImageError

MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_PIXELS = 40_000_000  # protects against "decompression bomb" images
_ALLOWED = {"JPEG": "image/jpeg", "PNG": "image/png"}


class ImageRejected(ValueError):
    """The upload is not an acceptable sighting photo."""


@dataclass(frozen=True)
class CleanImage:
    content: bytes
    content_type: str
    extension: str
    width: int
    height: int


def clean_image(data: bytes) -> CleanImage:
    if not data:
        raise ImageRejected("The file is empty.")
    if len(data) > MAX_IMAGE_BYTES:
        raise ImageRejected("Photos must be 10 MB or smaller.")

    try:
        with Image.open(io.BytesIO(data)) as probe:
            probe.verify()  # detects truncated or fake files
        image = Image.open(io.BytesIO(data))
    except (UnidentifiedImageError, OSError, SyntaxError) as exc:
        raise ImageRejected("The file is not a valid image.") from exc

    image_format = image.format
    if image_format not in _ALLOWED:
        raise ImageRejected("Only JPG and PNG photos are accepted.")
    if image.width * image.height > MAX_PIXELS:
        raise ImageRejected("The photo's resolution is too large.")

    image.load()
    # Rebuild the image from its raw pixels only: EXIF, GPS and other metadata are dropped.
    clean = Image.frombytes(image.mode, image.size, image.tobytes())
    if image.mode == "P" and image.getpalette():
        clean.putpalette(image.getpalette())

    out = io.BytesIO()
    if image_format == "JPEG":
        if clean.mode not in ("RGB", "L"):
            clean = clean.convert("RGB")
        clean.save(out, format="JPEG", quality=90)
        extension = "jpg"
    else:
        clean.save(out, format="PNG", optimize=True)
        extension = "png"

    return CleanImage(out.getvalue(), _ALLOWED[image_format], extension, clean.width, clean.height)
