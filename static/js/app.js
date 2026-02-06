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

    // File Upload Dropzone
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const fileNameDisplay = document.getElementById('fileName');

    if (dropZone && fileInput) {
        dropZone.addEventListener('click', () => fileInput.click());

        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('border-emerald-400', 'bg-emerald-50');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('border-emerald-400', 'bg-emerald-50');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('border-emerald-400', 'bg-emerald-50');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                fileInput.files = files;
                showFileName(files[0].name);
            }
        });

        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                showFileName(fileInput.files[0].name);
            }
        });

        function showFileName(name) {
            fileNameDisplay.textContent = `📎 ${name}`;
            fileNameDisplay.classList.remove('hidden');
        }
    }

    // Vision Strategy Toggle
    const visionBtns = document.querySelectorAll('.vision-btn');
    const visionInput = document.getElementById('visionStrategyInput');
    const visionHint = document.getElementById('visionHint');

    const visionHints = {
        'ai_gen': 'Generate new images with AI.',
        'hybrid': 'Use original images + AI enhancements.',
        'original': 'Keep original images only.',
        'text_only': 'No images, text content only.'
    };

    visionBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active state from all
            visionBtns.forEach(b => {
                b.classList.remove('bg-white', 'shadow', 'text-gray-800');
                b.classList.add('text-gray-500');
            });
            // Add active state to clicked
            btn.classList.add('bg-white', 'shadow', 'text-gray-800');
            btn.classList.remove('text-gray-500');
            // Update hidden input
            const value = btn.dataset.value;
            visionInput.value = value;
            // Update hint
            if (visionHint) visionHint.textContent = visionHints[value] || '';
        });
    });

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

        // SIMULATION
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

    // --- Helper Functions ---
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
        await wait(2000);

        addActivityCard('ingest', 'Ingestion Agent', 'Content parsed successfully.', 'completed');
        addActivityCard('rewrite', 'Rewrite Agent', 'Analyzing complexity and extracting glossary...', 'running');
        await wait(2500);

        addActivityCard('rewrite', 'Rewrite Agent', 'Targeting 5th Grade reading level...', 'running');
        await wait(3000);

        addActivityCard('vision', 'Vision Agent', 'Generating illustrative assets...', 'running');
    }

    function completeProgress() {
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
        contentView.innerText = data.markdown_content;
        contentView.innerHTML = parseMarkdown(data.markdown_content);
    }

    function wait(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

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

    // --- Console Logic ---
    const consoleToggleBtn = document.getElementById('consoleToggleBtn');
    const debugConsole = document.getElementById('debugConsole');
    const closeConsoleBtn = document.getElementById('closeConsoleBtn');
    const consoleOutput = document.getElementById('consoleOutput');
    let logInterval = null;

    if (consoleToggleBtn) {
        // Toggle Console
        consoleToggleBtn.addEventListener('click', () => {
            console.log("Toggle");
            debugConsole.classList.toggle('hidden');
            if (!debugConsole.classList.contains('hidden')) {
                startPollingLogs();
            } else {
                stopPollingLogs();
            }
        });

        closeConsoleBtn.addEventListener('click', () => {
            debugConsole.classList.add('hidden');
            stopPollingLogs();
        });

        // Make Console Draggable
        const consoleHeader = document.getElementById('consoleHeader');
        let isDragging = false;
        let currentX;
        let currentY;
        let initialX;
        let initialY;
        let xOffset = 0;
        let yOffset = 0;

        consoleHeader.addEventListener("mousedown", dragStart);
        document.addEventListener("mouseup", dragEnd);
        document.addEventListener("mousemove", drag);

        function dragStart(e) {
            initialX = e.clientX - xOffset;
            initialY = e.clientY - yOffset;
            if (e.target === consoleHeader || e.target.parentNode === consoleHeader) {
                isDragging = true;
            }
        }

        function dragEnd(e) {
            initialX = currentX;
            initialY = currentY;
            isDragging = false;
        }

        function drag(e) {
            if (isDragging) {
                e.preventDefault();
                currentX = e.clientX - initialX;
                currentY = e.clientY - initialY;
                xOffset = currentX;
                yOffset = currentY;
                setTranslate(currentX, currentY, debugConsole);
            }
        }

        function setTranslate(xPos, yPos, el) {
            el.style.transform = "translate3d(" + xPos + "px, " + yPos + "px, 0)";
        }
    }

    function startPollingLogs() {
        if (logInterval) clearInterval(logInterval);
        fetchLogs(); // Immediate fetch
        logInterval = setInterval(fetchLogs, 2000);
    }

    function stopPollingLogs() {
        if (logInterval) clearInterval(logInterval);
        logInterval = null;
    }

    async function fetchLogs() {
        try {
            const response = await fetch('/logs/');
            const data = await response.json();

            if (data.logs && data.logs.length > 0) {
                const html = data.logs.map(line => {
                    let color = 'text-gray-300';
                    if (line.includes('ERROR')) color = 'text-red-400';
                    if (line.includes('WARNING')) color = 'text-yellow-400';
                    if (line.includes('INFO')) color = 'text-blue-300';
                    return `<div class="${color} whitespace-pre-wrap font-mono text-[11px] hover:bg-gray-800">${line}</div>`;
                }).join('');

                consoleOutput.innerHTML = html;
                consoleOutput.scrollTop = consoleOutput.scrollHeight;
            }
        } catch (e) {
            console.error("Failed to fetch logs", e);
        }
    }

    // --- Settings Modal Logic ---
    const settingsBtn = document.getElementById('settingsBtn');
    const settingsModal = document.getElementById('settingsModal');
    const closeSettingsBtn = document.getElementById('closeSettingsBtn');
    const cancelSettingsBtn = document.getElementById('cancelSettingsBtn');
    const saveSettingsBtn = document.getElementById('saveSettingsBtn');
    const settingLLMProvider = document.getElementById('settingLLMProvider');
    const ollamaModelSection = document.getElementById('ollamaModelSection');
    const apiKeySection = document.getElementById('apiKeySection');
    const settingImageProvider = document.getElementById('settingImageProvider');
    const comfyuiUrlSection = document.getElementById('comfyuiUrlSection');

    if (settingsBtn && settingsModal) {
        // Load settings from localStorage
        function loadSettings() {
            const settings = JSON.parse(localStorage.getItem('convertit_settings') || '{}');

            if (settings.llm_provider) {
                settingLLMProvider.value = settings.llm_provider;
                toggleLLMSections(settings.llm_provider);
            }
            if (settings.ollama_model) {
                document.getElementById('settingOllamaModel').value = settings.ollama_model;
            }
            if (settings.api_key) {
                document.getElementById('settingAPIKey').value = settings.api_key;
            }
            if (settings.image_provider) {
                settingImageProvider.value = settings.image_provider;
                toggleImageSections(settings.image_provider);
            }
            if (settings.comfyui_url) {
                document.getElementById('settingComfyUIUrl').value = settings.comfyui_url;
            }
            if (settings.rag_folder) {
                document.getElementById('settingRAGFolder').value = settings.rag_folder;
            }
            if (settings.output_folder) {
                document.getElementById('settingOutputFolder').value = settings.output_folder;
            }
        }

        function toggleLLMSections(provider) {
            if (provider === 'local') {
                ollamaModelSection.classList.remove('hidden');
                apiKeySection.classList.add('hidden');
            } else {
                ollamaModelSection.classList.add('hidden');
                apiKeySection.classList.remove('hidden');
            }
        }

        function toggleImageSections(provider) {
            if (provider === 'comfyui') {
                comfyuiUrlSection.classList.remove('hidden');
            } else {
                comfyuiUrlSection.classList.add('hidden');
            }
        }

        settingLLMProvider.addEventListener('change', (e) => toggleLLMSections(e.target.value));
        settingImageProvider.addEventListener('change', (e) => toggleImageSections(e.target.value));

        settingsBtn.addEventListener('click', () => {
            loadSettings();
            settingsModal.classList.remove('hidden');
            lucide.createIcons();
        });

        const closeModal = () => {
            settingsModal.classList.add('hidden');
        };

        closeSettingsBtn.addEventListener('click', closeModal);
        cancelSettingsBtn.addEventListener('click', closeModal);

        // Close on backdrop click
        settingsModal.addEventListener('click', (e) => {
            if (e.target === settingsModal) closeModal();
        });

        saveSettingsBtn.addEventListener('click', async () => {
            const settings = {
                llm_provider: settingLLMProvider.value,
                ollama_model: document.getElementById('settingOllamaModel').value,
                api_key: document.getElementById('settingAPIKey').value,
                image_provider: settingImageProvider.value,
                comfyui_url: document.getElementById('settingComfyUIUrl').value,
                rag_folder: document.getElementById('settingRAGFolder').value,
                output_folder: document.getElementById('settingOutputFolder').value
            };

            // Save to localStorage
            localStorage.setItem('convertit_settings', JSON.stringify(settings));

            // Also send to backend (optional - will fail without Django but settings still saved locally)
            try {
                await fetch('/api/settings/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(settings)
                });
            } catch (e) {
                console.warn('Could not save settings to backend (using localStorage only):', e);
            }

            closeModal();

            // Show success feedback
            const btn = saveSettingsBtn;
            btn.textContent = '✓ Saved!';
            btn.classList.add('bg-emerald-700');
            setTimeout(() => {
                btn.textContent = 'Save Settings';
                btn.classList.remove('bg-emerald-700');
            }, 1500);
        });

        // Load on init
        loadSettings();
    }

    // --- Index Now Button ---
    const indexNowBtn = document.getElementById('indexNowBtn');
    const indexStatus = document.getElementById('indexStatus');

    if (indexNowBtn) {
        indexNowBtn.addEventListener('click', async () => {
            const ragFolder = document.getElementById('settingRAGFolder')?.value || './document/convertit/database';

            indexNowBtn.disabled = true;
            indexNowBtn.innerHTML = '<span class="animate-pulse">Indexing...</span>';
            if (indexStatus) indexStatus.textContent = '';

            try {
                const response = await fetch('/api/index/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ rag_folder: ragFolder })
                });

                const data = await response.json();

                if (data.success) {
                    indexNowBtn.innerHTML = '✓ Done';
                    indexNowBtn.classList.add('bg-emerald-100', 'text-emerald-700');
                    if (indexStatus) {
                        indexStatus.textContent = `Indexed: ${data.indexed}, Skipped: ${data.skipped}, Failed: ${data.failed}`;
                        indexStatus.classList.add('text-emerald-600');
                    }
                } else {
                    indexNowBtn.innerHTML = '✗ Error';
                    indexNowBtn.classList.add('bg-red-100', 'text-red-700');
                    if (indexStatus) indexStatus.textContent = data.error || 'Indexing failed';
                }
            } catch (e) {
                indexNowBtn.innerHTML = '✗ Error';
                if (indexStatus) indexStatus.textContent = 'Connection failed';
            }

            // Reset button after delay
            setTimeout(() => {
                indexNowBtn.disabled = false;
                indexNowBtn.innerHTML = '<i data-lucide="database" class="w-3 h-3"></i> Index Now';
                indexNowBtn.classList.remove('bg-emerald-100', 'text-emerald-700', 'bg-red-100', 'text-red-700');
                lucide.createIcons();
            }, 3000);
        });
    }
});
