import uuid
from datetime import datetime

from sse_starlette.sse import EventSourceResponse

from .fake_llm import fake_token_generator
from .models import StreamSession
from .stream_manager import stream_manager


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

        try:

            first_token_sent = False

            async for token in fake_token_generator(
                startup_delay=startup_delay,
                token_delay=token_delay,
            ):

                if token == "[DONE]":

                    yield {
                        "event": "done",
                        "data": "completed",
                    }

                    break

                # IMPORTANT:
                # First token latency should measure:
                # request start -> first visible token

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

        finally:
            stream_manager.complete_session(session.id)

    return EventSourceResponse(event_generator())