import logging
import requests
import os

logger = logging.getLogger(__name__)

BASE_URL = os.getenv("GENERATE_PROFILE_URL")
DEFAULT_ENDPOINT = os.getenv("GENERATE_PROFILE_ENDPOINT", "/api/generate-profile")

_FIELDS = ["position", "department", "level", "industry", "context"]


def _build_url(endpoint: str) -> str:
    if not BASE_URL:
        raise Exception("GENERATE_PROFILE_URL not set")
    return f"{BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"


def _parse_plain_text(text: str) -> dict:
    """
    Parse a pipe-separated plain string into profile fields.
    Format: "position | department | level | industry | context"
    Only position, department, and level are required.
    """
    parts = [p.strip() for p in text.split("|")]
    result = {}
    for i, field in enumerate(_FIELDS):
        if i < len(parts) and parts[i]:
            result[field] = parts[i]
    return result


def call_generate_profile(capability_code: str, input_data: dict, prompt_template=None, model_config=None):
    internal_keys = {"_tenant_id", "_user_id", "_login"}
    safe_input = {k: v for k, v in input_data.items() if k not in internal_keys}

    # Plain string input — parse pipe-separated fields
    if "text" in safe_input and not safe_input.get("position"):
        parsed = _parse_plain_text(safe_input["text"])
        safe_input = {**safe_input, **parsed}

    if not safe_input.get("position") or not safe_input.get("department") or not safe_input.get("level"):
        raise ValueError(
            "generate_profile requires position, department, and level. "
            "Pass as plain string: 'position | department | level | industry | context' "
            "or as JSON: {\"position\": \"...\", \"department\": \"...\", \"level\": \"...\"}"
        )

    payload = {
        "position":   safe_input["position"],
        "department": safe_input["department"],
        "level":      safe_input["level"],
    }

    if safe_input.get("industry"):
        payload["industry"] = safe_input["industry"]

    if safe_input.get("context"):
        payload["context"] = safe_input["context"]

    if prompt_template:
        payload["prompt"] = prompt_template

    if model_config:
        if model_config.get("model"):
            payload["model"] = model_config["model"]
        if model_config.get("temperature") is not None:
            payload["temperature"] = model_config["temperature"]

    login = input_data.get("_login", "")
    headers = {"Login": login} if login else {}

    response = requests.post(
        _build_url(DEFAULT_ENDPOINT),
        json=payload,
        headers=headers,
        timeout=120,
    )

    if not response.ok:
        logger.error("GenerateProfile service error %d: %s", response.status_code, response.text)

    response.raise_for_status()
    return response.json()


def handle_request(capability_code, input_data, file=None, prompt_template=None, model_config=None):
    return call_generate_profile(capability_code, input_data, prompt_template, model_config)
