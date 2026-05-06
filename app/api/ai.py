import json as _json
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.datastructures import UploadFile as StarletteUploadFile
from sqlalchemy.orm import Session
from core.database import get_db
from core.auth import get_current_user

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/gif",
    "text/plain",
    "text/csv",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "audio/mpeg",
    "audio/wav",
    "audio/ogg",
}
from core.intent import resolve_intent
from schemas.executes import ExecuteResponse, ExecutionDetail
from models.capability import MAIcapability
from models.initiative import MAIinitiative
from models.bot import MAIbot
from models.execution import TAIexecution
from services.prompt_resolver import get_prompt
from services.model_resolver import get_model
from core.dispatcher import dispatch

router = APIRouter(prefix="/api/ai", tags=["AI"])



@router.post(
    "/execute",
    response_model=ExecuteResponse,
    openapi_extra={
        "requestBody": {
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "input":      {"type": "string", "description": "Text input"},
                            "session_id": {"type": "string", "description": "Session ID"},
                            "bot_hint":   {"type": "string", "description": "Route hint: 'chatbot', 'chatinterface', or 'applicant'"},
                            "login":      {"type": "string", "description": "GoodBooks Login JSON (required for chatbot)"},
                            "file":       {"type": "string", "format": "binary", "description": "File upload"},
                        },
                    }
                }
            }
        }
    }
)
async def execute_ai(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    tenantId = current_user["tenantId"]
    userId = current_user["userId"]

    form = await request.form()
    input = form.get("input") or None
    session_id = form.get("session_id") or None
    bot_hint = form.get("bot_hint") or None
    login = form.get("login") or None
    raw_file = form.get("file")
    file = raw_file if isinstance(raw_file, StarletteUploadFile) and raw_file.filename else None

    if not input and not file:
        raise HTTPException(status_code=400, detail="Provide either input text or a file")

    # Validate uploaded file
    if file is not None:
        if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(status_code=400, detail="File type not allowed")
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large (max 50MB)")
        await file.seek(0)

    # Auto-detect input_type and build input_data
    if file is not None:
        input_type = "voice" if (file.content_type and file.content_type.startswith("audio/")) else "file"
        input_data = {"input_type": input_type}
    else:
        if bot_hint == "chatbot":
            input_data = {"message": input}
        else:
            try:
                parsed = _json.loads(input)
                input_data = parsed if isinstance(parsed, dict) else {"text": input}
            except (ValueError, TypeError):
                if session_id:
                    input_data = {"message": input}
                else:
                    input_data = {"text": input}

    if session_id:
        input_data["session_id"] = session_id

    # Pass tenant/user/login context for chatbot service
    input_data["_tenant_id"] = tenantId
    input_data["_user_id"] = userId
    if login:
        input_data["_login"] = login

    # Auto-resolve capabilityCode + botCode from input
    capabilityCode, botCode = resolve_intent(db, tenantId, input, file, session_id, bot_hint)

    if not capabilityCode:
        raise HTTPException(status_code=400, detail="Unable to detect capability from input")

    if not botCode:
        raise HTTPException(status_code=400, detail="No active bot found for detected capability")

    # Auto-resolve initiativeCode from botCode
    bot_lookup = db.query(MAIbot).filter(
        MAIbot.AIbotcode == botCode,
        MAIbot.TENANTID == tenantId
    ).first()
    if not bot_lookup:
        raise HTTPException(status_code=400, detail="Invalid Bot")

    initiative_lookup = db.query(MAIinitiative).filter(
        MAIinitiative.aiinitiativeid == bot_lookup.AIinitiativeid,
        MAIinitiative.tenantid == tenantId
    ).first()
    if not initiative_lookup:
        raise HTTPException(status_code=400, detail="Invalid Initiative")

    initiativeCode = initiative_lookup.aiinitiativecode

    prompt_template = get_prompt(
        db,
        initiativeCode,
        capabilityCode,
        tenantId
    )

    if not prompt_template:
        raise HTTPException(
            status_code=404,
            detail="Prompt template not configured"
        )


    model_config = get_model(db, tenantId)

    if not model_config:
        raise HTTPException(
            status_code=404,
            detail="Model not configured"
        )

    # 1️⃣ Validate Initiative
    initiative = db.query(MAIinitiative).filter(
        MAIinitiative.aiinitiativecode == initiativeCode,
        MAIinitiative.tenantid == tenantId
    ).first()

    if not initiative:
        raise HTTPException(status_code=400, detail="Invalid Initiative")

    # 2️⃣ Validate Capability
    capability = db.query(MAIcapability).filter(
        MAIcapability.AIcapabilitycode == capabilityCode,
        MAIcapability.TENANTID == tenantId
    ).first()

    if not capability:
        raise HTTPException(status_code=400, detail="Invalid Capability")

    # 3️⃣ Validate Bot
    bot = db.query(MAIbot).filter(
        MAIbot.AIbotcode == botCode,
        MAIbot.AIinitiativeid == initiative.aiinitiativeid,
        MAIbot.TENANTID == tenantId
    ).first()

    if not bot:
        raise HTTPException(status_code=400, detail="Invalid Bot")

    if bot.isreadonly != 1:
        raise HTTPException(status_code=403, detail="Bot is not read-only")

    # 4️⃣ Create Execution Log
    execution = TAIexecution(
        userid=userId,
        tenantid=tenantId,
        AIinitiativeid=initiative.aiinitiativeid,
        AIbotid=bot.AIbotid,
        AIcapabilityid=capability.AIcapabilityid,
        outcomestatus=0
    )

    try:
        db.add(execution)
        db.commit()
        db.refresh(execution)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create execution record")

    try:
        # 🔥 Call Service
        result = dispatch(
            initiativeCode,
            capabilityCode,
            input_data,
            file,
            prompt_template,
            model_config
        )

        # 6️⃣ Save Input & Output
        execution.inputpayload = input_data
        execution.outputpayload = result
        execution.sessionid = input_data.get("session_id")
        execution.outcomestatus = 1

        db.commit()
        db.refresh(execution)

    except Exception as e:
        logger.error("AI execution failed: %s", str(e), exc_info=True)
        execution.outcomestatus = -1
        execution.outputpayload = {"error": "execution_failed"}
        db.commit()
        raise HTTPException(status_code=500, detail="AI execution failed")

    return ExecuteResponse(
        executionId=execution.AIexecutionid,
        result=result
    )



@router.get("/execution/{execution_id}", response_model=ExecutionDetail)
def get_execution(
    execution_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    execution = db.query(TAIexecution).filter(
        TAIexecution.AIexecutionid == execution_id,
        TAIexecution.tenantid == current_user["tenantId"]
    ).first()

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    return execution

