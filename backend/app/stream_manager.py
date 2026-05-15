from datetime import datetime


class StreamManager:

    def __init__(self):
        self.active_streams = {}
        self.completed_streams = {}
        self.queued_streams = 0
        

    def reset(self):
        self.active_streams = {}
        self.completed_streams = {}
        self.queued_streams = 0

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

        return {
            "active_streams": len(self.active_streams),
            "completed_streams": len(self.completed_streams),
            "avg_tokens_per_stream": round(avg_tokens, 2),
            "avg_first_token_ms": round(avg_first_token_ms, 2),
            "queued_streams": self.queued_streams,
        }

    def increment_queue(self):
        self.queued_streams += 1


    def decrement_queue(self):
        if self.queued_streams > 0:
            self.queued_streams -= 1


stream_manager = StreamManager()