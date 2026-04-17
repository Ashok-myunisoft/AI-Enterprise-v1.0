from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from core.database import get_db
from models.ai_config_version import AIConfigVersion
from services.config_resolver import get_next_version

router = APIRouter( prefix="/api/config", tags=["AI Config"])


@router.post("/draft")
def create_draft(data: dict, db: Session = Depends(get_db)):
    version = get_next_version(db, data["name"])

    config = AIConfigVersion(
        name=data["name"],
        version=version,
        prompt=data["prompt"],
        model=data["model"],
        temperature=data.get("temperature", 0.7),
        max_tokens=data.get("max_tokens", 1000),
        status="draft",
        created_by="admin"
    )

    db.add(config)
    db.commit()
    return {"message": "Draft created", "version": version}


@router.post("/{config_id}/approve")
def approve_config(config_id: str, db: Session = Depends(get_db)):
    config = db.query(AIConfigVersion).get(config_id)

    if not config:
        raise HTTPException(404, "Config not found")

    # deactivate old
    db.query(AIConfigVersion).filter(
        AIConfigVersion.name == config.name
    ).update({"is_active": False})

    config.status = "approved"
    config.is_active = True
    config.approved_at = datetime.utcnow()
    config.approved_by = "admin"

    db.commit()
    return {"message": "Config approved & activated"}


@router.get("/{name}/active")
def get_active(name: str, db: Session = Depends(get_db)):
    config = db.query(AIConfigVersion).filter(
        AIConfigVersion.name == name,
        AIConfigVersion.is_active == True
    ).first()

    if not config:
        raise HTTPException(404, "No active config")

    return config
    