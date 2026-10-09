from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from job_hunt_api.config import get_settings
from job_hunt_api.database import get_db_session

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url=None,
)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready", tags=["system"])
def readiness(session: Session = Depends(get_db_session)) -> dict[str, str]:
    try:
        session.execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable.",
        ) from error

    return {"status": "ready"}
