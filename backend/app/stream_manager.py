from datetime import datetime
from .queue_manager import stream_semaphore
import random

class StreamManager:

    def __init__(self):
        self.active_streams = {}
        self.completed_streams = {}
        self.queued_streams = 0
        self.config = {
            "failure_rate": 0.0,
            "random_startup_delay": False,
            "token_jitter": False,
            "slow_stream_prob": 0.0
        }
        self.start_time = datetime.utcnow()
        self.total_completed_tokens = 0

    def reset(self):
        self.active_streams = {}
        self.completed_streams = {}
        self.queued_streams = 0
        self.start_time = datetime.utcnow()
        self.total_completed_tokens = 0

    def create_session(self, session):
        self.active_streams[session.id] = session

    def mark_first_token(self, session_id):

        session = self.active_streams.get(session_id)

        if session and not session.first_token_at:
            session.first_token_at = datetime.utcnow()

    def increment_token(self, session_id):

        session = self.active_streams.get(session_id)

        if session:
            session.token_count += 1

    def complete_session(self, session_id):

        session = self.active_streams.pop(session_id, None)

        if session:
            session.completed_at = datetime.utcnow()
            session.status = "completed"

            self.completed_streams[session.id] = session

    def get_metrics(self):

        completed = list(self.completed_streams.values())

        avg_tokens = 0
        avg_first_token_ms = 0

        if completed:

            avg_tokens = sum(
                session.token_count for session in completed
            ) / len(completed)

            first_token_times = []

            for session in completed:

                if session.first_token_at:

                    latency = (
                        session.first_token_at - session.started_at
                    ).total_seconds() * 1000

                    first_token_times.append(latency)

            if first_token_times:
                avg_first_token_ms = (
                    sum(first_token_times) / len(first_token_times)
                )

        now = datetime.utcnow()
        elapsed_seconds = (now - self.start_time).total_seconds()
        throughput = 0.0
        if elapsed_seconds > 0:
            throughput = len(self.completed_streams) / elapsed_seconds

        active_details = {}
        for sid, session in self.active_streams.items():
            active_time = (now - session.started_at).total_seconds()
            active_details[sid] = {
                "active_time": round(active_time, 1),
                "token_count": session.token_count
            }

        return {
            "active_streams": len(self.active_streams),
            "completed_streams": len(self.completed_streams),
            "avg_tokens_per_stream": round(avg_tokens, 2),
            "avg_first_token_ms": round(avg_first_token_ms, 2),
            "queued_streams": self.queued_streams,
            "throughput_sec": round(throughput, 2),
            "max_concurrent_slots": stream_semaphore.max_slots,
            "active_details": active_details
        }

    def increment_queue(self):
        self.queued_streams += 1


    def decrement_queue(self):
        if self.queued_streams > 0:
            self.queued_streams -= 1


stream_manager = StreamManager()