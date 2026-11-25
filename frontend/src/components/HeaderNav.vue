<script setup>
import { ref, computed } from 'vue';
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

// ==========================================
//  iOS 26 Liquid Glass 手指/鼠标拖动跟随交互
// ==========================================
const dockTrackRef = ref(null);
const isPointerDown = ref(false);
const isDragging = ref(false);
const dragOffsetPx = ref(0);
const dragPreviewIndex = ref(-1);

let pointerStartX = 0;
let activePointerId = null;
let cachedRect = null;
let suppressNextClick = false;

const getSlotMetrics = (clientX) => {
  const rect = cachedRect || dockTrackRef.value?.getBoundingClientRect();
  if (!rect || rect.width <= 0) return null;
  const count = bottomTabs.value.length || 4;
  const slotWidth = rect.width / count;
  const relX = clientX - rect.left;
  const clampedRelX = Math.min(rect.width - 0.5, Math.max(0, relX));
  const targetIdx = Math.min(count - 1, Math.max(0, Math.floor(clampedRelX / slotWidth)));

  const rawLeft = relX - slotWidth / 2;
  const maxLeft = rect.width - slotWidth;
  let boundedLeft = rawLeft;
  // 边缘橡皮筋弹性阻尼
  if (rawLeft < 0) {
    boundedLeft = rawLeft * 0.22;
  } else if (rawLeft > maxLeft) {
    boundedLeft = maxLeft + (rawLeft - maxLeft) * 0.22;
  }
  return { targetIdx, boundedLeft };
};

const onDockPointerDown = (e) => {
  if (e.pointerType === 'mouse' && e.button !== 0) return;
  if (!dockTrackRef.value) return;

  cachedRect = dockTrackRef.value.getBoundingClientRect();
  activePointerId = e.pointerId;
  pointerStartX = e.clientX;
  isPointerDown.value = true;
  isDragging.value = false;

  const metrics = getSlotMetrics(e.clientX);
  if (metrics) {
    dragPreviewIndex.value = metrics.targetIdx;
    dragOffsetPx.value = metrics.boundedLeft;
  }

  try {
    dockTrackRef.value.setPointerCapture(e.pointerId);
  } catch (err) {}
};

const onDockPointerMove = (e) => {
  if (!isPointerDown.value || e.pointerId !== activePointerId) return;
  const dx = Math.abs(e.clientX - pointerStartX);
  if (!isDragging.value && dx >= 4) {
    isDragging.value = true;
  }
  if (!isDragging.value) return;

  const metrics = getSlotMetrics(e.clientX);
  if (!metrics) return;

  dragOffsetPx.value = metrics.boundedLeft;
  if (metrics.targetIdx !== dragPreviewIndex.value) {
    dragPreviewIndex.value = metrics.targetIdx;
    if (typeof navigator !== 'undefined' && typeof navigator.vibrate === 'function') {
      try {
        navigator.vibrate(8);
      } catch (err) {}
    }
  }
};

const finishDockPointer = (e, shouldCommit = true) => {
  if (!isPointerDown.value || e.pointerId !== activePointerId) return;

  if (shouldCommit) {
    const metrics = getSlotMetrics(e.clientX);
    const finalIdx = isDragging.value
      ? (dragPreviewIndex.value >= 0 ? dragPreviewIndex.value : (metrics?.targetIdx ?? 0))
      : (metrics?.targetIdx ?? dragPreviewIndex.value);

    const targetTab = bottomTabs.value[finalIdx];
    if (targetTab) {
      emit('update:currentTab', targetTab.id);
    }
    suppressNextClick = true;
    setTimeout(() => {
      suppressNextClick = false;
    }, 80);
  }

  try {
    if (dockTrackRef.value?.hasPointerCapture?.(e.pointerId)) {
      dockTrackRef.value.releasePointerCapture(e.pointerId);
    }
  } catch (err) {}

  isPointerDown.value = false;
  isDragging.value = false;
  dragPreviewIndex.value = -1;
  activePointerId = null;
  cachedRect = null;
};

const handleTabClick = (tabId) => {
  if (suppressNextClick) return;
  emit('update:currentTab', tabId);
};

const visualActiveIndex = computed(() => {
  if (isDragging.value && dragPreviewIndex.value >= 0) {
    return dragPreviewIndex.value;
  }
  return activeTabIndex.value;
});

const lensStyle = computed(() => {
  const count = bottomTabs.value.length || 4;
  const widthPct = `${100 / count}%`;
  if (isDragging.value) {
    return {
      width: widthPct,
      transform: `translate3d(${dragOffsetPx.value.toFixed(1)}px, 0, 0) scale(1.06, 1.07)`
    };
  }
  return {
    width: widthPct,
    transform: `translate3d(${activeTabIndex.value * 100}%, 0, 0) scale(1, 1)`
  };
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

  <!--  仿 iPhone Liquid Glass 底部悬浮液态玻璃胶囊导航（支持按住拖动跟随切换） -->
  <nav
    aria-label="主导航栏"
    class="apple-liquid-dock bottom-3 sm:bottom-5 left-1/2 -translate-x-1/2 w-[calc(100%-24px)] max-w-[400px] sm:max-w-[460px] z-40 p-1.5"
  >
    <div
      ref="dockTrackRef"
      @pointerdown="onDockPointerDown"
      @pointermove="onDockPointerMove"
      @pointerup="finishDockPointer($event, true)"
      @pointercancel="finishDockPointer($event, false)"
      class="apple-liquid-dock-track relative flex items-center w-full h-[52px] sm:h-[56px]"
    >
      <!-- 流体滑动 & 拖动跟随液滴胶囊 -->
      <div
        v-if="hasActiveTab || isDragging"
        class="apple-liquid-lens"
        :class="{ 'is-dragging': isDragging }"
        :style="lensStyle"
      />

      <button
        v-for="(tab, idx) in bottomTabs"
        :key="tab.id"
        @click="handleTabClick(tab.id)"
        class="relative z-10 flex-1 h-full flex flex-col items-center justify-center gap-0.5 px-1 rounded-full transition-all duration-150 cursor-pointer min-w-0 select-none"
        :class="[
          (hasActiveTab || isDragging) && visualActiveIndex === idx
            ? 'text-rose-600 dark:text-rose-400 font-bold'
            : 'text-slate-600/90 hover:text-slate-900 dark:text-slate-300/80 dark:hover:text-white font-medium',
          isDragging && visualActiveIndex === idx ? 'scale-105' : '',
          !isDragging ? 'active:scale-90' : ''
        ]"
      >
        <component
          :is="tab.icon"
          class="w-[18px] h-[18px] sm:w-[20px] sm:h-[20px] shrink-0 transition-transform duration-150"
          :class="(hasActiveTab || isDragging) && visualActiveIndex === idx ? 'scale-105 stroke-[2.25]' : 'stroke-[1.75]'"
        />
        <span class="text-[10px] sm:text-[11px] leading-tight whitespace-nowrap truncate max-w-full tracking-tight">
          {{ tab.label }}
        </span>
      </button>
    </div>
  </nav>
</template>
