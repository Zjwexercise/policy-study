<script setup>
import { ref, watch, onMounted, computed } from 'vue';
import { api } from '../api';
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
  X
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

const categories = ['全部', '马原', '毛中特', '习思想', '史纲', '思修', '时政'];

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
  } catch (err) {
    console.error('加载错题失败', err);
  } finally {
    loading.value = false;
  }
};

watch(() => props.workbookId, loadWrongQuestions);
watch([selectedCategory, includeMastered], loadWrongQuestions);

// 标记掌握/重新标记
const toggleMaster = async (item) => {
  const nextStatus = !item.is_mastered;
  try {
    await api.toggleMasterWrong(item.question_id, nextStatus);
    item.is_mastered = nextStatus;
    if (!includeMastered.value && nextStatus) {
      // 动画淡出后从列表移出
      wrongQuestions.value = wrongQuestions.value.filter(q => q.question_id !== item.question_id);
    }
  } catch (err) {
    alert('操作失败: ' + err.message);
  }
};

// 清空错题本
const handleClearAll = async () => {
  if (!confirm('确定要清空错题记录吗？这不会影响练习册题目本身。')) return;
  try {
    await api.clearWrongBook(props.workbookId);
    wrongQuestions.value = [];
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
  <div class="max-w-4xl mx-auto px-3 sm:px-6 py-4 pb-24 lg:pb-12">
    <!-- Header & Statistics -->
    <div class="bg-white rounded-2xl p-4 sm:p-5 border border-slate-200 shadow-2xs mb-4">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
        <div class="flex items-center gap-2.5">
          <div class="p-2.5 bg-rose-50 text-rose-600 rounded-xl">
            <AlertCircle class="w-5 h-5" />
          </div>
          <div>
            <h2 class="text-base sm:text-lg font-bold text-slate-800">考研政治错题本</h2>
            <p class="text-xs text-slate-500">智能收录做错题目，重点消灭薄弱考点与陷阱</p>
          </div>
        </div>

        <div class="flex items-center gap-2">
          <button
            v-if="wrongQuestions.length > 0"
            @click="handleClearAll"
            class="px-3 py-1.5 text-xs text-rose-600 hover:bg-rose-50 border border-rose-200 rounded-lg transition cursor-pointer flex items-center gap-1"
          >
            <Trash2 class="w-3.5 h-3.5" />
            <span>清空错题</span>
          </button>
        </div>
      </div>

      <!-- Filters -->
      <div class="flex flex-wrap items-center justify-between gap-3 pt-3">
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

        <label class="flex items-center gap-1.5 text-xs text-slate-600 cursor-pointer select-none">
          <input 
            type="checkbox" 
            v-model="includeMastered" 
            class="rounded text-rose-600 focus:ring-rose-500 border-slate-300 w-3.5 h-3.5" 
          />
          <span>显示已掌握题目</span>
        </label>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="bg-white rounded-2xl p-12 text-center border border-slate-200 shadow-2xs">
      <div class="inline-block animate-spin w-8 h-8 border-3 border-rose-500 border-t-transparent rounded-full mb-3"></div>
      <p class="text-sm text-slate-500">加载错题中...</p>
    </div>

    <!-- Empty State -->
    <div v-else-if="wrongQuestions.length === 0" class="bg-white rounded-2xl p-12 text-center border border-slate-200 shadow-2xs">
      <div class="w-16 h-16 bg-emerald-50 text-emerald-500 rounded-full flex items-center justify-center mx-auto mb-3">
        <CheckCircle2 class="w-8 h-8" />
      </div>
      <h3 class="text-base font-bold text-slate-800">当前没有错题！</h3>
      <p class="text-xs text-slate-500 mt-1">太棒了！所有已做题目全部正确，或所有错题已被攻克掌握。</p>
    </div>

    <!-- Wrong Questions List -->
    <div v-else class="space-y-4">
      <div
        v-for="q in wrongQuestions"
        :key="q.wrong_id"
        class="bg-white rounded-2xl p-4 sm:p-6 border border-slate-200 shadow-2xs transition hover:border-slate-300"
        :class="{ 'opacity-60 bg-slate-50': q.is_mastered }"
      >
        <!-- Header -->
        <div class="flex items-center justify-between pb-3 border-b border-slate-100 gap-2">
          <div class="flex items-center gap-2 flex-wrap">
            <span class="text-xs font-bold text-slate-400">题号 {{ q.question_num }}</span>
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

          <!-- Actions -->
          <div class="flex items-center gap-1.5">
            <button
              @click="openNote(q)"
              class="p-1.5 rounded-lg border text-xs font-medium flex items-center gap-1 transition cursor-pointer"
              :class="q.note_content ? 'bg-blue-50 border-blue-200 text-blue-600' : 'border-slate-200 text-slate-500 hover:bg-slate-50'"
            >
              <FileText class="w-3.5 h-3.5" />
              <span class="hidden sm:inline">{{ q.note_content ? '查看笔记' : '添加笔记' }}</span>
            </button>

            <button
              @click="toggleMaster(q)"
              class="px-2.5 py-1 text-xs font-medium rounded-lg border transition cursor-pointer flex items-center gap-1"
              :class="[
                q.is_mastered 
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-300' 
                  : 'bg-slate-100 hover:bg-emerald-50 hover:text-emerald-700 hover:border-emerald-200 text-slate-700 border-slate-200'
              ]"
            >
              <CheckCircle2 class="w-3.5 h-3.5" />
              <span>{{ q.is_mastered ? '已掌握' : '标为已掌握' }}</span>
            </button>
          </div>
        </div>

        <!-- Stem -->
        <div class="mt-3 text-sm sm:text-base font-medium text-slate-800 leading-relaxed">
          {{ q.stem }}
        </div>

        <!-- Options -->
        <div class="mt-3 space-y-2">
          <div
            v-for="opt in q.options"
            :key="opt.key"
            class="p-2.5 rounded-xl border text-xs sm:text-sm flex items-start gap-2.5"
            :class="[
              q.answer.includes(opt.key)
                ? 'border-emerald-400 bg-emerald-50/60 text-emerald-950 font-medium'
                : (q.last_wrong_answer && q.last_wrong_answer.includes(opt.key)
                    ? 'border-rose-400 bg-rose-50/60 text-rose-950'
                    : 'border-slate-100 bg-slate-50/40 text-slate-600')
            ]"
          >
            <span 
              class="w-5 h-5 rounded-md flex items-center justify-center font-bold text-xs shrink-0"
              :class="q.answer.includes(opt.key) ? 'bg-emerald-600 text-white' : (q.last_wrong_answer && q.last_wrong_answer.includes(opt.key) ? 'bg-rose-600 text-white' : 'bg-slate-200 text-slate-700')"
            >
              {{ opt.key }}
            </span>
            <span class="flex-1">{{ opt.value }}</span>
          </div>
        </div>

        <!-- Answer and Explanation banner -->
        <div class="mt-4 p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
          <div class="flex items-center gap-4 text-xs font-semibold">
            <span class="text-rose-600">你的错选：{{ q.last_wrong_answer || '未记录' }}</span>
            <span class="text-emerald-700">正确答案：{{ q.answer }}</span>
          </div>
          <div class="text-xs text-slate-600 leading-relaxed border-t border-slate-200/60 pt-2">
            <strong class="text-slate-700">【解析】</strong>{{ q.explanation }}
          </div>
        </div>

        <!-- Note banner if present -->
        <div v-if="q.note_content" class="mt-2 p-2.5 bg-amber-50/70 border border-amber-200 rounded-xl text-xs text-amber-900">
          <span class="font-bold text-amber-800">笔记：</span>{{ q.note_content }}
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
