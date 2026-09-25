<script setup>
import { ref, onMounted } from 'vue';
import { api } from './api';
import HeaderNav from './components/HeaderNav.vue';
import PracticeView from './components/PracticeView.vue';
import WrongBookView from './components/WrongBookView.vue';
import NotesView from './components/NotesView.vue';
import WorkbooksView from './components/WorkbooksView.vue';
import StatsView from './components/StatsView.vue';
import MobileQrModal from './components/MobileQrModal.vue';

const currentTab = ref('practice'); // practice, wrong, notes, workbooks, stats
const workbooks = ref([]);
const activeWorkbookId = ref('all'); // 'all' 代表全部综合练习，数字代表单册独立练习
const showMobileQr = ref(false);

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

const startPractice = () => {
  currentTab.value = 'practice';
};

onMounted(() => {
  loadWorkbooks();
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
    />

    <!-- Main Content Area -->
    <main class="flex-1 w-full">
      <PracticeView 
        v-if="currentTab === 'practice'"
        :workbook-id="activeWorkbookId"
        :workbooks="workbooks"
        @switch-tab="currentTab = $event"
      />

      <WrongBookView 
        v-else-if="currentTab === 'wrong'"
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
      />
    </main>

    <!-- Mobile QR Modal -->
    <MobileQrModal 
      :show="showMobileQr"
      @close="showMobileQr = false"
    />
  </div>
</template>
