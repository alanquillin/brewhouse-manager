"""
Base Pydantic models with camelCase conversion.
"""

from pydantic import BaseModel, ConfigDict


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
