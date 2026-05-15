import { getEl } from './dom.js';
import { createStream } from './stream-client.js';
import { setResponseBox, appendToResponseBox } from './stream-ui.js';
import { resetMetrics, startMetricsPolling } from './metrics.js';

const normalBtn = getEl("normal-btn");
const streamBtn = getEl("stream-btn");
const simulateBtn = getEl("simulate-btn");
const streamCountInput = getEl("stream-count");
const startupDelayInput = getEl("startup-delay");
const tokenDelayInput = getEl("token-delay");
const resetBtn = getEl("reset-btn");

const maxSlotsSelect = getEl("max-slots");
const failureRateInput = getEl("failure-rate");
const slowStreamInput = getEl("slow-stream");
const randomStartupInput = getEl("random-startup");
const tokenJitterInput = getEl("token-jitter");

async function updateConfig() {
    const config = {
        max_concurrent_slots: parseInt(maxSlotsSelect.value),
        failure_rate: parseFloat(failureRateInput.value) / 100.0,
        slow_stream_prob: parseFloat(slowStreamInput.value),
        random_startup_delay: randomStartupInput.checked,
        token_jitter: tokenJitterInput.checked
    };
    try {
        await fetch("http://127.0.0.1:8000/config", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(config)
        });
    } catch (e) {
        console.error(e);
    }
}

maxSlotsSelect.addEventListener("change", updateConfig);
failureRateInput.addEventListener("change", updateConfig);
slowStreamInput.addEventListener("change", updateConfig);
randomStartupInput.addEventListener("change", updateConfig);
tokenJitterInput.addEventListener("change", updateConfig);

// TABS LOGIC
const tabBasics = getEl("tab-basics");
const tabConcurrent = getEl("tab-concurrent");
const sectionBasics = getEl("section-basics");
const sectionConcurrent = getEl("section-concurrent");

tabBasics.addEventListener("click", () => {
    tabBasics.classList.add("active");
    tabConcurrent.classList.remove("active");
    sectionBasics.style.display = "flex";
    sectionConcurrent.style.display = "none";
});

tabConcurrent.addEventListener("click", () => {
    tabConcurrent.classList.add("active");
    tabBasics.classList.remove("active");
    sectionConcurrent.style.display = "flex";
    sectionBasics.style.display = "none";
});

// NORMAL RESPONSE
normalBtn.addEventListener("click", async () => {
    setResponseBox("[Normal Response]\n\nWaiting for full response...\n");
    const response = await fetch("http://127.0.0.1:8000/normal-response");
    const data = await response.json();
    setResponseBox(data.response);
});

// STREAM RESPONSE
streamBtn.addEventListener("click", () => {
    setResponseBox("[Streaming Response]\n\n");
    createStream("http://127.0.0.1:8000/stream-response", {
        onMessage: (data) => appendToResponseBox(data)
    });
});

async function launchConcurrentStreams(count) {
    try {
        await fetch("http://127.0.0.1:8000/launch", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                count: count,
                startup_delay: Number(startupDelayInput.value),
                token_delay: Number(tokenDelayInput.value)
            })
        });
    } catch (e) {
        console.error("Launch error:", e);
    }
}

simulateBtn.addEventListener("click", async () => {
    await updateConfig();
    const count = Number(streamCountInput.value);
    launchConcurrentStreams(count);
});

resetBtn.addEventListener("click", async () => {
    await resetMetrics();
});

startMetricsPolling();