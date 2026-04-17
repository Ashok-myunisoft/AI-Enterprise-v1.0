from bots.base_bot import call_llm, build_messages

SYSTEM_PROMPT = """You are a helpful enterprise AI assistant.
Answer questions clearly and professionally.
If a question is outside your knowledge, say so politely and suggest the right resource."""


def respond(message: str, history: list, context: list, model_config: dict) -> str:
    return call_llm(build_messages(SYSTEM_PROMPT, history, message, context), model_config)
