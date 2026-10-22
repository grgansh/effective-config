import os
from pathlib import Path

import yaml
from dotenv import dotenv_values

BASE_DIR = Path(__file__).parent

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

KNOWN_KEYS = set(DEFAULTS)
INT_KEYS = {"port", "workers"}
BOOL_KEYS = {"debug"}
ALIASES = {"NUM_WORKERS": "workers"}
TRUTHY = {"true", "1", "yes", "on"}


def normalize_key(raw: str) -> str:
    """Turn 'APP_WORKERS', 'NUM_WORKERS', or 'workers' into a canonical key."""
    key = raw.strip()
    if key in ALIASES:
        return ALIASES[key]
    if key.upper().startswith("APP_"):
        key = key[4:]
    return key.lower()


def load_yaml_layer(env_name: str) -> dict:
    path = BASE_DIR / f"config.{env_name}.yaml"
    if not path.exists():
        return {}  # a missing file is not an error; the layer is just empty
    with path.open() as f:
        data = yaml.safe_load(f) or {}
    return {normalize_key(k): v for k, v in data.items()}


def load_env_layer(source: dict) -> dict:
    """Keep only APP_* variables and known aliases; ignore everything else."""
    return {
        normalize_key(k): v
        for k, v in source.items()
        if k.upper().startswith("APP_") or k in ALIASES
    }


def coerce(key: str, value):
    if key in INT_KEYS:
        return int(value)  # raises ValueError on bad input like "abc"
    if key in BOOL_KEYS:
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in TRUTHY
    return str(value)


def build_config(overrides: dict) -> dict:
    env_name = os.getenv("APP_ENV", "development")

    dotenv_path = BASE_DIR / ".env"
    dotenv_layer = dotenv_values(dotenv_path) if dotenv_path.exists() else {}

    layers = [
        DEFAULTS,                                  # 1. lowest
        load_yaml_layer(env_name),                 # 2. config.<env>.yaml
        load_env_layer(dotenv_layer),              # 3. .env file
        load_env_layer(dict(os.environ)),          # 4. OS environment
        overrides,                                 # 5. ?set= (highest)
    ]

    merged = {}
    for layer in layers:
        for key, value in layer.items():
            if key in KNOWN_KEYS:
                merged[key] = value  # later layers overwrite earlier ones

    # Coerce after merging so all layers follow the same rules
    return {key: coerce(key, merged[key]) for key in DEFAULTS}

