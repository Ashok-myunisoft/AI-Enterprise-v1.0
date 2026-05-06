import logging
import requests
import os

logger = logging.getLogger(__name__)
BASE_URL = os.getenv("CREATOR_AGENT_URL")


def call_creator(
    capability_code: str,
    input_data: dict,
    file=None,
    prompt_template: str = None,
    model_config: dict = None
):
    if capability_code != "GENERATE_VOUCHER":
        raise Exception("Unsupported Creator Capability")

    # 🔥 Accept both keys
    text = input_data.get("text") or input_data.get("input")
    if not text:
        raise Exception("'text' or 'input' field is required for Creator Agent")

    if not BASE_URL:
        raise Exception("CREATOR_AGENT_URL not set")

    url = f"{BASE_URL}/gbaiapi/voucher/from-text"

    # 🔥 SAFE CONFIG HANDLING
    model = model_config.get("model") if model_config else None
    temperature = model_config.get("temperature") if model_config else None

    # 🔥 PROMPT INJECTION (KEY FIX)
    final_text = text
    if prompt_template:
        final_text = f"{prompt_template}\n\nUser Request:\n{text}"

    # 🔥 FINAL PAYLOAD
    payload = {
        "text": final_text,   # 👈 IMPORTANT: injected prompt here
        "model": model,
        "temperature": temperature
    }

    logger.debug("creator request url=%s model=%s temperature=%s", url, model, temperature)

    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        logger.error("Creator service error: %s", str(e))
        raise Exception("Creator service failed")


def handle_request(
    capability_code,
    input_data,
    file=None,
    prompt_template=None,
    model_config=None
):
    return call_creator(
        capability_code,
        input_data,
        file,
        prompt_template,
        model_config
    )

    