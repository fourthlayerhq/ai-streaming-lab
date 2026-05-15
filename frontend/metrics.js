import { getEl, createEl } from './dom.js';

const LATENCY_HISTORY_MAX = 20;
const latencyHistory = [];

export function updateLatencyVisualization(streamId, latencyMs) {
    latencyHistory.push({ id: streamId, val: latencyMs });
    if (latencyHistory.length > LATENCY_HISTORY_MAX) {
        latencyHistory.shift();
    }

    const container = getEl("latency-history-bars");
    if (!container) return;
    
    container.innerHTML = "";
    
    const validHistory = latencyHistory.filter(item => item.val > 0).map(item => item.val);
    const minLatency = validHistory.length > 0 ? Math.min(...validHistory) : 0;
    const maxLatency = validHistory.length > 0 ? Math.max(...validHistory) : 100;
    
    // Ensure we don't divide by zero and scale effectively
    const range = Math.max(maxLatency - minLatency, 10);

    latencyHistory.forEach(item => {
        const bar = createEl("div");
        bar.className = "latency-bar";
        
        if (item.val === 0) {
            bar.style.opacity = "0.2";
            bar.style.height = "2%"; // minimal height to show existence
        } else {
            const normalized = Math.max(0, Math.min(1, (item.val - minLatency) / range));
            const exaggerated = Math.pow(normalized, 1.5); // Exaggerate spikes
            const heightPct = 5 + (exaggerated * 95);
            bar.style.height = `${Math.min(heightPct, 100)}%`;
        }
        
        bar.title = `stream-${item.id}\nfirst token latency\n${item.val}ms`;
        container.appendChild(bar);
    });
}

export function updateConcurrencyVisualization(activeCount, queuedCount) {
    const slotsContainer = getEl("concurrency-slots");
    if (!slotsContainer) return;
    
    slotsContainer.innerHTML = "";
    
    const MAX_SLOTS = 3; 
    const totalSlots = Math.max(MAX_SLOTS, activeCount);
    
    for (let i = 1; i <= totalSlots; i++) {
        const slot = createEl("div");
        if (i <= activeCount) {
            slot.className = "slot active-slot";
            slot.innerText = `[SLOT ${i}] ACTIVE`;
        } else {
            slot.className = "slot empty-slot";
            slot.innerText = `[SLOT ${i}] EMPTY`;
        }
        slotsContainer.appendChild(slot);
    }
    
    const queueEl = getEl("slot-queue-count");
    if (queueEl) queueEl.innerText = queuedCount;
}

export async function fetchMetrics() {
    try {
        const response = await fetch("http://127.0.0.1:8000/metrics");
        const metrics = await response.json();

        getEl("active-streams").innerText = metrics.active_streams;
        getEl("completed-streams").innerText = metrics.completed_streams;
        getEl("avg-tokens").innerText = metrics.avg_tokens_per_stream;
        getEl("first-token-latency").innerText = `${metrics.avg_first_token_ms} ms`;
        getEl("queued-streams").innerText = metrics.queued_streams;
        
        updateConcurrencyVisualization(metrics.active_streams, metrics.queued_streams);
    } catch (err) {
        console.error("Error fetching metrics:", err);
    }
}

export async function resetMetrics() {
    try {
        await fetch("http://127.0.0.1:8000/reset-metrics", {
            method: "POST"
        });
        latencyHistory.length = 0;
        const container = getEl("latency-history-bars");
        if (container) container.innerHTML = "";
    } catch (err) {
        console.error("Error resetting metrics:", err);
    }
}

export function startMetricsPolling(intervalMs = 1000) {
    setInterval(fetchMetrics, intervalMs);
}
