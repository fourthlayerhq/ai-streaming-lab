import asyncio

from fastapi import FastAPI

from .streaming import stream_response


app = FastAPI()


@app.get("/")
async def root():
    return {"message": "AI Streaming Lab"}


@app.get("/normal-response")
async def normal_response():
    await asyncio.sleep(5)

    return {
        "response": "AI engineering is increasingly becoming systems engineering."
    }


@app.get("/stream-response")
async def stream_endpoint():
    return await stream_response()
