"""
Runtime Integrity Tests — AI Streaming Lab Scheduler

Validates:
  - concurrency limits are enforced
  - queue drains correctly after workers free up
  - workers are released after failure (no slot leaks)
  - throughput metric reflects actual completions
  - failure rate approximation is statistically correct
  - metrics consistency (queued+active+completed+failed == total)
  - dynamic slot resizing works in-flight

Run:
    cd backend
    pytest tests/ -v
"""

import asyncio
import uuid
from contextlib import contextmanager
from datetime import datetime

import pytest

import app.stream_manager as sm_mod
from app.queue_manager import ConcurrencyManager
from app.stream_manager import StreamManager
from app.fake_llm import fake_token_generator, StreamingFailure
from app.models import StreamSession


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_session() -> StreamSession:
    return StreamSession(id=str(uuid.uuid4()), started_at=datetime.utcnow())


def fresh_manager(max_slots: int = 3) -> tuple[StreamManager, ConcurrencyManager]:
    """Return a pristine (manager, semaphore) pair with no shared global state.

    Uses real StreamManager.__init__ so production initialization logic is exercised.
    """
    sem = ConcurrencyManager()
    sem.max_slots = max_slots

    mgr = StreamManager()
    mgr.reset()  # ensure clean slate even if __init__ changes
    return mgr, sem


@contextmanager
def patched_semaphore(sem: ConcurrencyManager):
    """Temporarily replace the module-level stream_semaphore used by get_metrics()."""
    original = sm_mod.stream_semaphore
    sm_mod.stream_semaphore = sem
    try:
        yield
    finally:
        sm_mod.stream_semaphore = original


async def run_one_task(mgr: StreamManager, sem: ConcurrencyManager, config: dict = None, token_delay: float = 0.01):
    """
    Mirror of background_stream_task but injected with isolated mgr + sem
    so tests don't touch global singletons.
    """
    session = make_session()
    mgr.create_session(session)
    is_completed = False
    effective_config = config or mgr.config
    try:
        async with sem:
            mgr.assign_worker(session.id)
            first_token_sent = False
            try:
                async for token in fake_token_generator(
                    startup_delay=0,
                    token_delay=token_delay,
                    config=effective_config,
                ):
                    if token == "[DONE]":
                        is_completed = True
                        mgr.complete_session(session.id)
                        break
                    if not first_token_sent:
                        mgr.mark_first_token(session.id)
                        first_token_sent = True
                    mgr.increment_token(session.id)
            except StreamingFailure as e:
                is_completed = True
                mgr.fail_session(session.id, str(e))
    except Exception as e:
        is_completed = True
        mgr.fail_session(session.id, str(e))
    finally:
        if not is_completed:
            mgr.fail_session(session.id, "disconnected")


# ---------------------------------------------------------------------------
# 1. ConcurrencyManager — slot limits
# ---------------------------------------------------------------------------

class TestConcurrencyManager:

    @pytest.mark.asyncio
    async def test_max_slots_enforced(self):
        """Never more than max_slots workers active simultaneously."""
        sem = ConcurrencyManager()
        sem.max_slots = 3
        peak = 0
        lock = asyncio.Lock()

        async def worker():
            nonlocal peak
            async with sem:
                async with lock:
                    peak = max(peak, sem.active_slots)
                await asyncio.sleep(0.05)

        await asyncio.gather(*[worker() for _ in range(10)])
        assert peak <= 3, f"Peak concurrent slots {peak} exceeded max_slots=3"

    @pytest.mark.asyncio
    async def test_slots_released_after_normal_exit(self):
        """active_slots returns to 0 after all workers finish."""
        sem = ConcurrencyManager()
        sem.max_slots = 5

        async def worker():
            async with sem:
                await asyncio.sleep(0.01)

        await asyncio.gather(*[worker() for _ in range(5)])
        assert sem.active_slots == 0

    @pytest.mark.asyncio
    async def test_slots_released_after_exception(self):
        """Slot is freed even when the worker raises an exception."""
        sem = ConcurrencyManager()
        sem.max_slots = 2

        async def failing_worker():
            async with sem:
                raise RuntimeError("boom")

        for _ in range(4):
            with pytest.raises(RuntimeError):
                await failing_worker()

        assert sem.active_slots == 0

    @pytest.mark.asyncio
    async def test_dynamic_slot_increase_drains_queue(self):
        """Increasing max_slots while tasks are waiting should unblock them."""
        sem = ConcurrencyManager()
        sem.max_slots = 1
        results = []

        async def worker(tag):
            async with sem:
                results.append(tag)
                await asyncio.sleep(0.05)

        # Start 3 tasks — only 1 slot, so 2 will queue
        tasks = [asyncio.create_task(worker(i)) for i in range(3)]
        await asyncio.sleep(0.02)  # let them pile up

        # Expand to 3 slots — all should now proceed
        await sem.set_slots(3)
        await asyncio.gather(*tasks)

        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_dynamic_slot_decrease_respected(self):
        """Reducing max_slots prevents new acquisitions beyond new limit."""
        sem = ConcurrencyManager()
        sem.max_slots = 5
        await sem.set_slots(1)

        peak = 0
        lock = asyncio.Lock()

        async def worker():
            nonlocal peak
            async with sem:
                async with lock:
                    peak = max(peak, sem.active_slots)
                await asyncio.sleep(0.05)

        await asyncio.gather(*[worker() for _ in range(6)])
        assert peak <= 1


# ---------------------------------------------------------------------------
# 2. StreamManager — state lifecycle
# ---------------------------------------------------------------------------

class TestStreamManagerLifecycle:

    def test_create_session_adds_to_queued(self):
        mgr, _ = fresh_manager()
        s = make_session()
        mgr.create_session(s)
        assert s in mgr.queued_streams
        assert s.id not in mgr.active_streams

    def test_assign_worker_moves_queued_to_active(self):
        mgr, _ = fresh_manager()
        s = make_session()
        mgr.create_session(s)
        mgr.assign_worker(s.id)
        assert s not in mgr.queued_streams
        assert s.id in mgr.active_streams

    def test_complete_session_moves_active_to_completed(self):
        mgr, _ = fresh_manager()
        s = make_session()
        mgr.create_session(s)
        mgr.assign_worker(s.id)
        mgr.complete_session(s.id)
        assert s.id not in mgr.active_streams
        assert s in mgr.completed_streams

    def test_fail_session_from_active_moves_to_failed(self):
        mgr, _ = fresh_manager()
        s = make_session()
        mgr.create_session(s)
        mgr.assign_worker(s.id)
        mgr.fail_session(s.id, "injected failure")
        assert s.id not in mgr.active_streams
        assert s in mgr.failed_streams

    def test_fail_session_from_queued_moves_to_failed(self):
        """A session that never got a worker can still be failed cleanly."""
        mgr, _ = fresh_manager()
        s = make_session()
        mgr.create_session(s)
        mgr.fail_session(s.id, "cancelled before assignment")
        assert s not in mgr.queued_streams
        assert s in mgr.failed_streams

    def test_queued_never_negative(self):
        """Decrement logic must never make queued list negative."""
        mgr, _ = fresh_manager()
        s = make_session()
        mgr.create_session(s)
        mgr.assign_worker(s.id)
        mgr.complete_session(s.id)
        # Calling complete again should be a no-op, not corrupt state
        mgr.complete_session(s.id)
        assert len(mgr.queued_streams) == 0
        assert len(mgr.active_streams) == 0

    def test_events_logged_for_full_lifecycle(self):
        mgr, _ = fresh_manager()
        s = make_session()
        mgr.create_session(s)
        mgr.assign_worker(s.id)
        mgr.mark_first_token(s.id)
        mgr.complete_session(s.id)

        event_types = [e["type"] for e in mgr.events if e["stream_id"] == s.id]
        assert "queued" in event_types
        assert "assigned" in event_types
        assert "first_token" in event_types
        assert "completed" in event_types

    def test_reset_clears_all_state(self):
        mgr, _ = fresh_manager()
        for _ in range(3):
            s = make_session()
            mgr.create_session(s)
            mgr.assign_worker(s.id)
            mgr.complete_session(s.id)

        mgr.reset()
        assert mgr.queued_streams == []
        assert mgr.active_streams == {}
        assert mgr.completed_streams == []
        assert mgr.failed_streams == []
        assert mgr.events == []
        assert mgr.completion_times == []


# ---------------------------------------------------------------------------
# 3. Queue draining — integration
# ---------------------------------------------------------------------------

class TestQueueDraining:

    @pytest.mark.asyncio
    async def test_all_tasks_complete_with_limited_slots(self):
        """10 tasks through a 3-slot semaphore: all must complete."""
        mgr, sem = fresh_manager(max_slots=3)
        await asyncio.gather(*[run_one_task(mgr, sem) for _ in range(10)])

        total = len(mgr.completed_streams) + len(mgr.failed_streams)
        assert total == 10
        assert len(mgr.queued_streams) == 0
        assert len(mgr.active_streams) == 0

    @pytest.mark.asyncio
    async def test_queue_empties_after_all_tasks(self):
        mgr, sem = fresh_manager(max_slots=2)
        await asyncio.gather(*[run_one_task(mgr, sem) for _ in range(6)])
        assert len(mgr.queued_streams) == 0

    @pytest.mark.asyncio
    async def test_worker_count_never_exceeds_slots(self):
        """Sample active_slots at fine-grained intervals; never exceeds max."""
        sem = ConcurrencyManager()
        sem.max_slots = 3
        violations = []

        async def sampling_task():
            while True:
                if sem.active_slots > sem.max_slots:
                    violations.append(sem.active_slots)
                await asyncio.sleep(0.005)

        sampler = asyncio.create_task(sampling_task())

        mgr, _ = fresh_manager(max_slots=3)
        await asyncio.gather(*[run_one_task(mgr, sem) for _ in range(12)])

        sampler.cancel()
        assert violations == [], f"Slot violations: {violations}"


# ---------------------------------------------------------------------------
# 4. Worker release after failure
# ---------------------------------------------------------------------------

class TestWorkerReleaseAfterFailure:

    @pytest.mark.asyncio
    async def test_slots_freed_after_streaming_failure(self):
        """All slots must be free after 100% failure rate run."""
        sem = ConcurrencyManager()
        sem.max_slots = 3
        mgr, _ = fresh_manager(max_slots=3)
        config = {
            "failure_rate": 1.0,
            "random_startup_delay": False,
            "token_jitter": False,
            "slow_stream_prob": 0.0,
        }
        await asyncio.gather(*[
            run_one_task(mgr, sem, config=config) for _ in range(9)
        ])

        assert sem.active_slots == 0, f"Leaked slots: {sem.active_slots}"

    @pytest.mark.asyncio
    async def test_failed_tasks_recorded_correctly(self):
        """With 100% failure rate, all tasks must land in failed_streams."""
        sem = ConcurrencyManager()
        sem.max_slots = 3
        mgr, _ = fresh_manager(max_slots=3)
        config = {
            "failure_rate": 1.0,
            "random_startup_delay": False,
            "token_jitter": False,
            "slow_stream_prob": 0.0,
        }
        n = 6
        await asyncio.gather(*[
            run_one_task(mgr, sem, config=config) for _ in range(n)
        ])

        assert len(mgr.failed_streams) == n
        assert len(mgr.completed_streams) == 0

    @pytest.mark.asyncio
    async def test_new_tasks_proceed_after_slot_freed_by_failure(self):
        """After failed tasks release slots, subsequent tasks must run."""
        sem = ConcurrencyManager()
        sem.max_slots = 1
        mgr, _ = fresh_manager(max_slots=1)

        fail_config = {"failure_rate": 1.0, "random_startup_delay": False, "token_jitter": False, "slow_stream_prob": 0.0}
        ok_config = {"failure_rate": 0.0, "random_startup_delay": False, "token_jitter": False, "slow_stream_prob": 0.0}

        # Run one failing task first, then one succeeding task
        await run_one_task(mgr, sem, config=fail_config)
        await run_one_task(mgr, sem, config=ok_config)

        assert len(mgr.failed_streams) == 1
        assert len(mgr.completed_streams) == 1
        assert sem.active_slots == 0


# ---------------------------------------------------------------------------
# 5. Throughput correctness
# ---------------------------------------------------------------------------

class TestThroughputMetrics:

    @pytest.mark.asyncio
    async def test_throughput_reflects_completions(self):
        """completion_times length must match completed_streams length."""
        mgr, sem = fresh_manager(max_slots=5)
        n = 8
        await asyncio.gather(*[run_one_task(mgr, sem) for _ in range(n)])

        assert len(mgr.completion_times) == len(mgr.completed_streams)

    @pytest.mark.asyncio
    async def test_throughput_zero_for_no_completions(self):
        """If nothing completed yet, throughput window returns 0."""
        mgr, sem = fresh_manager()
        with patched_semaphore(sem):
            metrics = mgr.get_metrics()
        assert metrics["metrics"]["throughput"] == 0.0

    @pytest.mark.asyncio
    async def test_throughput_positive_after_completions(self):
        """throughput metric must be > 0 after streams complete successfully."""
        mgr, sem = fresh_manager(max_slots=5)
        n = 10
        await asyncio.gather(*[run_one_task(mgr, sem) for _ in range(n)])

        assert len(mgr.completed_streams) == n
        with patched_semaphore(sem):
            metrics = mgr.get_metrics()
        assert metrics["metrics"]["throughput"] > 0, (
            f"Expected throughput > 0 after {n} completions, got "
            f"{metrics['metrics']['throughput']}"
        )

    @pytest.mark.asyncio
    async def test_first_token_recorded_on_completed_sessions(self):
        """first_token_at must be set for all completed streams (not just averaged)."""
        mgr, sem = fresh_manager(max_slots=3)
        # Use a real token_delay so timestamps differ meaningfully
        await asyncio.gather(*[run_one_task(mgr, sem, token_delay=0.05) for _ in range(5)])

        assert len(mgr.completed_streams) == 5
        for session in mgr.completed_streams:
            assert session.first_token_at is not None, (
                f"stream {session.id} missing first_token_at"
            )
            assert session.first_token_at >= session.started_at


# ---------------------------------------------------------------------------
# 6. Failure rate approximation
# ---------------------------------------------------------------------------

class TestFailureRateApproximation:

    @pytest.mark.asyncio
    async def test_zero_failure_rate_produces_no_failures(self):
        mgr, sem = fresh_manager(max_slots=5)
        config = {"failure_rate": 0.0, "random_startup_delay": False, "token_jitter": False, "slow_stream_prob": 0.0}
        await asyncio.gather(*[run_one_task(mgr, sem, config=config) for _ in range(20)])
        assert len(mgr.failed_streams) == 0

    @pytest.mark.asyncio
    async def test_full_failure_rate_produces_all_failures(self):
        sem = ConcurrencyManager()
        sem.max_slots = 5
        mgr, _ = fresh_manager(max_slots=5)
        config = {"failure_rate": 1.0, "random_startup_delay": False, "token_jitter": False, "slow_stream_prob": 0.0}
        n = 20
        await asyncio.gather(*[run_one_task(mgr, sem, config=config) for _ in range(n)])
        assert len(mgr.failed_streams) == n

    @pytest.mark.asyncio
    async def test_partial_failure_rate_within_bounds(self):
        """50% failure rate over 300 samples → actual rate must be within ±15% of target.

        n=300 gives ~3σ confidence that a fair Bernoulli(0.5) stays in [0.35, 0.65].
        """
        mgr, sem = fresh_manager(max_slots=10)
        config = {"failure_rate": 0.5, "random_startup_delay": False, "token_jitter": False, "slow_stream_prob": 0.0}
        n = 300
        await asyncio.gather(*[run_one_task(mgr, sem, config=config) for _ in range(n)])

        total = len(mgr.completed_streams) + len(mgr.failed_streams)
        assert total == n, f"State invariant broken: {total} != {n}"

        actual_rate = len(mgr.failed_streams) / n
        assert 0.35 <= actual_rate <= 0.65, (
            f"Failure rate {actual_rate:.2f} is outside ±15% tolerance around 50% "
            f"(failed={len(mgr.failed_streams)}, completed={len(mgr.completed_streams)}, n={n})"
        )


# ---------------------------------------------------------------------------
# 7. Metrics consistency
# ---------------------------------------------------------------------------

class TestMetricsConsistency:

    @pytest.mark.asyncio
    async def test_total_invariant_holds(self):
        """queued + active + completed + failed must equal streams launched."""
        mgr, sem = fresh_manager(max_slots=3)
        config = {"failure_rate": 0.3, "random_startup_delay": False, "token_jitter": False, "slow_stream_prob": 0.0}
        n = 15
        await asyncio.gather(*[run_one_task(mgr, sem, config=config) for _ in range(n)])

        total = (
            len(mgr.queued_streams)
            + len(mgr.active_streams)
            + len(mgr.completed_streams)
            + len(mgr.failed_streams)
        )
        assert total == n, f"State invariant broken: {total} != {n}"

    @pytest.mark.asyncio
    async def test_no_duplicate_stream_ids_across_buckets(self):
        """A stream ID must appear in exactly one bucket after completion."""
        mgr, sem = fresh_manager(max_slots=4)
        config = {"failure_rate": 0.2, "random_startup_delay": False, "token_jitter": False, "slow_stream_prob": 0.0}
        await asyncio.gather(*[run_one_task(mgr, sem, config=config) for _ in range(20)])

        all_ids = (
            [s.id for s in mgr.queued_streams]
            + list(mgr.active_streams.keys())
            + [s.id for s in mgr.completed_streams]
            + [s.id for s in mgr.failed_streams]
        )
        assert len(all_ids) == len(set(all_ids)), "Duplicate stream ID found across state buckets"

    @pytest.mark.asyncio
    async def test_get_metrics_structure(self):
        """get_metrics() must return the expected schema with all required keys."""
        mgr, sem = fresh_manager(max_slots=2)
        await asyncio.gather(*[run_one_task(mgr, sem) for _ in range(3)])

        with patched_semaphore(sem):
            metrics = mgr.get_metrics()

        assert "queued" in metrics
        assert "active" in metrics
        assert "completed" in metrics
        assert "failed" in metrics
        assert "workers" in metrics
        assert "events" in metrics
        assert "max_slots" in metrics
        assert "metrics" in metrics

        inner = metrics["metrics"]
        assert "throughput" in inner
        assert "latencyHistory" in inner
        assert "queuePressure" in inner
        assert "avgTokens" in inner
        assert "avgFirstTokenMs" in inner

    @pytest.mark.asyncio
    async def test_latency_history_only_from_completed(self):
        """latencyHistory entries must only reference completed streams."""
        mgr, sem = fresh_manager(max_slots=5)
        config = {"failure_rate": 0.0, "random_startup_delay": False, "token_jitter": False, "slow_stream_prob": 0.0}
        await asyncio.gather(*[run_one_task(mgr, sem, config=config) for _ in range(10)])

        completed_ids = {s.id for s in mgr.completed_streams}
        with patched_semaphore(sem):
            metrics = mgr.get_metrics()

        for entry in metrics["metrics"]["latencyHistory"]:
            assert entry["stream_id"] in completed_ids, (
                f"Latency entry for {entry['stream_id']} not in completed_streams"
            )


# ---------------------------------------------------------------------------
# 8. fake_token_generator direct tests
# ---------------------------------------------------------------------------

class TestFakeTokenGenerator:

    @pytest.mark.asyncio
    async def test_yields_done_sentinel(self):
        tokens = []
        async for t in fake_token_generator(token_delay=0, config={}):
            tokens.append(t)
        assert tokens[-1] == "[DONE]"

    @pytest.mark.asyncio
    async def test_failure_rate_1_always_raises(self):
        config = {"failure_rate": 1.0}
        with pytest.raises(StreamingFailure):
            async for _ in fake_token_generator(token_delay=0, config=config):
                pass

    @pytest.mark.asyncio
    async def test_failure_rate_0_never_raises(self):
        config = {"failure_rate": 0.0}
        tokens = []
        async for t in fake_token_generator(token_delay=0, config=config):
            tokens.append(t)
        assert "[DONE]" in tokens

    @pytest.mark.asyncio
    async def test_yields_word_tokens_before_done(self):
        tokens = []
        async for t in fake_token_generator(token_delay=0, config={}):
            tokens.append(t)
        # Should have actual word tokens before [DONE]
        assert len(tokens) > 1
        assert tokens[-1] == "[DONE]"
        assert any(t != "[DONE]" for t in tokens)
