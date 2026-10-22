from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from config import KNOWN_KEYS, build_config, normalize_key

app = FastAPI(title="Effective Config")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],     # any origin may read this endpoint
    allow_methods=["GET"],   # only GET is needed
    allow_headers=["*"],
)


@app.get("/effective-config")
def effective_config(sets: list[str] = Query(default=[], alias="set")):
    overrides = {}
    for item in sets:
        if "=" not in item:
            raise HTTPException(400, f"Invalid override '{item}', expected key=value")
        raw_key, value = item.split("=", 1)  # split on the FIRST '=' only
        key = normalize_key(raw_key)
        if key not in KNOWN_KEYS:
            raise HTTPException(400, f"Unknown key '{key}'")
        overrides[key] = value  # a later set= for the same key wins

    try:
        config = build_config(overrides)
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    config["api_key"] = "****"  # mask the secret, always
    return config
