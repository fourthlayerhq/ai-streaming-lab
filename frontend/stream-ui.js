import { getEl, createEl } from './dom.js';
import { updateConcurrencyVisualization, updateLatencyVisualization } from './metrics.js';

export function createStreamCard(streamId) {
    const container = getEl("streams-container");
    const card = createEl("div");
    
    card.className = "stream-card";
    card.id = `stream-${streamId}`;
    
    const now = new Date();
    const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}.${now.getMilliseconds().toString().padStart(3, '0')}`;
    
    card.innerHTML = `
        <div class="stream-header">
            <span class="timestamp">[${timeStr}]</span>
            <span class="stream-id">STREAM-${streamId}</span>
            <span class="stream-status">INIT</span>
        </div>
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
            
            // Auto-scroll when active
            if (container.scrollHeight - container.scrollTop < container.clientHeight + 100) {
                container.scrollTop = container.scrollHeight;
            }
        },
        updateStatus: (statusText) => {
            statusElement.innerText = statusText.toUpperCase();
            card.classList.remove('queued', 'active', 'completed');
            const state = statusText.toLowerCase();
            if (['queued', 'active', 'completed'].includes(state)) {
                card.classList.add(state);
            }
            
            // Update timestamp on state change
            const tNow = new Date();
            const tStr = `${tNow.getHours().toString().padStart(2, '0')}:${tNow.getMinutes().toString().padStart(2, '0')}:${tNow.getSeconds().toString().padStart(2, '0')}.${tNow.getMilliseconds().toString().padStart(3, '0')}`;
            card.querySelector(".timestamp").innerText = `[${tStr}]`;
            
            const activeCount = container.querySelectorAll('.stream-card.active').length;
            const queuedCount = container.querySelectorAll('.stream-card.queued').length;
            updateConcurrencyVisualization(activeCount, queuedCount);
            
            if (state === 'completed') {
                updateRetention();
                if (firstTokenTime) {
                    const latency = Math.round(firstTokenTime - startTime);
                    updateLatencyVisualization(streamId, latency);
                }
            }
            
            container.scrollTop = container.scrollHeight;
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
    if (completedCards.length > 50) {
        const toRemove = completedCards.length - 50;
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
