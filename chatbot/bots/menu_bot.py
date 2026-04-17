from bots.base_bot import call_llm, build_messages

SYSTEM_PROMPT = """You are an enterprise application guide.
Help users navigate the application and understand its features.
The system includes: AI execution, report analysis, document extraction, voucher generation, admin management, and chatbot.
Guide users step-by-step when they ask how to do something."""


def respond(message: str, history: list, context: list, model_config: dict) -> str:
    return call_llm(build_messages(SYSTEM_PROMPT, history, message, context), model_config)
