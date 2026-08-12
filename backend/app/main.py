import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.routes import auth, email_analyzer, guardian_scanner
from app.config import settings
from app.core.rate_limit import limiter
from app.database import Base, engine
from app.models import EmailAnalysis, ScamScan, User  # noqa: F401 — ensures models are registered

logger = logging.getLogger("shield")

Base.metadata.create_all(bind=engine)

if settings.jwt_secret == "change-me-in-.env":
    logger.warning(
        "JWT_SECRET is still the default placeholder value. Tokens signed with it can be "
        "forged by anyone who reads this source. Set a long, random JWT_SECRET in .env "
        "before this is reachable outside your own machine."
    )

app = FastAPI(title="SHIELD API")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(email_analyzer.router)
app.include_router(guardian_scanner.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
