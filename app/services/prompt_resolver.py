import time
from sqlalchemy.orm import Session
from models.prompt_template import MAIprompttemplate

_cache: dict = {}
_TTL = 300  # 5 minutes


def get_prompt(
    db: Session,
    initiative_code: str,
    capability_code: str,
    tenant_id: int,
):
    key = (tenant_id, initiative_code, capability_code)
    entry = _cache.get(key)
    if entry and time.monotonic() - entry["ts"] < _TTL:
        return entry["val"]

    prompt = (
        db.query(MAIprompttemplate)
        .filter(
            MAIprompttemplate.initiativecode == initiative_code,
            MAIprompttemplate.capabilitycode == capability_code,
            MAIprompttemplate.tenantid == tenant_id,
            MAIprompttemplate.status == 1,
        )
        .order_by(MAIprompttemplate.version.desc())
        .first()
    )

    result = prompt.prompttemplate if prompt else None
    _cache[key] = {"val": result, "ts": time.monotonic()}
    return result


def invalidate_prompt(tenant_id: int, initiative_code: str, capability_code: str):
    _cache.pop((tenant_id, initiative_code, capability_code), None)
