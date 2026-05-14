import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .streaming import stream_response

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "AI Streaming Lab"}


@app.get("/normal-response")
async def normal_response():
    await asyncio.sleep(6)

    return {
        "response": "AI engineering is increasingly becoming systems engineering."
    }


@app.get("/stream-response")
async def stream_endpoint():
    return await stream_response()
