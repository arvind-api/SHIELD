from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.rate_limit import limiter
from app.models.user import User
from app.schemas.guardian_scanner import ScanRequest, ScanResponse
from app.services.guardian_scanner_service import scan_text as scan_text_service

router = APIRouter(prefix="/guardian-scanner", tags=["guardian-scanner"])


@router.post("/scan", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
def scan_text(
    request: Request,
    payload: ScanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ScanResponse:
    return scan_text_service(db=db, user_id=current_user.id, request=payload)
