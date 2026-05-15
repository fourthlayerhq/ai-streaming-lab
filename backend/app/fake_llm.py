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
    
    is_slow = False
    if config.get("slow_stream_prob", 0.0) > random.random():
        is_slow = True
        
    words = response.split()
    for word in words:
        
        # Inject failure
        if config.get("failure_rate", 0.0) > random.random():
            raise StreamingFailure("Random system failure injected")

        yield word + " "
        
        current_delay = token_delay
        if is_slow:
            current_delay *= random.uniform(2.0, 5.0)
        elif config.get("token_jitter"):
            current_delay *= random.uniform(0.5, 2.0)
            
        await asyncio.sleep(current_delay)

    yield "[DONE]"
