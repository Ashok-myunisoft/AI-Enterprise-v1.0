import logging
import requests
import os
import json

logger = logging.getLogger(__name__)

BASE_URL = os.getenv("APPLICANT_URL")
DEFAULT_ENDPOINT = os.getenv("APPLICANT_ENDPOINT", "/gbaiapi/applicant")
DEFAULT_FILE_ENDPOINT = os.getenv("APPLICANT_FILE_ENDPOINT", "/gbaiapi/applicant/upload-file")


def _build_url(endpoint: str) -> str:
    if not BASE_URL:
        raise Exception("APPLICANT_URL not set")
    return f"{BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"


def call_applicant(capability_code: str, input_data: dict, file=None, prompt_template=None, model_config=None):
    headers = {}
    login = input_data.get("_login", "")
    if login:
        headers["Login"] = login

    config_payload = {
        "prompt": prompt_template,
        "model": model_config.get("model") if model_config else None,
        "temperature": model_config.get("temperature") if model_config else None,
    }

    # Keep internal execution metadata out of the service payload.
    internal_keys = {"_tenant_id", "_user_id", "_login"}
    safe_input = {k: v for k, v in input_data.items() if k not in internal_keys}

    if file is not None:
        file.file.seek(0)
        file_bytes = file.file.read()

        files = {
            "file": (file.filename, file_bytes, file.content_type)
        }

        data = {
            **{k: v for k, v in safe_input.items() if v is not None},
            **{k: v for k, v in config_payload.items() if v is not None},
            "capability_code": capability_code,
        }

        response = requests.post(
            _build_url(DEFAULT_FILE_ENDPOINT),
            files=files,
            data=data,
            headers=headers,
            timeout=120
        )
    else:
        if "message" in safe_input and isinstance(safe_input["message"], list):
            safe_input["message"] = json.dumps(
                safe_input["message"],
                separators=(",", ":")
            )

        payload = {
            **{k: v for k, v in safe_input.items() if v is not None},
            **{k: v for k, v in config_payload.items() if v is not None},
            "capability_code": capability_code,
        }

        response = requests.post(
            _build_url(DEFAULT_ENDPOINT),
            json=payload,
            headers=headers,
            timeout=120
        )

    if not response.ok:
        logger.error("Applicant service error %d: %s", response.status_code, response.text)

    response.raise_for_status()
    return response.json()


def handle_request(capability_code, input_data, file=None, prompt_template=None, model_config=None):
    return call_applicant(capability_code, input_data, file, prompt_template, model_config)