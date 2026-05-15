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