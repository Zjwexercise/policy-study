<script setup>
import { ref, watch, onMounted, computed } from 'vue';
import { api } from '../api';
import confetti from 'canvas-confetti';
import { 
  AlertCircle, 
  CheckCircle2, 
  Trash2, 
  FileText, 
  Sparkles, 
  Play, 
  RotateCcw,
  Star,
  Check,
  X,
  Send,
  HelpCircle,
  Eye,
  BookOpen,
  ArrowRight
} from 'lucide-vue-next';
import NoteModal from './NoteModal.vue';

const props = defineProps({
  workbookId: {
    type: [Number, String],
    default: null
  }
});

const emit = defineEmits(['start-practice']);

const wrongQuestions = ref([]);
const loading = ref(false);
const selectedCategory = ref('全部');
const includeMastered = ref(false);
const activeNoteQuestion = ref(null);
const showNoteModal = ref(false);
const toastMsg = ref('');

// 模式：'quiz' (自测重做模式，选项可点击，隐去答案), 'review' (解析背诵模式，直接显示答案与错选)
const viewMode = ref('quiz');

// 各题目独立的作答交互状态
// 格式: { [qId]: { selected: ['A'], isSubmitted: bool, isCorrect: bool, userAns: '' } }
const redoStates = ref({});

const categories = ['全部', '马原', '毛中特', '习思想', '史纲', '思修', '时政'];

const showToast = (msg) => {
  toastMsg.value = msg;
  setTimeout(() => {
    if (toastMsg.value === msg) {
      toastMsg.value = '';
    }
  }, 2400);
};

const loadWrongQuestions = async () => {
  loading.value = true;
  try {
    const params = {
      include_mastered: includeMastered.value
    };
    if (props.workbookId && props.workbookId !== 'all') params.workbook_id = props.workbookId;
    if (selectedCategory.value !== '全部') params.category = selectedCategory.value;

    const data = await api.getWrongQuestions(params);
    wrongQuestions.value = data;

    // 智能恢复持久化作答状态：优先读取 localStorage，其次读取数据中已记录的 user_answer
    data.forEach(q => {
      const qid = q.question_id || q.id;
      const saved = localStorage.getItem(`policy_wb_redo_${qid}`);
      if (saved) {
        try {
          redoStates.value[qid] = JSON.parse(saved);
          return;
        } catch (e) {}
      }
      if (q.user_answer) {
        redoStates.value[qid] = {
          selected: q.user_answer.split(''),
          isSubmitted: true,
          isCorrect: q.is_correct === true || q.is_correct === 1,
          userAns: q.user_answer
        };
      }
    });
  } catch (err) {
    console.error('加载错题失败', err);
  } finally {
    loading.value = false;
  }
};

watch(() => props.workbookId, loadWrongQuestions);
watch([selectedCategory, includeMastered], loadWrongQuestions);

// 获取某道题的交互状态
const getRedoState = (qId) => {
  if (!redoStates.value[qId]) {
    redoStates.value[qId] = {
      selected: [],
      isSubmitted: false,
      isCorrect: null,
      userAns: ''
    };
  }
  return redoStates.value[qId];
};

// 判断某道题当前是否处于“正在重做/未提交”状态
const isQuestionTesting = (q) => {
  const state = redoStates.value[q.question_id || q.id];
  if (state) {
    return !state.isSubmitted;
  }
  return viewMode.value === 'quiz';
};

// 重做单道题（无论当前在什么模式，清空选项并进入自测状态）
const startRedoSingleQuestion = async (q) => {
  const qid = q.question_id || q.id;
  redoStates.value[qid] = {
    selected: [],
    isSubmitted: false,
    isCorrect: null,
    userAns: ''
  };
  localStorage.removeItem(`policy_wb_redo_${qid}`);
  q.user_answer = null;
  q.is_correct = null;
  q.last_wrong_answer = null;
  try {
    await api.resetQuestionAnswer(q.workbook_id, qid);
  } catch (e) {
    console.error('清空单题记录失败', e);
  }
  showToast(`第 ${q.question_num} 题已重置为未答，请重新作答！`);
};

// 点击选项
const handleOptionClick = (q, optKey) => {
  const qid = q.question_id || q.id;
  const state = getRedoState(qid);
  if (state.isSubmitted) return; // 已提交作答后不改变

  const isMulti = q.question_type === 'multiple';
  if (!isMulti) {
    state.selected = [optKey];
    submitRedo(q, optKey);
  } else {
    const idx = state.selected.indexOf(optKey);
    if (idx > -1) {
      state.selected.splice(idx, 1);
    } else {
      state.selected.push(optKey);
      state.selected.sort();
    }
  }
};

// 提交自测作答
const submitRedo = async (q, overrideAns = null) => {
  const qid = q.question_id || q.id;
  const state = getRedoState(qid);
  const finalAns = overrideAns || state.selected.join('');
  if (!finalAns) {
    alert('请至少选择一个选项');
    return;
  }

  try {
    const res = await api.submitAnswer(q.workbook_id, qid, finalAns);
    state.isSubmitted = true;
    state.userAns = finalAns;
    state.isCorrect = !!res.is_correct;
    q.user_answer = finalAns;
    q.is_correct = !!res.is_correct;

    // 持久化保存 redoState 到 localStorage，刷新绝不丢失
    localStorage.setItem(`policy_wb_redo_${qid}`, JSON.stringify({
      selected: state.selected,
      isSubmitted: true,
      isCorrect: state.isCorrect,
      userAns: finalAns
    }));

    // 同步到常规作答缓存，确保全局统计与进度完全一致
    localStorage.setItem(`policy_ans_${q.workbook_id}_${qid}`, finalAns);
    localStorage.setItem(`policy_ans_all_${qid}`, finalAns);
    localStorage.setItem(`policy_cor_${qid}`, res.is_correct ? '1' : '0');

    if (res.is_correct) {
      confetti({
        particleCount: 26,
        spread: 45,
        origin: { y: 0.7 }
      });
      showToast('🎉 重做正确！作答已记录，可随时点击【移出错题集】！');
    } else {
      q.wrong_count = (q.wrong_count || 1) + 1;
      q.last_wrong_answer = finalAns;
      showToast('❌ 回答仍有偏差，最新作答已实时记录！');
    }
  } catch (err) {
    alert('提交答案失败: ' + err.message);
  }
};

// 清空所有错题历史作答记录（清空旧选项，保留错题供重做）
const handleResetAllAnswers = async () => {
  if (!confirm('确定要清空所有错题的历史选择吗？\n\n所有错题仍会保留在错题本中，但之前的选项与作答痕迹会被清空，让你能从头全新自测！')) {
    return;
  }
  try {
    await api.resetWrongAnswers(props.workbookId);
    redoStates.value = {};
    for (const q of wrongQuestions.value) {
      const qid = q.question_id || q.id;
      localStorage.removeItem(`policy_wb_redo_${qid}`);
      q.user_answer = null;
      q.is_correct = null;
      q.last_wrong_answer = null;
    }
    viewMode.value = 'quiz';
    showToast('✨ 所有错题作答记录已清空，现在可以全新重做！');
  } catch (err) {
    alert('清空选项记录失败: ' + err.message);
  }
};

// 专项重练所有错题（跳转到练习界面刷题）
const handleStartPracticeRedo = async () => {
  try {
    await api.resetWrongAnswers(props.workbookId);
  } catch (e) {
    // ignore
  }
  emit('start-practice', { status: 'wrong', redo: true });
};

// 移出错题本 / 重新收录
const toggleMaster = async (item) => {
  const qid = item.question_id || item.id;
  const nextStatus = !item.is_mastered;
  try {
    await api.toggleMasterWrong(qid, nextStatus);
    item.is_mastered = nextStatus;
    if (!includeMastered.value && nextStatus) {
      // 从未掌握列表中平滑移除
      wrongQuestions.value = wrongQuestions.value.filter(q => (q.question_id || q.id) !== qid);
    }
    showToast(nextStatus ? '🏆 已成功移出错题集！' : '已重新收录进错题集');
  } catch (err) {
    alert('操作失败: ' + err.message);
  }
};

// 清空错题本
const handleClearAll = async () => {
  if (!confirm('确定要清空错题记录吗？这不会影响练习册题目本身。')) return;
  try {
    await api.clearWrongBook(props.workbookId);
    for (const q of wrongQuestions.value) {
      const qid = q.question_id || q.id;
      localStorage.removeItem(`policy_wb_redo_${qid}`);
    }
    wrongQuestions.value = [];
    showToast('错题本已全部清空');
  } catch (err) {
    alert('清空失败: ' + err.message);
  }
};

const openNote = (q) => {
  activeNoteQuestion.value = {
    id: q.question_id,
    question_num: q.question_num,
    category: q.category,
    stem: q.stem,
    note_content: q.note_content,
    has_note: !!q.note_content
  };
  showNoteModal.value = true;
};

const handleNoteSaved = (e) => {
  const target = wrongQuestions.value.find(q => q.question_id === e.questionId);
  if (target) {
    target.note_content = e.content;
  }
};

onMounted(() => {
  loadWrongQuestions();
});
</script>

<template>
  <div class="max-w-4xl mx-auto px-3 sm:px-6 py-4 pb-24 lg:pb-12 relative">
    <!-- Toast 通知 -->
    <div 
      v-if="toastMsg" 
      class="fixed top-20 left-1/2 -translate-x-1/2 z-50 bg-slate-900/90 text-white text-xs sm:text-sm font-medium px-4 py-2 rounded-full shadow-lg backdrop-blur-xs flex items-center gap-2 pointer-events-none transition-all duration-300 animate-in fade-in zoom-in-95"
    >
      <Sparkles class="w-4 h-4 text-amber-400" />
      <span>{{ toastMsg }}</span>
    </div>

    <!-- Header & Statistics -->
    <div class="bg-white rounded-2xl p-4 sm:p-5 border border-slate-200 shadow-2xs mb-4">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-100">
        <div class="flex items-center gap-3">
          <div class="p-3 bg-rose-50 text-rose-600 rounded-2xl shrink-0">
            <AlertCircle class="w-6 h-6" />
          </div>
          <div>
            <div class="flex items-center gap-2">
              <h2 class="text-base sm:text-lg font-bold text-slate-800">考研政治错题本</h2>
              <span v-if="wrongQuestions.length > 0" class="px-2 py-0.5 text-xs font-semibold rounded-full bg-rose-100 text-rose-700">
                {{ wrongQuestions.length }} 题待攻克
              </span>
            </div>
            <p class="text-xs text-slate-500 mt-0.5">智能收录做错题目，重点消灭易错点与命题陷阱</p>
          </div>
        </div>

        <!-- 顶部核心操作按钮组 -->
        <div class="flex items-center gap-2 flex-wrap">
          <!-- 专项重练所有错题 -->
          <button
            v-if="wrongQuestions.length > 0"
            @click="handleStartPracticeRedo"
            class="px-3.5 py-2 text-xs font-semibold rounded-xl bg-gradient-to-r from-rose-600 to-rose-700 hover:from-rose-700 hover:to-rose-800 text-white shadow-xs hover:shadow transition cursor-pointer flex items-center gap-1.5 active:scale-95"
            title="在专注做题界面从第 1 题开始全新重做所有错题"
          >
            <Play class="w-3.5 h-3.5 fill-white" />
            <span>专项重练所有错题</span>
          </button>

          <!-- 清空选项重新做 -->
          <button
            v-if="wrongQuestions.length > 0"
            @click="handleResetAllAnswers"
            class="px-3 py-2 text-xs font-medium text-slate-700 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-xl transition cursor-pointer flex items-center gap-1.5 active:scale-95"
            title="清空历史选择与选项痕迹，重置为全新自测状态"
          >
            <RotateCcw class="w-3.5 h-3.5 text-slate-500" />
            <span>清空作答记录重新做</span>
          </button>

          <!-- 清空错题本 -->
          <button
            v-if="wrongQuestions.length > 0"
            @click="handleClearAll"
            class="p-2 text-xs text-slate-400 hover:text-rose-600 hover:bg-rose-50 border border-slate-200 hover:border-rose-200 rounded-xl transition cursor-pointer"
            title="清空错题记录"
          >
            <Trash2 class="w-4 h-4" />
          </button>
        </div>
      </div>

      <!-- Mode & Filters -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-3.5">
        <!-- 学科分类 -->
        <div class="flex items-center gap-1 overflow-x-auto py-0.5 no-scrollbar">
          <button
            v-for="cat in categories"
            :key="cat"
            @click="selectedCategory = cat"
            class="px-2.5 py-1 text-xs font-medium rounded-lg shrink-0 transition cursor-pointer"
            :class="[
              selectedCategory === cat 
                ? 'bg-rose-600 text-white font-semibold shadow-2xs' 
                : 'text-slate-600 hover:bg-slate-100'
            ]"
          >
            {{ cat }}
          </button>
        </div>

        <!-- 模式切换与已掌握勾选 -->
        <div class="flex items-center gap-3 self-end sm:self-auto">
          <!-- 模式切换 Pills -->
          <div class="bg-slate-100 p-0.5 rounded-lg flex items-center text-xs">
            <button
              @click="viewMode = 'quiz'"
              class="px-2.5 py-1 rounded-md font-medium transition cursor-pointer flex items-center gap-1"
              :class="viewMode === 'quiz' ? 'bg-white text-rose-700 font-bold shadow-2xs' : 'text-slate-600 hover:text-slate-800'"
            >
              <span>📝 沉浸重做模式</span>
            </button>
            <button
              @click="viewMode = 'review'"
              class="px-2.5 py-1 rounded-md font-medium transition cursor-pointer flex items-center gap-1"
              :class="viewMode === 'review' ? 'bg-white text-slate-800 font-bold shadow-2xs' : 'text-slate-600 hover:text-slate-800'"
            >
              <span>📖 解析背诵模式</span>
            </button>
          </div>

          <label class="flex items-center gap-1.5 text-xs text-slate-600 cursor-pointer select-none">
            <input 
              type="checkbox" 
              v-model="includeMastered" 
              class="rounded text-rose-600 focus:ring-rose-500 border-slate-300 w-3.5 h-3.5" 
            />
            <span>显示已掌握</span>
          </label>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="bg-white rounded-2xl p-12 text-center border border-slate-200 shadow-2xs">
      <div class="inline-block animate-spin w-8 h-8 border-3 border-rose-500 border-t-transparent rounded-full mb-3"></div>
      <p class="text-sm text-slate-500">正在整理错题本...</p>
    </div>

    <!-- Empty State -->
    <div v-else-if="wrongQuestions.length === 0" class="bg-white rounded-2xl p-12 text-center border border-slate-200 shadow-2xs">
      <div class="w-16 h-16 bg-emerald-50 text-emerald-500 rounded-full flex items-center justify-center mx-auto mb-3">
        <CheckCircle2 class="w-8 h-8" />
      </div>
      <h3 class="text-base font-bold text-slate-800">当前没有待攻克错题！</h3>
      <p class="text-xs text-slate-500 mt-1 max-w-sm mx-auto">太棒了！所有做过的题全部正确，或已全部攻克掌握。继续刷题保持手感吧！</p>
      <button 
        @click="emit('start-practice')"
        class="mt-4 px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold rounded-xl transition cursor-pointer shadow-xs inline-flex items-center gap-1.5"
      >
        <Play class="w-3.5 h-3.5 fill-white" />
        <span>继续练习刷题</span>
      </button>
    </div>

    <!-- Wrong Questions List -->
    <div v-else class="space-y-4">
      <div
        v-for="(q, qIdx) in wrongQuestions"
        :key="q.wrong_id"
        class="bg-white rounded-2xl p-4 sm:p-6 border border-slate-200 shadow-2xs transition hover:border-slate-300"
        :class="{ 'opacity-65 bg-slate-50/70': q.is_mastered }"
      >
        <!-- Card Header -->
        <div class="flex items-center justify-between pb-3 border-b border-slate-100 gap-2">
          <div class="flex items-center gap-2 flex-wrap">
            <span class="text-xs font-bold text-slate-400">#{{ qIdx + 1 }} · 题号 {{ q.question_num }}</span>
            <span v-if="q.workbook_name" class="px-2 py-0.5 text-xs font-semibold rounded-md bg-purple-50 text-purple-700 border border-purple-200">
              {{ q.workbook_name }}
            </span>
            <span class="px-2 py-0.5 text-xs font-semibold rounded-md bg-blue-50 text-blue-700 border border-blue-100">
              {{ q.category }}
            </span>
            <span 
              class="px-2 py-0.5 text-xs font-semibold rounded-md"
              :class="q.question_type === 'multiple' ? 'bg-amber-50 text-amber-700' : 'bg-emerald-50 text-emerald-700'"
            >
              {{ q.question_type === 'multiple' ? '多选题' : '单选题' }}
            </span>
            <span class="px-2 py-0.5 text-xs font-bold rounded-md bg-rose-50 text-rose-600 border border-rose-200">
              做错 {{ q.wrong_count }} 次
            </span>
          </div>

          <!-- Actions on Card -->
          <div class="flex items-center gap-1.5">
            <!-- 单题重做按钮 -->
            <button
              @click="startRedoSingleQuestion(q)"
              class="px-2 py-1 rounded-lg border border-slate-200 text-xs font-medium text-slate-600 hover:text-rose-600 hover:bg-rose-50 hover:border-rose-200 transition cursor-pointer flex items-center gap-1"
              title="清空选项并重新做本题"
            >
              <RotateCcw class="w-3.5 h-3.5" />
              <span class="hidden sm:inline">重做本题</span>
            </button>

            <!-- 笔记按钮 -->
            <button
              @click="openNote(q)"
              class="p-1.5 rounded-lg border text-xs font-medium flex items-center gap-1 transition cursor-pointer"
              :class="q.note_content ? 'bg-blue-50 border-blue-200 text-blue-600' : 'border-slate-200 text-slate-500 hover:bg-slate-50'"
              title="错题考点笔记"
            >
              <FileText class="w-3.5 h-3.5" />
              <span class="hidden sm:inline">{{ q.note_content ? '笔记' : '加笔记' }}</span>
            </button>

            <!-- 移出错题集 / 重新收录按钮 -->
            <button
              @click="toggleMaster(q)"
              class="px-2.5 py-1 text-xs font-medium rounded-lg border transition cursor-pointer flex items-center gap-1 active:scale-95"
              :class="[
                q.is_mastered 
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-300 font-semibold' 
                  : 'bg-slate-50 hover:bg-rose-50 hover:text-rose-700 hover:border-rose-200 text-slate-700 border-slate-200'
              ]"
              :title="q.is_mastered ? '点击重新收录回错题本' : '攻克本题，直接移出错题集'"
            >
              <CheckCircle2 v-if="!q.is_mastered" class="w-3.5 h-3.5 text-slate-400 group-hover:text-rose-600" />
              <RotateCcw v-else class="w-3.5 h-3.5 text-emerald-600" />
              <span>{{ q.is_mastered ? '已移出(点击恢复)' : '移出错题集' }}</span>
            </button>
          </div>
        </div>

        <!-- Stem -->
        <div class="mt-3 text-sm sm:text-base font-medium text-slate-900 leading-relaxed">
          <span class="font-bold text-rose-600 mr-1">{{ q.question_num }}.</span>
          <span>{{ q.stem }}</span>
        </div>

        <!-- ============================================== -->
        <!-- 模式 A：自测作答中 (隐去答案与解析，可交互点击选项) -->
        <!-- ============================================== -->
        <div v-if="isQuestionTesting(q)" class="mt-4 space-y-2.5">
          <div
            v-for="opt in q.options"
            :key="opt.key"
            @click="handleOptionClick(q, opt.key)"
            class="group p-3 rounded-xl border-2 transition-all flex items-start gap-3 cursor-pointer select-none"
            :class="[
              getRedoState(q.question_id).selected.includes(opt.key)
                ? 'border-rose-500 bg-rose-50/50 text-slate-900 shadow-2xs'
                : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50 text-slate-700'
            ]"
          >
            <div
              class="w-6 h-6 rounded-lg flex items-center justify-center font-bold text-xs shrink-0 transition"
              :class="[
                getRedoState(q.question_id).selected.includes(opt.key)
                  ? 'bg-rose-600 text-white'
                  : 'bg-slate-100 group-hover:bg-slate-200 text-slate-700'
              ]"
            >
              {{ opt.key }}
            </div>
            <div class="text-xs sm:text-sm leading-relaxed pt-0.5 flex-1">
              {{ opt.value }}
            </div>
          </div>

          <!-- 多选题确认提交工具条 -->
          <div 
            v-if="q.question_type === 'multiple'"
            class="pt-3 flex items-center justify-between gap-3 border-t border-slate-100"
          >
            <div class="text-xs text-slate-500">
              已选：<span class="font-bold text-rose-600 font-mono">{{ getRedoState(q.question_id).selected.join('') || '未选' }}</span>
            </div>
            <button
              @click="submitRedo(q)"
              class="px-4 py-2 bg-rose-600 hover:bg-rose-700 active:bg-rose-800 text-white font-semibold text-xs rounded-xl shadow-2xs flex items-center gap-1.5 transition cursor-pointer"
            >
              <Send class="w-3.5 h-3.5" />
              <span>确认提交作答</span>
            </button>
          </div>
        </div>

        <!-- ============================================== -->
        <!-- 模式 B：已提交作答 或 解析背诵模式 (展示对错反馈与解析) -->
        <!-- ============================================== -->
        <div v-else class="mt-4 space-y-2">
          <!-- 选项静态/对比展示 -->
          <div
            v-for="opt in q.options"
            :key="opt.key"
            class="p-2.5 rounded-xl border text-xs sm:text-sm flex items-start gap-2.5"
            :class="[
              q.answer.includes(opt.key)
                ? 'border-emerald-400 bg-emerald-50/70 text-emerald-950 font-medium'
                : (
                    (redoStates[q.question_id]?.userAns || q.last_wrong_answer || '').includes(opt.key)
                      ? 'border-rose-400 bg-rose-50/70 text-rose-950'
                      : 'border-slate-100 bg-slate-50/40 text-slate-600'
                  )
            ]"
          >
            <span 
              class="w-5 h-5 rounded-md flex items-center justify-center font-bold text-xs shrink-0"
              :class="[
                q.answer.includes(opt.key) 
                  ? 'bg-emerald-600 text-white' 
                  : (
                      (redoStates[q.question_id]?.userAns || q.last_wrong_answer || '').includes(opt.key)
                        ? 'bg-rose-600 text-white' 
                        : 'bg-slate-200 text-slate-700'
                    )
              ]"
            >
              {{ opt.key }}
            </span>
            <span class="flex-1">{{ opt.value }}</span>
            <div class="shrink-0">
              <Check v-if="q.answer.includes(opt.key)" class="w-4 h-4 text-emerald-600 font-bold" />
              <X v-else-if="(redoStates[q.question_id]?.userAns || q.last_wrong_answer || '').includes(opt.key)" class="w-4 h-4 text-rose-600 font-bold" />
            </div>
          </div>

          <!-- 作答结果反馈 Banner -->
          <div 
            v-if="redoStates[q.question_id]?.isSubmitted"
            class="mt-3 p-3 rounded-xl flex items-center justify-between gap-3"
            :class="redoStates[q.question_id].isCorrect ? 'bg-emerald-50 border border-emerald-200 text-emerald-900' : 'bg-rose-50 border border-rose-200 text-rose-900'"
          >
            <div class="flex items-center gap-2 text-xs sm:text-sm">
              <span class="text-base">{{ redoStates[q.question_id].isCorrect ? '🎉' : '❌' }}</span>
              <span class="font-bold">
                {{ redoStates[q.question_id].isCorrect ? '重做正确！已记录最新作答！' : '回答仍有偏差，最新作答已实时记录！' }}
              </span>
              <span class="text-xs opacity-80">
                (本次作答: <strong class="font-mono">{{ redoStates[q.question_id].userAns }}</strong>)
              </span>
            </div>

            <div class="flex items-center gap-2 shrink-0">
              <button
                v-if="redoStates[q.question_id].isCorrect && !q.is_mastered"
                @click="toggleMaster(q)"
                class="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-lg shadow-2xs transition cursor-pointer flex items-center gap-1 active:scale-95"
                title="已攻克并移出错题集"
              >
                <CheckCircle2 class="w-3.5 h-3.5" />
                <span>移出错题集</span>
              </button>

              <button
                @click="startRedoSingleQuestion(q)"
                class="px-2 py-1 bg-white hover:bg-slate-100 border border-slate-200 text-slate-700 text-xs rounded-lg transition cursor-pointer flex items-center gap-1 active:scale-95"
              >
                <RotateCcw class="w-3 h-3 text-slate-500" />
                <span>再做一次</span>
              </button>
            </div>
          </div>

          <!-- 答案与解析 -->
          <div class="mt-3 p-3.5 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
            <div class="flex items-center justify-between flex-wrap gap-2 text-xs font-semibold">
              <div class="flex items-center gap-4">
                <span :class="redoStates[q.question_id]?.isSubmitted ? (redoStates[q.question_id]?.isCorrect ? 'text-emerald-700 font-bold' : 'text-rose-600 font-bold') : 'text-rose-600'">
                  {{ redoStates[q.question_id]?.isSubmitted ? (redoStates[q.question_id]?.isCorrect ? '最新作答：' + redoStates[q.question_id].userAns + ' (正确)' : '最新作答：' + redoStates[q.question_id].userAns + ' (错选)') : ('历史错选：' + (q.last_wrong_answer || '未记录')) }}
                </span>
                <span class="text-emerald-700 font-bold">
                  正确答案：{{ q.answer }}
                </span>
              </div>
              <button
                v-if="!redoStates[q.question_id]?.isSubmitted"
                @click="startRedoSingleQuestion(q)"
                class="text-xs text-rose-600 hover:text-rose-700 font-medium flex items-center gap-1 cursor-pointer"
              >
                <RotateCcw class="w-3 h-3" />
                <span>清空重做此题</span>
              </button>
            </div>
            <div class="text-xs text-slate-600 leading-relaxed border-t border-slate-200/60 pt-2">
              <strong class="text-slate-800">【试题考点解析】</strong>{{ q.explanation }}
            </div>
          </div>
        </div>

        <!-- Note banner if present -->
        <div v-if="q.note_content" class="mt-2.5 p-2.5 bg-amber-50/70 border border-amber-200 rounded-xl text-xs text-amber-900 flex items-start gap-2">
          <FileText class="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <div class="flex-1">
            <strong class="font-bold text-amber-800">考点笔记：</strong>{{ q.note_content }}
          </div>
        </div>
      </div>
    </div>

    <!-- Note Modal -->
    <NoteModal 
      :show="showNoteModal"
      :question="activeNoteQuestion"
      @close="showNoteModal = false"
      @saved="handleNoteSaved"
    />
  </div>
</template>
