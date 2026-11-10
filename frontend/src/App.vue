<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { api } from './api';
import HeaderNav from './components/HeaderNav.vue';
import PracticeView from './components/PracticeView.vue';
import WrongBookView from './components/WrongBookView.vue';
import KilledQuestionsView from './components/KilledQuestionsView.vue';
import NotesView from './components/NotesView.vue';
import WorkbooksView from './components/WorkbooksView.vue';
import StatsView from './components/StatsView.vue';
import MobileQrModal from './components/MobileQrModal.vue';
import SyncModal from './components/SyncModal.vue';
import LoginModal from './components/LoginModal.vue';
import { auth } from './auth';

const currentTab = ref('practice'); // practice, wrong, killed, notes, workbooks, stats
const workbooks = ref([]);
const activeWorkbookId = ref('all'); // 'all' 代表全部综合练习，数字代表单册独立练习
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
      activeWorkbookId.value = 'all';
    }
  } catch (err) {
    console.error('加载练习册列表失败', err);
  }
};

const selectWorkbook = (id) => {
  activeWorkbookId.value = id;
};

const startPractice = (options = {}) => {
  if (options && options.status) {
    practiceInitialStatus.value = options.status;
    practiceInitialRedo.value = !!options.redo;
  } else {
    practiceInitialStatus.value = 'all';
    practiceInitialRedo.value = false;
  }
  currentTab.value = 'practice';
};

// ==========================================
// 实时学习专注时长追踪逻辑 (防息屏/防挂机)
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
  flushStudyTime();
});
</script>

<template>
  <div class="min-h-screen bg-slate-50 flex flex-col selection:bg-rose-500 selection:text-white">
    <!-- Header Navigation -->
    <HeaderNav 
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
      <PracticeView 
        v-if="currentTab === 'practice'"
        :workbook-id="activeWorkbookId"
        :workbooks="workbooks"
        :initial-status="practiceInitialStatus"
        :initial-redo="practiceInitialRedo"
        @switch-tab="currentTab = $event"
      />

      <WrongBookView 
        v-else-if="currentTab === 'wrong'"
        :workbook-id="activeWorkbookId"
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
    />
  </div>
</template>
