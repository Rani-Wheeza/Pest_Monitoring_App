"""Unit tests for domain.images (US-03 acceptance criteria)."""
import io
import unittest

from PIL import Image

from domain.images import MAX_IMAGE_BYTES, ImageRejected, clean_image


def make_image(fmt: str, exif: bool = False, mode: str = "RGB", size=(40, 30)) -> bytes:
    image = Image.new(mode, size, color=(120, 160, 90) if mode == "RGB" else 1)
    out = io.BytesIO()
    kwargs = {}
    if exif:
        data = Image.Exif()
        data[0x010F] = "PhoneMaker"          # camera make
        data[0x8825] = {2: (52.0, 16.0, 0.0)}  # GPS info block
        kwargs["exif"] = data.tobytes()
    image.save(out, format=fmt, **kwargs)
    return out.getvalue()


class CleanImageTests(unittest.TestCase):
    def test_accepts_jpeg(self):
        result = clean_image(make_image("JPEG"))
        self.assertEqual(result.content_type, "image/jpeg")
        self.assertEqual(result.extension, "jpg")
        self.assertEqual((result.width, result.height), (40, 30))

    def test_accepts_png(self):
        result = clean_image(make_image("PNG"))
        self.assertEqual(result.content_type, "image/png")

    def test_accepts_palette_png(self):
        result = clean_image(make_image("PNG", mode="P"))
        self.assertEqual(result.content_type, "image/png")

    def test_strips_exif_and_gps(self):
        original = make_image("JPEG", exif=True)
        self.assertTrue(Image.open(io.BytesIO(original)).getexif())  # test data really has EXIF
        cleaned = clean_image(original)
        self.assertEqual(len(Image.open(io.BytesIO(cleaned.content)).getexif()), 0)

    def test_rejects_gif(self):
        with self.assertRaises(ImageRejected):
            clean_image(make_image("GIF", mode="P"))

    def test_rejects_non_image(self):
        with self.assertRaises(ImageRejected):
            clean_image(b"this is not a picture")

    def test_rejects_empty(self):
        with self.assertRaises(ImageRejected):
            clean_image(b"")

    def test_rejects_over_10_mb(self):
        with self.assertRaises(ImageRejected):
            clean_image(b"\xff" * (MAX_IMAGE_BYTES + 1))

    def test_rejects_truncated_file(self):
        with self.assertRaises(ImageRejected):
            clean_image(make_image("PNG")[:60])


if __name__ == "__main__":
    unittest.main()
