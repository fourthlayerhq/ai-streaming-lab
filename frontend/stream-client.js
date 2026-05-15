export function createStream(url, callbacks) {
    const { onMessage, onStatus, onDone, onError } = callbacks;
    const eventSource = new EventSource(url);

    if (onMessage) {
        eventSource.onmessage = (event) => onMessage(event.data);
    }

    if (onStatus) {
        eventSource.addEventListener("status", (event) => onStatus(event.data));
    }

    eventSource.addEventListener("done", () => {
        if (onDone) onDone();
        eventSource.close();
    });

    eventSource.onerror = (err) => {
        if (onError) onError(err);
        eventSource.close();
    };

    return eventSource;
}
