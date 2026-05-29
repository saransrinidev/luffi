from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"

    # SLM Speed Settings
    slm_fast_model: str = "llama3.2:1b"       # Tiny model for simple tasks
    slm_medium_model: str = "llama3.2:3b"     # Default for most tasks
    slm_heavy_model: str = "llama3.2:3b"      # Same as medium (no extra download)
    slm_agent_model: str = "qwen2.5:7b"      # Agent — needs structured output
    slm_max_tokens: int = 150                 # Keep responses short
    slm_temperature: float = 0.3             # Lower = faster, more deterministic
    slm_cache_enabled: bool = True
    slm_cache_ttl: int = 3600                # Cache for 1 hour
    slm_context_window: int = 512            # Small context = faster inference
    slm_num_predict: int = 150               # Limit output tokens
    slm_num_ctx: int = 512                   # Limit context size sent to model
    slm_repeat_penalty: float = 1.1          # Avoid repetition (stops rambling)

    # App
    hotkey: str = "ctrl+;"
    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "info"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
