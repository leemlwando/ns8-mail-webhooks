#!/usr/bin/env python3
"""
Minimal Mail Webhooks API Server (kickstart pattern)
"""

import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict

app = FastAPI(title="Mail Webhooks API", version="1.0.0")

# Read config from environment
MONGODB_URL = os.getenv("MONGODB_URL", "")
TRAEFIK_HOST = os.getenv("TRAEFIK_HOST", "")

class Config(BaseModel):
    mongodb_url: str = ""
    traefik_host: str = ""

@app.get("/status")
def get_status() -> Dict:
    return {
        "mongodb_url": MONGODB_URL,
        "traefik_host": TRAEFIK_HOST
    }

@app.get("/config")
def get_config() -> Config:
    return Config(mongodb_url=MONGODB_URL, traefik_host=TRAEFIK_HOST)

@app.post("/config")
def set_config(cfg: Config):
    # In kickstart, config is set via actions, not API; here, just accept and return
    return cfg
