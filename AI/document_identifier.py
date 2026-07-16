import logging
import os

import requests

logger = logging.getLogger(__name__)

BASE_URL = os.getenv("DOCUMENT_IDENTIFIER_URL", "http://217.217.249.121:8050")
ENDPOINT = os.getenv("DOCUMENT_IDENTIFIER_ENDPOINT", "/classify-document")
TIMEOUT = int(os.getenv("DOCUMENT_IDENTIFIER_TIMEOUT", "120"))


def _build_url() -> str:
    if not BASE_URL:
        raise ValueError("DOCUMENT_IDENTIFIER_URL is not configured")
    return f"{BASE_URL.rstrip('/')}/{ENDPOINT.lstrip('/')}"


def identify_document(file):
    if file is None:
        raise ValueError("File is required for Document Identifier")

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
            "Document Identifier service error %d: %s",
            response.status_code,
            response.text,
        )

    response.raise_for_status()

    try:
        return response.json()
    except ValueError:
        return {"result": response.text}
