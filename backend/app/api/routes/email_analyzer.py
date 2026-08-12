from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.rate_limit import limiter
from app.models.user import User
from app.schemas.email_analyzer import EmailAnalyzeRequest, EmailAnalyzeResponse
from app.services.email_analyzer_service import analyze_email as analyze_email_service

router = APIRouter(prefix="/email-analyzer", tags=["email-analyzer"])


@router.post("/analyze", response_model=EmailAnalyzeResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
def analyze_email(
    request: Request,
    payload: EmailAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EmailAnalyzeResponse:
    return analyze_email_service(db=db, user_id=current_user.id, request=payload)
