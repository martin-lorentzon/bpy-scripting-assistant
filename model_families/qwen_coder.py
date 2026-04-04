def build_fim_prompt(prefix, suffix):
    return f"<|fim_prefix|>{prefix}<|fim_suffix|>{suffix}<|fim_middle|>"
