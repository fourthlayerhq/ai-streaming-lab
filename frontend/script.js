const responseBox = document.getElementById("response-box");

const normalBtn = document.getElementById("normal-btn");
const streamBtn = document.getElementById("stream-btn");

const simulateBtn = document.getElementById("simulate-btn");
const streamCountInput = document.getElementById("stream-count");

const streamsContainer =
    document.getElementById("streams-container");

const metricsBox =
    document.getElementById("metrics-box");

// NORMAL RESPONSE

normalBtn.addEventListener("click", async () => {
    responseBox.innerHTML =
        "[Normal Response]\n\nWaiting for full response...\n";

    const response = await fetch(
        "http://127.0.0.1:8000/normal-response"
    );

    const data = await response.json();

    responseBox.innerHTML = data.response;
});


// STREAM RESPONSE

streamBtn.addEventListener("click", async () => {
    responseBox.innerHTML =
        "[Streaming Response]\n\n";

    const eventSource = new EventSource(
        "http://127.0.0.1:8000/stream-response"
    );

    eventSource.onmessage = (event) => {
        responseBox.innerHTML += event.data;
    };

    eventSource.addEventListener("done", () => {
        eventSource.close();
    });

    eventSource.onerror = () => {
        eventSource.close();
    };
});

function createStreamCard(streamId) {

    const card = document.createElement("div");

    card.className = "stream-card";

    card.id = `stream-${streamId}`;

    card.innerHTML = `
        <h4>Stream ${streamId}</h4>
        <div class="stream-output"></div>
    `;

    streamsContainer.appendChild(card);

    return card.querySelector(".stream-output");
}

async function launchConcurrentStreams(count) {

    streamsContainer.innerHTML = "";

    for (let i = 1; i <= count; i++) {

        const output = createStreamCard(i);

        const eventSource = new EventSource(
            "http://127.0.0.1:8000/stream-response"
        );

        eventSource.onmessage = (event) => {
            output.innerHTML += event.data;
        };

        eventSource.addEventListener("done", () => {
            eventSource.close();
        });

        eventSource.onerror = () => {
            eventSource.close();
        };
    }
}

simulateBtn.addEventListener("click", () => {

    const count = Number(streamCountInput.value);

    launchConcurrentStreams(count);
});


async function fetchMetrics() {

    const response = await fetch(
        "http://127.0.0.1:8000/metrics"
    );

    const metrics = await response.json();

    metricsBox.innerHTML = `
        <h3>System Metrics</h3>

        <p>
            Active Streams:
            ${metrics.active_streams}
        </p>

        <p>
            Completed Streams:
            ${metrics.completed_streams}
        </p>

        <p>
            Avg Tokens:
            ${metrics.avg_tokens_per_stream}
        </p>

        <p>
            Avg First Token:
            ${metrics.avg_first_token_ms} ms
        </p>
    `;
}

setInterval(fetchMetrics, 1000);