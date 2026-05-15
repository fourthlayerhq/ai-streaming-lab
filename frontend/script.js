import { getEl } from './dom.js';
import { createStream } from './stream-client.js';
import { createStreamCard, clearStreamsContainer, setResponseBox, appendToResponseBox } from './stream-ui.js';
import { resetMetrics, startMetricsPolling } from './metrics.js';

const normalBtn = getEl("normal-btn");
const streamBtn = getEl("stream-btn");
const simulateBtn = getEl("simulate-btn");
const streamCountInput = getEl("stream-count");
const startupDelayInput = getEl("startup-delay");
const tokenDelayInput = getEl("token-delay");
const resetBtn = getEl("reset-btn");

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
    clearStreamsContainer();

    const startupDelay = startupDelayInput.value;
    const tokenDelay = tokenDelayInput.value;

    for (let i = 1; i <= count; i++) {
        const cardUI = createStreamCard(i);
        
        createStream(`http://127.0.0.1:8000/stream-response?startup_delay=${startupDelay}&token_delay=${tokenDelay}`, {
            onMessage: (data) => cardUI.appendToken(data),
            onStatus: (data) => cardUI.updateStatus(data)
        });
    }
}

simulateBtn.addEventListener("click", () => {
    const count = Number(streamCountInput.value);
    launchConcurrentStreams(count);
});

resetBtn.addEventListener("click", async () => {
    await resetMetrics();
    clearStreamsContainer();
});

startMetricsPolling();