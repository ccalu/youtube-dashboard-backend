"""Servidor local mínimo para os endpoints de Shorts."""
import os
import sys
import warnings
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'), override=True)

# Silenciar warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%H:%M:%S')

# Silenciar libs ruidosas
for noisy in [
    "httpx", "httpcore", "hpack", "uvicorn.access", "uvicorn.error",
    "googleapiclient", "googleapiclient.discovery", "google.auth",
    "google.auth.transport", "google.auth.transport.requests",
    "urllib3", "openai", "whisper", "numba",
    "supabase", "postgrest", "gotrue", "realtime", "storage3",
    "asyncio", "watchfiles", "multipart",
]:
    logging.getLogger(noisy).setLevel(logging.ERROR)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shorts_endpoints import router

app = FastAPI(title="Shorts Factory API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
