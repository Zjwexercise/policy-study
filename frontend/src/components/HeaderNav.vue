<script setup>
import { computed } from 'vue';
import {
  BookOpen,
  AlertCircle,
  Library,
  BarChart3,
  RefreshCw,
  User,
  Cloud,
  Moon,
  Sun
} from 'lucide-vue-next';
import { auth } from '../auth';
import { isDark, toggleTheme } from '../theme';
import { currentLang, setLanguage, t } from '../i18n';

const toggleLanguage = () => {
  setLanguage(currentLang.value === 'th' ? 'zh' : 'th');
};

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

// 仿 App 底部导航：全端严格保留 4 个核心入口
const bottomTabs = computed(() => [
  { id: 'practice', label: t('nav_practice_short'), icon: BookOpen },
  { id: 'wrong', label: t('nav_wrong_short'), icon: AlertCircle },
  { id: 'workbooks', label: t('nav_workbooks_short'), icon: Library },
  { id: 'stats', label: t('nav_stats_short'), icon: BarChart3 }
]);

const isTabActive = (tabId) => {
  if (props.currentTab === tabId) return true;
  // 斩题本 / 笔记本作为统计中心下的二级页面，保持底部「统计」高亮，点击即可返回
  if (tabId === 'stats' && (props.currentTab === 'killed' || props.currentTab === 'notes')) {
    return true;
  }
  return false;
};
</script>

<template>
  <!-- 极简顶部状态栏：仅保留品牌Logo（点击回首页）+ 语言/主题/账号 -->
  <header class="bg-white/95 dark:bg-slate-900/95 backdrop-blur-md border-b border-slate-200 sticky top-0 z-30 shadow-2xs">
    <div class="max-w-5xl mx-auto px-3 sm:px-6">
      <div class="flex items-center justify-between h-12 sm:h-14 gap-3">
        <!-- Logo & 品牌名称（点击返回欢迎封面） -->
        <div
          @click="emit('update:currentTab', 'welcome')"
          class="flex items-center gap-2 shrink-0 cursor-pointer group select-none"
          title="点击返回欢迎首页"
        >
          <div class="w-8 h-8 bg-linear-to-tr from-rose-600 to-red-500 rounded-xl flex items-center justify-center text-white shadow-xs font-bold text-sm group-hover:scale-105 transition">
            政
          </div>
          <span class="font-bold text-slate-800 text-sm sm:text-base leading-tight group-hover:text-rose-600 transition">
            {{ t('brand_name') }}
          </span>
        </div>

        <!-- 右侧极简工具区（仅 3 项） -->
        <div class="flex items-center gap-1.5 sm:gap-2 shrink-0">
          <!-- 🌐 语言切换：中文 / 泰语 -->
          <button
            @click="toggleLanguage"
            class="flex items-center gap-1 px-2 sm:px-2.5 py-1.5 rounded-lg border text-xs font-semibold transition cursor-pointer shadow-2xs"
            :class="[
              currentLang === 'th'
                ? 'bg-indigo-50 text-indigo-700 border-indigo-200 hover:bg-indigo-100'
                : 'bg-slate-50 hover:bg-slate-100 text-slate-700 border-slate-200'
            ]"
            :title="currentLang === 'th' ? 'สลับเป็นภาษาจีน (点击切换为中文)' : 'สลับเป็นภาษาไทย (点击切换为泰语)'"
          >
            <span class="text-xs leading-none">🌐</span>
            <span class="font-bold">{{ currentLang === 'th' ? 'ไทย' : '中' }}</span>
          </button>

          <!-- 🌙 夜间/日间纯图标切换 -->
          <button
            @click="toggleTheme"
            class="p-1.5 sm:p-2 rounded-lg border transition cursor-pointer shadow-2xs"
            :class="[
              isDark
                ? 'bg-amber-950/40 text-amber-300 border-amber-700/60 hover:bg-amber-900/50'
                : 'bg-slate-50 hover:bg-slate-100 text-slate-700 border-slate-200'
            ]"
            :title="isDark ? '切换为日间模式' : '开启夜间护眼模式'"
          >
            <Sun v-if="isDark" class="w-4 h-4 text-amber-400" />
            <Moon v-else class="w-4 h-4 text-slate-600" />
          </button>

          <!-- 👤 用户账号与云同步入口（管理后台也在弹窗内） -->
          <button
            v-if="currentUser"
            @click="emit('open-login')"
            class="flex items-center gap-1.5 px-2 sm:px-2.5 py-1.5 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 text-xs font-semibold rounded-lg transition cursor-pointer shadow-2xs"
            :title="`当前账号：${currentUser.nickname || currentUser.username} (点击管理账号、云同步与后台)`"
          >
            <div class="w-4 h-4 sm:w-5 sm:h-5 rounded-full bg-rose-600 text-white text-[10px] font-bold flex items-center justify-center shrink-0">
              {{ (currentUser.nickname || currentUser.username || '用').slice(0, 1) }}
            </div>
            <span class="max-w-[72px] sm:max-w-[100px] truncate hidden sm:inline">{{ currentUser.nickname || currentUser.username }}</span>
            <span class="flex items-center gap-0.5 text-[10px] text-emerald-600 font-bold bg-white/80 dark:bg-slate-800/80 px-1 py-0.5 rounded border border-emerald-200">
              <RefreshCw v-if="syncStatus === 'syncing'" class="w-2.5 h-2.5 animate-spin text-amber-600" />
              <Cloud v-else class="w-2.5 h-2.5 text-emerald-600" />
              <span class="hidden md:inline">{{ syncStatus === 'syncing' ? t('nav_syncing') : t('nav_synced') }}</span>
            </span>
          </button>

          <button
            v-else
            @click="emit('open-login')"
            class="flex items-center gap-1 px-2.5 py-1.5 bg-linear-to-r from-rose-500 to-red-500 hover:from-rose-600 hover:to-red-600 text-white text-xs font-semibold rounded-lg transition cursor-pointer shadow-xs"
            title="登录账号开启云同步"
          >
            <User class="w-3.5 h-3.5" />
            <span>{{ t('nav_login') }}</span>
          </button>
        </div>
      </div>
    </div>
  </header>

  <!-- 仿 App 底部 4 按钮导航栏（电脑端居中悬浮圆角胶囊 Dock · 手机端贴底全宽） -->
  <nav
    aria-label="主导航栏"
    class="fixed bottom-0 left-0 right-0 sm:bottom-4 sm:left-1/2 sm:-translate-x-1/2 sm:right-auto sm:w-[480px] md:w-[520px] sm:max-w-[calc(100vw-2rem)] bg-white/95 dark:bg-slate-900/95 backdrop-blur-md border-t sm:border border-slate-200 dark:border-slate-700/80 sm:rounded-2xl z-40 px-2 sm:px-2.5 py-1.5 flex items-center justify-around gap-1 shadow-[0_-4px_20px_-4px_rgba(15,23,42,0.08)] sm:shadow-xl sm:shadow-slate-900/12 dark:sm:shadow-black/50"
  >
    <button
      v-for="tab in bottomTabs"
      :key="tab.id"
      @click="emit('update:currentTab', tab.id)"
      class="flex-1 flex flex-col sm:flex-row items-center justify-center gap-0.5 sm:gap-1.5 py-1.5 sm:py-2 px-1.5 sm:px-3 rounded-xl transition cursor-pointer min-w-0 select-none"
      :class="[
        isTabActive(tab.id)
          ? 'bg-rose-50 text-rose-700 font-bold shadow-2xs'
          : 'text-slate-500 hover:text-slate-800 hover:bg-slate-50 font-medium'
      ]"
    >
      <component :is="tab.icon" class="w-4 h-4 sm:w-4 sm:h-4 shrink-0" />
      <span class="text-[11px] sm:text-xs whitespace-nowrap truncate">{{ tab.label }}</span>
    </button>
  </nav>
</template>
