"""Servidor local mínimo para os endpoints de Shorts."""
import os
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'), override=True)

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)s %(message)s')

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
    uvicorn.run(app, host="0.0.0.0", port=8000)
