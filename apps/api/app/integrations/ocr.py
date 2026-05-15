from __future__ import annotations

from pathlib import Path

from app.config.settings import settings


class OCRClient:
    def extract_documents(self, documents: list[dict]) -> list[dict]:
        return [self.extract_document(document) for document in documents]

    def extract_document(self, document: dict) -> dict:
        storage_key = document.get("storage_key")
        file_path = Path(settings.local_storage_root) / storage_key if storage_key else None
        if file_path and file_path.exists():
            suffix = file_path.suffix.lower()
            if suffix == ".pdf":
                return self._extract_pdf(document, file_path)
            if suffix in {".png", ".jpg", ".jpeg", ".tiff"}:
                return self._extract_image(document, file_path)
        return {
            "document_id": document["id"],
            "document_type": document["document_type"],
            "status": "metadata_only",
            "confidence": 0.68,
            "text": "",
            "provider": "local_metadata_fallback",
        }

    def _extract_pdf(self, document: dict, file_path: Path) -> dict:
        try:
            from pypdf import PdfReader
        except ImportError:
            return self._missing_dependency(document, "pypdf")
        reader = PdfReader(str(file_path))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return {
            "document_id": document["id"],
            "document_type": document["document_type"],
            "status": "extracted",
            "confidence": 0.88 if text else 0.55,
            "text": text[:8000],
            "provider": "pypdf",
        }

    def _extract_image(self, document: dict, file_path: Path) -> dict:
        try:
            import pytesseract
            from PIL import Image
        except ImportError:
            return self._missing_dependency(document, "pytesseract_or_pillow")
        text = pytesseract.image_to_string(Image.open(file_path))
        return {
            "document_id": document["id"],
            "document_type": document["document_type"],
            "status": "extracted",
            "confidence": 0.86 if text else 0.5,
            "text": text[:8000],
            "provider": "pytesseract",
        }

    def _missing_dependency(self, document: dict, dependency: str) -> dict:
        return {
            "document_id": document["id"],
            "document_type": document["document_type"],
            "status": "dependency_missing",
            "confidence": 0.4,
            "text": "",
            "provider": dependency,
        }
