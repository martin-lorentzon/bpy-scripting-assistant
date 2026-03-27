import requests


def build_fim_prompt(prefix, suffix):
    return f"<|fim_prefix|>{prefix}<|fim_suffix|>{suffix}<|fim_middle|>"


def get_completion(session: requests.Session, api_base_url, model, prompt):
    url = f"{api_base_url.rstrip('/')}/api/generate"

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "raw": True,
        "options": {
            "stop": ["<|fim_prefix|>", "<|fim_suffix|>", "<|fim_middle|>", "<|endoftext|>", "\n"],
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
