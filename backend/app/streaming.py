import uuid
from datetime import datetime

from sse_starlette.sse import EventSourceResponse

from .fake_llm import fake_token_generator
from .models import StreamSession
from .stream_manager import stream_manager
from .queue_manager import stream_semaphore


async def stream_response(
    startup_delay=0,
    token_delay=0.1,
):

    async def event_generator():

        session = StreamSession(
            id=str(uuid.uuid4()),
            started_at=datetime.utcnow(),
        )

        stream_manager.create_session(session)

        is_queued = False
        try:

            stream_manager.increment_queue()
            is_queued = True

            yield {
                "event": "status",
                "data": "queued",
            }

            async with stream_semaphore:

                if is_queued:
                    stream_manager.decrement_queue()
                    is_queued = False

                yield {
                    "event": "status",
                    "data": "active",
                }

                first_token_sent = False

                from .fake_llm import StreamingFailure
                try:
                    async for token in fake_token_generator(
                        startup_delay=startup_delay,
                        token_delay=token_delay,
                        config=stream_manager.config
                    ):

                        if token == "[DONE]":

                            yield {
                                "event": "status",
                                "data": "completed",
                            }

                            yield {
                                "event": "done",
                                "data": "completed",
                            }

                            break

                        if not first_token_sent:

                            stream_manager.mark_first_token(
                                session.id
                            )

                            first_token_sent = True

                        stream_manager.increment_token(
                            session.id
                        )

                        yield {
                            "event": "message",
                            "data": token,
                        }
                except StreamingFailure as e:
                    yield {
                        "event": "status",
                        "data": "error",
                    }
                    yield {
                        "event": "error",
                        "data": str(e),
                    }

        finally:
            if is_queued:
                stream_manager.decrement_queue()
            stream_manager.complete_session(session.id)

    return EventSourceResponse(event_generator())