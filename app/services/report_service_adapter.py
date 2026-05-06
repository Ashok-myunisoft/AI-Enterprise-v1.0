import logging
import requests
import os
import json

logger = logging.getLogger(__name__)

BASE_URL = os.getenv("REPORT_ANALYZER_URL")


def call_report_analyzer(capability_code: str, input_data: dict, file=None, prompt_template=None, model_config=None):

    # 🔥 COMMON CONFIG
    config_payload = {
        "prompt": prompt_template,
        "model": model_config.get("model") if model_config else None,
        "temperature": model_config.get("temperature") if model_config else None
    }

    # 1️⃣ Chat
    if capability_code == "QUESTION_ANSWER":
        url = f"{BASE_URL}/chat"

        payload = {
            "session_id": input_data.get("session_id"),
            "content": input_data.get("message"),
            **config_payload
        }

        response = requests.post(url, json=payload, timeout=60)

    # 2️⃣ File
    elif file is not None:
        url = f"{BASE_URL}/upload-file"

        files = {
            "file": (file.filename, file.file, file.content_type)
        }

        response = requests.post(
            url,
            files=files,
            data=config_payload,
            timeout=120
        )

    # 3️⃣ JSON
    else:
        url = f"{BASE_URL}/upload-json"

        _internal_keys = {"_tenant_id", "_user_id", "_login", "session_id", "input_type"}
        safe_input = {k: v for k, v in input_data.items() if k not in _internal_keys}

        if "message" in safe_input and isinstance(safe_input["message"], list):
            safe_input["message"] = json.dumps(
                safe_input["message"],
                separators=(",", ":")
            )

        payload = {
            **safe_input,
            **config_payload
        }

        response = requests.post(url, json=payload, timeout=120)

    logger.debug("report_analyzer response: status=%d", response.status_code)

    response.raise_for_status()
    return response.json()


def handle_request(capability_code, input_data, file=None, prompt_template=None, model_config=None):
    return call_report_analyzer(capability_code, input_data, file, prompt_template, model_config)

    