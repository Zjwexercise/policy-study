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

// 初始页面：首次打开进入欢迎封面，会话期内刷新保留在当前界面
const currentTab = ref(sessionStorage.getItem('policy_current_tab') || 'welcome');
watch(currentTab, (val) => {
  sessionStorage.setItem('policy_current_tab', val);
});

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

const handleDataSynced = () => {
  loadWorkbooks();
};

onMounted(() => {
  loadWorkbooks();
  window.addEventListener('policy-data-synced', handleDataSynced);
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
  window.removeEventListener('policy-data-synced', handleDataSynced);
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
      />

      <NotesView 
        v-else-if="currentTab === 'notes'"
        :workbook-id="activeWorkbookId"
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
