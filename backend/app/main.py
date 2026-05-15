import asyncio
from pydantic import BaseModel

from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from .streaming import stream_response, background_stream_task
from .stream_manager import stream_manager
from .queue_manager import stream_semaphore

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

class ConfigUpdate(BaseModel):
    max_concurrent_slots: int = None
    failure_rate: float = None
    random_startup_delay: bool = None
    token_jitter: bool = None
    slow_stream_prob: float = None

@app.post("/config")
async def update_config(config: ConfigUpdate):
    if config.max_concurrent_slots is not None:
        await stream_semaphore.set_slots(config.max_concurrent_slots)
    
    if config.failure_rate is not None:
        stream_manager.config["failure_rate"] = config.failure_rate
    if config.random_startup_delay is not None:
        stream_manager.config["random_startup_delay"] = config.random_startup_delay
    if config.token_jitter is not None:
        stream_manager.config["token_jitter"] = config.token_jitter
    if config.slow_stream_prob is not None:
        stream_manager.config["slow_stream_prob"] = config.slow_stream_prob
        
    return {"status": "updated"}

class LaunchRequest(BaseModel):
    count: int
    startup_delay: int
    token_delay: int

@app.post("/launch")
async def launch_streams(req: LaunchRequest, background_tasks: BackgroundTasks):
    for _ in range(req.count):
        background_tasks.add_task(
            background_stream_task,
            startup_delay=req.startup_delay / 1000.0,
            token_delay=req.token_delay / 1000.0
        )
    return {"status": "launched", "count": req.count}
