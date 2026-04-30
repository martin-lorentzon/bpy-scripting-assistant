from abc import ABC, abstractmethod
import inspect


MODELS: list[type["BaseModelFamily"]] = []


class BaseModelFamily(ABC):
    activation_words: str = "base model"

    fim_stop_tokens: list[str] = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not inspect.isabstract(cls):
            MODELS.append(cls)

    @classmethod
    @abstractmethod
    def build_fim_prompt(cls, prefix: str, suffix: str) -> str:
        pass


class QwenCoder(BaseModelFamily):
    activation_words = "qwen coder"  # NOTE: Use spaces for separators

    fim_stop_tokens = ["<|fim_prefix|>", "<|fim_suffix|>",
                       "<|fim_middle|>", "<|cursor|>", "<|endoftext|>"]

    @classmethod
    def build_fim_prompt(cls, prefix, suffix, system_prompt=""):
        return f"{system_prompt}\n\n<|fim_prefix|>{prefix}<|fim_suffix|>{suffix}<|fim_middle|>"
