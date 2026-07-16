import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from core.database import get_db
from core.auth import get_current_user
from models.prompt_template import MAIprompttemplate
from models.model import MAImodel
from services.prompt_resolver import invalidate_prompt
from services.model_resolver import invalidate_model

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin"])


class PromptUpdateRequest(BaseModel):
    tenantId: int = Field(gt=0)
    initiativeCode: str = Field(min_length=1, max_length=100)
    capabilityCode: str = Field(min_length=1, max_length=100)
    promptTemplate: str = Field(min_length=1, max_length=50000)


class ModelUpdateRequest(BaseModel):
    tenantId: int = Field(gt=0)
    modelname: str = Field(min_length=1, max_length=100)


@router.put("/prompt")
def update_prompt(
    body: PromptUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if body.tenantId != current_user["tenantId"]:
        raise HTTPException(status_code=403, detail="Not authorized to modify this tenant")

    prompt = db.query(MAIprompttemplate).filter(
        MAIprompttemplate.tenantid == body.tenantId,
        MAIprompttemplate.initiativecode == body.initiativeCode,
        MAIprompttemplate.capabilitycode == body.capabilityCode
    ).first()

    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    prompt.prompttemplate = body.promptTemplate
    prompt.version += 1

    db.commit()
    invalidate_prompt(body.tenantId, body.initiativeCode, body.capabilityCode)

    logger.info(
        "Prompt updated: tenant=%s initiative=%s capability=%s user=%s",
        body.tenantId, body.initiativeCode, body.capabilityCode, current_user["userId"]
    )
    return {"message": "Prompt updated successfully"}


@router.put("/model")
def update_model(
    body: ModelUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if body.tenantId != current_user["tenantId"]:
        raise HTTPException(status_code=403, detail="Not authorized to modify this tenant")

    model = db.query(MAImodel).filter(
        MAImodel.tenantid == body.tenantId,
        MAImodel.status == 1
    ).first()

    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    model.modelname = body.modelname

    db.commit()
    invalidate_model(body.tenantId)

    logger.info(
        "Model updated: tenant=%s model=%s user=%s",
        body.tenantId, body.modelname, current_user["userId"]
    )
    return {"message": "Model updated successfully"}
