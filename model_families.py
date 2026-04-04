from abc import ABC


class BaseModelFamily(ABC):
    code_id: str = "MODEL"
    name: str = "model"
    fim_stop_tokens: list[str] = []
