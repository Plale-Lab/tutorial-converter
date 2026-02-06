<script setup>
import { ref } from 'vue';
import ConfigForm from './components/ConfigForm.vue';
import AnalysisFeed from './components/AnalysisFeed.vue';
import ReportViewer from './components/ReportViewer.vue';
import SettingsModal from './components/SettingsModal.vue';
import api from './services/api';
import { Settings } from 'lucide-vue-next';

const status = ref('idle'); // idle, running, complete, error
const events = ref([]);
const showSettings = ref(false);
const selectedReport = ref(null);

const handleReportSelection = (report) => {
    // Ensure report object has necessary fields for viewer
    selectedReport.value = {
        ...report,
        title: report.section_update ? report.section_update.replace(/_/g, ' ').toUpperCase() : (report.nodeName || 'System Message'),
        content: report.section_content || report.content || report.message
    };
};

const handleStart = async (config) => {
  status.value = 'running';
  events.value = [];
  selectedReport.value = null;
  
  // Inject keys from localStorage
  const enrichedConfig = {
    ...config,
    openai_api_key: localStorage.getItem('TA_OPENAI_API_KEY'),
    anthropic_api_key: localStorage.getItem('TA_ANTHROPIC_API_KEY'),
    google_api_key: localStorage.getItem('TA_GOOGLE_API_KEY'),
    groq_api_key: localStorage.getItem('TA_GROQ_API_KEY'),
    deepseek_api_key: localStorage.getItem('TA_DEEPSEEK_API_KEY'),
    qwen_api_key: localStorage.getItem('TA_QWEN_API_KEY'),
    ollama_base_url: localStorage.getItem('TA_OLLAMA_URL'),
    alpha_vantage_api_key: localStorage.getItem('TA_ALPHA_VANTAGE_API_KEY')
  };

  await api.streamAnalysis(enrichedConfig, (payload) => {
    // Flatten and normalize event data
    let processedEvent = {
        timestamp: new Date().toISOString(),
        rawEvent: payload.event,
        ...payload
    };

    if (payload.data) {
        processedEvent = { ...processedEvent, ...payload.data };
    }

    // Normalize Node Name
    processedEvent.nodeName = processedEvent.node || (payload.event === 'init' ? 'System' : null);
    if (!processedEvent.nodeName) return; // Skip unknown nodes without name

    // Normalize Content for Feed override
    processedEvent.displayContent = processedEvent.content || processedEvent.section_content || processedEvent.message;

    if (payload.event === 'complete') {
        status.value = 'complete';
    } else if (payload.event === 'error') {
        status.value = 'error';
    }
    
    // Update existing event or push new one
    const existingIndex = events.value.findIndex(e => e.nodeName === processedEvent.nodeName);
    if (existingIndex !== -1) {
        // Merge but preserve content if new one is empty
        const oldEvent = events.value[existingIndex];
        events.value[existingIndex] = { 
            ...oldEvent, 
            ...processedEvent,
            displayContent: processedEvent.displayContent || oldEvent.displayContent,
            // Also preserve report fields if not present in new
            rawEvent: processedEvent.rawEvent || oldEvent.rawEvent
        };
    } else {
        events.value.push(processedEvent);
    }
  });
};
</script>

<template>
  <div class="h-screen bg-white overflow-hidden flex font-sans selection:bg-emerald-100 selection:text-emerald-900">
    
    <!-- Column 1: Config & Branding (Fixed Width) -->
    <div class="w-[400px] flex flex-col border-r border-gray-200 bg-gray-50/50 shrink-0">
        <!-- Branding Header -->
        <div class="p-6 pb-4 border-b border-gray-100 flex items-center justify-between shrink-0">
             <div class="flex items-center gap-3">
                 <div class="w-8 h-8 bg-emerald-600 rounded-lg flex items-center justify-center text-white font-bold shadow-emerald-200 shadow-lg text-xs leading-none">TA+</div>
                 <div>
                    <h1 class="font-extrabold text-lg tracking-tight text-gray-900 leading-tight">TradingAgent Plus</h1>
                    <div class="text-[10px] font-medium text-gray-400 uppercase tracking-widest">v0.11.1</div>
                 </div>
             </div>
             
             <button @click="showSettings = true" class="p-1.5 text-gray-400 hover:text-gray-900 hover:bg-gray-200 rounded-md transition" title="API Settings">
                <Settings class="w-4 h-4" />
             </button>
        </div>

        <!-- Config Form Container -->
        <div class="flex-1 overflow-y-auto custom-scrollbar p-6 pt-4">
             <ConfigForm @start="handleStart" :is-running="status === 'running'" />
        </div>
    </div>

    <!-- Main Content Area (Flex) -->
    <div class="flex-1 flex min-w-0">
        
        <!-- Column 2: Live Feed (Proportional) -->
        <div class="w-[40%] flex flex-col border-r border-gray-200 h-full">
             <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between shrink-0 bg-white">
                <h3 class="text-sm font-bold text-gray-700 uppercase tracking-wider flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full" :class="status === 'running' ? 'bg-emerald-500 animate-pulse' : 'bg-gray-300'"></span>
                    Live Intelligence
                </h3>
                <span v-if="status === 'running'" class="text-[10px] text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-100">Streaming</span>
             </div>
             
             <div class="flex-1 overflow-hidden p-6 bg-gray-50/30">
                 <AnalysisFeed 
                    :events="events" 
                    :status="status" 
                    @select-report="handleReportSelection" 
                    :selected-node-id="selectedReport?.nodeName"
                 />
             </div>
        </div>

        <!-- Column 3: Report Viewer (Flex Fill) -->
        <div class="flex-1 flex flex-col h-full min-w-0 bg-white">
             <div class="px-6 py-4 border-b border-gray-100 shrink-0">
                <h3 class="text-sm font-bold text-gray-700 uppercase tracking-wider">Report Viewer</h3>
             </div>
             <div class="flex-1 overflow-hidden p-6">
                 <ReportViewer :report="selectedReport" />
             </div>
        </div>

    </div>

    <!-- Modals -->
    <SettingsModal :is-open="showSettings" @close="showSettings = false" />
  </div>
</template>

<style>
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: #e5e7eb;
  border-radius: 99px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background-color: #d1d5db;
}
</style>
