from fastapi import APIRouter, File, HTTPException, UploadFile, status

from src.attachment_schemas import AttachmentUploadResponse
from src.services.exceptions import ChatServiceError

router = APIRouter(prefix="/api", tags=["Attachments"])


@router.post(
    "/conversations/{conversation_id}/attachments",
    response_model=AttachmentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_attachment(
    conversation_id: str,
    file: UploadFile = File(...),
) -> AttachmentUploadResponse:
    from src.services.attachment_service import handle_attachment_upload
    from src.services.chat_service import build_chat_service

    service = build_chat_service()
    try:
        return await handle_attachment_upload(
            conversation_id=conversation_id,
            file=file,
            chat_service=service,
            conversation_mode=None,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found.",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except ChatServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
