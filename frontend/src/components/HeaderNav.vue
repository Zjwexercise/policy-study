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
  Swords,
  RefreshCw,
  User,
  Cloud
} from 'lucide-vue-next';
import { auth } from '../auth';

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
  'open-mobile-qr',
  'open-sync',
  'open-login'
]);

const currentUser = computed(() => auth.currentUser.value);
const syncStatus = computed(() => auth.syncStatus.value);

const totalQuestionsAll = computed(() => {
  return props.workbooks.reduce((sum, w) => sum + (w.total_questions || 0), 0);
});

// 历年真题分类
const zhentiWorkbooks = computed(() => {
  return props.workbooks.filter(w => w.name && (w.name.includes('真题') || (w.id >= 27 && w.id <= 33)));
});

// 冲刺10套卷分类
const taojuanWorkbooks = computed(() => {
  return props.workbooks.filter(w => !w.name || (!w.name.includes('真题') && !(w.id >= 27 && w.id <= 33)));
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
  emit('select-workbook', val === 'all' || val === 'random' ? val : Number(val));
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
                🌟 全部题库大综合 ({{ totalQuestionsAll }}题)
              </option>
              <option value="random" class="font-bold text-indigo-600">
                🎲 跨题库·盲盒随机抽题 ({{ totalQuestionsAll }}题无序)
              </option>
              
              <!-- 历年真题专区 -->
              <optgroup v-if="zhentiWorkbooks.length > 0" label="── 🏛️ 2019-2024 全国历年真题 ──">
                <option v-for="wb in zhentiWorkbooks" :key="wb.id" :value="wb.id">
                  {{ wb.name }}
                </option>
              </optgroup>

              <!-- 冲刺10套卷专区 -->
              <optgroup v-if="taojuanWorkbooks.length > 0" label="── 📚 考研政治冲刺10套卷 ──">
                <option v-for="wb in taojuanWorkbooks" :key="wb.id" :value="wb.id">
                  {{ wb.name }}
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

        <!-- Right Tools: User, Mobile QR & Sync -->
        <div class="flex items-center space-x-1 sm:space-x-1.5 shrink-0">
          <!-- 用户账户与自动云同步状态 -->
          <button
            v-if="currentUser"
            @click="emit('open-login')"
            class="flex items-center space-x-1.5 px-2 sm:px-2.5 py-1.5 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 text-xs sm:text-sm font-semibold rounded-lg transition cursor-pointer shadow-2xs"
            :title="`当前账号：${currentUser.nickname || currentUser.username} (点击管理账号与云同步)`"
          >
            <div class="w-4 h-4 sm:w-5 sm:h-5 rounded-full bg-rose-600 text-white text-[10px] font-bold flex items-center justify-center">
              {{ (currentUser.nickname || currentUser.username || '用').slice(0, 1) }}
            </div>
            <span class="max-w-[70px] sm:max-w-[100px] truncate hidden sm:inline">{{ currentUser.nickname || currentUser.username }}</span>
            <span class="flex items-center gap-0.5 text-[10px] text-emerald-600 font-bold bg-white/80 px-1 py-0.5 rounded border border-emerald-200">
              <RefreshCw v-if="syncStatus === 'syncing'" class="w-2.5 h-2.5 animate-spin text-amber-600" />
              <Cloud v-else class="w-2.5 h-2.5 text-emerald-600" />
              <span class="hidden md:inline">{{ syncStatus === 'syncing' ? '同步中' : '已同步' }}</span>
            </span>
          </button>

          <!-- 未登录：登录/注册入口 -->
          <button
            v-else
            @click="emit('open-login')"
            class="flex items-center space-x-1 px-2 sm:px-2.5 py-1.5 bg-linear-to-r from-rose-500 to-red-500 hover:from-rose-600 hover:to-red-600 text-white text-xs sm:text-sm font-semibold rounded-lg transition cursor-pointer shadow-xs"
            title="登录账号开启自动双向云同步，跨端刷题免手动复制"
          >
            <User class="w-3.5 h-3.5 sm:w-4 sm:h-4" />
            <span>登录</span>
            <span class="hidden sm:inline">/注册</span>
          </button>

          <button
            @click="emit('open-sync')"
            class="hidden md:flex items-center space-x-1 px-2 sm:px-2.5 py-1.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 text-xs sm:text-sm font-semibold rounded-lg transition cursor-pointer shadow-2xs"
            title="跨端同步电脑与手机的做题记录"
          >
            <RefreshCw class="w-3.5 h-3.5 sm:w-4 sm:h-4 text-indigo-600" />
            <span class="hidden sm:inline">口令同步</span>
          </button>

          <button
            @click="emit('open-mobile-qr')"
            class="hidden md:flex items-center space-x-1 px-2 sm:px-2.5 py-1.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-200 text-xs sm:text-sm font-medium rounded-lg transition cursor-pointer"
            title="手机扫码直接在床上或自习室刷题"
          >
            <Smartphone class="w-3.5 h-3.5 sm:w-4 sm:h-4 text-emerald-600" />
            <span class="hidden sm:inline">手机扫码刷题</span>
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

      <!-- 手机底栏特别增加：我的 / 账号登录 -->
      <button
        @click="emit('open-login')"
        class="flex flex-col items-center justify-center py-1 px-1 rounded-lg transition flex-1 cursor-pointer min-w-0"
        :class="currentUser ? 'text-rose-600 font-semibold' : 'text-slate-500 hover:text-slate-800'"
      >
        <div class="relative">
          <User class="w-4 h-4 sm:w-5 sm:h-5 mb-0.5" />
          <span v-if="currentUser" class="absolute -top-0.5 -right-0.5 w-2 h-2 bg-emerald-500 rounded-full border border-white"></span>
        </div>
        <span class="text-[10px] sm:text-[11px] truncate tracking-tight">
          {{ currentUser ? (currentUser.nickname || currentUser.username) : '我的登录' }}
        </span>
      </button>
    </div>
  </header>
</template>
