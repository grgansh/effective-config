# Effective Config

A small FastAPI service that merges configuration from four layers and applies per-request overrides. It shows how real applications handle settings across development, staging, and production, following the [12-factor app](https://12factor.net/config) principle that configuration lives outside the code.

## Features

- Merges four configuration layers with a clear precedence order
- Accepts per-request overrides through `?set=key=value` query parameters
- Normalizes aliases (`NUM_WORKERS` → `workers`) and environment prefixes (`APP_*`)
- Coerces values to the correct types (`int`, `bool`, `str`)
- Masks secrets in every response
- Allows cross-origin requests from browsers (CORS)

## Configuration precedence

Later layers override earlier ones, from lowest to highest:

| Priority | Layer | Source |
|---|---|---|
| 1 (lowest) | Defaults | Hardcoded in `config.py` |
| 2 | Environment YAML | `config.<APP_ENV>.yaml` (default: `config.development.yaml`) |
| 3 | `.env` file | Project root, variables such as `NUM_WORKERS` |
| 4 | OS environment | Variables with the `APP_` prefix, such as `APP_WORKERS` |
| 5 (highest) | Query overrides | `?set=key=value` in the request URL |

Supported keys and types:

| Key | Type | Default |
|---|---|---|
| `port` | integer | `8000` |
| `workers` | integer | `1` |
| `debug` | boolean (`true`, `1`, `yes`, `on`, case-insensitive) | `false` |
| `log_level` | string | `info` |
| `api_key` | string (always masked as `****`) | `default-secret-000` |

## Requirements

- [uv](https://docs.astral.sh/uv/) (manages Python and dependencies)

Python is installed automatically by uv if needed. The version is pinned in `.python-version`.

## Getting started

```bash
# Clone and install dependencies
git clone https://github.com/grgansh/effective-config.git
cd effective-config
uv sync

# Create your local environment file
cp .env.example .env

# Start the server
uv run uvicorn main:app --reload
```

The API is now available at `http://127.0.0.1:8000`. Interactive docs are at `http://127.0.0.1:8000/docs`.

## Usage

### Get the effective configuration

```bash
curl "http://127.0.0.1:8000/effective-config"
```

```json
{"port": 8900, "workers": 8, "debug": false, "log_level": "info", "api_key": "****"}
```

### Apply overrides

Repeat `set` for each override. Overrides win over every other layer.

```bash
curl "http://127.0.0.1:8000/effective-config?set=port=9000&set=debug=true"
```

Unknown keys return `400 Bad Request`, so typos such as `?set=prot=9000` are reported instead of ignored.

## Running tests

```bash
uv run pytest
```

## Project structure

```
├── main.py                  # FastAPI app and endpoints
├── config.py                # layer merging, normalization, coercion
├── config.development.yaml  # development layer
├── .env.example             # template for local variables
├── tests/test_config.py     # precedence, coercion, and API tests
├── pyproject.toml           # dependencies and project metadata
└── uv.lock                  # exact dependency versions
```

## Deployment

This project deploys to [Vercel](https://vercel.com). Set `APP_WORKERS`, `APP_DEBUG`, and `APP_API_KEY` in the project's environment variables. The file `requirements.txt` is generated from `uv.lock`:

```bash
uv export --no-dev --no-hashes --no-emit-project -o requirements.txt
```

## Security notes

- Secrets are never returned by the API. `api_key` is always masked.
- `.env` is excluded from git. Only `.env.example` is committed.
- Set production secrets in the hosting platform's dashboard, not in files.
- Query parameters appear in logs and browser history, so do not pass real secrets through `?set=`.
