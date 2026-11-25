<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue';
import { api } from './api';
import HeaderNav from './components/HeaderNav.vue';
import WelcomeCoverView from './components/WelcomeCoverView.vue';
import PracticeView from './components/PracticeView.vue';
import WrongBookView from './components/WrongBookView.vue';
import KilledQuestionsView from './components/KilledQuestionsView.vue';
import NotesView from './components/NotesView.vue';
import WorkbooksView from './components/WorkbooksView.vue';
import StatsView from './components/StatsView.vue';
import MobileQrModal from './components/MobileQrModal.vue';
import SyncModal from './components/SyncModal.vue';
import LoginModal from './components/LoginModal.vue';
import AdminView from './components/AdminView.vue';
import { auth } from './auth';

// 有效的标签页列表
const VALID_TABS = ['welcome', 'practice', 'wrong', 'killed', 'notes', 'workbooks', 'stats', 'admin'];

// 初始页面：多级持久化恢复（URL hash -> localStorage -> sessionStorage -> 默认 welcome）
// 彻底解决刷新、手机息屏、锁屏或后台切回时自动跳回首页欢迎界面的问题
const getInitialTab = () => {
  try {
    const hash = window.location.hash.replace(/^#\/?/, '').trim();
    if (hash && VALID_TABS.includes(hash)) {
      return hash;
    }
    const localSaved = localStorage.getItem('policy_current_tab');
    if (localSaved && VALID_TABS.includes(localSaved)) {
      return localSaved;
    }
    const sessionSaved = sessionStorage.getItem('policy_current_tab');
    if (sessionSaved && VALID_TABS.includes(sessionSaved)) {
      return sessionSaved;
    }
  } catch (e) {}
  return 'welcome';
};

const currentTab = ref(getInitialTab());

watch(currentTab, (val) => {
  if (val && VALID_TABS.includes(val)) {
    try {
      localStorage.setItem('policy_current_tab', val);
      sessionStorage.setItem('policy_current_tab', val);
      if (window.location.hash.replace(/^#\/?/, '') !== val) {
        window.location.hash = val;
      }
    } catch (e) {}
  }
}, { immediate: true });

// 监听浏览器前进/后退/URL Hash 变更
const handleHashChange = () => {
  try {
    const hash = window.location.hash.replace(/^#\/?/, '').trim();
    if (hash && VALID_TABS.includes(hash) && currentTab.value !== hash) {
      currentTab.value = hash;
    }
  } catch (e) {}
};

const workbooks = ref([]);
const activeWorkbookId = ref(localStorage.getItem('policy_active_wb_id') || 'all'); // 记忆用户最后打开的练习册
const showMobileQr = ref(false);
const showSyncModal = ref(false);
const showLoginModal = ref(false);
const practiceInitialStatus = ref('all');
const practiceInitialRedo = ref(false);

const handleLoginSuccess = () => {
  loadWorkbooks();
};

const loadWorkbooks = async () => {
  try {
    const list = await api.getWorkbooks();
    workbooks.value = list;
    if (!activeWorkbookId.value) {
      activeWorkbookId.value = localStorage.getItem('policy_active_wb_id') || 'all';
    }
  } catch (err) {
    console.error('加载练习册列表失败', err);
  }
};

const selectWorkbook = (id) => {
  activeWorkbookId.value = id;
  localStorage.setItem('policy_active_wb_id', String(id));
};

const startPractice = (options = {}) => {
  if (options && options.status) {
    practiceInitialStatus.value = options.status;
    practiceInitialRedo.value = !!options.redo;
  } else {
    practiceInitialStatus.value = 'all';
    practiceInitialRedo.value = false;
  }
  if (options && options.workbookId) {
    selectWorkbook(options.workbookId);
  }
  currentTab.value = 'practice';
};

// ==========================================
// 实时学习专注时长追踪逻辑 (防息屏、防挂机)
// ==========================================
let accumulatedSeconds = 0;
let lastActiveTime = Date.now();
let timerInterval = null;

const recordActivity = () => {
  lastActiveTime = Date.now();
};

const flushStudyTime = async () => {
  if (accumulatedSeconds >= 5) {
    const toReport = accumulatedSeconds;
    accumulatedSeconds = 0;
    try {
      await api.reportStudyTime(toReport);
    } catch (e) {
      accumulatedSeconds += toReport;
    }
  }
};

onMounted(() => {
  loadWorkbooks();
  window.addEventListener('hashchange', handleHashChange);
  auth.initAuth().then(() => {
    loadWorkbooks();
  });

  // 监听用户活跃交互
  ['mousemove', 'keydown', 'touchstart', 'scroll', 'click'].forEach(evt => {
    window.addEventListener(evt, recordActivity, { passive: true });
  });

  // 每秒检测活跃状态并计时
  timerInterval = setInterval(() => {
    const isVisible = document.visibilityState === 'visible';
    const isRecentlyActive = (Date.now() - lastActiveTime) < 90 * 1000; // 90秒内有操作视为活跃
    if (isVisible && isRecentlyActive) {
      accumulatedSeconds++;
    }
    // 每 25 秒自动向后端/本地归档一次
    if (accumulatedSeconds >= 25) {
      flushStudyTime();
    }
  }, 1000);

  // 页面切出或关闭时自动提交当前累计
  window.addEventListener('beforeunload', flushStudyTime);
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') {
      flushStudyTime();
    } else {
      recordActivity();
    }
  });
});

onUnmounted(() => {
  if (timerInterval) clearInterval(timerInterval);
  window.removeEventListener('hashchange', handleHashChange);
  flushStudyTime();
});
</script>

<template>
  <div class="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col selection:bg-rose-500 selection:text-white transition-colors duration-200">
    <!-- Header Navigation: 仅在进入具体学习板块时显示完整工具栏与练习册下拉 -->
    <HeaderNav 
      v-if="currentTab !== 'welcome'"
      :current-tab="currentTab"
      :workbooks="workbooks"
      :active-workbook-id="activeWorkbookId"
      @update:current-tab="currentTab = $event"
      @select-workbook="selectWorkbook"
      @open-mobile-qr="showMobileQr = true"
      @open-sync="showSyncModal = true"
      @open-login="showLoginModal = true"
    />

    <!-- Main Content Area -->
    <main class="flex-1 w-full">
      <!-- 欢迎界面（独立首页门户：Logo + 登录系统 + 题库直通） -->
      <WelcomeCoverView 
        v-if="currentTab === 'welcome'"
        :workbooks="workbooks"
        :active-workbook-id="activeWorkbookId"
        @start-practice="startPractice"
        @select-workbook="selectWorkbook"
        @switch-tab="currentTab = $event"
        @open-mobile-qr="showMobileQr = true"
        @open-sync="showSyncModal = true"
        @open-login="showLoginModal = true"
      />

      <!-- 答题练习页面 -->
      <PracticeView 
        v-else-if="currentTab === 'practice'"
        :workbook-id="activeWorkbookId"
        :workbooks="workbooks"
        :initial-status="practiceInitialStatus"
        :initial-redo="practiceInitialRedo"
        @switch-tab="currentTab = $event"
        @switch-workbook="selectWorkbook"
      />

      <WrongBookView 
        v-else-if="currentTab === 'wrong'"
        @start-practice="startPractice"
      />

      <KilledQuestionsView 
        v-else-if="currentTab === 'killed'"
        :workbook-id="activeWorkbookId"
        @start-practice="currentTab = 'practice'"
        @switch-tab="currentTab = $event"
      />

      <NotesView 
        v-else-if="currentTab === 'notes'"
        :workbook-id="activeWorkbookId"
        @switch-tab="currentTab = $event"
      />

      <WorkbooksView 
        v-else-if="currentTab === 'workbooks'"
        :workbooks="workbooks"
        :active-workbook-id="activeWorkbookId"
        @refresh-workbooks="loadWorkbooks"
        @select-workbook="selectWorkbook"
        @start-practice="startPractice"
      />

      <StatsView 
        v-else-if="currentTab === 'stats'"
        @open-sync="showSyncModal = true"
        @open-mobile-qr="showMobileQr = true"
        @switch-tab="currentTab = $event"
      />

      <AdminView 
        v-else-if="currentTab === 'admin'"
        @switch-tab="currentTab = $event"
      />
    </main>

    <!-- Mobile QR Modal -->
    <MobileQrModal 
      :show="showMobileQr"
      @close="showMobileQr = false"
      @open-sync="showSyncModal = true"
    />

    <!-- Cross-Device Data Sync Modal -->
    <SyncModal 
      :show="showSyncModal"
      @close="showSyncModal = false"
      @synced="loadWorkbooks"
    />

    <!-- User Login & Multi-Device Cloud Sync Modal -->
    <LoginModal 
      :show="showLoginModal"
      @close="showLoginModal = false"
      @login-success="handleLoginSuccess"
      @open-admin="currentTab = 'admin'"
    />
  </div>
</template>
