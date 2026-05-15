import { getEl, createEl } from './dom.js';

const LATENCY_HISTORY_MAX = 20;
const latencyHistory = [];

function updateLatencyVisualization(latencyMs) {
    latencyHistory.push(latencyMs);
    if (latencyHistory.length > LATENCY_HISTORY_MAX) {
        latencyHistory.shift();
    }

    const container = getEl("latency-history-bars");
    if (!container) return;
    
    container.innerHTML = "";
    
    const maxLatency = Math.max(...latencyHistory, 100);

    latencyHistory.forEach(val => {
        const bar = createEl("div");
        bar.className = "latency-bar";
        
        const heightPct = Math.min((val / maxLatency) * 100, 100);
        bar.style.height = `${heightPct}%`;
        bar.title = `${val} ms`;
        
        // Dim the bar slightly if it's 0 to maintain layout structure
        if (val === 0) {
            bar.style.opacity = "0.2";
            bar.style.height = "2%"; // minimal height to show existence
        }
        
        container.appendChild(bar);
    });
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
        
        updateLatencyVisualization(metrics.avg_first_token_ms);
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
