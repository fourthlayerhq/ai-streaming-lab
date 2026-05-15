import asyncio
import random


class StreamingFailure(Exception):
    pass


async def fake_token_generator(
    startup_delay=0,
    token_delay=0.1,
    config=None
):
    if config is None:
        config = {}

    response = """
    Streaming responses dramatically improve perceived latency.
    Users feel systems are faster because feedback starts immediately.
    """

    if config.get("random_startup_delay"):
        startup_delay += random.uniform(0.1, 1.5)

    await asyncio.sleep(startup_delay)

    failure_rate = config.get("failure_rate", 0.0)
    should_fail = random.random() < failure_rate

    words = response.split()

    if should_fail:
        fail_after_tokens = random.randint(
            1,
            max(1, len(words) - 1)
        )
    else:
        fail_after_tokens = None

    is_slow = (
        config.get("slow_stream_prob", 0.0)
        > random.random()
    )

    for index, word in enumerate(words):

        if should_fail and index >= fail_after_tokens:
            raise StreamingFailure(
                "Random system failure injected"
            )

        yield word + " "

        current_delay = token_delay

        if is_slow:
            current_delay *= random.uniform(2.0, 5.0)
        elif config.get("token_jitter"):
            current_delay *= random.uniform(0.5, 2.0)

        await asyncio.sleep(current_delay)

    yield "[DONE]"