import time
import os
from models.model import MAImodel

_cache: dict = {}
_TTL = 300  # 5 minutes


def get_model(db, tenant_id: int):
    entry = _cache.get(tenant_id)
    if entry and time.monotonic() - entry["ts"] < _TTL:
        return entry["val"]

    model = db.query(MAImodel).filter(
        MAImodel.status == 1,
        MAImodel.tenantid == tenant_id,
    ).first()

    # Cache as a plain dict — ORM objects become detached after the session closes
    result = {
        "model": model.modelcode,
        "temperature": float(os.getenv("DEFAULT_TEMPERATURE", "0.7")),
    } if model else None

    _cache[tenant_id] = {"val": result, "ts": time.monotonic()}
    return result


def invalidate_model(tenant_id: int):
    _cache.pop(tenant_id, None)
