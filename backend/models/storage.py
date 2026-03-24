"""Load/save JSON files for route and model use (lists or single models)."""
import json
from typing import TypeVar

from pydantic import BaseModel, TypeAdapter, ValidationError

T = TypeVar("T", bound=BaseModel)


def load_optional(filepath: str, model_class: type[T]) -> list[T]:
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
        adapter = TypeAdapter(list[model_class])
        return adapter.validate_python(data)
    except (FileNotFoundError, json.JSONDecodeError, ValidationError) as e:
        if isinstance(e, ValidationError):
            print(f"[Storage] Validation error reading {filepath}: {e}")
        return []


def load_optional_single(filepath: str, model_class: type[T]) -> T | None:
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
        adapter = TypeAdapter(model_class)
        return adapter.validate_python(data)
    except (FileNotFoundError, json.JSONDecodeError, ValidationError) as e:
        if isinstance(e, ValidationError):
            print(f"[Storage] Validation error reading {filepath}: {e}")
        return None


def save(filepath: str, data: list[BaseModel]) -> None:
    with open(filepath, "w") as f:
        json.dump([d.model_dump() for d in data], f, indent=2)
        f.write("\n")


def save_single(filepath: str, model: BaseModel) -> None:
    with open(filepath, "w") as f:
        json.dump(model.model_dump(), f, indent=2)
        f.write("\n")
