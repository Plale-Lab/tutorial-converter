document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('convertForm');
    const startBtn = document.getElementById('startBtn');
    const statusBadge = document.getElementById('statusBadge');
    const activityFeed = document.getElementById('activityFeed');
    const resultContainer = document.getElementById('resultContainer');
    const emptyState = document.getElementById('emptyState');
    const contentView = document.getElementById('contentView');
    const downloadLink = document.getElementById('downloadLink');
    const exportActions = document.getElementById('exportActions');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // 1. UI Reset & Start State
        startBtn.disabled = true;
        startBtn.innerHTML = `<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i> Processing...`;
        statusBadge.classList.remove('hidden');
        activityFeed.innerHTML = ''; // Clear feed
        exportActions.classList.add('hidden');
        contentView.classList.add('hidden');
        emptyState.classList.remove('hidden');
        lucide.createIcons();

        // 2. Add Initial Logs
        addActivityCard('system', 'Initializing Pipeline', 'Allocating resources...', 'running');
        await wait(600);
        
        // 3. Prepare Data
        const formData = new FormData(form);
        const url = formData.get('url');

        // SIMULATION: Because backend is sync (blocking), we can't stream real progress easily without WebSockets.
        // We will simulate the "Running" steps visually before the main request completes (or while waiting if async).
        // Since the 'convert' view is blocking, the fetch will hang until done.
        // To make UI responsive, we show "Ingesting" -> "Thinking" before we get the result.
        
        simulateProgressSteps();

        try {
            // 4. Send Request
            const response = await fetch('/convert/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (!response.ok) throw new Error('Network response was not ok');
            
            const data = await response.json();

            // 5. Handle Success
            if (data.success) {
                completeProgress();
                renderResult(data);
            } else {
                addActivityCard('error', 'Process Failed', data.error || 'Unknown error', 'error');
            }

        } catch (error) {
            console.error('Error:', error);
            addActivityCard('error', 'Network Error', error.message, 'error');
        } finally {
            startBtn.disabled = false;
            startBtn.innerHTML = `<i data-lucide="play" class="w-4 h-4 fill-current"></i> Start Processing`;
            statusBadge.classList.add('hidden');
            lucide.createIcons();
        }
    });

    function addActivityCard(type, title, message, status = 'completed') {
        const icons = {
            system: 'cpu',
            ingest: 'file-search',
            rewrite: 'pen-tool',
            vision: 'image',
            assembly: 'layout',
            success: 'check-circle-2',
            error: 'alert-triangle'
        };
        
        const colors = {
            running: 'border-emerald-500 border-l-4 bg-white',
            completed: 'border-gray-200 border-l-4 bg-white opacity-80',
            error: 'border-red-500 border-l-4 bg-red-50'
        };

        const card = document.createElement('div');
        card.className = `p-4 rounded-lg shadow-sm border ${colors[status]} transition-all animate-in slide-in-from-left-2 duration-300`;
        card.innerHTML = `
            <div class="flex items-start gap-3">
                <div class="${status === 'running' ? 'text-emerald-600 animate-pulse' : 'text-gray-400'}">
                    <i data-lucide="${icons[type] || 'activity'}" class="w-5 h-5"></i>
                </div>
                <div>
                    <h4 class="text-sm font-semibold text-gray-900">${title}</h4>
                    <p class="text-xs text-gray-500 mt-1">${message}</p>
                </div>
            </div>
        `;
        
        activityFeed.appendChild(card);
        // Auto scroll
        activityFeed.scrollTop = activityFeed.scrollHeight;
        lucide.createIcons();
    }

    async function simulateProgressSteps() {
        // Steps simulated while waiting for the blocking backend
        addActivityCard('ingest', 'Ingestion Agent', 'Scraping and parsing content source...', 'running');
        await wait(2000); // Fake delay
        
        addActivityCard('ingest', 'Ingestion Agent', 'Content parsed successfully.', 'completed');
        addActivityCard('rewrite', 'Rewrite Agent', 'Analyzing complexity and extracting glossary...', 'running');
        await wait(2500); 
        
        addActivityCard('rewrite', 'Rewrite Agent', 'Targeting 5th Grade reading level...', 'running');
        await wait(3000);
        
        addActivityCard('vision', 'Vision Agent', 'Generating illustrative assets...', 'running');
    }

    function completeProgress() {
        // Clear running states
        activityFeed.innerHTML = '';
        const steps = [
            ['ingest', 'Ingestion Complete', 'Source content parsed.'],
            ['rewrite', 'Rewrite Logic Applied', 'Content simplified and glossary added.'],
            ['vision', 'Assets Generated', 'Images synthesized and embedded.'],
            ['assembly', 'Final Assembly', 'PDF rendered successfully.'],
            ['success', 'Pipeline Finished', 'Document is ready for review.']
        ];
        
        steps.forEach(step => addActivityCard(step[0], step[1], step[2], 'completed'));
    }

    function renderResult(data) {
        emptyState.classList.add('hidden');
        contentView.classList.remove('hidden');
        exportActions.classList.remove('hidden');
        
        downloadLink.href = data.pdf_url;
        
        // Simple Markdown Rendering (Basic replacement or use a lib if added)
        // For now, we inject text. Ideally, use marked.js
        contentView.innerText = data.markdown_content; 
        
        // If we want HTML preview, we should return HTML from view or render markdown in JS
        // Let's assume the view returns raw text for this iteration.
        // Enhacement: Use a simple MD parser
        contentView.innerHTML = parseMarkdown(data.markdown_content);
    }

    function wait(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    // Very Basic Markdown Parser for preview
    function parseMarkdown(text) {
        if (!text) return '';
        let html = text
            .replace(/^# (.*$)/gim, '<h1 class="text-2xl font-bold mb-4">$1</h1>')
            .replace(/^## (.*$)/gim, '<h2 class="text-xl font-bold mb-3 mt-6">$1</h2>')
            .replace(/^### (.*$)/gim, '<h3 class="text-lg font-bold mb-2 mt-4">$1</h3>')
            .replace(/\*\*(.*)\*\*/gim, '<b>$1</b>')
            .replace(/\!\[(.*?)\]\((.*?)\)/gim, '<img src="$2" alt="$1" class="rounded-lg shadow-md my-4 max-h-64 object-contain">')
            .replace(/\n/gim, '<br>');
        return html;
    }
});
