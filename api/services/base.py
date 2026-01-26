"""
Base service class with common transformation utilities.
"""

from typing import Any, Dict, List, Union


def to_camel_case(string: str) -> str:
    """Convert snake_case to camelCase"""
    components = string.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def transform_dict_to_camel_case(data: Union[Dict, List, Any]) -> Union[Dict, List, Any]:
    """
    Recursively transform dict keys from snake_case to camelCase.
    Also removes None values from the output.
    """
    if data is None:
        return None

    if isinstance(data, dict):
        transformed = {}
        for key, val in data.items():
            # Skip None values
            if val is None:
                continue

            # Convert key to camelCase
            camel_key = to_camel_case(key) if "_" in key else key

            # Recursively transform nested structures
            if isinstance(val, dict):
                val = transform_dict_to_camel_case(val)
            elif isinstance(val, list):
                val = [transform_dict_to_camel_case(v) if isinstance(v, (dict, list)) else v for v in val]

            transformed[camel_key] = val

        return transformed

    elif isinstance(data, list):
        return [transform_dict_to_camel_case(item) if isinstance(item, (dict, list)) else item for item in data]

    else:
        return data


class BaseService:
    """
    Base service class with common transformation methods.
    """

    @staticmethod
    def transform_response(model_instance, **kwargs):
        """
        Transform SQLAlchemy model to dict with camelCase keys.
        Override in subclasses for custom logic.
        """
        if not model_instance:
            return None

        data = model_instance.to_dict()
        return transform_dict_to_camel_case(data)

    @staticmethod
    def transform_response_list(model_instances, **kwargs):
        """Transform list of SQLAlchemy models to list of dicts with camelCase keys"""
        return [BaseService.transform_response(instance, **kwargs) for instance in model_instances]
