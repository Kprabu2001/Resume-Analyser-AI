from fastapi import APIRouter, HTTPException

from app.dependencies.auth_dependency import CurrentUserIdDep
from app.dependencies.db_dependency import AppSessionDep
from app.models.schemas import ChatRequest, ChatResponse
from app.services.chat_service import ChatService
from app.services.resume_service import ResumeService

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/", response_model=ChatResponse)
def chat(request: ChatRequest, app_session: AppSessionDep, user_id: CurrentUserIdDep):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    chat_service = ChatService(app_session)

    session_id = request.session_id
    if not session_id:
        session = chat_service.create_session(user_id)
        session_id = session.id

    resume = None
    if request.resume_id:
        resume = ResumeService(app_session).get_by_id(request.resume_id, user_id)

    result = chat_service.get_ai_response(
        session_id=session_id,
        user_message=request.message,
        user_id=user_id,
        resume=resume,
    )

    return ChatResponse(
        session_id=session_id,
        reply=result["reply"],
        intent=result["intent"],
    )


@router.delete("/session/{session_id}")
def delete_session(session_id: str, app_session: AppSessionDep, user_id: CurrentUserIdDep):
    ChatService(app_session).clear_session(session_id)
    return {"message": f"Session {session_id} cleared."}


@router.get("/history/{session_id}")
def chat_history(session_id: str, app_session: AppSessionDep, user_id: CurrentUserIdDep):
    return {
        "session_id": session_id,
        "messages": ChatService(app_session).get_history(session_id),
    }
