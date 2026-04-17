import logging
import requests
import os

logger = logging.getLogger(__name__)
BASE_URL = os.getenv("CHATBOT_AGENT_URL")


def call_chatbot(capability_code: str, input_data: dict, file=None, prompt_template=None, model_config=None):

    session_id = input_data.get("session_id")
    content = input_data.get("message") or input_data.get("text", "")
    login = input_data.get("_login", "")
    headers = {"Login": login}

    payload = {
        "message": content,
        "prompt": prompt_template,
        "model": model_config.get("model") if model_config else None,
        "temperature": model_config.get("temperature") if model_config else None
    }

    if session_id:
        url = f"{BASE_URL}/gbaiapi/thread_chat"
        payload["thread_id"] = session_id
    else:
        url = f"{BASE_URL}/gbaiapi/chat"

    response = requests.post(url, json=payload, headers=headers, timeout=120)

    if not response.ok:
        logger.error("Chatbot error %d: %s", response.status_code, response.text)

    response.raise_for_status()
    return response.json()


def handle_request(capability_code, input_data, file=None, prompt_template=None, model_config=None):
    return call_chatbot(capability_code, input_data, file, prompt_template, model_config)