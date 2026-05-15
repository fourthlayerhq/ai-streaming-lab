import { getEl } from './dom.js';

export async function fetchMetrics() {
    try {
        const response = await fetch("http://127.0.0.1:8000/metrics");
        const metrics = await response.json();

        getEl("active-streams").innerText = metrics.active_streams;
        getEl("completed-streams").innerText = metrics.completed_streams;
        getEl("avg-tokens").innerText = metrics.avg_tokens_per_stream;
        getEl("first-token-latency").innerText = `${metrics.avg_first_token_ms} ms`;
        getEl("queued-streams").innerText = metrics.queued_streams;
    } catch (err) {
        console.error("Error fetching metrics:", err);
    }
}

export async function resetMetrics() {
    try {
        await fetch("http://127.0.0.1:8000/reset-metrics", {
            method: "POST"
        });
    } catch (err) {
        console.error("Error resetting metrics:", err);
    }
}

export function startMetricsPolling(intervalMs = 1000) {
    setInterval(fetchMetrics, intervalMs);
}
