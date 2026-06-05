from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

from fastapi import UploadFile
from pypdf import PdfReader

from src.attachment_schemas import AttachmentResource, AttachmentUploadResponse
from src.mock.schemas import MessageExchangeResponse, QuickActionMode
from src.services.chat_service import ChatService
from src.services.lab_results_service import generate_lab_results_reply

BASE_UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "uploads"
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
ALLOWED_CONTENT_TYPES = frozenset({"application/pdf", "text/plain"})
ALLOWED_EXTENSIONS = frozenset({".pdf", ".txt"})


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^\w.\- ]", "_", name).strip() or "upload"
    return cleaned[:120]


def _resolve_content_type(filename: str, reported_type: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return "application/pdf"
    if ext == ".txt":
        return "text/plain"
    normalized = reported_type.split(";")[0].strip().lower()
    if normalized in ALLOWED_CONTENT_TYPES:
        return normalized
    return normalized


def _validate_upload(filename: str, content_type: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            "Only PDF (.pdf) and plain text (.txt) files are accepted. "
            "Images and scans are not supported — use a text-based document."
        )
    resolved = _resolve_content_type(filename, content_type)
    if resolved not in ALLOWED_CONTENT_TYPES:
        raise ValueError(
            f"Unsupported file type '{content_type}'. "
            "Upload a .pdf or .txt file with selectable/copyable text (not a photo or scan)."
        )
    return resolved


def _extract_text(content_type: str, data: bytes) -> str:
    if content_type == "text/plain":
        return data.decode("utf-8", errors="replace")
    if content_type == "application/pdf":
        reader = PdfReader(BytesIO(data))
        parts: list[str] = []
        for page in reader.pages[:20]:
            text = page.extract_text()
            if text:
                parts.append(text)
        return "\n".join(parts)
    return ""


async def handle_attachment_upload(
    *,
    conversation_id: str,
    file: UploadFile,
    chat_service: ChatService,
    conversation_mode: QuickActionMode | None,
) -> AttachmentUploadResponse:
    conversation = chat_service._store.get_conversation(conversation_id)
    if not conversation:
        raise KeyError(conversation_id)

    filename = _safe_filename(file.filename or "upload")
    content_type = _validate_upload(
        filename,
        file.content_type or "application/octet-stream",
    )

    raw = await file.read()
    if len(raw) > MAX_UPLOAD_BYTES:
        raise ValueError(f"File too large (max {MAX_UPLOAD_BYTES // (1024 * 1024)} MB).")
    if len(raw) == 0:
        raise ValueError("Empty file.")

    extracted = _extract_text(content_type, raw)
    if not extracted.strip():
        raise ValueError(
            "No text could be extracted from this file. "
            "Upload a text-based PDF or a .txt file (not a scanned image or photo saved as PDF)."
        )

    attachment_id = str(uuid.uuid4())
    dest_dir = BASE_UPLOAD_DIR / conversation_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / f"{attachment_id}_{filename}"
    dest_path.write_bytes(raw)

    effective_mode: QuickActionMode | None = conversation.get("mode") or conversation_mode

    attachment = AttachmentResource(
        id=attachment_id,
        conversation_id=conversation_id,
        filename=filename,
        content_type=content_type,
        size_bytes=len(raw),
        created_at=_utc_now_iso(),
    )

    message_exchange: MessageExchangeResponse | None = None
    if effective_mode == "lab_results":
        user_content = (
            f"[Uploaded file: {filename}]\n\n"
            f"Extracted text (preview):\n{extracted[:1500]}"
        )
        reply = generate_lab_results_reply(extracted)
        message_exchange = chat_service._store.add_message_exchange(
            conversation_id,
            content=user_content,
            assistant_content=reply.content,
            mode="lab_results",
            metadata=reply.metadata,
        )
    else:
        message_exchange = chat_service._store.add_message_exchange(
            conversation_id,
            content=f"[Uploaded file: {filename}]",
            assistant_content=(
                f"File '{filename}' received ({len(extracted)} characters extracted). "
                "Switch to Lab Results mode to interpret numeric lab values from this document."
            ),
            mode=effective_mode,
        )

    return AttachmentUploadResponse(
        attachment=attachment,
        extracted_chars=len(extracted),
        message_exchange=message_exchange,
    )
