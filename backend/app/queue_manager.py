import asyncio


MAX_CONCURRENT_STREAMS = 3

stream_semaphore = asyncio.Semaphore(
    MAX_CONCURRENT_STREAMS
)