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

// 仿 Apple iOS 26 底部液态玻璃导航：全端严格保留 4 个核心入口
const bottomTabs = computed(() => [
  { id: 'practice', label: t('nav_practice_short'), icon: BookOpen },
  { id: 'wrong', label: t('nav_wrong_short'), icon: AlertCircle },
  { id: 'workbooks', label: t('nav_workbooks_short'), icon: Library },
  { id: 'stats', label: t('nav_stats_short'), icon: BarChart3 }
]);

const isTabActive = (tabId) => {
  if (props.currentTab === tabId) return true;
  if (tabId === 'stats' && (props.currentTab === 'killed' || props.currentTab === 'notes')) {
    return true;
  }
  return false;
};

const activeTabIndex = computed(() => {
  const idx = bottomTabs.value.findIndex(tab => isTabActive(tab.id));
  return idx >= 0 ? idx : 0;
});

const hasActiveTab = computed(() => {
  return bottomTabs.value.some(tab => isTabActive(tab.id));
});
</script>

<template>
  <!-- 苹果磨砂玻璃顶栏 -->
  <header class="apple-liquid-header sticky top-0 z-30">
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

        <!-- 右侧极简玻璃胶囊工具区（仅 3 项） -->
        <div class="flex items-center gap-1.5 sm:gap-2 shrink-0">
          <!-- 🌐 语言切换：中文 / 泰语 -->
          <button
            @click="toggleLanguage"
            class="apple-glass-pill flex items-center gap-1 px-2.5 py-1.5 rounded-full text-xs font-semibold transition cursor-pointer active:scale-95"
            :class="[
              currentLang === 'th'
                ? 'text-indigo-700 dark:text-indigo-300'
                : 'text-slate-700 dark:text-slate-200'
            ]"
            :title="currentLang === 'th' ? 'สลับเป็นภาษาจีน (点击切换为中文)' : 'สลับเป็นภาษาไทย (点击切换为泰语)'"
          >
            <span class="text-xs leading-none">🌐</span>
            <span class="font-bold">{{ currentLang === 'th' ? 'ไทย' : '中' }}</span>
          </button>

          <!-- 🌙 夜间/日间纯图标切换 -->
          <button
            @click="toggleTheme"
            class="apple-glass-pill p-1.5 sm:p-2 rounded-full transition cursor-pointer active:scale-95"
            :class="isDark ? 'text-amber-300' : 'text-slate-600'"
            :title="isDark ? '切换为日间模式' : '开启夜间护眼模式'"
          >
            <Sun v-if="isDark" class="w-4 h-4 text-amber-400" />
            <Moon v-else class="w-4 h-4 text-slate-600" />
          </button>

          <!-- 👤 用户账号与云同步入口 -->
          <button
            v-if="currentUser"
            @click="emit('open-login')"
            class="apple-glass-pill flex items-center gap-1.5 px-2 sm:px-2.5 py-1.5 text-rose-700 text-xs font-semibold rounded-full transition cursor-pointer active:scale-95"
            :title="`当前账号：${currentUser.nickname || currentUser.username} (点击管理账号、云同步与后台)`"
          >
            <div class="w-4 h-4 sm:w-5 sm:h-5 rounded-full bg-linear-to-tr from-rose-600 to-red-500 text-white text-[10px] font-bold flex items-center justify-center shrink-0 shadow-2xs">
              {{ (currentUser.nickname || currentUser.username || '用').slice(0, 1) }}
            </div>
            <span class="max-w-[72px] sm:max-w-[100px] truncate hidden sm:inline">{{ currentUser.nickname || currentUser.username }}</span>
            <span class="flex items-center gap-0.5 text-[10px] text-emerald-600 font-bold bg-white/70 dark:bg-slate-800/70 px-1.5 py-0.5 rounded-full border border-emerald-200/70">
              <RefreshCw v-if="syncStatus === 'syncing'" class="w-2.5 h-2.5 animate-spin text-amber-600" />
              <Cloud v-else class="w-2.5 h-2.5 text-emerald-600" />
              <span class="hidden md:inline">{{ syncStatus === 'syncing' ? t('nav_syncing') : t('nav_synced') }}</span>
            </span>
          </button>

          <button
            v-else
            @click="emit('open-login')"
            class="flex items-center gap-1 px-3 py-1.5 bg-linear-to-r from-rose-500 to-red-500 hover:from-rose-600 hover:to-red-600 text-white text-xs font-semibold rounded-full transition cursor-pointer shadow-xs active:scale-95"
            title="登录账号开启云同步"
          >
            <User class="w-3.5 h-3.5" />
            <span>{{ t('nav_login') }}</span>
          </button>
        </div>
      </div>
    </div>
  </header>

  <!--  仿 iPhone Liquid Glass 底部悬浮液态玻璃胶囊导航（4 核心入口） -->
  <nav
    aria-label="主导航栏"
    class="apple-liquid-dock bottom-3 sm:bottom-5 left-1/2 -translate-x-1/2 w-[calc(100%-24px)] max-w-[400px] sm:max-w-[460px] z-40 p-1.5"
  >
    <div class="relative flex items-center w-full h-[52px] sm:h-[56px]">
      <!-- 流体滑动高亮液滴胶囊 -->
      <div
        v-if="hasActiveTab"
        class="apple-liquid-lens"
        :style="{
          width: `${100 / bottomTabs.length}%`,
          transform: `translateX(${activeTabIndex * 100}%)`
        }"
      />

      <button
        v-for="tab in bottomTabs"
        :key="tab.id"
        @click="emit('update:currentTab', tab.id)"
        class="relative z-10 flex-1 h-full flex flex-col items-center justify-center gap-0.5 px-1 rounded-full transition-all duration-200 cursor-pointer min-w-0 select-none active:scale-90"
        :class="[
          isTabActive(tab.id)
            ? 'text-rose-600 dark:text-rose-400 font-bold'
            : 'text-slate-600/90 hover:text-slate-900 dark:text-slate-300/80 dark:hover:text-white font-medium'
        ]"
      >
        <component
          :is="tab.icon"
          class="w-[18px] h-[18px] sm:w-[20px] sm:h-[20px] shrink-0 transition-transform duration-200"
          :class="isTabActive(tab.id) ? 'scale-105 stroke-[2.25]' : 'stroke-[1.75]'"
        />
        <span class="text-[10px] sm:text-[11px] leading-tight whitespace-nowrap truncate max-w-full tracking-tight">
          {{ tab.label }}
        </span>
      </button>
    </div>
  </nav>
</template>
