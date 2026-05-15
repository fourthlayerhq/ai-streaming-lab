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
        
        bar.setAttribute('data-tooltip', `stream-${item.id.substring(0, 5)}\nfirst token: ${item.val}ms`);
        container.appendChild(bar);
    });
}

export function updateConcurrencyVisualization(metrics) {
    const slotsContainer = getEl("concurrency-slots");
    if (!slotsContainer) return;
    
    slotsContainer.innerHTML = "";
    
    const activeCount = metrics.active_streams;
    const queuedCount = metrics.queued_streams;
    const maxSlots = metrics.max_concurrent_slots || 3;
    const activeDetails = metrics.active_details || {};
    
    const activeIds = Object.keys(activeDetails);
    
    for (let i = 1; i <= maxSlots; i++) {
        const slot = createEl("div");
        if (i <= activeIds.length) {
            const sid = activeIds[i-1];
            const details = activeDetails[sid];
            const shortId = sid.substring(0, 5);
            slot.className = "slot active-slot";
            slot.innerHTML = `
                <div class="slot-id">[SLOT ${i}] str-${shortId}</div>
                <div class="slot-metrics">active ${details.active_time}s</div>
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

export async function fetchMetrics() {
    try {
        const response = await fetch("http://127.0.0.1:8000/metrics");
        const metrics = await response.json();

        getEl("active-streams").innerText = metrics.active_streams;
        getEl("completed-streams").innerText = metrics.completed_streams;
        getEl("avg-tokens").innerText = metrics.avg_tokens_per_stream;
        getEl("first-token-latency").innerText = `${metrics.avg_first_token_ms} ms`;
        getEl("queued-streams").innerText = metrics.queued_streams;
        getEl("throughput").innerText = metrics.throughput_sec.toFixed(1);
        
        updateConcurrencyVisualization(metrics);
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
