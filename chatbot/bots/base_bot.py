import requests
import logging

logger = logging.getLogger(__name__)


def call_llm(messages: list, model_config: dict, max_tokens: int = 1500) -> str:
    resp = requests.post(
        f"{model_config['endpoint']}/chat/completions",
        headers={"Authorization": f"Bearer {model_config['apikey']}",
                 "Content-Type": "application/json"},
        json={"model": model_config["modelcode"], "messages": messages, "max_tokens": max_tokens},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def build_messages(system_prompt: str, history: list, user_message: str, context: list = None) -> list:
    messages = [{"role": "system", "content": system_prompt}]

    if context:
        messages.append({
            "role": "system",
            "content": "Relevant context from past interactions:\n" + "\n---\n".join(context)
        })

    messages.extend(history[-10:])   # last 5 exchanges
    messages.append({"role": "user", "content": user_message})
    return messages
