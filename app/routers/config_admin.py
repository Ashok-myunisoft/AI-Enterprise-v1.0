from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from core.database import get_db
from core.auth import get_current_user
from models.ai_config_version import AIConfigVersion
from services.config_resolver import get_next_version

router = APIRouter(prefix="/api/config", tags=["AI Config"])


class ConfigDraftRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    prompt: str = Field(..., min_length=1)
    model: str = Field(..., min_length=1, max_length=100)
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(1000, ge=1, le=32000)


@router.post("/draft")
def create_draft(
    data: ConfigDraftRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    version = get_next_version(db, data.name)

    config = AIConfigVersion(
        name=data.name,
        version=version,
        prompt=data.prompt,
        model=data.model,
        temperature=data.temperature,
        max_tokens=data.max_tokens,
        status="draft",
        created_by=str(current_user["userId"])
    )

    db.add(config)
    db.commit()
    return {"message": "Draft created", "version": version}


@router.post("/{config_id}/approve")
def approve_config(
    config_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    config = db.get(AIConfigVersion, config_id)

    if not config:
        raise HTTPException(404, "Config not found")

    db.query(AIConfigVersion).filter(
        AIConfigVersion.name == config.name
    ).update({"is_active": False})

    config.status = "approved"
    config.is_active = True
    config.approved_at = datetime.utcnow()
    config.approved_by = str(current_user["userId"])

    db.commit()
    return {"message": "Config approved & activated"}


@router.get("/{name}/active")
def get_active(
    name: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    config = db.query(AIConfigVersion).filter(
        AIConfigVersion.name == name,
        AIConfigVersion.is_active == True
    ).first()

    if not config:
        raise HTTPException(404, "No active config")

    return config
