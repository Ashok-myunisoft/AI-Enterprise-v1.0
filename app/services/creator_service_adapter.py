import requests
import os

BASE_URL = os.getenv("CREATOR_AGENT_URL")


def call_creator(capability_code: str, input_data: dict, file=None, prompt_template=None, model_config=None):

    if capability_code != "GENERATE_VOUCHER":
        raise Exception("Unsupported Creator Capability")

    text = input_data.get("text")
    if not text:
        raise Exception("'text' field is required for Creator Agent")

    url = f"{BASE_URL}/gbaiapi/voucher/from-text"

    # 🔥 CONFIG INJECTION
    payload = {
        "text": text,
        "prompt": prompt_template,
        "model": model_config.get("model") if model_config else None
    }

    response = requests.post(url, json=payload, timeout=120)

    response.raise_for_status()
    return response.json()


def handle_request(capability_code, input_data, file=None, prompt_template=None, model_config=None):
    return call_creator(capability_code, input_data, file, prompt_template, model_config)