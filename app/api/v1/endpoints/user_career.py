from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.core.exceptions import LLMRateLimitError
from app.dependencies.auth import get_current_career_user
from app.dependencies.database import get_db
from app.models.user import User
from app.schemas.career import (
    CareerAdviceResponse,
    CareerEvaluationOption,
    CareerJobMatchesResponse,
)
from app.schemas.career_chat import CareerChatRequest, CareerChatResponse
from app.schemas.resume import ResumeResponse
from app.schemas.user import UserCreate, UserResponse
from app.services import career as career_service
from app.services.auth import register_career_user
from app.services import resume as resume_service

router = APIRouter(
    prefix="/user-career",
    tags=["User Career"],
)


@router.post(
    "/register-user",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    """Register a career-portal user account."""
    try:
        return register_career_user(db, user_data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post(
    "/upload-cv",
    response_model=ResumeResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_cv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_career_user),
):
    """Upload and parse the logged-in career user's CV."""
    try:
        return resume_service.upload_resume(db=db, user=current_user, file=file)
    except LLMRateLimitError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=exc.message)


@router.get(
    "/resumes",
    response_model=list[ResumeResponse],
)
def get_my_resumes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_career_user),
):
    """List CVs uploaded by the logged-in career user."""
    return resume_service.get_user_resumes(db, current_user.id)


@router.post(
    "/chat",
    response_model=CareerChatResponse,
)
def career_chat(
    data: CareerChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_career_user),
):
    """Chat privately with the user's professional AI career coach."""
    try:
        response = career_service.chat_with_career_coach(
            db=db,
            user=current_user,
            message=data.message,
            history=data.history,
            resume_id=data.resume_id,
        )
        return CareerChatResponse(response=response)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except LLMRateLimitError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=exc.message)
@router.post(
    "/resumes/{resume_id}/evaluate",
    response_model=CareerJobMatchesResponse | CareerAdviceResponse,
)
def evaluate_cv(
    resume_id: UUID,
    option: CareerEvaluationOption = Query(
        CareerEvaluationOption.EXISTING_JOBS,
        description=(
            "existing_jobs checks this CV against HR-created jobs and returns matches "
            "above 60%. ai_career asks AI to suggest suitable career paths."
        ),
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_career_user),
):
    try:
        if option == CareerEvaluationOption.AI_CAREER:
            return career_service.get_ai_career_suggestions(
                db, resume_id, current_user
            )
        return career_service.match_existing_jobs(db, resume_id, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except LLMRateLimitError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=exc.message)
