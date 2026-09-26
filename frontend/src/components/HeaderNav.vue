<script setup>
import { computed } from 'vue';
import { 
  BookOpen, 
  AlertCircle, 
  FileText, 
  Library, 
  BarChart3, 
  Smartphone, 
  ChevronDown,
  Layers,
  Sparkles,
  Swords
} from 'lucide-vue-next';

const props = defineProps({
  currentTab: {
    type: String,
    required: true
  },
  workbooks: {
    type: Array,
    default: () => []
  },
  activeWorkbookId: {
    type: [Number, String],
    default: 'all'
  }
});

const emit = defineEmits([
  'update:currentTab', 
  'select-workbook', 
  'open-mobile-qr'
]);

const totalQuestionsAll = computed(() => {
  return props.workbooks.reduce((sum, w) => sum + (w.total_questions || 0), 0);
});

const tabs = [
  { id: 'practice', label: '刷题练习', icon: BookOpen },
  { id: 'wrong', label: '错题本', icon: AlertCircle },
  { id: 'killed', label: '斩题本', icon: Swords },
  { id: 'notes', label: '考点笔记', icon: FileText },
  { id: 'workbooks', label: '练习册中心', icon: Library },
  { id: 'stats', label: '学习统计', icon: BarChart3 },
];

const handleSelectChange = (val) => {
  emit('select-workbook', val === 'all' ? 'all' : Number(val));
};
</script>

<template>
  <header class="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-xs">
    <div class="max-w-7xl mx-auto px-3 sm:px-6">
      <div class="flex items-center justify-between h-14 sm:h-16 gap-2">
        <!-- Logo & Title -->
        <div class="flex items-center space-x-2 shrink-0">
          <div class="w-8 h-8 sm:w-9 sm:h-9 bg-linear-to-tr from-rose-600 to-red-500 rounded-xl flex items-center justify-center text-white shadow-sm font-bold text-base">
            政
          </div>
          <div>
            <div class="flex items-center gap-1.5">
              <span class="font-bold text-slate-800 text-sm sm:text-base leading-tight">考研政治刷题掌上宝</span>
              <span class="hidden md:inline-block px-1.5 py-0.5 text-[10px] font-semibold bg-red-50 text-red-600 rounded border border-red-200">
                2027备考
              </span>
            </div>
            <p class="hidden sm:block text-[11px] text-slate-500 leading-tight">单册独立刷 · 全库综合练</p>
          </div>
        </div>

        <!-- 练习册切换：支持【综合合并】与【独立单本】 -->
        <div class="flex items-center">
          <div class="relative flex items-center max-w-[170px] sm:max-w-[270px]">
            <select 
              :value="activeWorkbookId" 
              @change="handleSelectChange($event.target.value)"
              class="w-full appearance-none bg-slate-50 hover:bg-slate-100 text-slate-800 text-xs sm:text-sm font-medium py-1.5 pl-2.5 pr-7 rounded-lg border border-slate-200 focus:outline-hidden focus:ring-2 focus:ring-rose-500/20 truncate cursor-pointer transition shadow-2xs"
            >
              <!-- 综合模式选项 -->
              <option value="all" class="font-bold text-rose-600">
                🌟 全部练习册（全库综合跨本练 - {{ totalQuestionsAll }}题）
              </option>
              
              <!-- 独立分册练习选项 -->
              <optgroup label="── 分册单独练习 ──">
                <option v-for="wb in workbooks" :key="wb.id" :value="wb.id">
                  📖 {{ wb.name }} ({{ wb.total_questions }}题)
                </option>
              </optgroup>
            </select>
            <ChevronDown class="w-3.5 h-3.5 text-slate-400 absolute right-2 pointer-events-none" />
          </div>
        </div>

        <!-- Desktop Navigation Tabs -->
        <nav class="hidden lg:flex items-center space-x-1">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="emit('update:currentTab', tab.id)"
            class="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition cursor-pointer"
            :class="[
              currentTab === tab.id
                ? 'bg-rose-50 text-rose-700 font-semibold'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
            ]"
          >
            <component :is="tab.icon" class="w-4 h-4" />
            <span>{{ tab.label }}</span>
          </button>
        </nav>

        <!-- Right Tools: Mobile QR -->
        <div class="flex items-center space-x-1.5">
          <button
            @click="emit('open-mobile-qr')"
            class="flex items-center space-x-1 px-2.5 py-1.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-200 text-xs sm:text-sm font-medium rounded-lg transition cursor-pointer"
            title="手机扫码直接在床上或自习室刷题"
          >
            <Smartphone class="w-3.5 h-3.5 sm:w-4 sm:h-4 text-emerald-600" />
            <span class="hidden sm:inline">手机扫码刷题</span>
            <span class="sm:hidden">手机端</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Mobile Bottom Navigation Bar -->
    <div class="lg:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 z-40 px-1 py-1 flex justify-around items-center shadow-lg">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        @click="emit('update:currentTab', tab.id)"
        class="flex flex-col items-center justify-center py-1 px-1 rounded-lg transition text-slate-500 flex-1 cursor-pointer min-w-0"
        :class="[
          currentTab === tab.id ? 'text-rose-600 font-semibold' : 'hover:text-slate-800'
        ]"
      >
        <component :is="tab.icon" class="w-4 h-4 sm:w-5 sm:h-5 mb-0.5" />
        <span class="text-[10px] sm:text-[11px] truncate tracking-tight">{{ tab.label }}</span>
      </button>
    </div>
  </header>
</template>
