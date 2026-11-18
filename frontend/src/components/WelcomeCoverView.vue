<script setup>
import { computed } from 'vue';
import { 
  Play, 
  ArrowRight, 
  BookOpen, 
  Swords, 
  AlertCircle, 
  Moon, 
  Sun, 
  Sparkles, 
  FileText, 
  CheckCircle2, 
  Flame, 
  Smartphone, 
  BarChart3, 
  Compass, 
  Library,
  Layers,
  GraduationCap
} from 'lucide-vue-next';
import { isDark, toggleTheme } from '../theme';
import { auth } from '../auth';

const props = defineProps({
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
  'start-practice', 
  'select-workbook', 
  'switch-tab'
]);

const currentUser = computed(() => auth.currentUser.value);

// 计算当前练习册名称
const currentWorkbook = computed(() => {
  if (props.activeWorkbookId === 'all') {
    return { id: 'all', name: '全部题库大综合 (1524+题)' };
  }
  if (props.activeWorkbookId === 'random') {
    return { id: 'random', name: '跨题库·盲盒随机抽题' };
  }
  const idNum = Number(props.activeWorkbookId);
  return props.workbooks.find(w => w.id === idNum) || { id: idNum, name: '当前练习册' };
});

// 计算各分类数量
const totalCount = computed(() => {
  return props.workbooks.reduce((sum, w) => sum + (w.total_questions || 0), 0) || 1524;
});

const ti1000Count = computed(() => {
  const wb = props.workbooks.find(w => w.id === 39);
  return wb ? wb.total_questions : 996;
});

const zhentiCount = computed(() => {
  const wb = props.workbooks.find(w => w.id === 33);
  return wb ? wb.total_questions : 198;
});

const taojuanCount = computed(() => {
  const wb = props.workbooks.find(w => w.id === 19);
  return wb ? wb.total_questions : 330;
});

// 开始练习
const handleStart = (wbId = null) => {
  if (wbId !== null) {
    emit('select-workbook', wbId);
  }
  emit('start-practice');
};

const handleJumpTab = (tab) => {
  emit('switch-tab', tab);
};
</script>

<template>
  <div class="w-full max-w-6xl mx-auto px-4 sm:px-6 py-6 sm:py-10">
    <!-- 顶部封面 Hero 卡片 -->
    <div class="relative overflow-hidden rounded-3xl bg-linear-to-br from-rose-600 via-red-600 to-amber-600 text-white p-6 sm:p-10 shadow-xl mb-8">
      <!-- 装饰背景光斑 -->
      <div class="absolute -right-16 -top-16 w-72 h-72 bg-white/10 rounded-full blur-2xl pointer-events-none"></div>
      <div class="absolute -left-12 -bottom-12 w-64 h-64 bg-amber-400/20 rounded-full blur-2xl pointer-events-none"></div>

      <div class="relative z-10 max-w-3xl">
        <!-- 标签栏 -->
        <div class="flex flex-wrap items-center gap-2 mb-4">
          <span class="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-white/20 backdrop-blur-md text-xs font-semibold text-white tracking-wide border border-white/20 shadow-xs">
            <GraduationCap class="w-3.5 h-3.5" />
            2027 考研政治随身备考平台
          </span>
          <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-amber-400/30 backdrop-blur-md text-[11px] font-bold text-amber-100 border border-amber-300/30">
            <Flame class="w-3.5 h-3.5 text-amber-300" />
            精雕细刻 1000 题 + 历年真题 + 冲刺 10 套卷
          </span>
          <!-- 快捷夜间护眼切换 -->
          <button 
            @click="toggleTheme" 
            class="ml-auto inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-black/25 hover:bg-black/40 backdrop-blur-md text-xs font-medium text-white/90 border border-white/20 transition cursor-pointer shadow-xs"
            :title="isDark ? '切换至日间明亮模式' : '切换至夜间黑暗模式'"
          >
            <Moon v-if="!isDark" class="w-3.5 h-3.5 text-amber-300" />
            <Sun v-else class="w-3.5 h-3.5 text-amber-300" />
            <span>{{ isDark ? '日间模式' : '夜间护眼' }}</span>
          </button>
        </div>

        <!-- 主标题 -->
        <h1 class="text-2xl sm:text-4xl md:text-5xl font-black tracking-tight leading-tight sm:leading-tight mb-3">
          考研政治 · 随身极速刷题宝
        </h1>

        <!-- 副标题与名言 -->
        <p class="text-sm sm:text-base md:text-lg text-rose-100 font-medium mb-4 max-w-2xl leading-relaxed">
          全面整合《1000题》五大科目、2019-2024历年真题及冲刺模拟客观题。每一道细致推敲，助你冲刺政治客观题 40+ 高分！
        </p>

        <div class="p-3 sm:p-3.5 rounded-2xl bg-black/20 backdrop-blur-md border border-white/15 text-xs sm:text-sm text-white/90 italic mb-6 inline-block">
          💬 “志之所趋，无远弗届，穷山距海，不能限也。今日的每一次积累，都是考场上势如破竹的底气。”
        </div>

        <!-- 核心行动按钮 -->
        <div class="flex flex-wrap items-center gap-3 sm:gap-4">
          <!-- 立即开始刷题 -->
          <button
            @click="handleStart(null)"
            class="flex items-center gap-2 px-6 sm:px-8 py-3 sm:py-3.5 rounded-xl bg-white text-rose-600 hover:bg-rose-50 active:bg-rose-100 font-bold text-sm sm:text-base shadow-lg transition transform hover:-translate-y-0.5 cursor-pointer"
          >
            <Play class="w-4 h-4 sm:w-5 sm:h-5 fill-current" />
            <span>立即进入答题</span>
            <ArrowRight class="w-4 h-4 sm:w-5 sm:h-5" />
          </button>

          <!-- 继续上次练习 -->
          <button
            @click="handleStart(currentWorkbook.id)"
            class="flex items-center gap-2 px-4 sm:px-5 py-3 sm:py-3.5 rounded-xl bg-white/20 hover:bg-white/30 active:bg-white/40 backdrop-blur-md text-white font-semibold text-xs sm:text-sm border border-white/30 transition cursor-pointer"
            :title="`继续练习：${currentWorkbook.name}`"
          >
            <BookOpen class="w-4 h-4 text-amber-300 shrink-0" />
            <span class="max-w-[200px] truncate">继续：{{ currentWorkbook.name }}</span>
          </button>

          <!-- 错题快速重练 -->
          <button
            @click="handleJumpTab('wrong')"
            class="flex items-center gap-1.5 px-3.5 sm:px-4 py-3 sm:py-3.5 rounded-xl bg-black/20 hover:bg-black/35 text-white/90 text-xs sm:text-sm font-medium border border-white/20 transition cursor-pointer"
          >
            <AlertCircle class="w-4 h-4 text-rose-300" />
            <span>复习错题</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 三大核心题库专区卡片 (点击直达) -->
    <div class="mb-8">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-base sm:text-lg font-bold text-slate-800 flex items-center gap-2">
          <Compass class="w-5 h-5 text-rose-600" />
          <span>核心题库专区 · 一键开刷</span>
        </h2>
        <span class="text-xs text-slate-500 font-medium">涵盖全科目 · 题量充足 · 精准解析</span>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <!-- 专区 1：1000 题精选 -->
        <div 
          @click="handleStart(39)"
          class="group relative overflow-hidden rounded-2xl bg-white p-5 border border-slate-200 hover:border-rose-300 shadow-2xs hover:shadow-md transition cursor-pointer flex flex-col justify-between"
        >
          <div class="flex items-start justify-between mb-3">
            <div class="w-10 h-10 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center font-bold text-lg group-hover:scale-105 transition">
              🎯
            </div>
            <span class="px-2 py-0.5 rounded-md text-[11px] font-bold bg-rose-50 text-rose-600 border border-rose-100">
              共 {{ ti1000Count }} 题
            </span>
          </div>
          <div>
            <h3 class="font-bold text-slate-800 group-hover:text-rose-600 transition text-base mb-1">
              精雕细刻 1000 题
            </h3>
            <p class="text-xs text-slate-500 leading-relaxed mb-3">
              涵盖马原、毛中特、习思想、史纲、思修五大板块，官方考点逐题深度精讲。
            </p>
          </div>
          <div class="pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-semibold text-rose-600">
            <span>开始练习 1000 题</span>
            <ArrowRight class="w-3.5 h-3.5 group-hover:translate-x-1 transition" />
          </div>
        </div>

        <!-- 专区 2：历年真题专区 -->
        <div 
          @click="handleStart(33)"
          class="group relative overflow-hidden rounded-2xl bg-white p-5 border border-slate-200 hover:border-indigo-300 shadow-2xs hover:shadow-md transition cursor-pointer flex flex-col justify-between"
        >
          <div class="flex items-start justify-between mb-3">
            <div class="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold text-lg group-hover:scale-105 transition">
              🏛️
            </div>
            <span class="px-2 py-0.5 rounded-md text-[11px] font-bold bg-indigo-50 text-indigo-600 border border-indigo-100">
              共 {{ zhentiCount }} 题
            </span>
          </div>
          <div>
            <h3 class="font-bold text-slate-800 group-hover:text-indigo-600 transition text-base mb-1">
              2019-2024 历年真题
            </h3>
            <p class="text-xs text-slate-500 leading-relaxed mb-3">
              连续6年全国统考全真选择题，深度把握真题命题规律与考点命制套路。
            </p>
          </div>
          <div class="pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-semibold text-indigo-600">
            <span>刷历年全真真题</span>
            <ArrowRight class="w-3.5 h-3.5 group-hover:translate-x-1 transition" />
          </div>
        </div>

        <!-- 专区 3：冲刺 10 套卷 -->
        <div 
          @click="handleStart(19)"
          class="group relative overflow-hidden rounded-2xl bg-white p-5 border border-slate-200 hover:border-amber-300 shadow-2xs hover:shadow-md transition cursor-pointer flex flex-col justify-between"
        >
          <div class="flex items-start justify-between mb-3">
            <div class="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center font-bold text-lg group-hover:scale-105 transition">
              📝
            </div>
            <span class="px-2 py-0.5 rounded-md text-[11px] font-bold bg-amber-50 text-amber-600 border border-amber-100">
              共 {{ taojuanCount }} 题
            </span>
          </div>
          <div>
            <h3 class="font-bold text-slate-800 group-hover:text-amber-600 transition text-base mb-1">
              考研政治冲刺 10 套卷
            </h3>
            <p class="text-xs text-slate-500 leading-relaxed mb-3">
              10套全真模拟试卷客观题全收录，考前全真实战模考，强化解题手感。
            </p>
          </div>
          <div class="pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-semibold text-amber-600">
            <span>进入冲刺模考套卷</span>
            <ArrowRight class="w-3.5 h-3.5 group-hover:translate-x-1 transition" />
          </div>
        </div>
      </div>
    </div>

    <!-- 备考利器与特色功能 -->
    <div class="mb-8">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-base sm:text-lg font-bold text-slate-800 flex items-center gap-2">
          <Sparkles class="w-5 h-5 text-amber-500" />
          <span>高效刷题黑科技 · 科学提分</span>
        </h2>
      </div>

      <div class="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
        <!-- 功能 1: 斩题模式 -->
        <div 
          @click="handleJumpTab('killed')"
          class="bg-white p-4 rounded-2xl border border-slate-200 hover:border-slate-300 shadow-2xs transition cursor-pointer group"
        >
          <div class="w-8 h-8 rounded-lg bg-rose-50 text-rose-600 flex items-center justify-center mb-2.5">
            <Swords class="w-4 h-4" />
          </div>
          <h4 class="font-bold text-slate-800 text-sm mb-1 group-hover:text-rose-600 transition">
            一键斩题
          </h4>
          <p class="text-xs text-slate-500 leading-tight">
            熟题一键斩落移出题库，告别无意义重复，专心攻克薄弱盲区。
          </p>
        </div>

        <!-- 功能 2: 错题本 -->
        <div 
          @click="handleJumpTab('wrong')"
          class="bg-white p-4 rounded-2xl border border-slate-200 hover:border-slate-300 shadow-2xs transition cursor-pointer group"
        >
          <div class="w-8 h-8 rounded-lg bg-red-50 text-red-600 flex items-center justify-center mb-2.5">
            <AlertCircle class="w-4 h-4" />
          </div>
          <h4 class="font-bold text-slate-800 text-sm mb-1 group-hover:text-red-600 transition">
            智能错题本
          </h4>
          <p class="text-xs text-slate-500 leading-tight">
            自动汇集错题，支持【错题重练】与消错自测，针对性逐个击破。
          </p>
        </div>

        <!-- 功能 3: 学习统计 -->
        <div 
          @click="handleJumpTab('stats')"
          class="bg-white p-4 rounded-2xl border border-slate-200 hover:border-slate-300 shadow-2xs transition cursor-pointer group"
        >
          <div class="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center mb-2.5">
            <BarChart3 class="w-4 h-4" />
          </div>
          <h4 class="font-bold text-slate-800 text-sm mb-1 group-hover:text-indigo-600 transition">
            数据统计与专注
          </h4>
          <p class="text-xs text-slate-500 leading-tight">
            精准记录做题量、各科正确率分布，防挂机科学追踪学习专注时长。
          </p>
        </div>

        <!-- 功能 4: 手机多端同步 -->
        <div 
          @click="$emit('open-mobile-qr')"
          class="bg-white p-4 rounded-2xl border border-slate-200 hover:border-slate-300 shadow-2xs transition cursor-pointer group"
        >
          <div class="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center mb-2.5">
            <Smartphone class="w-4 h-4" />
          </div>
          <h4 class="font-bold text-slate-800 text-sm mb-1 group-hover:text-emerald-600 transition">
            手机扫码即刷
          </h4>
          <p class="text-xs text-slate-500 leading-tight">
            手机扫码即用，自习室、床上、通勤路上多端数据自动无缝双向云同步。
          </p>
        </div>
      </div>
    </div>

    <!-- 底部暖心寄语 -->
    <div class="text-center py-6 border-t border-slate-200 text-xs text-slate-400">
      <p class="mb-1 font-semibold text-slate-500">考研政治刷题掌上宝 · 助力 2027 考研学子一战成硕</p>
      <p>政治客观题目标 40+ · 每天坚持 20 分钟 · 积跬步以至千里</p>
    </div>
  </div>
</template>
