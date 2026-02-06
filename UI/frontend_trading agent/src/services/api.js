// Removed unused import

// Native EventSource only supports GET. The backend uses POST for /api/analyze.
// So we need fetch-event-source or similar wrapper.
// Actually, I didn't install @microsoft/fetch-event-source.
// I should install it or use a simple fetch reader.
// Let's use a simple fetch reader for MVP to avoid extradeps if possible, OR add the dep.
// Adding dep is safer.
// "npm install @microsoft/fetch-event-source"
// I will add this to the installation instructions or run it now.
// For now, I'll write the code assuming I can install it.

// Wait, I can use a simple async generator with fetch if I don't need auto-reconnect logic which native EventSource provides (but doesn't support POST).
// The backend uses sse_starlette.
// Let's try using fetch and reading the body stream.

export const api = {
    async getConfig() {
        const res = await fetch('/api/config');
        return res.json();
    },

    async analyze(params, onMessage, onError, onComplete) {
        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(params),
            });

            if (!response.ok) {
                throw new Error(`Error: ${response.statusText}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                buffer += chunk;

                // Split by double newline (standard SSE)
                const lines = buffer.split('\n\n');
                buffer = lines.pop(); // Keep incomplete chunk

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const dataStr = line.replace('data: ', '').trim();
                        if (dataStr === '[DONE]') {
                            onComplete();
                            return;
                        }
                        try {
                            const data = JSON.parse(dataStr);
                            onMessage(data);
                        } catch (e) {
                            console.error('Failed to parse SSE data:', dataStr, e);
                        }
                    } else if (line.startsWith('event: ')) {
                        // We might want to track event type but usually data follows
                        // unique to sse_starlette, it sends event name then data
                        // My simple parser needs to handle "event: ... \n data: ..."
                        // Let's refine the parser.
                    }
                }
            }
            onComplete();

        } catch (err) {
            onError(err);
        }
    }
};

// Refined parser logic to handle multi-line SSE messages if needed
// MVP: simplified version above might miss the "event" field.
// Let's make it robust.

async function streamAnalysis(params, onEvent) {
    const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params)
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    try {
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });

            // Split by double newline (handles \r\n\r\n or \n\n)
            const parts = buffer.split(/\r\n\r\n|\n\n/);
            buffer = parts.pop(); // Keep incomplete chunk

            for (const message of parts) {
                parseAndEmit(message, onEvent);
            }
        }

        // Process any remaining buffer
        if (buffer.trim()) {
            parseAndEmit(buffer, onEvent);
        }

    } finally {
        reader.releaseLock();
    }
}

function parseAndEmit(message, onEvent) {
    const lines = message.split(/\r?\n/);
    let event = 'message';
    let data = '';

    for (const line of lines) {
        if (line.startsWith('event: ')) {
            event = line.substring(7).trim();
        } else if (line.startsWith('data: ')) {
            data = line.substring(6).trim();
        }
    }

    if (data) {
        try {
            onEvent({ event, data: JSON.parse(data) });
        } catch (e) {
            console.warn('Non-JSON data:', data);
            onEvent({ event, data });
        }
    }
}

export default {
    getConfig: async () => {
        const res = await fetch('/api/config');
        return res.json();
    },
    streamAnalysis
};
