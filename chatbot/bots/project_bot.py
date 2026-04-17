from bots.base_bot import call_llm, build_messages

SYSTEM_PROMPT = """You are an enterprise project management assistant.
Help users with project information, status updates, timelines, task tracking, and project-related questions.
Be concise and structured in your responses. Use bullet points for lists."""


def respond(message: str, history: list, context: list, model_config: dict) -> str:
    return call_llm(build_messages(SYSTEM_PROMPT, history, message, context), model_config)
