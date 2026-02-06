<script setup>
import { ref, onMounted } from 'vue';
import { X, Save, Key, ShieldCheck, Server, Settings, Check, Loader2 } from 'lucide-vue-next';

const props = defineProps({
  isOpen: Boolean
});

const emit = defineEmits(['close']);

const openaiKey = ref('');
const anthropicKey = ref('');
const googleKey = ref('');
const groqKey = ref('');
const deepseekKey = ref('');
const qwenKey = ref('');
const ollamaUrl = ref('http://localhost:11434/v1');
const alphaVantageKey = ref('');

const ollamaStatus = ref('idle'); // idle, checking, connected, error
const isCheckingOllama = ref(false);
const ollamaModels = ref([]);
const ollamaCtx = ref(4096);
// Fixed gears for context length
const ollamaCtxOptions = [4096, 8192, 16384, 32768, 65536, 131072, 262144];
const ollamaCtxIndex = ref(0);

const updateOllamaCtxFromIndex = () => {
    ollamaCtx.value = ollamaCtxOptions[ollamaCtxIndex.value];
};

const ollamaModelInput = ref('');

const formatContextLength = (val) => {
    if (val >= 1024) return `${Math.round(val / 1024)}k`;
    return val;
};



const notification = ref({
    show: false,
    title: '',
    message: '',
    type: 'info', // info, success, error
    loading: false,
    action: null, // 'pull' or 'run'
    model: null
});

const closeNotification = () => {
    notification.value.show = false;
};

const stopPull = async () => {
    if (!notification.value.model) return;
    
    try {
        await fetch('http://localhost:8000/api/ollama/cancel', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                action: 'cancel',
                model: notification.value.model
            })
        });
        notification.value.loading = false;
        notification.value.type = 'error';
        notification.value.title = 'Process Stopped';
        notification.value.message = 'The model pulling process was cancelled by user.';
    } catch (e) {
        console.error("Stop error:", e);
    }
};

const pollStatus = async (model) => {
    const pollInterval = setInterval(async () => {
        if (!notification.value.show || notification.value.model !== model) {
            clearInterval(pollInterval);
            return;
        }

        try {
            const res = await fetch(`http://localhost:8000/api/ollama/status/${model}`);
            if (res.ok) {
                const statusData = await res.json();
                
                // Update message if still pulling
                if (statusData.status === 'pulling') {
                    notification.value.message = statusData.message;
                } else if (statusData.status === 'success') {
                    clearInterval(pollInterval);
                    notification.value.loading = false;
                    notification.value.type = 'success';
                    notification.value.title = 'Success';
                    notification.value.message = statusData.message;
                } else if (statusData.status === 'error' || statusData.status === 'cancelled') {
                    clearInterval(pollInterval);
                    notification.value.loading = false;
                    notification.value.type = 'error';
                    notification.value.title = statusData.status === 'cancelled' ? 'Cancelled' : 'Error';
                    notification.value.message = statusData.message;
                }
            }
        } catch (e) {
            console.error("Poll error:", e);
        }
    }, 1000);
};

const handleOllamaAction = async (action) => {
    if (!ollamaModelInput.value) return;
    
    // Show loading notification
    notification.value = {
        show: true,
        title: action === 'pull' ? 'Pulling Model...' : 'Loading Model...',
        message: action === 'pull' 
            ? `Downloading ${ollamaModelInput.value} in background...` 
            : `Loading ${ollamaModelInput.value} into memory...`,
        type: 'info',
        loading: true,
        action: action,
        model: ollamaModelInput.value
    };
    
    try {
        const response = await fetch('http://localhost:8000/api/ollama/manage', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: action,
                model: ollamaModelInput.value,
                ollama_url: ollamaUrl.value
            })
        });
        
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Request failed');
        }
        
        // Handle "started" status for background jobs (pull) vs "success" for instant (run)
        if (data.status === 'started') {
             notification.value.message = data.message;
             // Start Polling if it's a pull action
             if (action === 'pull') {
                 pollStatus(ollamaModelInput.value);
             }
        } else {
             notification.value.loading = false;
             notification.value.type = 'success';
             notification.value.title = 'Success';
             notification.value.message = data.message;
        }
        
    } catch (e) {
        notification.value.loading = false;
        notification.value.type = 'error';
        notification.value.title = 'Error';
        notification.value.message = e.message;
    }
};

const checkOllamaConnection = async () => {
    isCheckingOllama.value = true;
    ollamaStatus.value = 'checking';
    ollamaModels.value = [];
    
    // Normalize URL: remove /v1 suffix to get base for /api/tags checks if needed, 
    // but standard OpenAI compatible endpoint is /v1/models
    try {
        const cleanUrl = ollamaUrl.value.replace(/\/v1\/?$/, '');
        let response = null;
        
        // Try /v1/models (OpenAI standard)
        try {
           response = await fetch(`${cleanUrl}/v1/models`);
        } catch (e) {
           // Fallback to /api/tags (Ollama native)
           response = await fetch(`${cleanUrl}/api/tags`);
        }

        if (response && response.ok) {
            const data = await response.json();
            // Handle both formats
            if (data.data) {
                // OpenAI format
                ollamaModels.value = data.data.map(m => m.id);
            } else if (data.models) {
                // Ollama format
                ollamaModels.value = data.models.map(m => m.name);
            }
            ollamaStatus.value = 'connected';
        } else {
            throw new Error('Invalid response');
        }
    } catch (err) {
        console.error('Ollama connection failed:', err);
        ollamaStatus.value = 'error';
    } finally {
        isCheckingOllama.value = false;
    }
};

const saved = ref(false); // 'en' or 'zh'

const language = ref('en'); // 'en' or 'zh'

onMounted(() => {
  openaiKey.value = localStorage.getItem('TA_OPENAI_API_KEY') || '';
  anthropicKey.value = localStorage.getItem('TA_ANTHROPIC_API_KEY') || '';
  googleKey.value = localStorage.getItem('TA_GOOGLE_API_KEY') || '';
  groqKey.value = localStorage.getItem('TA_GROQ_API_KEY') || '';
  deepseekKey.value = localStorage.getItem('TA_DEEPSEEK_API_KEY') || '';
  qwenKey.value = localStorage.getItem('TA_QWEN_API_KEY') || '';
  ollamaUrl.value = localStorage.getItem('TA_OLLAMA_URL') || 'http://localhost:11434/v1';
  alphaVantageKey.value = localStorage.getItem('TA_ALPHA_VANTAGE_API_KEY') || '';
  language.value = localStorage.getItem('TA_LANGUAGE') || 'en';
  ollamaCtx.value = Number(localStorage.getItem('TA_OLLAMA_CTX')) || 4096;
  // Sync index
  const foundIndex = ollamaCtxOptions.indexOf(ollamaCtx.value);
  ollamaCtxIndex.value = foundIndex !== -1 ? foundIndex : 0;
});

const saveSettings = () => {
  localStorage.setItem('TA_OPENAI_API_KEY', openaiKey.value);
  localStorage.setItem('TA_ANTHROPIC_API_KEY', anthropicKey.value);
  localStorage.setItem('TA_GOOGLE_API_KEY', googleKey.value);
  localStorage.setItem('TA_GROQ_API_KEY', groqKey.value);
  localStorage.setItem('TA_DEEPSEEK_API_KEY', deepseekKey.value);
  localStorage.setItem('TA_QWEN_API_KEY', qwenKey.value);
  localStorage.setItem('TA_OLLAMA_URL', ollamaUrl.value);
  localStorage.setItem('TA_ALPHA_VANTAGE_API_KEY', alphaVantageKey.value);
  localStorage.setItem('TA_LANGUAGE', language.value);
  localStorage.setItem('TA_OLLAMA_CTX', ollamaCtx.value);
  
  saved.value = true;
  setTimeout(() => {
    saved.value = false;
    emit('close');
  }, 800);
};
</script>

<template>
  <Teleport to="body">
    <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <!-- Backdrop -->
      <div class="absolute inset-0 bg-gray-900/60 backdrop-blur-sm transition-opacity" @click="$emit('close')"></div>

      <!-- Modal -->
      <div class="relative w-full max-w-2xl bg-white rounded-2xl shadow-2xl ring-1 ring-black/5 flex flex-col max-h-[90vh]">
        
        <!-- Header -->
        <div class="p-6 border-b border-gray-100 flex items-center justify-between shrink-0">
            <div class="flex items-center gap-3">
                <div class="p-2 bg-emerald-50 rounded-lg text-emerald-600">
                    <Key class="w-6 h-6" />
                </div>
                <div>
                    <h3 class="text-xl font-bold text-gray-900">TradingAgent Plus Configuration</h3>
                    <p class="text-xs text-gray-500">Securely configure your AI models and data feeds.</p>
                </div>
            </div>
            <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600 transition p-1 hover:bg-gray-100 rounded-full">
                <X class="w-6 h-6" />
            </button>
        </div>

        <!-- Scrollable Content -->
        <div class="flex-1 overflow-y-auto p-6 custom-scrollbar">
            <form @submit.prevent="saveSettings" class="space-y-8">
            
            <!-- General Settings -->
            <div>
                <h4 class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-4 border-b border-gray-100 pb-2">General Settings</h4>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Interface Language</label>
                    <select v-model="language" class="input-field">
                        <option value="en">English</option>
                        <option value="zh">Chinese (Simplified)</option>
                    </select>
                </div>
            </div>

            <!-- Data Vendors -->
            <div>
                <h4 class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-4 border-b border-gray-100 pb-2">Data Venders (Required)</h4>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Alpha Vantage API Key</label>
                    <div class="relative">
                        <input v-model="alphaVantageKey" type="password" placeholder="YOUR_KEY" 
                            class="w-full pl-10 pr-3 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:bg-white outline-none transition text-sm font-mono text-gray-600 placeholder:text-gray-400" />
                        <ShieldCheck class="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
                    </div>
                </div>
            </div>

            <!-- Model Providers -->
            <div>
                <h4 class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-4 border-b border-gray-100 pb-2">LLM Providers</h4>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <!-- OpenAI -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">OpenAI API Key</label>
                        <input v-model="openaiKey" type="password" placeholder="sk-..." class="input-field" />
                    </div>

                    <!-- Anthropic -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Anthropic (Claude) Key</label>
                        <input v-model="anthropicKey" type="password" placeholder="sk-ant-..." class="input-field" />
                    </div>

                    <!-- Google -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Google Gemini Key</label>
                        <input v-model="googleKey" type="password" placeholder="AIza..." class="input-field" />
                    </div>

                    <!-- Groq -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Groq API Key</label>
                        <input v-model="groqKey" type="password" placeholder="gsk_..." class="input-field" />
                    </div>

                    <!-- Deepseek -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Deepseek API Key</label>
                        <input v-model="deepseekKey" type="password" placeholder="sk-..." class="input-field" />
                    </div>

                    <!-- Qwen -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Qwen (DashScope) Key</label>
                        <input v-model="qwenKey" type="password" placeholder="sk-..." class="input-field" />
                    </div>
                </div>

                <!-- Local / Ollama -->
                <div class="mt-6">
                     <div class="flex items-center justify-between mb-1">
                        <label class="block text-sm font-medium text-gray-700 flex items-center gap-2">
                            <Server class="w-4 h-4" /> Local LLM (Ollama) URL
                        </label>
                        <span v-if="ollamaStatus === 'connected'" class="text-xs font-medium text-emerald-600 flex items-center gap-1">
                            <span class="w-2 h-2 rounded-full bg-emerald-500"></span> Connected
                        </span>
                        <span v-else-if="ollamaStatus === 'error'" class="text-xs font-medium text-red-500 flex items-center gap-1">
                            <span class="w-2 h-2 rounded-full bg-red-500"></span> Connection Failed
                        </span>
                     </div>
                     <div class="flex gap-2">
                        <input v-model="ollamaUrl" type="text" placeholder="http://localhost:11434/v1" class="input-field font-mono text-gray-600 flex-1" />
                        <button type="button" @click="checkOllamaConnection" :disabled="isCheckingOllama" class="px-4 py-2.5 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium rounded-xl transition text-sm flex items-center gap-2 whitespace-nowrap">
                            <span v-if="isCheckingOllama" class="w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full animate-spin"></span>
                            <span v-else>Check</span>
                        </button>
                     </div>
                     <p v-if="ollamaModels.length > 0" class="mt-2 text-xs text-gray-500">
                        Available Models: <span class="font-mono text-emerald-600">{{ ollamaModels.slice(0, 3).join(', ') }}{{ ollamaModels.length > 3 ? ` +${ollamaModels.length - 3} more` : '' }}</span>
                     </p>

                     <!-- Context Length Slider -->
                     <div class="mt-4 pt-4 border-t border-gray-100">
                        <div class="flex items-center justify-between mb-2">
                            <label class="text-sm font-medium text-gray-700 flex items-center gap-2">
                                <Settings class="w-4 h-4" /> Context Length
                            </label>
                            <span class="text-xs font-mono font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded">{{ formatContextLength(ollamaCtx) }}</span>
                        </div>
                        <p class="text-xs text-gray-400 mb-3">Determines how much conversation history local LLMs can remember available RAM.</p>
                        
                        <!-- Fixed Gear Slider: Mapped to indices 0-6 -->
                        <div class="relative w-full h-6 flex items-center select-none mt-2">
                            <!-- Steps Markers (Visual) -->
                            <div class="absolute w-full flex justify-between px-1 pointer-events-none z-0">
                                <span v-for="step in 7" :key="step" class="w-1 h-1 bg-gray-300 rounded-full"></span>
                            </div>

                            <input 
                                type="range" 
                                v-model.number="ollamaCtxIndex" 
                                min="0" 
                                max="6" 
                                step="1"
                                class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-emerald-600 z-10 relative"
                                @input="updateOllamaCtxFromIndex"
                            />
                        </div>
                        <div class="flex justify-between text-[10px] text-gray-400 mt-1 font-mono">
                            <span>4k</span>
                            <span>8k</span>
                            <span>16k</span>
                            <span>32k</span>
                            <span>64k</span>
                            <span>128k</span>
                            <span>256k</span>
                        </div>
                     </div>

                     <!-- Model Management (Frontend Prototype) -->
                     <div class="mt-4 pt-4 border-t border-gray-100">
                        <h5 class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Model Management</h5>
                        <div class="flex gap-2">
                            <input v-model="ollamaModelInput" type="text" placeholder="e.g. llama3" class="input-field font-mono text-gray-600 flex-1" />
                            <div class="flex gap-1">
                                <button type="button" @click="handleOllamaAction('pull')" class="px-3 py-2 bg-blue-50 text-blue-600 hover:bg-blue-100 rounded-lg text-xs font-bold transition">
                                    Pull
                                </button>
                                <button type="button" @click="handleOllamaAction('run')" class="px-3 py-2 bg-emerald-50 text-emerald-600 hover:bg-emerald-100 rounded-lg text-xs font-bold transition">
                                    Run
                                </button>
                            </div>
                        </div>
                        <p class="text-[10px] text-gray-400 mt-2 flex justify-between items-center">
                            <span>* Management commands will be processed by the backend.</span>
                            <a href="https://ollama.com/search" target="_blank" class="text-emerald-600 hover:text-emerald-700 hover:underline">
                                Browse supported models on Ollama.com &rarr;
                            </a>
                        </p>
                     </div>
                </div>
            </div>

            </form>
        </div>

            <!-- Notification Overlay -->
            <div v-if="notification.show" class="absolute inset-0 bg-white/90 backdrop-blur-sm z-50 flex items-center justify-center rounded-2xl">
                <div class="text-center p-6 max-w-sm">
                    <div v-if="notification.loading" class="mb-4 flex justify-center">
                        <Loader2 class="w-10 h-10 text-emerald-600 animate-spin" />
                    </div>
                    <div v-else-if="notification.type === 'success'" class="mb-4 flex justify-center">
                        <div class="w-10 h-10 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center">
                            <Check class="w-6 h-6" />
                        </div>
                    </div>
                     <div v-else-if="notification.type === 'error'" class="mb-4 flex justify-center">
                        <div class="w-10 h-10 bg-red-100 text-red-600 rounded-full flex items-center justify-center">
                            <X class="w-6 h-6" />
                        </div>
                    </div>

                    <h3 class="text-lg font-bold text-gray-900 mb-2">{{ notification.title }}</h3>
                    <p class="text-sm text-gray-600 mb-6 leading-relaxed">{{ notification.message }}</p>

                    <div class="flex justify-center gap-3">
                         <button v-if="notification.loading && notification.action === 'pull'" @click="stopPull" class="px-5 py-2.5 bg-red-100 hover:bg-red-200 active:bg-red-300 text-red-700 font-bold rounded-xl transition text-sm">
                            Stop Process
                        </button>
                        <button v-if="!notification.loading" @click="closeNotification" class="px-5 py-2.5 bg-gray-900 active:bg-gray-800 text-white font-bold rounded-xl transition text-sm">
                            Close
                        </button>
                    </div>
                </div>
            </div>

            <!-- Footer -->
            <div class="p-6 border-t border-gray-100 shrink-0 bg-gray-50/50 rounded-b-2xl">
            <button @click="saveSettings" class="w-full flex items-center justify-center gap-2 bg-gray-900 hover:bg-gray-800 text-white font-semibold py-3.5 rounded-xl transition-all active:scale-[0.99] shadow-lg shadow-gray-200">
               <span v-if="saved" class="flex items-center gap-2 text-emerald-400">Settings Saved!</span>
               <span v-else class="flex items-center gap-2"><Save class="w-4 h-4" /> Save Configuration</span>
            </button>
        </div>

      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.input-field {
    @apply w-full px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:bg-white outline-none transition text-sm font-mono text-gray-600 placeholder:text-gray-400;
}
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: #e5e7eb;
  border-radius: 99px;
}
</style>
