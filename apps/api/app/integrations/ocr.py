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
            if suffix in {".txt", ".csv"}:
                return self._extract_text(document, file_path)
        sidecar = self._sidecar_path(file_path)
        if sidecar and sidecar.exists():
            return self._extract_text(document, sidecar)
        confidence = self._metadata_confidence(document=document, file_path=file_path, sidecar_path=sidecar)
        return {
            "document_id": document["id"],
            "document_type": document["document_type"],
            "status": "metadata_only",
            "confidence": confidence,
            "text": "",
            "provider": "local_metadata_fallback",
            "confidence_factors": {
                "storage_key_present": bool(storage_key),
                "file_exists": bool(file_path and file_path.exists()),
                "sidecar_exists": bool(sidecar and sidecar.exists()),
                "known_document_type": document.get("document_type") in DOCUMENT_TYPE_BASE_CONFIDENCE,
            },
        }

    def _sidecar_path(self, file_path: Path | None) -> Path | None:
        if not file_path:
            return None
        return file_path.with_suffix(file_path.suffix + ".txt")

    def _extract_text(self, document: dict, file_path: Path) -> dict:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        confidence = self._text_confidence(text=text, provider="local_text")
        return {
            "document_id": document["id"],
            "document_type": document["document_type"],
            "status": "extracted",
            "confidence": confidence,
            "text": text[:8000],
            "provider": "local_text",
        }

    def _extract_pdf(self, document: dict, file_path: Path) -> dict:
        try:
            from pypdf import PdfReader
        except ImportError:
            return self._missing_dependency(document, "pypdf")
        reader = PdfReader(str(file_path))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        confidence = self._text_confidence(text=text, provider="pypdf", page_count=len(reader.pages))
        return {
            "document_id": document["id"],
            "document_type": document["document_type"],
            "status": "extracted",
            "confidence": confidence,
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
        confidence = self._text_confidence(text=text, provider="pytesseract")
        return {
            "document_id": document["id"],
            "document_type": document["document_type"],
            "status": "extracted",
            "confidence": confidence,
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

    def _metadata_confidence(self, *, document: dict, file_path: Path | None, sidecar_path: Path | None) -> float:
        score = DOCUMENT_TYPE_BASE_CONFIDENCE.get(document.get("document_type"), 0.24)
        if document.get("storage_key"):
            score += 0.08
        if file_path:
            suffix = file_path.suffix.lower()
            if suffix in {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".txt", ".csv"}:
                score += 0.07
            if file_path.exists():
                score += 0.18
        if sidecar_path and sidecar_path.exists():
            score += 0.12
        if document.get("file_name"):
            score += 0.04
        return round(min(score, 0.62), 2)

    def _text_confidence(self, *, text: str, provider: str, page_count: int | None = None) -> float:
        normalized = " ".join(text.split())
        if not normalized:
            return 0.35
        length_score = min(len(normalized) / 1200, 1.0) * 0.24
        line_score = min(len(text.splitlines()) / 12, 1.0) * 0.12
        keyword_score = min(_keyword_hits(normalized) / 5, 1.0) * 0.18
        provider_base = {"local_text": 0.45, "pypdf": 0.42, "pytesseract": 0.38}.get(provider, 0.36)
        page_bonus = 0.04 if page_count and page_count > 0 else 0
        return round(min(provider_base + length_score + line_score + keyword_score + page_bonus, 0.96), 2)


DOCUMENT_TYPE_BASE_CONFIDENCE = {
    "business_registration": 0.32,
    "tax_certificate": 0.31,
    "bank_letter": 0.28,
    "financial_statement": 0.3,
    "sustainability_certificate": 0.27,
    "insurance_certificate": 0.27,
    "quality_certificate": 0.27,
}

CONFIDENCE_KEYWORDS = {
    "legal name",
    "company name",
    "registration",
    "tax",
    "gstin",
    "country",
    "website",
    "certificate",
    "statement",
}


def _keyword_hits(text: str) -> int:
    lowered = text.lower()
    return sum(1 for keyword in CONFIDENCE_KEYWORDS if keyword in lowered)
