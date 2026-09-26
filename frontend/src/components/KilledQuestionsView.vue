<script setup>
import { ref, watch, onMounted, computed } from 'vue';
import { api } from '../api';
import { 
  Swords, 
  RotateCcw, 
  Sparkles, 
  Play, 
  Check, 
  FileText, 
  Search,
  CheckCircle2,
  Trash2,
  BookOpen
} from 'lucide-vue-next';
import NoteModal from './NoteModal.vue';

const props = defineProps({
  workbookId: {
    type: [Number, String],
    default: 'all'
  }
});

const emit = defineEmits(['start-practice']);

const killedQuestions = ref([]);
const loading = ref(false);
const selectedCategory = ref('全部');
const searchKeyword = ref('');
const activeNoteQuestion = ref(null);
const showNoteModal = ref(false);

const categories = ['全部', '马原', '毛中特', '史纲', '思修', '时政'];

const loadKilledQuestions = async () => {
  loading.value = true;
  try {
    const params = {};
    if (props.workbookId && props.workbookId !== 'all') params.workbook_id = props.workbookId;
    if (selectedCategory.value !== '全部') params.category = selectedCategory.value;
    if (searchKeyword.value.trim()) params.keyword = searchKeyword.value.trim();

    const data = await api.getKilledQuestions(params);
    killedQuestions.value = data;
  } catch (err) {
    console.error('加载斩题本失败', err);
  } finally {
    loading.value = false;
  }
};

watch(() => props.workbookId, loadKilledQuestions);
watch(selectedCategory, loadKilledQuestions);

let searchTimer = null;
const handleSearchInput = () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(loadKilledQuestions, 300);
};

// 撤销斩杀（复活题目）
const reviveQuestion = async (item) => {
  try {
    const targetWbId = item.workbook_id || props.workbookId;
    await api.toggleKillQuestion(targetWbId, item.id, false);
    item.is_killed = 0;
    // 从列表中即时剔除
    killedQuestions.value = killedQuestions.value.filter(q => q.id !== item.id);
  } catch (err) {
    alert('复活失败: ' + err.message);
  }
};

// 全部复活（清空斩题本）
const handleReviveAll = async () => {
  if (!confirm('确定要一键复活所有已斩杀的熟题吗？复活后它们将重新出现在常规刷题列表中。')) return;
  try {
    await api.clearKilledQuestions(props.workbookId);
    killedQuestions.value = [];
  } catch (err) {
    alert('一键复活失败: ' + err.message);
  }
};

const openNote = (q) => {
  activeNoteQuestion.value = {
    id: q.id,
    question_num: q.question_num,
    category: q.category,
    stem: q.stem,
    note_content: q.note_content,
    has_note: !!q.note_content
  };
  showNoteModal.value = true;
};

const handleNoteSaved = (e) => {
  const target = killedQuestions.value.find(q => q.id === e.questionId);
  if (target) {
    target.note_content = e.content;
  }
};

onMounted(() => {
  loadKilledQuestions();
});
</script>

<template>
  <div class="max-w-4xl mx-auto px-3 sm:px-6 py-4 pb-24 lg:pb-12">
    <!-- Header Banner -->
    <div class="bg-white rounded-2xl p-4 sm:p-5 border border-slate-200 shadow-2xs mb-4">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div class="flex items-start sm:items-center gap-3">
          <div class="p-2.5 sm:p-3 bg-linear-to-tr from-slate-900 to-slate-700 text-rose-400 rounded-xl shadow-xs shrink-0">
            <Swords class="w-6 h-6 sm:w-7 sm:h-7" />
          </div>
          <div>
            <div class="flex items-center gap-2 flex-wrap">
              <h2 class="text-base sm:text-lg font-bold text-slate-900">熟题斩杀本 (已彻底掌握题库)</h2>
              <span class="px-2 py-0.5 text-xs font-semibold rounded-md bg-rose-50 text-rose-700 border border-rose-200">
                已斩 {{ killedQuestions.length }} 题
              </span>
            </div>
            <p class="text-xs text-slate-500 mt-0.5">
              已被斩杀的题目在常规刷题中默认隐藏，不用每次重复刷熟悉的题；随时点击“复活”即可放回刷题库。
            </p>
          </div>
        </div>

        <div class="flex items-center gap-2 self-end sm:self-auto shrink-0">
          <button
            v-if="killedQuestions.length > 0"
            @click="handleReviveAll"
            class="px-3 py-1.5 rounded-lg border border-slate-200 bg-slate-50 hover:bg-slate-100 text-slate-700 text-xs font-medium flex items-center gap-1.5 transition cursor-pointer"
            title="将当前已斩杀的熟题全部复活，重新放回题库"
          >
            <RotateCcw class="w-3.5 h-3.5 text-slate-500" />
            <span>一键全部复活</span>
          </button>

          <button
            @click="emit('start-practice')"
            class="px-3.5 py-1.5 bg-rose-600 hover:bg-rose-700 active:bg-rose-800 text-white text-xs font-semibold rounded-lg shadow-xs flex items-center gap-1.5 transition cursor-pointer"
          >
            <Play class="w-3.5 h-3.5 fill-current" />
            <span>去刷未斩题目</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Filters & Search Toolbar -->
    <div class="bg-white rounded-2xl p-3 sm:p-4 border border-slate-200 shadow-2xs mb-4">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <!-- 学科分类筛选 -->
        <div class="flex items-center gap-1 overflow-x-auto py-0.5 no-scrollbar">
          <button
            v-for="cat in categories"
            :key="cat"
            @click="selectedCategory = cat"
            class="px-2.5 py-1 text-xs font-medium rounded-lg shrink-0 transition cursor-pointer"
            :class="[
              selectedCategory === cat 
                ? 'bg-slate-900 text-white font-semibold shadow-2xs' 
                : 'text-slate-600 hover:bg-slate-100'
            ]"
          >
            {{ cat }}
          </button>
        </div>

        <!-- 关键词搜索框 -->
        <div class="relative w-full sm:w-64">
          <input
            v-model="searchKeyword"
            @input="handleSearchInput"
            type="text"
            placeholder="搜索题干或考点关键词..."
            class="w-full text-xs bg-slate-50 border border-slate-200 rounded-lg pl-8 pr-3 py-1.5 text-slate-800 focus:outline-hidden focus:ring-2 focus:ring-rose-500/20"
          />
          <Search class="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2 pointer-events-none" />
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="bg-white rounded-2xl p-12 text-center border border-slate-200 shadow-2xs">
      <div class="inline-block animate-spin w-8 h-8 border-3 border-rose-500 border-t-transparent rounded-full mb-3"></div>
      <p class="text-sm text-slate-500">正在调取已斩杀题目...</p>
    </div>

    <!-- Empty State -->
    <div v-else-if="killedQuestions.length === 0" class="bg-white rounded-2xl p-12 text-center border border-slate-200 shadow-2xs">
      <div class="w-14 h-14 bg-slate-100 rounded-2xl flex items-center justify-center text-slate-400 mx-auto mb-3">
        <Swords class="w-7 h-7" />
      </div>
      <h3 class="text-base font-bold text-slate-800">斩题本空空如也</h3>
      <p class="text-xs text-slate-500 max-w-md mx-auto mt-1 leading-relaxed">
        在刷题过程中遇到已经倒背如流的简单题或必拿分题，点击题目右上角或解析下方的【<span class="font-bold text-rose-600">⚔️ 斩题</span>】按钮，即可将题目永久斩杀至此，后续刷题将不再重复出现，助你专项攻坚薄弱题！
      </p>
      <button 
        @click="emit('start-practice')"
        class="mt-4 px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold rounded-xl transition cursor-pointer"
      >
        前往刷题练习
      </button>
    </div>

    <!-- Question Cards List -->
    <div v-else class="space-y-4">
      <div 
        v-for="(item, idx) in killedQuestions" 
        :key="item.id"
        class="bg-white rounded-2xl p-4 sm:p-5 border border-slate-200 shadow-2xs hover:shadow-xs transition"
      >
        <!-- Question Meta Header -->
        <div class="flex items-center justify-between pb-3 mb-3 border-b border-slate-100 gap-2">
          <div class="flex items-center gap-1.5 flex-wrap">
            <span class="px-2 py-0.5 text-xs font-bold rounded-md bg-slate-900 text-rose-400 flex items-center gap-1">
              <Swords class="w-3 h-3" /> 已斩杀
            </span>
            <span 
              v-if="item.workbook_name"
              class="px-2 py-0.5 text-xs font-medium rounded-md bg-purple-50 text-purple-700 border border-purple-200"
            >
              {{ item.workbook_name }}
            </span>
            <span class="px-2 py-0.5 text-xs font-medium rounded-md bg-blue-50 text-blue-700 border border-blue-100">
              {{ item.category }}
            </span>
            <span 
              class="px-2 py-0.5 text-xs font-medium rounded-md"
              :class="item.question_type === 'multiple' ? 'bg-amber-50 text-amber-700 border border-amber-200' : 'bg-emerald-50 text-emerald-700 border border-emerald-200'"
            >
              {{ item.question_type === 'multiple' ? '多选题' : '单选题' }}
            </span>
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-2">
            <button
              @click="openNote(item)"
              class="px-2 py-1 text-xs font-medium rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-600 transition flex items-center gap-1 cursor-pointer"
              title="查看/编辑考点笔记"
            >
              <FileText class="w-3.5 h-3.5 text-slate-400" />
              <span>{{ item.note_content ? '查看笔记' : '添加笔记' }}</span>
            </button>

            <!-- 复活本题按钮 -->
            <button
              @click="reviveQuestion(item)"
              class="px-2.5 py-1 text-xs font-semibold rounded-lg bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-200 transition flex items-center gap-1 cursor-pointer"
              title="撤销斩杀，将此题放回常规刷题库"
            >
              <RotateCcw class="w-3.5 h-3.5 text-emerald-600" />
              <span>复活此题</span>
            </button>
          </div>
        </div>

        <!-- Stem -->
        <div class="text-sm sm:text-base font-medium text-slate-900 leading-relaxed mb-3">
          <span class="font-bold text-rose-600 mr-1.5">{{ item.question_num }}.</span>
          <span>{{ item.stem }}</span>
        </div>

        <!-- Options with highlight on correct answer -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-3">
          <div 
            v-for="opt in item.options" 
            :key="opt.key"
            class="p-2.5 rounded-xl border text-xs leading-relaxed flex items-start gap-2 select-none"
            :class="[
              item.answer.includes(opt.key)
                ? 'bg-emerald-50/80 border-emerald-300 text-emerald-950 font-medium'
                : 'bg-slate-50/40 border-slate-200/60 text-slate-500'
            ]"
          >
            <span 
              class="w-5 h-5 rounded-md flex items-center justify-center font-bold text-xs shrink-0"
              :class="item.answer.includes(opt.key) ? 'bg-emerald-600 text-white' : 'bg-slate-200 text-slate-600'"
            >
              {{ opt.key }}
            </span>
            <span class="pt-0.5 flex-1">{{ opt.value }}</span>
            <Check v-if="item.answer.includes(opt.key)" class="w-4 h-4 text-emerald-600 shrink-0 self-center" />
          </div>
        </div>

        <!-- Answer & Explanation -->
        <div class="bg-slate-50 border border-slate-100 rounded-xl p-3 text-xs text-slate-700 leading-relaxed">
          <div class="flex items-center gap-2 mb-1.5 font-bold text-slate-800">
            <span>正确答案：<strong class="font-mono text-emerald-600">{{ item.answer }}</strong></span>
            <span class="text-slate-300">|</span>
            <span class="flex items-center gap-1 text-slate-600 font-normal">
              <Sparkles class="w-3.5 h-3.5 text-amber-500" /> 名师考点精析
            </span>
          </div>
          <p class="whitespace-pre-line text-slate-600 font-normal">
            {{ item.explanation || '考查本章节核心基础知识点与核心概念。' }}
          </p>
        </div>

        <!-- Note snippet if any -->
        <div v-if="item.note_content" class="mt-2 p-2.5 bg-amber-50/70 border border-amber-200/80 rounded-xl text-xs text-amber-900">
          <span class="font-bold">我的笔记：</span>{{ item.note_content }}
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
