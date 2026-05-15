import { getEl, createEl } from './dom.js';
import { updateConcurrencyVisualization, updateLatencyVisualization } from './metrics.js';

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
    
    const startTime = performance.now();
    let firstTokenTime = null;
    
    return {
        appendToken: (token) => {
            if (!firstTokenTime) {
                firstTokenTime = performance.now();
            }
            outputElement.innerHTML += token;
        },
        updateStatus: (statusText) => {
            statusElement.innerText = `Status: ${statusText}`;
            card.classList.remove('queued', 'active', 'completed');
            const state = statusText.toLowerCase();
            if (['queued', 'active', 'completed'].includes(state)) {
                card.classList.add(state);
            }
            
            const activeCount = container.querySelectorAll('.stream-card.active').length;
            const queuedCount = container.querySelectorAll('.stream-card.queued').length;
            updateConcurrencyVisualization(activeCount, queuedCount);
            
            if (state === 'completed') {
                updateRetention();
                if (firstTokenTime) {
                    const latency = Math.round(firstTokenTime - startTime);
                    updateLatencyVisualization(latency);
                }
            }
        }
    };
}

export function clearStreamsContainer() {
    const container = getEl("streams-container");
    if (container) {
        container.innerHTML = "";
    }
}

function updateRetention() {
    const container = getEl("streams-container");
    if (!container) return;
    const completedCards = Array.from(container.querySelectorAll('.stream-card.completed'));
    if (completedCards.length > 20) {
        const toRemove = completedCards.length - 20;
        for (let i = 0; i < toRemove; i++) {
            completedCards[i].remove();
        }
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
