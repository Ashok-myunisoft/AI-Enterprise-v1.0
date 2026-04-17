from bots.base_bot import call_llm, build_messages

SYSTEM_PROMPT = """You are an enterprise business formula and calculation expert.
Help users understand business formulas, KPIs, metrics, and calculations.
Show step-by-step working when doing calculations.
Present formulas clearly using plain text notation."""


def respond(message: str, history: list, context: list, model_config: dict) -> str:
    return call_llm(build_messages(SYSTEM_PROMPT, history, message, context), model_config)
