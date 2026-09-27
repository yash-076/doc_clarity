import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.guided import (
    SendMessageRequest,
    MessageResponse,
    ConversationResponse,
)
from app.services.conversation_service import ConversationService

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.post(
    "/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a message in a multi-turn document conversation",
    description="Processes user follow-up message, rewrites query if ambiguous, retrieves relevant document chunks, and generates grounded assistant response with citations."
)
async def send_message(
    conversation_id: uuid.UUID,
    req: SendMessageRequest,
    db: Session = Depends(get_db)
):
    service = ConversationService()
    return await service.send_message(
        db=db,
        conversation_id=conversation_id,
        content=req.content
    )


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get conversation history",
    description="Returns complete conversation trajectory with user messages, assistant responses, citations, and confidence metrics."
)
def get_conversation(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    service = ConversationService()
    return service.get_conversation(db=db, conversation_id=conversation_id)
