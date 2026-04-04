from abc import ABC, abstractmethod
import inspect
import requests
import subprocess


PROVIDERS: list[type["BaseLLMProvider"]] = []


class BaseLLMProvider(ABC):
    code_id: str = "PROVIDER"
    name: str = "Provider"
    base_url: str = "http://"

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not inspect.isabstract(cls):
            PROVIDERS.append(cls)

    @classmethod
    @abstractmethod
    def get_models(cls, timeout=5) -> list[str]:
        pass

    @classmethod
    @abstractmethod
    def prompt(cls, session: requests.Session, base_url: str, model: str, prompt: str, **kwargs) -> str:
        pass


class Ollama(BaseLLMProvider):
    code_id = "OLLAMA"
    name = "Ollama"
    base_url = "http://localhost:11434"

    @classmethod
    def get_models(cls, timeout=5):
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                check=True,
                timeout=timeout
            )

            lines = result.stdout.strip().split("\n")
            models = []

            # Skip header line (usually: NAME ID SIZE MODIFIED)
            for line in lines[1:]:
                parts = line.split()
                if parts:
                    models.append(parts[0])

            return models

        except subprocess.TimeoutExpired:
            print(f"ollama list timed out after {timeout} seconds")
            return []
        except subprocess.CalledProcessError as e:
            print("Error running ollama:", e)
            return []
        except FileNotFoundError:
            print("Ollama is not installed or not in PATH.")
            return []

    @classmethod
    def prompt(cls, session, base_url, model, prompt, **kwargs):
        url = f"{base_url.rstrip('/')}/api/generate"

        allowed_options = {"num_thread", "num_predict", "stop", "temperature"}
        options = {k: v for k, v in kwargs.items() if k in allowed_options}

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": kwargs.get("stream", False),
            "raw": kwargs.get("raw", True),
            "options": {
                "stop": kwargs.get("stop", ["<|fim_prefix|>", "<|fim_suffix|>", "<|fim_middle|>", "<|cursor|>", "<|endoftext|>", "\n"]),
                ""
            },
        }


def get_completion(session: requests.Session, base_url, model, prompt):

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "raw": True,
        "options": {
            "stop": ,
            "num_predict": 64,  # Limit output length for speed
            "temperature": 0.0,  # Lower temperature is faster/more deterministic
            "num_thread": 4     # Ensure Ollama uses enough CPU cores
        }
    }

    try:
        response = session.post(url, json=payload, timeout=(2, 10))
        response.raise_for_status()
        return response.json().get("response", "Error: Key 'response' not found")

    except requests.exceptions.RequestException as e:
        return f"Error: {e}"
