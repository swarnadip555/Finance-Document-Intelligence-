import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import fitz  # PyMuPDF
import docx

from modules.ocr_processor import ocr_engine

class PDFExtractor:
    def __init__(self, min_text_len_for_digital: int = 40):
        self.min_text_len_for_digital = min_text_len_for_digital

    def extract_document(self, file_path: str) -> Dict[str, Any]:
        """
        Main extraction entry point. Handles PDF and DOCX files.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = path.suffix.lower()
        if ext == ".pdf":
            return self._extract_pdf(file_path)
        elif ext in [".docx", ".doc"]:
            return self._extract_docx(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    def _extract_pdf(self, file_path: str) -> Dict[str, Any]:
        doc = fitz.open(file_path)
        pages_data: List[Dict[str, Any]] = []
        total_pages = len(doc)
        total_scanned_pages = 0

        for page_idx in range(total_pages):
            page = doc[page_idx]
            page_no = page_idx + 1

            # Extract native text
            native_text = page.get_text("text").strip()
            image_list = page.get_images(full=True)

            is_scanned = False
            ocr_used = False
            confidence = 1.0
            warning = None

            # Detect if page is essentially scanned (very little text but images present)
            if len(native_text) < self.min_text_len_for_digital and len(image_list) > 0:
                is_scanned = True
                total_scanned_pages += 1
                # Try OCR on rendered pixmap
                try:
                    pix = page.get_pixmap(dpi=150)
                    img_bytes = pix.tobytes("png")
                    ocr_res = ocr_engine.process_image_bytes(img_bytes)
                    ocr_text = ocr_res.get("text", "")
                    if len(ocr_text) > len(native_text):
                        final_text = ocr_text
                        ocr_used = True
                        confidence = ocr_res.get("confidence", 0.8)
                        warning = ocr_res.get("warning")
                    else:
                        final_text = native_text
                except Exception as e:
                    final_text = native_text
                    warning = f"OCR invocation failed: {str(e)}"
            else:
                final_text = native_text

            # Detect rough heading / section from first non-empty lines
            lines = [l.strip() for l in final_text.split("\n") if l.strip()]
            section_hint = lines[0] if lines else f"Page {page_no}"

            pages_data.append({
                "page_no": page_no,
                "text": final_text,
                "char_count": len(final_text),
                "word_count": len(final_text.split()),
                "is_scanned": is_scanned,
                "ocr_used": ocr_used,
                "confidence": confidence,
                "warning": warning,
                "section_hint": section_hint[:80]
            })

        is_predominantly_scanned = total_scanned_pages > (total_pages / 2)

        return {
            "file_path": file_path,
            "total_pages": total_pages,
            "scanned_pages_count": total_scanned_pages,
            "is_predominantly_scanned": is_predominantly_scanned,
            "pages": pages_data,
            "full_text": "\n\n".join([f"--- Page {p['page_no']} [{p['section_hint']}] ---\n{p['text']}" for p in pages_data])
        }

    def _extract_docx(self, file_path: str) -> Dict[str, Any]:
        doc = docx.Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        full_text = "\n\n".join(paragraphs)

        # In DOCX, simulate pages by chunks of paragraphs
        chunk_size = 8
        pages_data = []
        for i in range(0, max(1, len(paragraphs)), chunk_size):
            chunk = paragraphs[i:i + chunk_size]
            page_no = (i // chunk_size) + 1
            chunk_text = "\n".join(chunk)
            pages_data.append({
                "page_no": page_no,
                "text": chunk_text,
                "char_count": len(chunk_text),
                "word_count": len(chunk_text.split()),
                "is_scanned": False,
                "ocr_used": False,
                "confidence": 1.0,
                "warning": None,
                "section_hint": chunk[0][:80] if chunk else f"Section {page_no}"
            })

        return {
            "file_path": file_path,
            "total_pages": len(pages_data),
            "scanned_pages_count": 0,
            "is_predominantly_scanned": False,
            "pages": pages_data,
            "full_text": full_text
        }

pdf_extractor = PDFExtractor()

