from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from core.config import JWT_SECRET_KEY, JWT_ALGORITHM

security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        tenant_id = payload.get("tenantId")
        user_id = payload.get("userId")

        if tenant_id is None or user_id is None:
            raise HTTPException(status_code=401, detail="Token missing tenantId or userId claims")

        return {"tenantId": tenant_id, "userId": user_id}

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
