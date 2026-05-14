const responseBox = document.getElementById("response-box");

const normalBtn = document.getElementById("normal-btn");
const streamBtn = document.getElementById("stream-btn");


// NORMAL RESPONSE

normalBtn.addEventListener("click", async () => {
    responseBox.innerHTML = "Waiting for full response...\n";

    const response = await fetch(
        "http://127.0.0.1:8000/normal-response"
    );

    const data = await response.json();

    responseBox.innerHTML = data.response;
});


// STREAM RESPONSE

streamBtn.addEventListener("click", async () => {
    responseBox.innerHTML = "Streaming response...\n\n";

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