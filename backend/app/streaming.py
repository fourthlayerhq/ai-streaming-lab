from sse_starlette.sse import EventSourceResponse

from .fake_llm import fake_token_generator


async def stream_response():
    async def event_generator():
        async for token in fake_token_generator():
            if token == "[DONE]":
                yield {
                    "event": "done",
                    "data": "completed",
                }

                break

            yield {
                "event": "message",
                "data": token,
            }

    return EventSourceResponse(event_generator())
