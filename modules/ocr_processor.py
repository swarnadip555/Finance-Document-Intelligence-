import io
import logging
from typing import Dict, Any, Optional
from PIL import Image

try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False

logger = logging.getLogger(__name__)

class OCRProcessor:
    def __init__(self, tesseract_cmd: Optional[str] = None):
        if tesseract_cmd and PYTESSERACT_AVAILABLE:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    def is_ocr_available(self) -> bool:
        if not PYTESSERACT_AVAILABLE:
            return False
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    def process_image(self, image: Image.Image) -> Dict[str, Any]:
        """
        Runs OCR on a PIL Image. Returns extracted text, confidence, and page metadata.
        If tesseract binary is not configured on system, falls back gracefully.
        """
        if not self.is_ocr_available():
            return {
                "text": "[OCR Engine not locally configured - PyTesseract engine unavailable]",
                "confidence": 0.0,
                "is_ocr": True,
                "warning": "OCR engine binary (tesseract) not found on host machine. Native digital PDF text was used."
            }

        try:
            # Run image to data to get confidence score
            ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            confidences = [int(c) for c in ocr_data.get("conf", []) if str(c).isdigit() and int(c) >= 0]
            avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

            text = pytesseract.image_to_string(image)
            return {
                "text": text.strip(),
                "confidence": round(avg_conf / 100.0, 2),
                "is_ocr": True,
                "warning": None if avg_conf > 60 else "Low OCR quality detected on this page."
            }
        except Exception as e:
            logger.warning(f"OCR processing failed: {e}")
            return {
                "text": "",
                "confidence": 0.0,
                "is_ocr": True,
                "warning": f"OCR extraction error: {str(e)}"
            }

    def process_image_bytes(self, image_bytes: bytes) -> Dict[str, Any]:
        try:
            img = Image.open(io.BytesIO(image_bytes))
            return self.process_image(img)
        except Exception as e:
            return {
                "text": "",
                "confidence": 0.0,
                "is_ocr": True,
                "warning": f"Image decoding error: {str(e)}"
            }

ocr_engine = OCRProcessor()

