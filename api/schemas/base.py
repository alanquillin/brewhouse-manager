"""
Base Pydantic models with camelCase conversion.
"""

from pydantic import BaseModel, ConfigDict

from lib.util import camel_to_snake

def to_camel(string: str) -> str:
    """Convert snake_case to camelCase"""
    components = string.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


class CamelCaseModel(BaseModel):
    """
    Base model with automatic camelCase alias generation.
    Allows API to use camelCase (JavaScript convention) while
    Python code uses snake_case (Python convention).
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,  # Allow both snake_case and camelCase
        from_attributes=True,  # Allow ORM mode (from SQLAlchemy models)
    )

    def transform_meta(self, original_data):
        if not original_data:
            return {}

        if not isinstance(original_data, dict):
            return original_data
        
        data = {}
        for k, v in original_data.items():
            if isinstance(v, dict):
                v = self.transform_meta(v)
            if isinstance(v, list):
                v = [self.transform_meta(i) for i in v]
            data[camel_to_snake(k)] = v
        return data
