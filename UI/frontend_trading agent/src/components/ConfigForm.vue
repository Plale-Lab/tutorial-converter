<script setup>
import { ref, onMounted, computed, watch } from 'vue';
import api from '../services/api';
import { Loader2, Calendar, Search, LineChart, Users, Newspaper, FileText, CheckSquare, Square } from 'lucide-vue-next';

defineProps({
    isRunning: Boolean
});

const emit = defineEmits(['start']);

const config = ref(null);
const loading = ref(true);

// Form State
const ticker = ref('');
const analysisDate = ref(new Date().toISOString().split('T')[0]);
const selectedAnalysts = ref([]);
const researchDepth = ref(1);
const selectedProvider = ref('openai'); // Default
const deepModel = ref('');
const shallowModel = ref('');

const isAllSelected = computed(() => {
    return config.value?.analysts?.length > 0 && selectedAnalysts.value.length === config.value.analysts.length;
});

const toggleAllAgents = () => {
    if (isAllSelected.value) {
        selectedAnalysts.value = [];
    } else {
        selectedAnalysts.value = [...(config.value?.analysts || [])];
    }
};

const getAgentIcon = (name) => {
    if (name.includes('Market')) return LineChart;
    if (name.includes('Social')) return Users;
    if (name.includes('News')) return Newspaper;
    if (name.includes('Fundamental')) return FileText;
    return Search; // Fallback
};

onMounted(async () => {
  try {
    config.value = await api.getConfig();
    selectedAnalysts.value = config.value.analysts;
    updateModels();
  } catch (e) {
    console.error('Failed to load config', e);
  } finally {
    loading.value = false;
  }
});

const updateModels = () => {
    const defaults = config.value?.default_models?.[selectedProvider.value] || config.value?.default_models?.['openai'];
    deepModel.value = defaults?.deep || '';
    shallowModel.value = defaults?.shallow || '';
};

watch(selectedProvider, updateModels);

const startAnalysis = () => {
  if (!ticker.value) return; // Simple validation
  emit('start', {
    ticker: ticker.value,
    analysis_date: analysisDate.value,
    analysts: selectedAnalysts.value,
    research_depth: researchDepth.value,
    llm_provider: selectedProvider.value,
    deep_thinker: deepModel.value,
    shallow_thinker: shallowModel.value,
  });
};
</script>

<template>
  <div class="space-y-6">
    
    <div v-if="loading" class="flex justify-center py-12">
      <Loader2 class="animate-spin text-emerald-500 w-8 h-8" />
    </div>

    <form v-else @submit.prevent="startAnalysis">
      
      <!-- Top Row: Ticker & Date -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div class="relative group">
           <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Target Asset</label>
           <div class="relative">
             <input v-model="ticker" type="text" placeholder="e.g. NVDA" 
               class="w-full text-lg font-mono font-medium p-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 focus:bg-white transition-all outline-none" required />
             <Search class="absolute right-3 top-3.5 w-5 h-5 text-gray-400 group-focus-within:text-emerald-500 transition-colors" />
           </div>
        </div>

        <div class="relative group">
           <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Analysis Date</label>
           <div class="relative">
             <input v-model="analysisDate" type="date" 
               class="w-full text-lg p-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 focus:bg-white transition-all outline-none font-sans text-gray-800" required />
           </div>
        </div>
      </div>

      <div class="border-t border-gray-100 mb-8"></div>

      <!-- Agents -->
      <div class="mb-8">
        <div class="flex items-center justify-between mb-4">
            <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider">Active Agents</label>
            <button type="button" @click="toggleAllAgents" class="text-xs font-medium text-emerald-600 hover:text-emerald-500 transition flex items-center gap-1">
                <CheckSquare v-if="isAllSelected" class="w-3 h-3" />
                <Square v-else class="w-3 h-3" />
                {{ isAllSelected ? 'Deselect All' : 'Select All' }}
            </button>
        </div>
        
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <label v-for="analyst in config.analysts" :key="analyst" 
             class="relative flex items-center p-3 rounded-lg border cursor-pointer transition-all duration-200 group select-none overflow-hidden"
             :class="selectedAnalysts.includes(analyst) ? 'bg-emerald-50/50 border-emerald-200 shadow-sm' : 'bg-white border-gray-100 hover:bg-gray-50 hover:border-gray-200'">
            
            <!-- Selection Indicator Bar -->
            <div class="absolute left-0 top-0 bottom-0 w-1 transition-colors duration-200"
                 :class="selectedAnalysts.includes(analyst) ? 'bg-emerald-500' : 'bg-transparent'"></div>

            <div class="flex items-center gap-3 pl-2 w-full">
                <!-- Custom Checkbox -->
                <div class="relative flex items-center justify-center w-5 h-5 transition-colors rounded border"
                     :class="selectedAnalysts.includes(analyst) ? 'bg-emerald-500 border-emerald-500' : 'bg-white border-gray-300 group-hover:border-gray-400'">
                    <CheckSquare v-if="selectedAnalysts.includes(analyst)" class="w-3.5 h-3.5 text-white" />
                    <input type="checkbox" :value="analyst" v-model="selectedAnalysts" class="absolute inset-0 opacity-0 cursor-pointer" />
                </div>

                <!-- Icon -->
                <component :is="getAgentIcon(analyst)" 
                    class="w-5 h-5 transition-colors"
                    :class="selectedAnalysts.includes(analyst) ? 'text-emerald-600' : 'text-gray-400 group-hover:text-gray-500'" />

                <!-- Label -->
                <span class="text-sm font-medium transition-colors" 
                      :class="selectedAnalysts.includes(analyst) ? 'text-gray-900' : 'text-gray-600 group-hover:text-gray-900'">
                    {{ analyst }}
                </span>
            </div>
          </label>
        </div>
      </div>

      <!-- Iterations -->
      <div class="mb-8 p-4 bg-gray-50/80 rounded-xl border border-gray-100">
        <div class="flex justify-between items-center mb-2">
            <label class="text-sm font-medium text-gray-700">Research Iterations</label>
            <div class="flex items-center gap-1.5 bg-white border border-gray-200 px-3 py-1 rounded-md shadow-sm">
                <span class="text-emerald-600 font-bold text-lg">{{ researchDepth }}</span>
                <span class="text-xs text-gray-400 uppercase tracking-wide">Rounds</span>
            </div>
        </div>
        <input v-model.number="researchDepth" type="range" min="1" max="5" 
            class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-emerald-500 hover:accent-emerald-400 transition" />
         <p class="text-[10px] text-gray-400 mt-2 text-center">* Higher depth increases accuracy but takes longer.</p>
      </div>

      <!-- Provider Selection & Model Override -->
      <div class="mb-8">
        <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Model Configuration</label>
        
        <div class="space-y-4">
            <!-- Provider Dropdown -->
            <div class="relative">
                <select v-model="selectedProvider" class="w-full p-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:bg-white outline-none appearance-none font-medium text-gray-700 cursor-pointer transition">
                    <option v-for="p in config.llm_providers" :key="p" :value="p">
                        {{ p.charAt(0).toUpperCase() + p.slice(1) }}
                    </option>
                </select>
                <div class="absolute right-3 top-3.5 pointer-events-none text-gray-400">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                </div>
            </div>

            <!-- Model Names -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                   <label class="block text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-1">Deep Reasoning Model</label>
                   <input v-model="deepModel" type="text" placeholder="e.g. gpt-4o" 
                     class="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:bg-white outline-none transition text-sm font-mono text-gray-600" />
                </div>
                <div>
                   <label class="block text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-1">Fast Reasoning Model</label>
                   <input v-model="shallowModel" type="text" placeholder="e.g. gpt-4o-mini" 
                     class="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:bg-white outline-none transition text-sm font-mono text-gray-600" />
                </div>
            </div>
            <p class="text-[10px] text-gray-400 text-center">Edit above to use custom models (e.g. 'gpt-oss:20b')</p>
        </div>
      </div>

      <!-- Button -->
      <button type="submit" :disabled="isRunning"
        class="w-full bg-emerald-600 hover:bg-emerald-500 text-white text-lg font-bold py-4 rounded-xl shadow-lg shadow-emerald-200 transform active:scale-[0.98] transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none flex items-center justify-center gap-2">
        <span v-if="!isRunning">Start Research Operation</span>
        <span v-else class="flex items-center gap-2">
            <Loader2 class="animate-spin w-5 h-5" /> Processing...
        </span>
      </button>

    </form>
  </div>
</template>
