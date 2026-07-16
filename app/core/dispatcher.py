import importlib
import os
from core.registry import SERVICE_REGISTRY

_DEFAULT_TEMPERATURE = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))


def dispatch(initiative_code, capability_code, input_data, file=None, prompt_template=None, model_config=None):

    module_path = SERVICE_REGISTRY.get(initiative_code)

    if not module_path:
        raise Exception(f"Unsupported initiative: {initiative_code}")

    module = importlib.import_module(module_path)

    # Convert MAImodel ORM object to dict expected by adapters.
    # If model_config is already a dict (e.g. from a config version override), use it directly.
    model_dict = None
    if model_config is not None:
        if isinstance(model_config, dict):
            model_dict = model_config
        else:
            model_dict = {
                "model": model_config.modelcode,
                "temperature": _DEFAULT_TEMPERATURE,
            }

    return module.handle_request(
        capability_code,
        input_data,
        file=file,
        prompt_template=prompt_template,
        model_config=model_dict,
    )







