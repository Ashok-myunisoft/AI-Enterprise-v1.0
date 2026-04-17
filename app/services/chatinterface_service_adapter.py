import logging
import requests
import os

logger = logging.getLogger(__name__)

BASE_URL = os.getenv("CHATINTERFACE_AGENT_URL")


def call_chatinterface(capability_code: str, input_data: dict, file=None, prompt_template=None, model_config=None):
    content = input_data.get("message") or input_data.get("text", "")
    login = input_data.get("_login", "")
    headers = {"Login": login}

    url = f"{BASE_URL}/gbaiapi/chat_Interface"

    # 🔥 CONFIG INJECTION
    payload = {
        "message": content,
        "prompt": prompt_template,
        "model": model_config.get("model") if model_config else None,
        "temperature": model_config.get("temperature") if model_config else None
    }

    response = requests.post(url, json=payload, headers=headers, timeout=120)

    if not response.ok:
        logger.error("ChatInterface service error %d: %s", response.status_code, response.text)

    response.raise_for_status()
    return response.json()


def handle_request(capability_code, input_data, file=None, prompt_template=None, model_config=None):
    return call_chatinterface(capability_code, input_data, file, prompt_template, model_config)