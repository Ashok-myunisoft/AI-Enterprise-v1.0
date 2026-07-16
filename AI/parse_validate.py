import logging
import os

import requests

logger = logging.getLogger(__name__)

BASE_URL = os.getenv("PARSE_VALIDATE_URL", "http://217.217.249.121:8030")
ENDPOINT = os.getenv("PARSE_VALIDATE_ENDPOINT", "/process-document")
TIMEOUT = int(os.getenv("PARSE_VALIDATE_TIMEOUT", "120"))


def _build_url() -> str:
    if not BASE_URL:
        raise ValueError("PARSE_VALIDATE_URL is not configured")
    return f"{BASE_URL.rstrip('/')}/{ENDPOINT.lstrip('/')}"


def parse_and_validate(file):
    if file is None:
        raise ValueError("File is required for Parse and Validate")

    file.file.seek(0)
    files = {
        "file": (file.filename, file.file, file.content_type)
    }

    response = requests.post(
        _build_url(),
        files=files,
        timeout=TIMEOUT,
    )

    if not response.ok:
        logger.error(
            "Parse and Validate service error %d: %s",
            response.status_code,
            response.text,
        )

    response.raise_for_status()

    try:
        return response.json()
    except ValueError:
        return {"result": response.text}
