import os
import json
import uuid
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from config import UPLOADS_DIR, PROCESSED_DIR, ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB

DOCS_METADATA_FILE = PROCESSED_DIR / "documents.json"
FACTS_METADATA_DIR = PROCESSED_DIR / "facts"
FACTS_METADATA_DIR.mkdir(parents=True, exist_ok=True)

def _load_metadata() -> Dict[str, Any]:
    if not DOCS_METADATA_FILE.exists():
        return {}
    try:
        with open(DOCS_METADATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_metadata(data: Dict[str, Any]) -> None:
    with open(DOCS_METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def validate_file(filename: str, file_size_bytes: int) -> tuple[bool, Optional[str]]:
    if file_size_bytes <= 0:
        return False, "File is empty (0 bytes)."
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Unsupported file format '{ext}'. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}"
    max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size_bytes > max_bytes:
        return False, f"File size exceeds maximum allowed limit of {MAX_FILE_SIZE_MB}MB."
    return True, None

def save_uploaded_file(
    file_bytes: bytes,
    filename: str,
    entity: str = "Unknown Entity",
    doc_type: str = "Annual Report",
    period: str = "FY 2024-25",
    currency: str = "INR",
    scale: str = "crores",
    uploaded_by: str = "analyst"
) -> Dict[str, Any]:
    valid, err = validate_file(filename, len(file_bytes))
    if not valid:
        raise ValueError(err)

    doc_id = str(uuid.uuid4())[:8]
    sanitized_name = f"{doc_id}_{Path(filename).name}"
    save_path = UPLOADS_DIR / sanitized_name

    with open(save_path, "wb") as f:
        f.write(file_bytes)

    doc_info = {
        "id": doc_id,
        "filename": filename,
        "stored_filename": sanitized_name,
        "file_path": str(save_path),
        "file_size": len(file_bytes),
        "entity": entity,
        "document_type": doc_type,
        "period": period,
        "currency": currency.upper(),
        "scale": scale.lower(),
        "status": "uploaded",
        "created_at": datetime.now().isoformat(),
        "uploaded_by": uploaded_by,
        "page_count": 0,
        "is_scanned": False,
        "error_message": None,
    }

    metadata = _load_metadata()
    metadata[doc_id] = doc_info
    _save_metadata(metadata)
    return doc_info

def list_documents() -> List[Dict[str, Any]]:
    metadata = _load_metadata()
    return list(metadata.values())

def get_document(doc_id: str) -> Optional[Dict[str, Any]]:
    metadata = _load_metadata()
    return metadata.get(doc_id)

def update_document(doc_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    metadata = _load_metadata()
    if doc_id not in metadata:
        return None
    metadata[doc_id].update(updates)
    _save_metadata(metadata)
    return metadata[doc_id]

def delete_document(doc_id: str) -> bool:
    metadata = _load_metadata()
    if doc_id not in metadata:
        return False
    doc_info = metadata.pop(doc_id)
    _save_metadata(metadata)

    file_path = Path(doc_info.get("file_path", ""))
    if file_path.exists():
        try:
            file_path.unlink()
        except Exception:
            pass

    facts_file = FACTS_METADATA_DIR / f"{doc_id}_facts.json"
    if facts_file.exists():
        try:
            facts_file.unlink()
        except Exception:
            pass
    return True

def save_document_facts(doc_id: str, facts: Dict[str, Any]) -> None:
    facts_file = FACTS_METADATA_DIR / f"{doc_id}_facts.json"
    with open(facts_file, "w", encoding="utf-8") as f:
        json.dump(facts, f, indent=2, ensure_ascii=False)

def get_document_facts(doc_id: str) -> Optional[Dict[str, Any]]:
    facts_file = FACTS_METADATA_DIR / f"{doc_id}_facts.json"
    if not facts_file.exists():
        return None
    try:
        with open(facts_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def update_fact_review(doc_id: str, metric_code: str, new_value: float, reviewer: str = "analyst", reason: str = "") -> Optional[Dict[str, Any]]:
    facts = get_document_facts(doc_id)
    if not facts:
        return None

    for item in facts.get("extracted_facts", []):
        if item.get("metric_code") == metric_code:
            old_val = item.get("normalized_value")
            item["normalized_value"] = new_value
            item["review_status"] = "manually_verified"
            item["audit_history"] = item.get("audit_history", [])
            item["audit_history"].append({
                "timestamp": datetime.now().isoformat(),
                "reviewer": reviewer,
                "previous_value": old_val,
                "new_value": new_value,
                "reason": reason
            })
            save_document_facts(doc_id, facts)
            return item
    return None

