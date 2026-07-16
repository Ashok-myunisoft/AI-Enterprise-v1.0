import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from AI.parse_validate import parse_and_validate


def handle_request(capability_code, input_data, file=None, prompt_template=None, model_config=None):
    if capability_code != "PARSE_VALIDATE_DOCUMENT":
        raise ValueError("Unsupported Parse and Validate capability")

    return parse_and_validate(file)
