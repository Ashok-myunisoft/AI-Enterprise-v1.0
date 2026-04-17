import logging
import requests
import os

logger = logging.getLogger(__name__)

BASE_URL = os.getenv("EXTRACTOR_AGENT")


def call_extractor(capability_code: str, input_data: dict, file=None, prompt_template=None, model_config=None):

    if file is None:
        raise Exception("File is required for Extractor")

    url = f"{BASE_URL}/gbaiapi/ice_upload"

    file.file.seek(0)
    file_bytes = file.file.read()

    files = {
        "files": (file.filename, file_bytes, file.content_type)
    }

    # 🔥 CONFIG INJECTION (as form data)
    data = {
        "prompt": prompt_template,
        "model": model_config.get("model") if model_config else None
    }

    response = requests.post(
        url,
        files=files,
        data=data,
        timeout=120
    )

    if not response.ok:
        logger.error("Extractor service error %d: %s", response.status_code, response.text)

    response.raise_for_status()
    return response.json()


def handle_request(capability_code, input_data, file=None, prompt_template=None, model_config=None):
    return call_extractor(capability_code, input_data, file, prompt_template, model_config)