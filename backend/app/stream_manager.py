from datetime import datetime
from .queue_manager import stream_semaphore
import random
import uuid

class StreamManager:

    def __init__(self):
        self.queued_streams = []
        self.active_streams = {}
        self.completed_streams = []
        self.failed_streams = []
        
        self.events = []
        
        self.config = {
            "failure_rate": 0.0,
            "random_startup_delay": False,
            "token_jitter": False,
            "slow_stream_prob": 0.0
        }
        self.start_time = datetime.utcnow()
        self.total_completed_tokens = 0
        
        # for throughput rolling window
        self.completion_times = []

    def reset(self):
        self.queued_streams = []
        self.active_streams = {}
        self.completed_streams = []
        self.failed_streams = []
        self.events = []
        self.start_time = datetime.utcnow()
        self.total_completed_tokens = 0
        self.completion_times = []

    def log_event(self, stream_id, event_type, details=""):
        self.events.append({
            "stream_id": stream_id,
            "type": event_type,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        })
        if len(self.events) > 300:
            self.events.pop(0)

    def create_session(self, session):
        self.queued_streams.append(session)
        self.log_event(session.id, "queued")

    def assign_worker(self, session_id):
        # Move from queued to active
        session = next((s for s in self.queued_streams if s.id == session_id), None)
        if session:
            self.queued_streams.remove(session)
            session.started_at = datetime.utcnow()
            self.active_streams[session.id] = session
            self.log_event(session.id, "assigned", "worker assigned")

    def mark_first_token(self, session_id):
        session = self.active_streams.get(session_id)
        if session and not session.first_token_at:
            session.first_token_at = datetime.utcnow()
            latency = int((session.first_token_at - session.started_at).total_seconds() * 1000)
            self.log_event(session.id, "first_token", f"{latency}ms latency")

    def increment_token(self, session_id):
        session = self.active_streams.get(session_id)
        if session:
            session.token_count += 1

    def complete_session(self, session_id):
        session = self.active_streams.pop(session_id, None)
        if session:
            session.completed_at = datetime.utcnow()
            session.status = "completed"
            self.completed_streams.append(session)
            
            duration = round((session.completed_at - session.started_at).total_seconds(), 1)
            self.log_event(session.id, "completed", f"in {duration}s")
            
            # Record for throughput rolling window (last 60s)
            self.completion_times.append(datetime.utcnow())
            # Cleanup old completion times
            cutoff = datetime.utcnow().timestamp() - 60
            self.completion_times = [t for t in self.completion_times if t.timestamp() > cutoff]

    def fail_session(self, session_id, error_msg):
        session = self.active_streams.pop(session_id, None)
        if not session:
            session = next((s for s in self.queued_streams if s.id == session_id), None)
            if session:
                self.queued_streams.remove(session)
                
        if session:
            session.completed_at = datetime.utcnow()
            session.status = "failed"
            self.failed_streams.append(session)
            self.log_event(session.id, "error", str(error_msg))

    def get_metrics(self):
        # Throughput over last 60 seconds
        cutoff = datetime.utcnow().timestamp() - 60
        self.completion_times = [t for t in self.completion_times if t.timestamp() > cutoff]
        throughput = len(self.completion_times) / 60.0

        now = datetime.utcnow()

        workers_state = []
        for sid, session in self.active_streams.items():
            active_time = (now - session.started_at).total_seconds()
            workers_state.append({
                "stream_id": sid,
                "active_time": round(active_time, 1),
                "token_count": session.token_count
            })

        latency_history = []
        # Return the last 20 completed streams latency
        for session in self.completed_streams[-20:]:
            if session.first_token_at:
                lat = int((session.first_token_at - session.started_at).total_seconds() * 1000)
                latency_history.append({
                    "stream_id": session.id,
                    "first_token_ms": lat,
                    "completed_duration_s": round((session.completed_at - session.started_at).total_seconds(), 1)
                })

        avg_tokens = 0
        avg_first_token_ms = 0
        if self.completed_streams:
            avg_tokens = sum(s.token_count for s in self.completed_streams) / len(self.completed_streams)
            latencies = [int((s.first_token_at - s.started_at).total_seconds() * 1000) for s in self.completed_streams if s.first_token_at]
            if latencies:
                avg_first_token_ms = sum(latencies) / len(latencies)

        q_pressure = 0
        if stream_semaphore.max_slots > 0:
            q_pressure = len(self.queued_streams) / float(stream_semaphore.max_slots * 2)

        return {
            "queued": [{"id": s.id} for s in self.queued_streams],
            "active": [{"id": s.id} for s in self.active_streams.values()],
            "completed": [{"id": s.id} for s in self.completed_streams],
            "failed": [{"id": s.id} for s in self.failed_streams],
            "workers": workers_state,
            "metrics": {
                "throughput": round(throughput, 2),
                "latencyHistory": latency_history,
                "queuePressure": round(q_pressure, 2),
                "avgTokens": round(avg_tokens, 2),
                "avgFirstTokenMs": round(avg_first_token_ms, 2)
            },
            "events": self.events,
            "max_slots": stream_semaphore.max_slots
        }