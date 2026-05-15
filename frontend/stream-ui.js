import { getEl, createEl } from './dom.js';
import { updateConcurrencyVisualization, updateLatencyVisualization } from './metrics.js';

const streamStates = new Map();
let totalEvents = 0;

function getFormattedTime() {
    const now = new Date();
    return `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}.${now.getMilliseconds().toString().padStart(3, '0')}`;
}

function appendEventLog(streamId, eventName, detailsStr = "") {
    const container = getEl("streams-container");
    if (!container) return;
    
    const logLine = createEl("div");
    logLine.className = `stream-log-line event-${eventName}`;
    
    let message = "";
    if (eventName === 'queued') message = `stream-${streamId} queued`;
    else if (eventName === 'assigned') message = `slot assigned &rarr; stream-${streamId}`;
    else if (eventName === 'first_token') message = `stream-${streamId} first token received ${detailsStr}`;
    else if (eventName === 'completed') message = `stream-${streamId} completed ${detailsStr}`;
    else if (eventName === 'error') message = `stream-${streamId} error ${detailsStr}`;
    else message = `stream-${streamId} ${eventName} ${detailsStr}`;
    
    logLine.innerHTML = `
        <span class="timestamp">[${getFormattedTime()}]</span>
        <span class="log-message">${message}</span>
    `;
    
    container.appendChild(logLine);
    
    totalEvents++;
    const countEl = getEl("event-count");
    if (countEl) countEl.innerText = `${totalEvents} EVENTS`;
    
    const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 120;
    if (isNearBottom) {
        container.scrollTop = container.scrollHeight;
    }
    
    updateRetention();
}

function recalculateConcurrency() {
    let active = 0;
    let queued = 0;
    for (const state of streamStates.values()) {
        if (state === 'queued') queued++;
        if (state === 'active') active++;
    }
    updateConcurrencyVisualization(active, queued);
}

export function createStreamCard(streamId) {
    streamStates.set(streamId, 'initializing');
    
    const startTime = performance.now();
    let firstTokenTime = null;
    
    return {
        appendToken: (token) => {
            if (!firstTokenTime) {
                firstTokenTime = performance.now();
                const latency = Math.round(firstTokenTime - startTime);
                appendEventLog(streamId, 'first_token', `(${latency}ms)`);
            }
        },
        updateStatus: (statusText) => {
            const state = statusText.toLowerCase();
            streamStates.set(streamId, state);
            
            recalculateConcurrency();
            
            if (state === 'queued') {
                appendEventLog(streamId, 'queued');
            } else if (state === 'active') {
                appendEventLog(streamId, 'assigned');
            } else if (state === 'completed') {
                let durationStr = "";
                if (firstTokenTime) {
                    const duration = ((performance.now() - startTime) / 1000).toFixed(1);
                    durationStr = `in ${duration}s`;
                    const latency = Math.round(firstTokenTime - startTime);
                    updateLatencyVisualization(streamId, latency);
                }
                appendEventLog(streamId, 'completed', durationStr);
                streamStates.delete(streamId);
                recalculateConcurrency();
            } else if (state === 'error') {
                appendEventLog(streamId, 'error');
                streamStates.delete(streamId);
                recalculateConcurrency();
            }
        }
    };
}

export function clearStreamsContainer() {
    const container = getEl("streams-container");
    if (container) {
        container.innerHTML = "";
    }
    streamStates.clear();
    totalEvents = 0;
    const countEl = getEl("event-count");
    if (countEl) countEl.innerText = `0 EVENTS`;
    recalculateConcurrency();
}

function updateRetention() {
    const container = getEl("streams-container");
    if (!container) return;
    
    // Limit total log lines to 250 to keep DOM light but preserve recent history
    while (container.children.length > 250) {
        container.removeChild(container.firstChild);
    }
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
