import importlib
from core.registry import SERVICE_REGISTRY


def dispatch(initiative_code, capability_code, input_data, file=None, prompt_template=None, model_config=None):

    module_path = SERVICE_REGISTRY.get(initiative_code)

    if not module_path:
        raise Exception(f"Unsupported initiative: {initiative_code}")

    module = importlib.import_module(module_path)

    # Convert MAImodel ORM object to dict expected by adapters
    model_dict = None
    if model_config is not None:
        model_dict = {
            "model": model_config.modelcode,
            "temperature": 0.7,
        }

    return module.handle_request(
        capability_code,
        input_data,
        file=file,
        prompt_template=prompt_template,
        model_config=model_dict,
    )







