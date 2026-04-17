import uuid
import logging

from memory.pg_history import save_message, get_history, ensure_table
from memory.faiss_store import search, add_text
from agents import sql_agent
from bots import general_bot, report_bot, menu_bot, project_bot, formula_bot, schema_bot
from bots.base_bot import call_llm

logger = logging.getLogger(__name__)

BOT_MAP = {
    "general": general_bot,
    "report":  report_bot,
    "menu":    menu_bot,
    "project": project_bot,
    "formula": formula_bot,
    "schema":  schema_bot,
}

_CLASSIFY_PROMPT = """Classify this user message into exactly one category. Reply with ONLY the category name, nothing else.

Categories:
- general  : greetings, general questions, small talk
- report   : report analysis, insights, trends, analytics, charts
- menu     : app navigation, features, how-to, help
- project  : project info, status, timelines, tasks, milestones
- formula  : formulas, calculations, metrics, KPIs, percentages
- schema   : database structure, tables, columns, relationships
- sql      : questions needing live data (totals, counts, lists, lookups)

Message: {message}"""


def _classify(message: str, model_config: dict) -> str:
    try:
        result = call_llm(
            [{"role": "user", "content": _CLASSIFY_PROMPT.format(message=message)}],
            model_config,
            max_tokens=10
        ).strip().lower()
        return result if result in {*BOT_MAP, "sql"} else "general"
    except Exception:
        return "general"


def chat(message: str, session_id: str, tenant_id: int, user_id: int, model_config: dict) -> dict:
    ensure_table()

    if not session_id:
        session_id = str(uuid.uuid4())

    history = get_history(session_id)
    context = search(tenant_id, message, top_k=3)
    intent  = _classify(message, model_config)

    logger.info("session=%s tenant=%s intent=%s", session_id, tenant_id, intent)

    if intent == "sql":
        result       = sql_agent.run(message, model_config, history)
        response_text = result["answer"]
        extra         = {"sql": result.get("sql"), "data": result.get("data", [])}
    else:
        bot_module    = BOT_MAP.get(intent, general_bot)
        response_text = bot_module.respond(message, history, context, model_config)
        extra         = {}

    save_message(session_id, tenant_id, user_id, "user",      message,       intent)
    save_message(session_id, tenant_id, user_id, "assistant", response_text, intent)
    add_text(tenant_id, f"Q: {message}\nA: {response_text}")

    return {
        "response":   response_text,
        "session_id": session_id,
        "bot_used":   intent,
        **extra,
    }
