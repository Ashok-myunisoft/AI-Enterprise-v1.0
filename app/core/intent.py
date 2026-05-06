import json as _json
import logging
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
from models.capability import MAIcapability
from models.bot import MAIbot
from models.initiative import MAIinitiative
from models.prompt_template import MAIprompttemplate


def resolve_intent(db: Session, tenant_id: int, input_text: str = None, file=None, session_id: str = None, bot_hint: str = None):
    """
    Rule-based intent resolution by initiative:
      - bot_hint=chatbot            → CHATBOT_AGENT   (explicit chatbot routing)
      - bot_hint=applicant          → APPLICANT_AGENT (explicit applicant routing)
      - session_id + text           → REPORT_ANALYZER (QUESTION_ANSWER chat)
      - session_id + file           → REPORT_ANALYZER (upload-file to existing session)
      - File (no session/hint)      → EXTRACTOR_AGENT (document extraction)
      - JSON text (no session/hint) → REPORT_ANALYZER (upload-json for initial analysis)
      - Plain text (no session/hint)→ CREATOR_AGENT   (voucher/text generation)
    """

    # Determine rule — bot_hint takes highest priority
    if bot_hint == "chatinterface":
        rule = "chatinterface"
    elif bot_hint == "chatbot":
        rule = "chatbot"
    elif bot_hint == "applicant":
        rule = "applicant"
    elif session_id:
        rule = "report_session"
    elif file is not None:
        rule = "file"
    elif input_text:
        try:
            _json.loads(input_text)
            rule = "json"
        except (ValueError, TypeError):
            rule = "text"
    else:
        return None, None

    # Map rule → initiative keyword
    initiative_keyword = {
        "chatbot":        "chatbot",
        "chatinterface":  "chatinterface",
        "applicant":      "applicant",
        "file":           "extract",
        "json":           "report",
        "text":           "creator",
        "report_session": "report",
    }[rule]

    # Find the first active prompt template linked to the target initiative
    templates = db.query(MAIprompttemplate).filter(
        MAIprompttemplate.tenantid == tenant_id,
        MAIprompttemplate.status == 1
    ).all()

    logger.debug("[intent] rule=%s keyword=%s templates_found=%d", rule, initiative_keyword, len(templates))

    target_template = None
    for t in templates:
        if initiative_keyword in t.initiativecode.lower():
            target_template = t
            break

    if not target_template:
        logger.debug("[intent] FAIL: no template matched keyword=%r", initiative_keyword)
        return None, None

    # Resolve capability
    capability = db.query(MAIcapability).filter(
        MAIcapability.AIcapabilitycode == target_template.capabilitycode,
        MAIcapability.TENANTID == tenant_id
    ).first()

    if not capability:
        logger.debug("[intent] FAIL: capability not found for code=%r", target_template.capabilitycode)
        return None, None

    # Resolve initiative
    initiative = db.query(MAIinitiative).filter(
        MAIinitiative.aiinitiativecode == target_template.initiativecode,
        MAIinitiative.tenantid == tenant_id
    ).first()

    if not initiative:
        return capability.AIcapabilitycode, None

    # Resolve bot
    bot = db.query(MAIbot).filter(
        MAIbot.AIinitiativeid == initiative.aiinitiativeid,
        MAIbot.TENANTID == tenant_id,
        MAIbot.isreadonly == 1
    ).first()

    if not bot:
        return capability.AIcapabilitycode, None

    return capability.AIcapabilitycode, bot.AIbotcode
