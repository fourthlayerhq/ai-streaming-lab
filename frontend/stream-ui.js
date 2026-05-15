import { getEl, createEl } from './dom.js';

export function createStreamCard(streamId) {
    const container = getEl("streams-container");
    const card = createEl("div");
    
    card.className = "stream-card";
    card.id = `stream-${streamId}`;
    
    card.innerHTML = `
        <h4>Stream ${streamId}</h4>
        <div class="stream-status">Status: initializing</div>
        <div class="stream-output"></div>
    `;
    
    container.appendChild(card);
    
    const outputElement = card.querySelector(".stream-output");
    const statusElement = card.querySelector(".stream-status");
    
    return {
        appendToken: (token) => {
            outputElement.innerHTML += token;
        },
        updateStatus: (statusText) => {
            statusElement.innerText = `Status: ${statusText}`;
        }
    };
}

export function clearStreamsContainer() {
    const container = getEl("streams-container");
    if (container) {
        container.innerHTML = "";
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
