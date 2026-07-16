import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from AI.document_identifier import identify_document


def handle_request(capability_code, input_data, file=None, prompt_template=None, model_config=None):
    if capability_code != "IDENTIFY_DOCUMENT":
        raise ValueError("Unsupported Document Identifier capability")

    return identify_document(file)
