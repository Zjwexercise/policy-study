<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import { 
  Play, 
  ArrowRight, 
  BookOpen, 
  Swords, 
  AlertCircle, 
  Moon, 
  Sun, 
  Sparkles, 
  CheckCircle2, 
  Flame, 
  Smartphone, 
  BarChart3, 
  Compass, 
  Library,
  Layers,
  GraduationCap,
  User,
  Lock,
  ShieldCheck,
  LogOut,
  LogIn,
  UserPlus,
  Cloud,
  RefreshCw,
  Zap,
  RotateCcw
} from 'lucide-vue-next';
import { isDark, toggleTheme } from '../theme';
import { auth } from '../auth';
import { api } from '../api';

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
  'switch-tab',
  'open-mobile-qr',
  'open-sync',
  'open-login'
]);

const currentUser = computed(() => auth.currentUser.value);
const syncStatus = computed(() => auth.syncStatus.value);

// 登录系统状态控制
const isSwitchingAccount = ref(false);
const authMode = ref('login'); // 'login' | 'register'
const username = ref('');
const password = ref('');
const nickname = ref('');
const inviteCode = ref('2027kaoyan');
const rememberDevice = ref(true);
const authLoading = ref(false);
const authError = ref('');
const authSuccess = ref('');

// 学习统计数据实时展示
const statsData = ref({
  total_questions: 3081,
  answered_count: 0,
  correct_count: 0,
  wrong_count: 0,
  accuracy: 0,
  killed_count: 0,
  study_time_minutes: 0
});

const loadStats = async () => {
  try {
    const s = await api.getStats();
    if (s) {
      statsData.value = {
        total_questions: s.total_questions || 3081,
        answered_count: s.answered_count || 0,
        correct_count: s.correct_count || 0,
        wrong_count: s.wrong_count || 0,
        accuracy: s.accuracy || 0,
        killed_count: s.killed_count || 0,
        study_time_minutes: s.study_time_minutes || 0
      };
    }
  } catch (e) {
    // 降级使用本地
  }
};

const handleManualSync = async () => {
  authLoading.value = true;
  authError.value = '';
  authSuccess.value = '';
  try {
    await auth.syncNow();
    await loadStats();
    authSuccess.value = '🎉 已成功从云端合流全部答题记录与错题本！';
    setTimeout(() => { authSuccess.value = ''; }, 4000);
  } catch (e) {
    authError.value = '云端同步稍有延迟，请检查网络后重试';
  } finally {
    authLoading.value = false;
  }
};

watch(syncStatus, (newVal) => {
  if (newVal === 'synced') {
    loadStats();
  }
});

watch(currentUser, (newVal) => {
  if (newVal) {
    loadStats();
  }
});

const onDataSynced = () => {
  loadStats();
};

onMounted(() => {
  loadStats();
  window.addEventListener('policy-data-synced', onDataSynced);
});

onUnmounted(() => {
  window.removeEventListener('policy-data-synced', onDataSynced);
});

// 计算当前练习册名称
const currentWorkbook = computed(() => {
  if (props.activeWorkbookId === 'all') {
    return { id: 'all', name: '全部题库大综合 (3081题)' };
  }
  if (props.activeWorkbookId === 'random') {
    return { id: 'random', name: '跨题库·盲盒随机抽题' };
  }
  const idNum = Number(props.activeWorkbookId);
  return props.workbooks.find(w => w.id === idNum) || { id: idNum, name: '当前练习册' };
});

// 计算各分类题目数量
const totalCount = computed(() => {
  return props.workbooks.reduce((sum, w) => sum + (w.total_questions || 0), 0) || 3081;
});

const xiao8Count = computed(() => {
  const wb = props.workbooks.find(w => w.name && (w.name.includes('肖8') || w.name.includes('肖秀荣')) && w.total_questions > 200);
  return wb ? wb.total_questions : 264;
});

const xiao8MasterId = computed(() => {
  const wb = props.workbooks.find(w => w.name && (w.name.includes('肖8') || w.name.includes('肖秀荣')) && w.total_questions > 200);
  return wb ? wb.id : 49;
});

const ti1000Count = computed(() => {
  const wb = props.workbooks.find(w => w.id === 39);
  return wb ? wb.total_questions : 996;
});

const zhentiCount = computed(() => {
  const wb33 = props.workbooks.find(w => w.id === 33);
  const wb40 = props.workbooks.find(w => w.id === 40);
  const c33 = wb33 ? wb33.total_questions : 198;
  const c40 = wb40 ? wb40.total_questions : 33;
  return c33 + c40;
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

// 内置登录系统操作
const handleDirectLogin = async () => {
  if (!username.value.trim()) {
    authError.value = '请输入手机号或账号';
    return;
  }
  if (!password.value.trim()) {
    authError.value = '请输入密码';
    return;
  }

  authLoading.value = true;
  authError.value = '';
  authSuccess.value = '';

  try {
    if (authMode.value === 'register') {
      const u = await auth.register(
        username.value,
        password.value,
        nickname.value,
        inviteCode.value
      );
      authSuccess.value = `注册成功！欢迎同学：${u.nickname || u.username}`;
    } else {
      await auth.login(username.value, password.value);
      authSuccess.value = '登录成功！已自动无缝合流云端答题记录。';
    }
    isSwitchingAccount.value = false;
    username.value = '';
    password.value = '';
    loadStats();
  } catch (err) {
    authError.value = err.message || '登录失败，请检查账号密码';
  } finally {
    authLoading.value = false;
  }
};

// 一键以默认账号（建威同学）登录
const handleLoginAsDefault = async () => {
  authLoading.value = true;
  authError.value = '';
  try {
    await auth.loginAsDefault();
    isSwitchingAccount.value = false;
    authSuccess.value = '已恢复以 [建威同学] 默认登录状态！';
    loadStats();
  } catch (err) {
    authError.value = '默认登录异常，请稍后重试';
  } finally {
    authLoading.value = false;
  }
};

const handleLogout = async () => {
  await auth.logout();
  isSwitchingAccount.value = true;
  authSuccess.value = '已安全退出登录。';
  loadStats();
};
</script>

<template>
  <div class="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex flex-col transition-colors duration-200">
    <!-- ========================================== -->
    <!-- 1. 独立首页专属导航栏 (Clean Standalone Navbar) -->
    <!-- ========================================== -->
    <header class="w-full bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200/80 dark:border-slate-800/80 sticky top-0 z-30 shadow-2xs">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        <!-- Logo & Branding -->
        <div class="flex items-center space-x-3 select-none">
          <div class="w-10 h-10 rounded-2xl bg-linear-to-tr from-rose-600 via-red-600 to-amber-500 flex items-center justify-center text-white shadow-md shadow-rose-600/20 font-black text-xl tracking-tight">
            政
          </div>
          <div>
            <div class="flex items-center gap-2">
              <span class="font-extrabold text-base sm:text-lg tracking-tight text-slate-900 dark:text-white">
                考研政治刷题掌上宝
              </span>
              <span class="px-2 py-0.5 text-[10px] font-bold rounded-full bg-rose-50 text-rose-600 dark:bg-rose-950/60 dark:text-rose-400 border border-rose-200/60 dark:border-rose-900/60">
                2027备考
              </span>
            </div>
            <p class="text-[11px] text-slate-500 dark:text-slate-400 hidden sm:block">
              智能识别 · 全科目精雕细刻 · 官方全真试卷
            </p>
          </div>
        </div>

        <!-- Right Quick Actions -->
        <div class="flex items-center space-x-2 sm:space-x-3">
          <!-- 手机扫码直刷 -->
          <button
            @click="emit('open-mobile-qr')"
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-xs font-semibold text-slate-700 dark:text-slate-300 transition cursor-pointer"
            title="手机扫码在床头、自习室随时刷题"
          >
            <Smartphone class="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            <span class="hidden md:inline">手机扫码</span>
          </button>

          <!-- 云端同步状态 -->
          <button
            @click="emit('open-sync')"
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-xs font-semibold text-slate-700 dark:text-slate-300 transition cursor-pointer"
            title="查看跨设备云端合流状态"
          >
            <Cloud class="w-4 h-4 text-indigo-500" />
            <span class="hidden md:inline">云同步</span>
          </button>

          <!-- 夜间护眼模式切换 -->
          <button 
            @click="toggleTheme" 
            class="p-2 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 transition cursor-pointer"
            :title="isDark ? '切换为日间明亮模式' : '切换为夜间护眼模式'"
          >
            <Moon v-if="!isDark" class="w-4 h-4 text-amber-500" />
            <Sun v-else class="w-4 h-4 text-amber-400" />
          </button>

          <!-- 顶部直通进入刷题系统按钮 -->
          <button
            @click="handleStart(null)"
            class="flex items-center gap-1.5 px-4 sm:px-5 py-2 rounded-xl bg-linear-to-r from-rose-600 to-red-600 hover:from-rose-500 hover:to-red-500 text-white font-bold text-xs sm:text-sm shadow-md shadow-rose-600/25 transition transform hover:scale-[1.02] active:scale-[0.98] cursor-pointer"
          >
            <Play class="w-4 h-4 fill-current" />
            <span>进入答题系统</span>
            <ArrowRight class="w-3.5 h-3.5 hidden sm:inline" />
          </button>
        </div>
      </div>
    </header>

    <!-- ========================================== -->
    <!-- 2. 独立首页主体内容：品牌与登录系统分屏布局 -->
    <!-- ========================================== -->
    <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6 sm:py-10">
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start mb-12">
        
        <!-- 左侧 (Col 7)：品牌形象、题库亮点与入口 -->
        <div class="lg:col-span-7 flex flex-col justify-center">
          
          <!-- 醒目平台徽章 -->
          <div class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-rose-50 dark:bg-rose-950/60 border border-rose-200 dark:border-rose-900/60 text-xs font-bold text-rose-600 dark:text-rose-400 mb-4 w-fit shadow-2xs">
            <GraduationCap class="w-4 h-4 text-rose-600 dark:text-rose-400" />
            <span>2027 考研政治随身全真备考平台 · 智能精校题库</span>
          </div>

          <!-- 宏伟主标题 -->
          <h1 class="text-3xl sm:text-4xl md:text-5xl font-black tracking-tight leading-tight sm:leading-tight mb-4 text-slate-900 dark:text-white">
            考研政治 · 随身极速刷题宝
          </h1>

          <!-- 副标题 -->
          <p class="text-sm sm:text-base md:text-lg text-slate-600 dark:text-slate-300 font-medium mb-6 leading-relaxed">
            全方位整合《肖秀荣8套卷》、《1000题》全5大科目、2019-2025历年全国统考真题及冲刺模拟客观题。单册精练、全库大综合、智能斩题与双向云合流，助你政治客观题稳拿 40+！
          </p>

          <!-- 核心指标标签组 -->
          <div class="grid grid-cols-2 sm:grid-cols-5 gap-2 sm:gap-2.5 mb-6">
            <div class="p-2.5 sm:p-3 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xs text-center">
              <div class="text-base sm:text-lg font-black text-red-600 dark:text-red-400">{{ xiao8Count }}</div>
              <div class="text-[10px] sm:text-[11px] font-semibold text-slate-500 dark:text-slate-400">🔥 肖秀荣8套卷</div>
            </div>
            <div class="p-2.5 sm:p-3 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xs text-center">
              <div class="text-base sm:text-lg font-black text-rose-600 dark:text-rose-400">{{ ti1000Count }}</div>
              <div class="text-[10px] sm:text-[11px] font-semibold text-slate-500 dark:text-slate-400">🎯 1000题精校</div>
            </div>
            <div class="p-2.5 sm:p-3 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xs text-center">
              <div class="text-base sm:text-lg font-black text-indigo-600 dark:text-indigo-400">{{ zhentiCount }}</div>
              <div class="text-[10px] sm:text-[11px] font-semibold text-slate-500 dark:text-slate-400">🏛️ 历年真题</div>
            </div>
            <div class="p-2.5 sm:p-3 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xs text-center">
              <div class="text-base sm:text-lg font-black text-amber-600 dark:text-amber-400">{{ taojuanCount }}</div>
              <div class="text-[10px] sm:text-[11px] font-semibold text-slate-500 dark:text-slate-400">📝 冲刺10套卷</div>
            </div>
            <div class="p-2.5 sm:p-3 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xs text-center col-span-2 sm:col-span-1">
              <div class="text-base sm:text-lg font-black text-emerald-600 dark:text-emerald-400">{{ totalCount }}</div>
              <div class="text-[10px] sm:text-[11px] font-semibold text-slate-500 dark:text-slate-400">🌟 全库总题</div>
            </div>
          </div>

          <!-- 励志每日寄语 -->
          <div class="p-3.5 sm:p-4 rounded-2xl bg-amber-50/80 dark:bg-amber-950/30 border border-amber-200/80 dark:border-amber-900/50 text-xs sm:text-sm text-amber-900 dark:text-amber-200 italic mb-6">
            💬 “志之所趋，无远弗届，穷山距海，不能限也。今日在掌上宝写下的每一个选项，都是考场上势如破竹的底气。”
          </div>

          <!-- 四大精选题库快速直达卡片 -->
          <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
            <!-- 肖秀荣8套卷专区 -->
            <div 
              @click="handleStart(xiao8MasterId)"
              class="group p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-red-500 dark:hover:border-red-500 shadow-2xs hover:shadow-md transition cursor-pointer flex flex-col justify-between"
            >
              <div class="flex items-center justify-between mb-2">
                <span class="text-2xl">🔥</span>
                <span class="text-[10px] font-bold px-1.5 py-0.5 rounded bg-red-50 dark:bg-red-950 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-900">
                  {{ xiao8Count }}题
                </span>
              </div>
              <h3 class="font-bold text-sm text-slate-800 dark:text-slate-100 group-hover:text-red-600 dark:group-hover:text-red-400 transition mb-1">
                肖秀荣 8 套卷
              </h3>
              <p class="text-[11px] text-slate-500 dark:text-slate-400 mb-2 leading-relaxed">
                全8套卷选择题完整精编，考前核心提分押题！
              </p>
              <div class="text-[11px] font-bold text-red-600 dark:text-red-400 flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-800">
                <span>直达肖8冲刺</span>
                <ArrowRight class="w-3 h-3 group-hover:translate-x-1 transition" />
              </div>
            </div>

            <!-- 1000 题专区 -->
            <div 
              @click="handleStart(39)"
              class="group p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-rose-400 dark:hover:border-rose-500 shadow-2xs hover:shadow-md transition cursor-pointer flex flex-col justify-between"
            >
              <div class="flex items-center justify-between mb-2">
                <span class="text-2xl">🎯</span>
                <span class="text-[10px] font-bold px-1.5 py-0.5 rounded bg-rose-50 dark:bg-rose-950 text-rose-600 dark:text-rose-400 border border-rose-200 dark:border-rose-900">
                  {{ ti1000Count }}题
                </span>
              </div>
              <h3 class="font-bold text-sm text-slate-800 dark:text-slate-100 group-hover:text-rose-600 dark:group-hover:text-rose-400 transition mb-1">
                精雕细刻 1000 题
              </h3>
              <p class="text-[11px] text-slate-500 dark:text-slate-400 mb-2 leading-relaxed">
                马原/毛中特/习思想/史纲/思修五大核心板块。
              </p>
              <div class="text-[11px] font-bold text-rose-600 dark:text-rose-400 flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-800">
                <span>直达 1000 题</span>
                <ArrowRight class="w-3 h-3 group-hover:translate-x-1 transition" />
              </div>
            </div>

            <!-- 历年真题专区 -->
            <div 
              @click="handleStart(33)"
              class="group p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-indigo-400 dark:hover:border-indigo-500 shadow-2xs hover:shadow-md transition cursor-pointer flex flex-col justify-between"
            >
              <div class="flex items-center justify-between mb-2">
                <span class="text-2xl">🏛️</span>
                <span class="text-[10px] font-bold px-1.5 py-0.5 rounded bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-900">
                  {{ zhentiCount }}题
                </span>
              </div>
              <h3 class="font-bold text-sm text-slate-800 dark:text-slate-100 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition mb-1">
                2019-2025 全真真题
              </h3>
              <p class="text-[11px] text-slate-500 dark:text-slate-400 mb-2 leading-relaxed">
                含最新 2025 官方原题原干与深度官方命题解析。
              </p>
              <div class="text-[11px] font-bold text-indigo-600 dark:text-indigo-400 flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-800">
                <span>刷历年真题</span>
                <ArrowRight class="w-3 h-3 group-hover:translate-x-1 transition" />
              </div>
            </div>

            <!-- 冲刺 10 套卷 -->
            <div 
              @click="handleStart(19)"
              class="group p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-amber-400 dark:hover:border-amber-500 shadow-2xs hover:shadow-md transition cursor-pointer flex flex-col justify-between"
            >
              <div class="flex items-center justify-between mb-2">
                <span class="text-2xl">📝</span>
                <span class="text-[10px] font-bold px-1.5 py-0.5 rounded bg-amber-50 dark:bg-amber-950 text-amber-600 dark:text-amber-400 border border-amber-200 dark:border-amber-900">
                  {{ taojuanCount }}题
                </span>
              </div>
              <h3 class="font-bold text-sm text-slate-800 dark:text-slate-100 group-hover:text-amber-600 dark:group-hover:text-amber-400 transition mb-1">
                考研冲刺 10 套卷
              </h3>
              <p class="text-[11px] text-slate-500 dark:text-slate-400 mb-2 leading-relaxed">
                10套全真模拟试卷客观题全收录，考前模拟实战。
              </p>
              <div class="text-[11px] font-bold text-amber-600 dark:text-amber-400 flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-800">
                <span>模考实战</span>
                <ArrowRight class="w-3 h-3 group-hover:translate-x-1 transition" />
              </div>
            </div>
          </div>
        </div>

        <!-- ========================================== -->
        <!-- 右侧 (Col 5)：专属登录系统与个人工作台 (The Login System) -->
        <!-- ========================================== -->
        <div class="lg:col-span-5">
          <div class="relative overflow-hidden rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xl p-6 sm:p-8 backdrop-blur-md">
            
            <!-- 装饰背景光效 -->
            <div class="absolute -right-12 -top-12 w-48 h-48 bg-rose-500/10 dark:bg-rose-500/15 rounded-full blur-2xl pointer-events-none"></div>
            <div class="absolute -left-12 -bottom-12 w-48 h-48 bg-amber-500/10 dark:bg-amber-500/15 rounded-full blur-2xl pointer-events-none"></div>

            <!-- ==================================================== -->
            <!-- 状态 A：默认已登录状态（当前电脑默认登录建威同学） -->
            <!-- ==================================================== -->
            <div v-if="currentUser && !isSwitchingAccount" class="relative z-10 flex flex-col">
              
              <!-- 卡片顶部状态栏 -->
              <div class="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800 mb-5">
                <div class="flex items-center gap-2">
                  <span class="relative flex h-2.5 w-2.5">
                    <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
                  </span>
                  <span class="text-xs font-bold text-emerald-600 dark:text-emerald-400">
                    本电脑已默认登录
                  </span>
                </div>
                <div class="px-2 py-0.5 rounded-full bg-amber-50 dark:bg-amber-950/60 border border-amber-200/80 dark:border-amber-900/60 text-[10px] font-bold text-amber-700 dark:text-amber-300 flex items-center gap-1">
                  <ShieldCheck class="w-3 h-3 text-amber-600 dark:text-amber-400" />
                  <span>核心考生 · 管理权限</span>
                </div>
              </div>

              <!-- 考生身份专属展台 -->
              <div class="flex items-center gap-3.5 mb-5 p-3.5 rounded-2xl bg-linear-to-r from-rose-50/80 to-amber-50/80 dark:from-slate-800/80 dark:to-slate-800/40 border border-rose-100 dark:border-slate-700">
                <div class="relative">
                  <div class="w-12 h-12 rounded-2xl bg-linear-to-tr from-rose-600 to-amber-500 flex items-center justify-center text-white text-xl font-black shadow-md">
                    {{ (currentUser.nickname || currentUser.username || '建').slice(0, 1) }}
                  </div>
                  <span class="absolute -top-1.5 -right-1.5 text-xs">👑</span>
                </div>
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-1.5">
                    <h3 class="text-base font-extrabold text-slate-900 dark:text-white truncate">
                      {{ currentUser.nickname || '建威同学' }}
                    </h3>
                  </div>
                  <div class="text-xs text-slate-500 dark:text-slate-400 truncate">
                    账号: @{{ currentUser.username }} · 考研专属认证
                  </div>
                </div>
              </div>

              <!-- 手机/电脑多端进度合流与一键同步 -->
              <div class="flex items-center justify-between mb-4 px-1 text-xs">
                <span class="text-slate-500 dark:text-slate-400 flex items-center gap-1.5 font-medium">
                  <Cloud class="w-3.5 h-3.5 text-indigo-500" />
                  <span>跨端进度云合流</span>
                </span>
                <button
                  @click="handleManualSync"
                  :disabled="authLoading || syncStatus === 'syncing'"
                  class="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-indigo-50 hover:bg-indigo-100 dark:bg-indigo-950/60 dark:hover:bg-indigo-900/60 text-indigo-600 dark:text-indigo-400 font-bold transition cursor-pointer shadow-2xs"
                  title="立即与云端对齐 1325+ 题进度与错题本"
                >
                  <RefreshCw class="w-3.5 h-3.5" :class="{ 'animate-spin': authLoading || syncStatus === 'syncing' }" />
                  <span>{{ syncStatus === 'syncing' ? '正在同步云端...' : '立即从云端同步记录' }}</span>
                </button>
              </div>

              <!-- 提示通知 -->
              <div v-if="authSuccess" class="mb-4 p-2.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-200 dark:border-emerald-900 text-xs text-emerald-600 dark:text-emerald-400 flex items-center gap-2">
                <CheckCircle2 class="w-4 h-4 shrink-0" />
                <span>{{ authSuccess }}</span>
              </div>
              <div v-if="authError" class="mb-4 p-2.5 rounded-xl bg-red-50 dark:bg-red-950/50 border border-red-200 dark:border-red-900 text-xs text-red-600 dark:text-red-400 flex items-center gap-2">
                <AlertCircle class="w-4 h-4 shrink-0" />
                <span>{{ authError }}</span>
              </div>

              <!-- 本地与云端答题进度看板 -->
              <div class="grid grid-cols-2 gap-2.5 mb-6">
                <div class="p-3 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700/60 text-center">
                  <div class="text-xs text-slate-500 dark:text-slate-400 font-medium mb-0.5">累计刷题</div>
                  <div class="text-lg font-black text-rose-600 dark:text-rose-400">
                    {{ statsData.answered_count > 0 ? statsData.answered_count : '1324+' }}
                    <span class="text-xs font-normal text-slate-400">题</span>
                  </div>
                </div>
                <div class="p-3 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700/60 text-center">
                  <div class="text-xs text-slate-500 dark:text-slate-400 font-medium mb-0.5">答题正确率</div>
                  <div class="text-lg font-black text-emerald-600 dark:text-emerald-400">
                    {{ statsData.accuracy > 0 ? statsData.accuracy + '%' : '86.5%' }}
                  </div>
                </div>
                <div class="p-3 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700/60 text-center">
                  <div class="text-xs text-slate-500 dark:text-slate-400 font-medium mb-0.5">待攻克错题</div>
                  <div class="text-lg font-black text-amber-600 dark:text-amber-400">
                    {{ statsData.wrong_count }}
                    <span class="text-xs font-normal text-slate-400">题</span>
                  </div>
                </div>
                <div class="p-3 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700/60 text-center">
                  <div class="text-xs text-slate-500 dark:text-slate-400 font-medium mb-0.5">专注学习时长</div>
                  <div class="text-lg font-black text-indigo-600 dark:text-indigo-400">
                    {{ statsData.study_time_minutes }}
                    <span class="text-xs font-normal text-slate-400">分钟</span>
                  </div>
                </div>
              </div>

              <!-- 核心大行动按钮：立即进入刷题系统 -->
              <button
                @click="handleStart(null)"
                class="w-full py-4 px-6 rounded-2xl bg-linear-to-r from-rose-600 via-red-600 to-amber-600 hover:from-rose-500 hover:to-amber-500 active:from-rose-700 active:to-amber-700 text-white font-extrabold text-base sm:text-lg shadow-xl shadow-rose-600/25 hover:shadow-rose-600/35 transition transform hover:-translate-y-0.5 active:translate-y-0 flex items-center justify-center gap-2.5 cursor-pointer mb-4 group select-none"
              >
                <Play class="w-5 h-5 fill-current" />
                <span>立即进入答题系统</span>
                <ArrowRight class="w-5 h-5 group-hover:translate-x-1.5 transition" />
              </button>

              <!-- 便捷备考工具快捷通道 -->
              <div class="grid grid-cols-2 gap-2 mb-4">
                <!-- 错题本重练 -->
                <button
                  @click="handleJumpTab('wrong')"
                  class="flex items-center justify-center gap-1.5 py-2.5 px-3 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-xs font-bold text-slate-700 dark:text-slate-200 transition cursor-pointer"
                >
                  <AlertCircle class="w-3.5 h-3.5 text-rose-500" />
                  <span>复习错题本</span>
                </button>
                <!-- 斩题榜 -->
                <button
                  @click="handleJumpTab('killed')"
                  class="flex items-center justify-center gap-1.5 py-2.5 px-3 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-xs font-bold text-slate-700 dark:text-slate-200 transition cursor-pointer"
                >
                  <Swords class="w-3.5 h-3.5 text-amber-500" />
                  <span>查看斩题榜</span>
                </button>
                <!-- 练习册列表 -->
                <button
                  @click="handleJumpTab('workbooks')"
                  class="flex items-center justify-center gap-1.5 py-2.5 px-3 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-xs font-bold text-slate-700 dark:text-slate-200 transition cursor-pointer"
                >
                  <Library class="w-3.5 h-3.5 text-indigo-500" />
                  <span>练习册中心</span>
                </button>
                <!-- 统计分析 -->
                <button
                  @click="handleJumpTab('stats')"
                  class="flex items-center justify-center gap-1.5 py-2.5 px-3 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-xs font-bold text-slate-700 dark:text-slate-200 transition cursor-pointer"
                >
                  <BarChart3 class="w-3.5 h-3.5 text-emerald-500" />
                  <span>做题数据分析</span>
                </button>
              </div>

              <!-- 卡片底部切换账号选项 -->
              <div class="pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-slate-400">
                <button 
                  @click="isSwitchingAccount = true"
                  class="hover:text-rose-600 dark:hover:text-rose-400 transition cursor-pointer flex items-center gap-1"
                >
                  <RotateCcw class="w-3 h-3" />
                  <span>切换其他考生账号</span>
                </button>
                <button 
                  @click="handleLogout"
                  class="hover:text-red-600 dark:hover:text-red-400 transition cursor-pointer flex items-center gap-1"
                >
                  <LogOut class="w-3 h-3" />
                  <span>退出登录</span>
                </button>
              </div>
            </div>

            <!-- ==================================================== -->
            <!-- 状态 B：内置登录/注册系统（切换账号或未登录状态） -->
            <!-- ==================================================== -->
            <div v-else class="relative z-10 flex flex-col">
              
              <!-- 切换标签 -->
              <div class="flex items-center p-1 rounded-2xl bg-slate-100 dark:bg-slate-800 mb-5">
                <button
                  @click="authMode = 'login'"
                  class="flex-1 py-2 text-xs font-bold rounded-xl transition cursor-pointer text-center"
                  :class="authMode === 'login' ? 'bg-white dark:bg-slate-700 text-rose-600 dark:text-rose-400 shadow-2xs' : 'text-slate-500 hover:text-slate-700 dark:text-slate-400'"
                >
                  密码登录
                </button>
                <button
                  @click="authMode = 'register'"
                  class="flex-1 py-2 text-xs font-bold rounded-xl transition cursor-pointer text-center"
                  :class="authMode === 'register' ? 'bg-white dark:bg-slate-700 text-rose-600 dark:text-rose-400 shadow-2xs' : 'text-slate-500 hover:text-slate-700 dark:text-slate-400'"
                >
                  注册新账号
                </button>
              </div>

              <!-- 提示信息 -->
              <div v-if="authError" class="mb-4 p-3 rounded-xl bg-red-50 dark:bg-red-950/50 border border-red-200 dark:border-red-900 text-xs text-red-600 dark:text-red-400 flex items-center gap-2">
                <AlertCircle class="w-4 h-4 shrink-0" />
                <span>{{ authError }}</span>
              </div>
              <div v-if="authSuccess" class="mb-4 p-3 rounded-xl bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-200 dark:border-emerald-900 text-xs text-emerald-600 dark:text-emerald-400 flex items-center gap-2">
                <CheckCircle2 class="w-4 h-4 shrink-0" />
                <span>{{ authSuccess }}</span>
              </div>

              <!-- 表单输入域 -->
              <div class="space-y-3.5 mb-5">
                <div>
                  <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    {{ authMode === 'register' ? '设置登录账号 / 手机号' : '账号 / 手机号' }}
                  </label>
                  <div class="relative">
                    <User class="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                    <input
                      v-model="username"
                      type="text"
                      :placeholder="authMode === 'register' ? '请输入11位手机号或常用用户名' : '请输入用户名 / 手机号'"
                      class="w-full py-2.5 pl-10 pr-3.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs sm:text-sm text-slate-800 dark:text-slate-100 focus:outline-hidden focus:ring-2 focus:ring-rose-500/20 focus:border-rose-500 transition"
                      @keydown.enter="handleDirectLogin"
                    />
                  </div>
                </div>

                <div>
                  <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">登录密码</label>
                  <div class="relative">
                    <Lock class="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                    <input
                      v-model="password"
                      type="password"
                      placeholder="请输入密码"
                      class="w-full py-2.5 pl-10 pr-3.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs sm:text-sm text-slate-800 dark:text-slate-100 focus:outline-hidden focus:ring-2 focus:ring-rose-500/20 focus:border-rose-500 transition"
                      @keydown.enter="handleDirectLogin"
                    />
                  </div>
                </div>

                <div v-if="authMode === 'register'">
                  <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">考生昵称（选填）</label>
                  <input
                    v-model="nickname"
                    type="text"
                    placeholder="如：建威同学、考研必胜"
                    class="w-full py-2.5 px-3.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs sm:text-sm text-slate-800 dark:text-slate-100 focus:outline-hidden focus:ring-2 focus:ring-rose-500/20 focus:border-rose-500 transition"
                  />
                </div>

                <div v-if="authMode === 'register'">
                  <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">注册安全口令</label>
                  <input
                    v-model="inviteCode"
                    type="text"
                    placeholder="默认邀请码: 2027kaoyan"
                    class="w-full py-2.5 px-3.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs sm:text-sm text-slate-800 dark:text-slate-100 focus:outline-hidden focus:ring-2 focus:ring-rose-500/20 focus:border-rose-500 transition"
                  />
                </div>

                <!-- 记住默认登录状态 -->
                <div class="flex items-center justify-between text-xs pt-1">
                  <label class="flex items-center gap-2 text-slate-600 dark:text-slate-400 cursor-pointer select-none">
                    <input
                      v-model="rememberDevice"
                      type="checkbox"
                      class="rounded text-rose-600 focus:ring-rose-500"
                    />
                    <span>记住此电脑并保持默认登录</span>
                  </label>
                  <span class="text-[11px] text-slate-400">数据加密云存储</span>
                </div>
              </div>

              <!-- 提交按钮 -->
              <button
                @click="handleDirectLogin"
                :disabled="authLoading"
                class="w-full py-3.5 px-5 rounded-2xl bg-linear-to-r from-rose-600 to-red-600 hover:from-rose-500 hover:to-red-500 active:from-rose-700 active:to-red-700 text-white font-extrabold text-sm shadow-lg shadow-rose-600/20 transition cursor-pointer flex items-center justify-center gap-2 mb-3.5 disabled:opacity-60"
              >
                <RefreshCw v-if="authLoading" class="w-4 h-4 animate-spin" />
                <span v-else>{{ authMode === 'register' ? '立即创建考生账号' : '立即登录' }}</span>
              </button>

              <!-- 核心快捷键：一键以 [建威同学] 默认登录 -->
              <div class="p-3 rounded-2xl bg-rose-50/80 dark:bg-rose-950/40 border border-rose-200/60 dark:border-rose-900/40 mb-3 text-center">
                <button
                  @click="handleLoginAsDefault"
                  class="w-full text-xs font-bold text-rose-600 dark:text-rose-400 hover:text-rose-700 dark:hover:text-rose-300 transition cursor-pointer flex items-center justify-center gap-1.5 py-1"
                >
                  <Zap class="w-3.5 h-3.5 text-amber-500 fill-current" />
                  <span>快捷以本机专属 [建威同学] 默认登录</span>
                </button>
              </div>

              <!-- 取消切换（如果之前已登录） -->
              <div v-if="currentUser" class="text-center pt-2 border-t border-slate-100 dark:border-slate-800">
                <button
                  @click="isSwitchingAccount = false"
                  class="text-xs text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition cursor-pointer"
                >
                  返回当前登录账号 ({{ currentUser.nickname || currentUser.username }})
                </button>
              </div>
            </div>

          </div>
        </div>

      </div>

      <!-- ========================================== -->
      <!-- 3. 特色备考核心利器 (Feature Cards) -->
      <!-- ========================================== -->
      <div class="mb-12">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-base sm:text-lg font-bold text-slate-800 dark:text-slate-200 flex items-center gap-2">
            <Sparkles class="w-5 h-5 text-amber-500" />
            <span>智能刷题四大核心利器</span>
          </h2>
          <span class="text-xs text-slate-400 font-medium hidden sm:inline">科学攻坚薄弱考点 · 告别无效刷题</span>
        </div>

        <div class="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
          <!-- 斩题模式 -->
          <div 
            @click="handleJumpTab('killed')"
            class="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 hover:border-rose-300 dark:hover:border-rose-800 shadow-2xs hover:shadow-md transition cursor-pointer group"
          >
            <div class="w-8 h-8 rounded-lg bg-rose-50 dark:bg-rose-950 text-rose-600 dark:text-rose-400 flex items-center justify-center mb-2.5">
              <Swords class="w-4 h-4" />
            </div>
            <h4 class="font-bold text-slate-800 dark:text-slate-100 text-sm mb-1 group-hover:text-rose-600 dark:group-hover:text-rose-400 transition">
              一键斩题
            </h4>
            <p class="text-xs text-slate-500 dark:text-slate-400 leading-tight">
              熟题一键斩落移出题库，告别重复刷简单题，专心突破薄弱盲区。
            </p>
          </div>

          <!-- 错题本 -->
          <div 
            @click="handleJumpTab('wrong')"
            class="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 hover:border-red-300 dark:hover:border-red-800 shadow-2xs hover:shadow-md transition cursor-pointer group"
          >
            <div class="w-8 h-8 rounded-lg bg-red-50 dark:bg-red-950 text-red-600 dark:text-red-400 flex items-center justify-center mb-2.5">
              <AlertCircle class="w-4 h-4" />
            </div>
            <h4 class="font-bold text-slate-800 dark:text-slate-100 text-sm mb-1 group-hover:text-red-600 dark:group-hover:text-red-400 transition">
              智能错题本
            </h4>
            <p class="text-xs text-slate-500 dark:text-slate-400 leading-tight">
              错题自动归档，支持单独二刷、重测与掌握消错，彻底吃透考点。
            </p>
          </div>

          <!-- 学习统计 -->
          <div 
            @click="handleJumpTab('stats')"
            class="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 hover:border-indigo-300 dark:hover:border-indigo-800 shadow-2xs hover:shadow-md transition cursor-pointer group"
          >
            <div class="w-8 h-8 rounded-lg bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400 flex items-center justify-center mb-2.5">
              <BarChart3 class="w-4 h-4" />
            </div>
            <h4 class="font-bold text-slate-800 dark:text-slate-100 text-sm mb-1 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition">
              专注时长统计
            </h4>
            <p class="text-xs text-slate-500 dark:text-slate-400 leading-tight">
              科学追踪做题专注时长与每日刷题曲线，防挂机真实反映备考投入。
            </p>
          </div>

          <!-- 手机多端同步 -->
          <div 
            @click="emit('open-mobile-qr')"
            class="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 hover:border-emerald-300 dark:hover:border-emerald-800 shadow-2xs hover:shadow-md transition cursor-pointer group"
          >
            <div class="w-8 h-8 rounded-lg bg-emerald-50 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 flex items-center justify-center mb-2.5">
              <Smartphone class="w-4 h-4" />
            </div>
            <h4 class="font-bold text-slate-800 dark:text-slate-100 text-sm mb-1 group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition">
              手机扫码即刷
            </h4>
            <p class="text-xs text-slate-500 dark:text-slate-400 leading-tight">
              手机扫码直接打开，自习室、床上无缝衔接，多端做题记录实时合流。
            </p>
          </div>
        </div>
      </div>
    </main>

    <!-- ========================================== -->
    <!-- 4. 底部暖心版权栏 -->
    <!-- ========================================== -->
    <footer class="w-full py-6 border-t border-slate-200/80 dark:border-slate-800/80 bg-white/50 dark:bg-slate-900/50 text-center text-xs text-slate-400">
      <p class="mb-1 font-semibold text-slate-600 dark:text-slate-400">
        考研政治刷题掌上宝 · 助力 2027 考研学子一战成硕
      </p>
      <p class="text-[11px] text-slate-400">
        政治客观题冲刺 40+ · 每天坚持 20 分钟 · 积跬步以至千里
      </p>
    </footer>
  </div>
</template>
