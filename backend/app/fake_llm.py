import asyncio


async def fake_token_generator(
    startup_delay=0,
    token_delay=0.1,
):

    response = """
    Streaming responses dramatically improve perceived latency.
    Users feel systems are faster because feedback starts immediately.
    """

    await asyncio.sleep(startup_delay)

    for word in response.split():

        yield word + " "

        await asyncio.sleep(token_delay)

    yield "[DONE]"
