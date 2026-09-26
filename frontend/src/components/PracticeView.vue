<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import { api } from '../api';
import confetti from 'canvas-confetti';
import { 
  Check, 
  X, 
  Star, 
  FileText, 
  ChevronLeft, 
  ChevronRight, 
  RotateCcw, 
  Shuffle, 
  LayoutGrid, 
  HelpCircle,
  Eye,
  Send,
  Sparkles,
  BookOpen,
  Swords
} from 'lucide-vue-next';
import AnswerSheetModal from './AnswerSheetModal.vue';
import NoteModal from './NoteModal.vue';

const props = defineProps({
  workbookId: {
    type: [Number, String],
    default: null
  },
  workbooks: {
    type: Array,
    default: () => []
  }
});

const emit = defineEmits(['switch-tab']);

const questions = ref([]);
const loading = ref(false);
const currentIndex = ref(0);
const selectedOptions = ref([]); // For multiple choice
const showAnswerSheet = ref(false);
const showNoteModal = ref(false);
const hideKilled = ref(true); // 隐藏已斩熟题（熟题不再重复刷）
const toastMsg = ref('');

const showToast = (msg) => {
  toastMsg.value = msg;
  setTimeout(() => {
    if (toastMsg.value === msg) {
      toastMsg.value = '';
    }
  }, 2200);
};

// 模式：study (即时解析背题), exam (模考模式，做完全部才看解析)
const practiceMode = ref('study'); 
const isRandomOrder = ref(false);

// 筛选条件
const selectedCategory = ref('全部');
const selectedType = ref('全部');
const selectedStatus = ref('all'); // all, unattempted, wrong, starred

const categories = ['全部', '马原', '毛中特', '史纲', '思修', '时政'];
const types = [
  { id: '全部', label: '全部题型' },
  { id: 'single', label: '单选题' },
  { id: 'multiple', label: '多选题' }
];

const currentQuestion = computed(() => {
  if (questions.value.length === 0) return null;
  return questions.value[currentIndex.value] || null;
});

const hasAnsweredCurrent = computed(() => {
  if (!currentQuestion.value) return false;
  return currentQuestion.value.user_answer !== null && 
         currentQuestion.value.user_answer !== undefined && 
         currentQuestion.value.user_answer !== '';
});

// 加载题目
const loadQuestions = async () => {
  if (!props.workbookId) return;
  loading.value = true;
  try {
    const params = {};
    if (selectedCategory.value !== '全部') params.category = selectedCategory.value;
    if (selectedType.value !== '全部') params.question_type = selectedType.value;
    if (selectedStatus.value !== 'all') params.status = selectedStatus.value;
    params.hide_killed = hideKilled.value;

    let data = await api.getQuestions(props.workbookId, params);
    if (isRandomOrder.value) {
      data = [...data].sort(() => Math.random() - 0.5);
    }
    questions.value = data;
    currentIndex.value = 0;
    resetSelection();
  } catch (err) {
    console.error('加载题目失败', err);
  } finally {
    loading.value = false;
  }
};

// 监听题号切换
watch(currentIndex, () => {
  resetSelection();
});

const resetSelection = () => {
  selectedOptions.value = [];
  if (currentQuestion.value && currentQuestion.value.user_answer) {
    selectedOptions.value = currentQuestion.value.user_answer.split('');
  }
};

// 监听练习册或筛选改变
watch(() => props.workbookId, () => {
  loadQuestions();
});

watch([selectedCategory, selectedType, selectedStatus, isRandomOrder, hideKilled], () => {
  loadQuestions();
});

// 点击选项
const handleOptionClick = (key) => {
  if (!currentQuestion.value) return;

  // 如果已经作答，且处于即时解析模式，不允许修改（若想重做需点击重做本题）
  if (hasAnsweredCurrent.value && practiceMode.value === 'study') {
    return;
  }

  const isMulti = currentQuestion.value.question_type === 'multiple';

  if (!isMulti) {
    // 单选：直接选定并提交
    selectedOptions.value = [key];
    doSubmit(key);
  } else {
    // 多选：勾选或取消
    const idx = selectedOptions.value.indexOf(key);
    if (idx > -1) {
      selectedOptions.value.splice(idx, 1);
    } else {
      selectedOptions.value.push(key);
      selectedOptions.value.sort();
    }
  }
};

// 提交多选题答案
const submitMultiple = () => {
  if (selectedOptions.value.length === 0) {
    alert('请至少选择一个选项');
    return;
  }
  const ans = selectedOptions.value.join('');
  doSubmit(ans);
};

// 提交核心逻辑
const doSubmit = async (answer) => {
  if (!currentQuestion.value) return;
  try {
    const targetWbId = currentQuestion.value.workbook_id || props.workbookId;
    const res = await api.submitAnswer(
      targetWbId, 
      currentQuestion.value.id, 
      answer
    );
    currentQuestion.value.user_answer = answer;
    currentQuestion.value.is_correct = res.is_correct;
    
    // 如果回答正确，触发小烟花
    if (res.is_correct && practiceMode.value === 'study') {
      confetti({
        particleCount: 25,
        spread: 40,
        origin: { y: 0.8 }
      });
    }
  } catch (err) {
    alert('提交答案失败: ' + err.message);
  }
};

// 重做当前题目
const redoCurrentQuestion = () => {
  if (!currentQuestion.value) return;
  currentQuestion.value.user_answer = null;
  currentQuestion.value.is_correct = null;
  selectedOptions.value = [];
};

// 收藏切换
const toggleStar = async () => {
  if (!currentQuestion.value) return;
  const nextVal = !currentQuestion.value.is_starred;
  try {
    const targetWbId = currentQuestion.value.workbook_id || props.workbookId;
    await api.toggleStar(targetWbId, currentQuestion.value.id, nextVal);
    currentQuestion.value.is_starred = nextVal;
  } catch (err) {
    console.error('收藏失败', err);
  }
};

// 斩杀/复活熟题切换
const toggleKill = async () => {
  if (!currentQuestion.value) return;
  const nextVal = !currentQuestion.value.is_killed;
  try {
    const targetWbId = currentQuestion.value.workbook_id || props.workbookId;
    await api.toggleKillQuestion(targetWbId, currentQuestion.value.id, nextVal);
    currentQuestion.value.is_killed = nextVal ? 1 : 0;
    if (nextVal) {
      showToast('⚔️ 熟题已斩杀！后续刷题将自动跳过此题');
    } else {
      showToast('🛡️ 题目已复活，已重新加入练习题库');
    }
  } catch (err) {
    console.error('斩题操作失败', err);
    showToast('操作失败，请重试');
  }
};

// 切换上/下一题
const prevQuestion = () => {
  if (currentIndex.value > 0) {
    currentIndex.value--;
  }
};

const nextQuestion = () => {
  if (currentIndex.value < questions.value.length - 1) {
    currentIndex.value++;
  }
};

// 快捷键支持
const handleKeyDown = (e) => {
  if (showNoteModal.value || showAnswerSheet.value) return;
  
  // 排除输入框内的按键
  if (['INPUT', 'TEXTAREA'].includes(e.target.tagName)) return;

  const key = e.key.toUpperCase();
  if (['A', 'B', 'C', 'D'].includes(key)) {
    handleOptionClick(key);
  } else if (['1', '2', '3', '4'].includes(e.key)) {
    const map = { '1': 'A', '2': 'B', '3': 'C', '4': 'D' };
    handleOptionClick(map[e.key]);
  } else if (e.key === 'Enter') {
    if (currentQuestion.value?.question_type === 'multiple' && !hasAnsweredCurrent.value) {
      submitMultiple();
    }
  } else if (e.key === 'ArrowLeft' || e.key === 'j') {
    prevQuestion();
  } else if (e.key === 'ArrowRight' || e.key === 'k') {
    nextQuestion();
  }
};

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown);
  loadQuestions();
});

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown);
});
</script>

<template>
  <div class="max-w-4xl mx-auto px-3 sm:px-6 py-4 pb-24 lg:pb-12">
    <!-- Filter and Toolbar Area -->
    <div class="bg-white rounded-2xl p-3 sm:p-4 border border-slate-200 shadow-2xs mb-4">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <!-- 学科分类过滤 -->
        <div class="flex items-center gap-1 overflow-x-auto py-0.5 no-scrollbar">
          <button
            v-for="cat in categories"
            :key="cat"
            @click="selectedCategory = cat"
            class="px-2.5 py-1 text-xs font-medium rounded-lg shrink-0 transition cursor-pointer"
            :class="[
              selectedCategory === cat 
                ? 'bg-rose-600 text-white shadow-2xs font-semibold' 
                : 'text-slate-600 hover:bg-slate-100'
            ]"
          >
            {{ cat }}
          </button>
        </div>

        <!-- 模式与辅助按钮 -->
        <div class="flex items-center gap-2">
          <!-- 题型筛选 -->
          <select 
            v-model="selectedType"
            class="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2 py-1 text-slate-700 cursor-pointer"
          >
            <option v-for="t in types" :key="t.id" :value="t.id">{{ t.label }}</option>
          </select>

          <!-- 乱序开关 -->
          <button
            @click="isRandomOrder = !isRandomOrder"
            class="p-1.5 rounded-lg border text-xs font-medium flex items-center gap-1 transition cursor-pointer"
            :class="[
              isRandomOrder 
                ? 'bg-indigo-50 border-indigo-200 text-indigo-700' 
                : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100'
            ]"
            title="开启/关闭随机乱序"
          >
            <Shuffle class="w-3.5 h-3.5" />
            <span class="hidden sm:inline">乱序</span>
          </button>

          <!-- 隐藏已斩熟题开关 -->
          <button
            @click="hideKilled = !hideKilled"
            class="px-2.5 py-1.5 rounded-lg border text-xs font-medium flex items-center gap-1 transition cursor-pointer select-none"
            :class="[
              hideKilled 
                ? 'bg-rose-50 border-rose-200 text-rose-700 font-semibold' 
                : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100'
            ]"
            :title="hideKilled ? '已开启熟题过滤：斩杀的熟题不会再出现' : '已关闭熟题过滤：所有题目均会出现'"
          >
            <Swords class="w-3.5 h-3.5" :class="{ 'text-rose-600': hideKilled }" />
            <span>{{ hideKilled ? '已隐藏熟题' : '显示熟题' }}</span>
          </button>

          <!-- 答题卡抽屉触发 -->
          <button
            @click="showAnswerSheet = true"
            class="px-2.5 py-1.5 rounded-lg border border-slate-200 bg-slate-50 hover:bg-slate-100 text-slate-700 text-xs font-medium flex items-center gap-1 transition cursor-pointer"
          >
            <LayoutGrid class="w-3.5 h-3.5 text-slate-500" />
            <span>答题卡</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Main Question Box -->
    <div v-if="loading" class="bg-white rounded-2xl p-12 text-center border border-slate-200 shadow-2xs">
      <div class="inline-block animate-spin w-8 h-8 border-3 border-rose-500 border-t-transparent rounded-full mb-3"></div>
      <p class="text-sm text-slate-500">正在调取题目，准备刷题...</p>
    </div>

    <div v-else-if="!currentQuestion" class="bg-white rounded-2xl p-12 text-center border border-slate-200 shadow-2xs">
      <BookOpen class="w-12 h-12 text-slate-300 mx-auto mb-3" />
      <h3 class="text-base font-bold text-slate-700">暂无符合条件的题目</h3>
      <p class="text-xs text-slate-400 mt-1">请尝试切换分类或导入新的政治练习册PDF</p>
      <button 
        @click="emit('switch-tab', 'workbooks')"
        class="mt-4 px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold rounded-xl transition cursor-pointer"
      >
        前往上传练习册
      </button>
    </div>

    <div v-else class="space-y-4">
      <!-- Question Card -->
      <div class="bg-white rounded-2xl p-4 sm:p-6 border border-slate-200 shadow-2xs relative">
        <!-- Question Meta Info -->
        <div class="flex items-center justify-between pb-3 mb-4 border-b border-slate-100 gap-2">
          <div class="flex items-center gap-2 flex-wrap">
            <span class="text-xs font-bold text-slate-400">
              第 {{ currentIndex + 1 }} / {{ questions.length }} 题
            </span>
            <!-- 来源练习册标签（综合练习模式下格外清晰） -->
            <span 
              v-if="currentQuestion.workbook_name"
              class="px-2 py-0.5 text-xs font-semibold rounded-md bg-purple-50 text-purple-700 border border-purple-200 shrink-0"
            >
              📖 {{ currentQuestion.workbook_name }}
            </span>
            <span class="px-2 py-0.5 text-xs font-semibold rounded-md bg-blue-50 text-blue-700 border border-blue-100">
              {{ currentQuestion.category }}
            </span>
            <span 
              class="px-2 py-0.5 text-xs font-semibold rounded-md"
              :class="[
                currentQuestion.question_type === 'multiple' 
                  ? 'bg-amber-50 text-amber-700 border border-amber-200' 
                  : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
              ]"
            >
              {{ currentQuestion.question_type === 'multiple' ? '多选题 (2分)' : '单选题 (1分)' }}
            </span>
          </div>

          <!-- Question Actions -->
          <div class="flex items-center gap-1.5">
            <!-- 斩杀熟题按钮 -->
            <button
              @click="toggleKill"
              class="px-2 sm:px-2.5 py-1.5 rounded-lg border text-xs font-medium flex items-center gap-1 transition cursor-pointer"
              :class="[
                currentQuestion.is_killed 
                  ? 'bg-rose-900 border-rose-900 text-rose-100 shadow-2xs font-semibold' 
                  : 'border-slate-200 text-slate-500 hover:text-rose-700 hover:bg-rose-50 hover:border-rose-200'
              ]"
              :title="currentQuestion.is_killed ? '已斩杀！点击可复活' : '已熟练掌握？点击斩杀，后续刷题不再出现'"
            >
              <Swords class="w-3.5 h-3.5" :class="currentQuestion.is_killed ? 'text-rose-200' : 'text-slate-400'" />
              <span class="hidden sm:inline">{{ currentQuestion.is_killed ? '已斩熟题' : '斩熟题' }}</span>
            </button>

            <button
              @click="toggleStar"
              class="p-1.5 rounded-lg border transition cursor-pointer"
              :class="[
                currentQuestion.is_starred 
                  ? 'bg-amber-50 border-amber-200 text-amber-500' 
                  : 'border-slate-200 text-slate-400 hover:text-slate-600 hover:bg-slate-50'
              ]"
              title="收藏本题"
            >
              <Star class="w-4 h-4" :class="{ 'fill-amber-500': currentQuestion.is_starred }" />
            </button>
            <button
              @click="showNoteModal = true"
              class="p-1.5 rounded-lg border transition cursor-pointer"
              :class="[
                currentQuestion.has_note || currentQuestion.note_content
                  ? 'bg-blue-50 border-blue-200 text-blue-600'
                  : 'border-slate-200 text-slate-400 hover:text-slate-600 hover:bg-slate-50'
              ]"
              title="记录考点笔记"
            >
              <FileText class="w-4 h-4" />
            </button>
          </div>
        </div>

        <!-- Question Stem (题干) -->
        <div class="text-base sm:text-lg font-medium text-slate-900 leading-relaxed tracking-wide">
          <span class="font-bold text-rose-600 mr-1.5">{{ currentQuestion.question_num }}.</span>
          <span>{{ currentQuestion.stem }}</span>
        </div>

        <!-- Options List -->
        <div class="mt-6 space-y-3">
          <div
            v-for="opt in currentQuestion.options"
            :key="opt.key"
            @click="handleOptionClick(opt.key)"
            class="group p-3.5 sm:p-4 rounded-xl border-2 transition-all flex items-start gap-3 cursor-pointer select-none"
            :class="[
              // 作答后的判定样式
              hasAnsweredCurrent
                ? (
                    // 该选项是正确答案之一
                    currentQuestion.answer.includes(opt.key)
                      ? 'border-emerald-500 bg-emerald-50/70 text-emerald-950 font-medium'
                      // 用户选了该项但是是错的
                      : (currentQuestion.user_answer.includes(opt.key)
                          ? 'border-rose-500 bg-rose-50/70 text-rose-950'
                          : 'border-slate-200/80 bg-slate-50/50 text-slate-400 opacity-60')
                  )
                // 未作答时的选中状态
                : (
                    selectedOptions.includes(opt.key)
                      ? 'border-rose-500 bg-rose-50/40 text-slate-900 shadow-xs'
                      : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50 text-slate-800'
                  )
            ]"
          >
            <!-- Option Key Badge (A, B, C, D) -->
            <div
              class="w-7 h-7 rounded-lg flex items-center justify-center font-bold text-sm shrink-0 transition"
              :class="[
                hasAnsweredCurrent
                  ? (
                      currentQuestion.answer.includes(opt.key)
                        ? 'bg-emerald-600 text-white'
                        : (currentQuestion.user_answer.includes(opt.key)
                            ? 'bg-rose-600 text-white'
                            : 'bg-slate-200 text-slate-600')
                    )
                  : (
                      selectedOptions.includes(opt.key)
                        ? 'bg-rose-600 text-white'
                        : 'bg-slate-100 group-hover:bg-slate-200 text-slate-700'
                    )
              ]"
            >
              <span>{{ opt.key }}</span>
            </div>

            <!-- Option Text -->
            <div class="text-sm sm:text-base leading-relaxed pt-0.5 flex-1">
              {{ opt.value }}
            </div>

            <!-- Feedback Icon -->
            <div v-if="hasAnsweredCurrent" class="shrink-0 pt-0.5">
              <Check v-if="currentQuestion.answer.includes(opt.key)" class="w-5 h-5 text-emerald-600 font-bold" />
              <X v-else-if="currentQuestion.user_answer.includes(opt.key)" class="w-5 h-5 text-rose-600 font-bold" />
            </div>
          </div>
        </div>

        <!-- Multiple Choice Submit Button (多选题提交按钮) -->
        <div 
          v-if="currentQuestion.question_type === 'multiple' && !hasAnsweredCurrent"
          class="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between gap-3"
        >
          <div class="text-xs text-slate-500">
            已选：<span class="font-bold text-rose-600 font-mono">{{ selectedOptions.join('') || '未选' }}</span>
            <span class="hidden sm:inline text-slate-400 ml-2">（多选题支持按回车快捷提交）</span>
          </div>
          <button
            @click="submitMultiple"
            class="px-5 py-2.5 bg-rose-600 hover:bg-rose-700 active:bg-rose-800 text-white font-semibold text-sm rounded-xl shadow-xs flex items-center gap-1.5 transition cursor-pointer"
          >
            <Send class="w-4 h-4" />
            <span>确认作答</span>
          </button>
        </div>
      </div>

      <!-- Result & Explanation Box (即时解析区域) -->
      <div 
        v-if="hasAnsweredCurrent"
        class="bg-white rounded-2xl p-4 sm:p-6 border border-slate-200 shadow-2xs animate-in slide-in-from-bottom-2 duration-300"
      >
        <!-- Result Banner -->
        <div 
          class="p-4 rounded-xl flex items-center justify-between gap-3 mb-4"
          :class="[
            currentQuestion.is_correct 
              ? 'bg-emerald-50 border border-emerald-200 text-emerald-800' 
              : 'bg-rose-50 border border-rose-200 text-rose-800'
          ]"
        >
          <div class="flex items-center gap-2.5">
            <div 
              class="w-8 h-8 rounded-full flex items-center justify-center font-bold text-white shrink-0"
              :class="currentQuestion.is_correct ? 'bg-emerald-600' : 'bg-rose-600'"
            >
              <Check v-if="currentQuestion.is_correct" class="w-5 h-5" />
              <X v-else class="w-5 h-5" />
            </div>
            <div>
              <div class="font-bold text-sm sm:text-base">
                {{ currentQuestion.is_correct ? '回答正确！' : '回答错误！已自动收录到错题本' }}
              </div>
              <div class="text-xs mt-0.5 opacity-90 flex items-center gap-3">
                <span>你的作答：<strong class="font-mono text-sm underline">{{ currentQuestion.user_answer }}</strong></span>
                <span>正确答案：<strong class="font-mono text-sm underline">{{ currentQuestion.answer }}</strong></span>
              </div>
            </div>
          </div>

          <div class="flex items-center gap-1.5 shrink-0">
            <!-- 斩杀熟题快捷按钮 -->
            <button
              @click="toggleKill"
              class="px-2.5 py-1 text-xs font-medium rounded-lg transition cursor-pointer flex items-center gap-1 border shadow-2xs"
              :class="[
                currentQuestion.is_killed
                  ? 'bg-rose-900 text-white border-rose-900 font-semibold'
                  : 'bg-white/90 hover:bg-white text-slate-700 border-slate-200 hover:text-rose-700 hover:border-rose-200'
              ]"
              :title="currentQuestion.is_killed ? '已斩杀，点击可复活' : '完全熟练？一键斩杀不再重复刷此题'"
            >
              <Swords class="w-3.5 h-3.5" :class="currentQuestion.is_killed ? 'text-rose-200' : 'text-rose-600'" />
              <span>{{ currentQuestion.is_killed ? '已斩熟题' : '斩掉此题' }}</span>
            </button>

            <button
              @click="redoCurrentQuestion"
              class="px-2.5 py-1 text-xs font-medium rounded-lg bg-white/80 hover:bg-white text-slate-700 border border-slate-200 transition cursor-pointer flex items-center gap-1"
              title="清空当前作答重新做一次"
            >
              <RotateCcw class="w-3.5 h-3.5" />
              <span>重做本题</span>
            </button>
          </div>
        </div>

        <!-- 详细考点解析 -->
        <div class="space-y-2">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-slate-700 flex items-center gap-1">
              <Sparkles class="w-3.5 h-3.5 text-amber-500" /> 考点精析
            </span>
            <button
              @click="showNoteModal = true"
              class="text-xs text-rose-600 hover:text-rose-700 font-medium flex items-center gap-1 cursor-pointer"
            >
              <FileText class="w-3.5 h-3.5" />
              <span>{{ currentQuestion.has_note ? '编辑笔记' : '添加笔记' }}</span>
            </button>
          </div>
          <div class="p-3.5 bg-slate-50 border border-slate-100 rounded-xl text-xs sm:text-sm text-slate-700 leading-relaxed whitespace-pre-line font-normal">
            {{ currentQuestion.explanation || '暂无针对本题的详细解析' }}
          </div>
        </div>

        <!-- 笔记预览（若有） -->
        <div v-if="currentQuestion.note_content" class="mt-3 p-3 bg-amber-50/70 border border-amber-200/80 rounded-xl text-xs text-amber-900">
          <div class="font-bold flex items-center gap-1 mb-1 text-amber-800">
            <FileText class="w-3.5 h-3.5" /> 我的备考笔记：
          </div>
          <p class="whitespace-pre-line">{{ currentQuestion.note_content }}</p>
        </div>
      </div>

      <!-- Navigation Bar (Previous / Next Buttons) -->
      <div class="flex items-center justify-between gap-3 pt-2">
        <button
          @click="prevQuestion"
          :disabled="currentIndex === 0"
          class="flex-1 sm:flex-none px-5 py-2.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-40 disabled:pointer-events-none text-slate-700 text-sm font-medium flex items-center justify-center gap-1.5 shadow-2xs transition cursor-pointer"
        >
          <ChevronLeft class="w-4 h-4" />
          <span>上一题</span>
        </button>

        <!-- 中间进度指示 -->
        <div class="hidden sm:flex items-center gap-2 text-xs text-slate-500">
          <span>键盘快捷键：A/B/C/D 选答案 · Enter 提交 · ←/→ 翻题</span>
        </div>

        <button
          @click="nextQuestion"
          :disabled="currentIndex >= questions.length - 1"
          class="flex-1 sm:flex-none px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 active:bg-slate-950 disabled:opacity-40 disabled:pointer-events-none text-white text-sm font-semibold flex items-center justify-center gap-1.5 shadow-2xs transition cursor-pointer"
        >
          <span>下一题</span>
          <ChevronRight class="w-4 h-4" />
        </button>
      </div>
    </div>

    <!-- Modals -->
    <AnswerSheetModal 
      :show="showAnswerSheet"
      :questions="questions"
      :current-index="currentIndex"
      @close="showAnswerSheet = false"
      @jump="currentIndex = $event"
    />

    <NoteModal 
      :show="showNoteModal"
      :question="currentQuestion"
      @close="showNoteModal = false"
      @saved="currentQuestion.note_content = $event.content; currentQuestion.has_note = true;"
    />

    <!-- Floating Toast Notification -->
    <transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="transform -translate-y-2 opacity-0"
      enter-to-class="transform translate-y-0 opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="transform translate-y-0 opacity-100"
      leave-to-class="transform -translate-y-2 opacity-0"
    >
      <div 
        v-if="toastMsg"
        class="fixed top-18 left-1/2 -translate-x-1/2 z-50 bg-slate-900/95 backdrop-blur-md text-white text-xs sm:text-sm font-semibold px-4 py-2.5 rounded-xl shadow-xl border border-slate-700/80 flex items-center gap-2 pointer-events-none"
      >
        <span>{{ toastMsg }}</span>
      </div>
    </transition>
  </div>
</template>
