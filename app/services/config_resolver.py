from sqlalchemy.orm import Session
from models.ai_config_version import AIConfigVersion


def get_active_config(db: Session, name: str):
    return (
        db.query(AIConfigVersion)
        .filter(
            AIConfigVersion.name == name,
            AIConfigVersion.is_active == True
        )
        .first()   # 🔥 FIX: add ()
    )


def get_next_version(db: Session, name: str):
    last = (
        db.query(AIConfigVersion)
        .filter(AIConfigVersion.name == name)
        .order_by(AIConfigVersion.version.desc())
        .first()   # 🔥 FIX: add ()
    )

    return 1 if not last else last.version + 1
    