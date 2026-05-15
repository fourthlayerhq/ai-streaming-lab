# AI Streaming Lab

Exploring AI response streaming, perceived latency and real-time system design.

---

## The Core Idea

Two AI systems can take the exact same total time to generate a response.

But the one that streams tokens progressively feels dramatically faster to users.

This project demonstrates that difference.

---

## What This Demo Shows

### Normal Response
- user waits several seconds
- no intermediate feedback
- full response appears at once

### Streaming Response
- tokens appear immediately
- continuous feedback loop
- system feels responsive

Same backend latency.

Very different user experience.

### Concurrent Streaming Simulation

The system can launch multiple simultaneous AI streams to simulate real-world concurrency.

It tracks:

- active streams
- queued streams
- completed streams
- average tokens per stream
- first token latency

This demonstrates how streaming systems behave under load and why concurrency management becomes important in real-time AI infrastructure.

---

## Live Latency Visualization

The system tracks first-token latency over time. This latency history helps visualize queue pressure and concurrency effects under load. The UI intentionally exposes real-time systems behavior, making it easier to observe bottlenecks and system recovery.

Each stream also transitions through a visible lifecycle:

```txt
queued → active → completed
```

---

## Why This Matters

Modern AI applications are increasingly real-time systems.

The challenge is no longer just:
- generating responses

But also:
- perceived responsiveness
- streaming UX
- concurrency handling
- infrastructure reliability
- system scalability

---

## Architecture

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

---

## Tech Stack

- FastAPI
- Server-Sent Events (SSE)
- Vanilla JavaScript
- HTML/CSS

---

## Running The Project

### Backend

```bash
cd backend

pip install -r requirements.txt

uvicorn app.main:app --reload
```

Backend runs on:

```txt
http://127.0.0.1:8000
```

---

### Frontend

```bash
cd frontend

python -m http.server 3000
```

Frontend runs on:

```txt
http://localhost:3000
```

---

## Why SSE Instead Of WebSockets?

For AI token streaming, SSE is often:
- simpler
- lighter
- easier to implement
- sufficient for one-way streaming

This repo intentionally keeps architecture minimal and focused.

---

## Future Improvements

- Real LLM integration
- Redis queues
- Observability
- Retry handling
- Rate limiting
- Streaming markdown rendering

---

## Important Note

This project intentionally focuses on one engineering concept:

> Why streaming dramatically improves perceived latency in AI systems.

It is not intended to be a full AI framework or ChatGPT clone.


## Architecture Notes

Detailed architecture breakdown available here:

- [Streaming Architecture](./architecture/streaming-architecture.md)