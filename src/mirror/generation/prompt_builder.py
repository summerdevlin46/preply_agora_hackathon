"""
mirror/generation/prompt_builder.py

Trivial now — just selects the right narrative prompt from the cleanup output.
All prompt construction happens in cleanup.py.
"""
from mirror.generation.cleanup import MODES


def get_avatar_prompt(prompts: dict[str, str], mode: str) -> str:
    """
    Returns the avatar prompt for the given mode.
    Falls back to error_detective if mode is unrecognised.
    """
    if mode not in MODES:
        raise ValueError(f"Unknown mode '{mode}'. Must be one of {MODES}")
    return prompts[mode]
