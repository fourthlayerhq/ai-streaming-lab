import { getEl, createEl } from './dom.js';

let lastRenderedTimestamp = null;
let totalEventsSeen = 0;

function formatTimestamp(isoString) {
    const d = new Date(isoString);
    return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}:${d.getSeconds().toString().padStart(2, '0')}.${d.getMilliseconds().toString().padStart(3, '0')}`;
}

export function renderEvents(events) {
    if (!events || events.length === 0) return;

    const container = getEl("streams-container");
    if (!container) return;

    // Find the index of the first new event
    let startIndex = 0;
    if (lastRenderedTimestamp) {
        for (let i = events.length - 1; i >= 0; i--) {
            if (events[i].timestamp === lastRenderedTimestamp) {
                startIndex = i + 1;
                break;
            }
        }
        // If we didn't find the last rendered, it means they cycled out. We'll just render all.
    }

    let addedAny = false;

    for (let i = startIndex; i < events.length; i++) {
        const ev = events[i];
        
        const logLine = createEl("div");
        logLine.className = `stream-log-line event-${ev.type}`;
        
        let message = `stream-${ev.stream_id.substring(0, 5)} ${ev.type} ${ev.details}`;
        
        logLine.innerHTML = `
            <span class="timestamp">[${formatTimestamp(ev.timestamp)}]</span>
            <span class="log-message">${message}</span>
        `;
        
        container.appendChild(logLine);
        addedAny = true;
        totalEventsSeen++;
        lastRenderedTimestamp = ev.timestamp;
    }

    if (addedAny) {
        const countEl = getEl("event-count");
        if (countEl) countEl.innerText = `${totalEventsSeen} EVENTS`;

        const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 150;
        if (isNearBottom) {
            container.scrollTop = container.scrollHeight;
        }

        // Limit DOM nodes
        while (container.children.length > 300) {
            container.removeChild(container.firstChild);
        }
    }
}

export function clearStreamsContainer() {
    const container = getEl("streams-container");
    if (container) {
        container.innerHTML = "";
    }
    lastRenderedTimestamp = null;
    totalEventsSeen = 0;
    const countEl = getEl("event-count");
    if (countEl) countEl.innerText = `0 EVENTS`;
}

export function setResponseBox(text) {
    const box = getEl("response-box");
    if (box) {
        box.innerHTML = text;
    }
}

export function appendToResponseBox(text) {
    const box = getEl("response-box");
    if (box) {
        box.innerHTML += text;
    }
}
