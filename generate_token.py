import os
from dotenv import load_dotenv
from jose import jwt

load_dotenv()

# ── Change these to match your DB values ──────────────────────
TENANT_ID = 1   # must exist in maiinitiative.tenantid
USER_ID   = 1   # any valid user id
# ──────────────────────────────────────────────────────────────

SECRET    = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

if not SECRET:
    raise ValueError("JWT_SECRET_KEY is not set in .env")

payload = {
    "tenantId": TENANT_ID,
    "userId":   USER_ID
}

token = jwt.encode(payload, SECRET, algorithm=ALGORITHM)

print("\nYour JWT token:\n")
print(f"Bearer {token}")
print("\nCopy the full line above (including 'Bearer ') into the authorization box.\n")


