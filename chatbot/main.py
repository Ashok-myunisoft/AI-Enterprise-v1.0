import logging
from fastapi import FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from orchestrator import chat
from config import CHATBOT_INTERNAL_SECRET

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)

if not CHATBOT_INTERNAL_SECRET:
    logging.getLogger(__name__).warning(
        "CHATBOT_INTERNAL_SECRET is not set — /chat endpoint is unauthenticated!"
    )

app = FastAPI(title="Chatbot Service", version="1.0.0")

_api_key_header = APIKeyHeader(name="X-Internal-Secret", auto_error=False)


def _require_internal_secret(secret: Optional[str] = Security(_api_key_header)):
    if CHATBOT_INTERNAL_SECRET and secret != CHATBOT_INTERNAL_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")


class ChatRequest(BaseModel):
    message:           str
    session_id:        Optional[str]         = None
    tenant_id:         int
    user_id:           int
    model_config_data: Dict[str, Any]


class ChatResponse(BaseModel):
    response:   str
    session_id: str
    bot_used:   str
    sql:        Optional[str]  = None
    data:       Optional[List] = None


@app.post("/chat", response_model=ChatResponse, dependencies=[Security(_require_internal_secret)])
def chat_endpoint(req: ChatRequest):
    try:
        result = chat(
            message=req.message,
            session_id=req.session_id,
            tenant_id=req.tenant_id,
            user_id=req.user_id,
            model_config=req.model_config_data,
        )
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {"status": "Chatbot Service Running"}


if __name__ == "__main__":
    import uvicorn
    from config import CHATBOT_PORT
    uvicorn.run(app, host="0.0.0.0", port=CHATBOT_PORT)
