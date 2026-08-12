from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database — swap DATABASE_URL to a postgresql:// URL to move off SQLite.
    database_url: str = "sqlite:///./shield.db"

    # Auth
    jwt_secret: str = "change-me-in-.env"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    # AI — when anthropic_api_key is unset, the AI client wrapper falls back
    # to rule-based mock mode automatically.
    anthropic_api_key: str | None = None
    use_mock_ai: bool = False

    # CORS
    frontend_origin: str = "http://localhost:3000"

    # Session cookie (httpOnly JWT storage)
    cookie_name: str = "shield_access_token"
    # False for local http dev. Must be True (with HTTPS) in any real deployment —
    # otherwise the browser will silently refuse to set/send the cookie.
    cookie_secure: bool = False
    # "lax" works for local dev (same-site). Cross-site deployments (frontend and
    # backend on different domains, e.g. Vercel + Render) need "none", which also
    # requires cookie_secure=True — browsers reject SameSite=None without Secure.
    cookie_samesite: str = "lax"


settings = Settings()
