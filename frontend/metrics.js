import { getEl, createEl } from './dom.js';

export function updateLatencyVisualization(history) {
    const container = getEl("latency-history-bars");
    if (!container) return;

    container.innerHTML = "";

    if (!history || history.length === 0) return;

    const minLatency = Math.min(...history.map(i => i.first_token_ms));
    const maxLatency = Math.max(...history.map(i => i.first_token_ms));
    const range = Math.max(maxLatency - minLatency, 10);

    history.forEach(item => {
        const bar = createEl("div");
        bar.className = "latency-bar";

        const normalized = Math.max(0, Math.min(1, (item.first_token_ms - minLatency) / range));
        const exaggerated = Math.pow(normalized, 1.5);
        const heightPct = 5 + (exaggerated * 95);
        bar.style.height = `${Math.min(heightPct, 100)}%`;

        bar.setAttribute('data-tooltip', `stream-${item.stream_id.substring(0, 5)}\nfirst token: ${item.first_token_ms}ms\ncompleted: ${item.completed_duration_s}s`);
        container.appendChild(bar);
    });
}

export function updateConcurrencyVisualization(metrics) {
    const slotsContainer = getEl("concurrency-slots");
    if (!slotsContainer) return;

    slotsContainer.innerHTML = "";

    const activeCount = metrics.active.length;
    const queuedCount = metrics.queued.length;
    const maxSlots = metrics.max_slots || 3;
    const workers = metrics.workers || [];

    for (let i = 1; i <= maxSlots; i++) {
        const slot = createEl("div");
        if (i <= workers.length) {
            const worker = workers[i - 1];
            const shortId = worker.stream_id.substring(0, 5);
            slot.className = "slot active-slot";
            slot.innerHTML = `
                <div class="slot-id">[SLOT ${i}] str-${shortId}</div>
                <div class="slot-metrics">active ${worker.active_time}s</div>
            `;
        } else {
            slot.className = "slot empty-slot";
            slot.innerHTML = `[SLOT ${i}]<br>EMPTY`;
        }
        slotsContainer.appendChild(slot);
    }

    const pressureText = getEl("pressure-text");
    const pressureFill = getEl("pressure-bar-fill");

    if (pressureText && pressureFill) {
        let pressure = 0;
        let total = activeCount + queuedCount;
        if (total > 0 && maxSlots > 0) {
            pressure = queuedCount / (maxSlots * 2);
            pressure = Math.min(pressure, 1);
        }

        let state = "LOW";
        let fillClass = "low";
        if (pressure >= 0.8) { state = "CRITICAL"; fillClass = "critical"; }
        else if (pressure >= 0.5) { state = "HIGH"; fillClass = "high"; }
        else if (pressure >= 0.2) { state = "MEDIUM"; fillClass = "medium"; }

        pressureText.innerText = `${state} (${Math.round(pressure * 100)}%)`;
        pressureFill.className = `pressure-fill ${fillClass}`;
        pressureFill.style.width = `${Math.round(pressure * 100)}%`;
    }
}

import { renderEvents } from './stream-ui.js';

export async function fetchMetrics() {
    try {
        const response = await fetch("http://127.0.0.1:8000/metrics");
        const metrics = await response.json();

        // The endpoint is actually get_metrics which returns the full dictionary 
        // including active_streams etc under the root, OR wait:
        // Let's check `get_metrics` output in backend:
        // "queued", "active", "completed", "failed", "workers", "metrics", "events", "max_slots"

        getEl("active-streams").innerText = metrics.active.length;
        getEl("completed-streams").innerText = metrics.completed.length;
        getEl("avg-tokens").innerText = metrics.metrics.avgTokens;
        getEl("first-token-latency").innerText = `${metrics.metrics.avgFirstTokenMs} ms`;
        getEl("queued-streams").innerText = metrics.queued.length;
        getEl("throughput").innerText = metrics.metrics.throughput.toFixed(1);

        updateConcurrencyVisualization(metrics);
        updateLatencyVisualization(metrics.metrics.latencyHistory);
        renderEvents(metrics.events);

        const debugEl = getEl("debug-output");
        if (debugEl) {
            debugEl.innerText = `queued: ${metrics.queued.length}\nactive: ${metrics.active.length}\ncompleted: ${metrics.completed.length}\nfailed: ${metrics.failed.length}\nworkers occupied: ${metrics.workers.length}/${metrics.max_slots}`;
        }
    } catch (err) {
        console.error("Error fetching metrics:", err);
    }
}

export async function resetMetrics() {
    try {
        await fetch("http://127.0.0.1:8000/reset-metrics", {
            method: "POST"
        });
        const container = getEl("latency-history-bars");
        if (container) container.innerHTML = "";
    } catch (err) {
        console.error("Error resetting metrics:", err);
    }
}

export function startMetricsPolling(intervalMs = 1000) {
    setInterval(fetchMetrics, intervalMs);
}
