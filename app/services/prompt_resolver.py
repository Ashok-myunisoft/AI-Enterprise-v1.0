from sqlalchemy.orm import Session
from models.prompt_template import MAIprompttemplate


def get_prompt(
    db: Session,
    initiative_code: str,
    capability_code: str,
    tenant_id: int
):
    prompt = (
        db.query(MAIprompttemplate)
        .filter(
            MAIprompttemplate.initiativecode == initiative_code,
            MAIprompttemplate.capabilitycode == capability_code,
            MAIprompttemplate.tenantid == tenant_id,
            MAIprompttemplate.status == 1
        )
        .order_by(MAIprompttemplate.version.desc())
        .first()
    )

    if not prompt:
        return None

    return prompt.prompttemplate