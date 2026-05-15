# AI Streaming Lab Architecture

```txt
Frontend UI
    ↓
FastAPI Backend
    ↓
SSE Streaming Endpoint
    ↓
Concurrency Limiter (Semaphore)
    ↓
Fake Token Generator
    ↓
Stream Metrics Manager
```

## Components

### Frontend UI
- launches streams
- visualizes concurrent responses
- polls metrics dashboard

### FastAPI Backend
Handles:
- normal responses
- streaming responses
- metrics endpoint

### SSE Streaming Endpoint
Streams tokens incrementally to clients using Server-Sent Events.

### Concurrency Limiter
Uses an asyncio semaphore to simulate infrastructure constraints and concurrent stream limits.

### Fake Token Generator
Simulates token-by-token LLM output with configurable delays.

### Stream Metrics Manager
Tracks:
- active streams
- queued streams
- completed streams
- average first token latency
- token counts
```