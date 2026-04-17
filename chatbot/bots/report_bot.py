from bots.base_bot import call_llm, build_messages

SYSTEM_PROMPT = """You are an enterprise report analyst.
Help users understand reports, trends, insights, and analytics.
Provide clear explanations of data patterns, KPIs, and business insights.
When referencing numbers, be precise and contextual."""


def respond(message: str, history: list, context: list, model_config: dict) -> str:
    return call_llm(build_messages(SYSTEM_PROMPT, history, message, context), model_config)
