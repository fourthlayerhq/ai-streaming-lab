import asyncio


async def fake_token_generator():
    text = (
        "AI engineering is increasingly becoming systems engineering."
    )

    for token in text.split():
        await asyncio.sleep(0.4)
        yield token + " "
    
    yield "[DONE]"
