import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .streaming import stream_response
from .stream_manager import stream_manager

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
async def stream_response_endpoint(
    startup_delay: int = 0,
    token_delay: int = 100,
):
    return await stream_response(
        startup_delay=startup_delay / 1000,
        token_delay=token_delay / 1000,
    )

@app.get("/metrics")
async def metrics():
    return stream_manager.get_metrics()

@app.post("/reset-metrics")
async def reset_metrics():

    stream_manager.reset()

    return {"status": "reset"}
