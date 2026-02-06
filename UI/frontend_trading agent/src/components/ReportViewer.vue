<script setup>
import { computed } from 'vue';
import { FileText, Bot } from 'lucide-vue-next';
import MarkdownIt from 'markdown-it';

const md = new MarkdownIt({ html: true, linkify: true, typographer: true });

const props = defineProps({
  report: {
    type: Object, // { title, content, nodeName, timestamp }
    default: null
  }
});

const renderMarkdown = (text) => {
    if (!text) return '';
    return md.render(text);
};
</script>

<template>
  <div class="bg-white rounded-xl border border-gray-200 shadow-sm h-[calc(100vh-140px)] flex flex-col overflow-hidden">
    
    <!-- Header -->
    <div class="bg-gray-50 px-6 py-4 border-b border-gray-100 flex items-center justify-between shrink-0">
        <h3 class="text-sm font-bold text-gray-700 uppercase tracking-wider flex items-center gap-2">
            <FileText class="w-4 h-4 text-emerald-600" />
            Report Viewer
        </h3>
        <span v-if="report" class="text-xs text-gray-400 font-mono">
           {{ report.timestamp ? new Date(report.timestamp).toLocaleTimeString() : '' }}
        </span>
    </div>

    <!-- Content -->
    <div class="flex-1 overflow-y-auto custom-scrollbar p-8 bg-white relative">
        
        <!-- Empty State -->
        <div v-if="!report" class="absolute inset-0 flex flex-col items-center justify-center text-gray-300">
             <Bot class="w-12 h-12 mb-3 text-gray-200" />
             <p class="text-sm font-medium">Select a completed task to view details</p>
        </div>

        <!-- Report Content -->
        <div v-else class="animate-in fade-in zoom-in-95 duration-200">
            <div class="mb-6 pb-4 border-b border-gray-100">
                 <h2 class="text-2xl font-bold text-gray-900 mb-1">{{ report.title.replace(/_/g, ' ') }}</h2>
                 <p class="text-sm text-emerald-600 font-medium">@{{ report.nodeName }}</p>
            </div>
            
            <div class="prose prose-emerald max-w-none text-gray-700 leading-relaxed" v-html="renderMarkdown(report.content)"></div>
        </div>

    </div>
  </div>
</template>

<style scoped>
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
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background-color: #d1d5db;
}
</style>
