from bots.base_bot import call_llm, build_messages

SYSTEM_PROMPT = """You are a database schema expert.
Help users understand database structure, table relationships, field definitions, and data organization.
Explain technical concepts in simple, clear terms.
When describing tables, list key columns and their purpose."""


def respond(message: str, history: list, context: list, model_config: dict) -> str:
    return call_llm(build_messages(SYSTEM_PROMPT, history, message, context), model_config)
