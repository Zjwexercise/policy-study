<script setup>
import { ref, onMounted, computed } from 'vue';
import { api } from '../api';
import { 
  FileText, 
  Trash2, 
  Edit3, 
  Search, 
  Copy, 
  Check, 
  BookOpen, 
  Sparkles 
} from 'lucide-vue-next';
import NoteModal from './NoteModal.vue';

const props = defineProps({
  workbookId: {
    type: [Number, String],
    default: null
  }
});

const notes = ref([]);
const loading = ref(false);
const searchQuery = ref('');
const activeNoteQuestion = ref(null);
const showNoteModal = ref(false);
const copiedAll = ref(false);

const loadNotes = async () => {
  loading.value = true;
  try {
    const targetId = (props.workbookId && props.workbookId !== 'all') ? props.workbookId : null;
    const data = await api.getNotes(targetId);
    notes.value = data;
  } catch (err) {
    console.error('获取笔记失败', err);
  } finally {
    loading.value = false;
  }
};

const filteredNotes = computed(() => {
  if (!searchQuery.value.trim()) return notes.value;
  const q = searchQuery.value.toLowerCase();
  return notes.value.filter(n => 
    n.content.toLowerCase().includes(q) ||
    n.stem.toLowerCase().includes(q) ||
    n.category.toLowerCase().includes(q)
  );
});

const openEditModal = (note) => {
  activeNoteQuestion.value = {
    id: note.question_id,
    question_num: note.question_num,
    category: note.category,
    stem: note.stem,
    note_content: note.content,
    has_note: true
  };
  showNoteModal.value = true;
};

const deleteNote = async (note) => {
  if (!confirm('确定要删除这条笔记吗？')) return;
  try {
    await api.saveNote(note.question_id, '');
    notes.value = notes.value.filter(n => n.note_id !== note.note_id);
  } catch (err) {
    alert('删除笔记失败: ' + err.message);
  }
};

const copyAllNotes = () => {
  if (notes.value.length === 0) return;
  const text = notes.value.map((n, idx) => {
    return `【${n.category} 第${n.question_num}题】\n题干：${n.stem}\n答案：${n.answer}\n我的笔记：\n${n.content}\n-----------------------`;
  }).join('\n\n');

  navigator.clipboard.writeText(text);
  copiedAll.value = true;
  setTimeout(() => {
    copiedAll.value = false;
  }, 2000);
};

onMounted(() => {
  loadNotes();
});
</script>

<template>
  <div class="max-w-4xl mx-auto px-3 sm:px-6 py-4 pb-24 lg:pb-12">
    <!-- Header -->
    <div class="bg-white rounded-2xl p-4 sm:p-5 border border-slate-200 shadow-2xs mb-4">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
        <div class="flex items-center gap-2.5">
          <div class="p-2.5 bg-amber-50 text-amber-600 rounded-xl">
            <FileText class="w-5 h-5" />
          </div>
          <div>
            <h2 class="text-base sm:text-lg font-bold text-slate-800">考研政治专属考点笔记</h2>
            <p class="text-xs text-slate-500">考前冲刺、错点串讲、高频易混考点总结宝库</p>
          </div>
        </div>

        <button
          v-if="notes.length > 0"
          @click="copyAllNotes"
          class="px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-xl flex items-center gap-1.5 transition shadow-2xs cursor-pointer"
        >
          <component :is="copiedAll ? Check : Copy" class="w-3.5 h-3.5" />
          <span>{{ copiedAll ? '已复制全部笔记！' : '一键导出全部笔记' }}</span>
        </button>
      </div>

      <!-- Search bar -->
      <div class="pt-3">
        <div class="relative">
          <Search class="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input 
            type="text" 
            v-model="searchQuery"
            placeholder="搜索笔记关键词、考点、题干内容..."
            class="w-full bg-slate-50 border border-slate-200 text-xs sm:text-sm pl-9 pr-4 py-2 rounded-xl focus:outline-hidden focus:ring-2 focus:ring-amber-500/20 focus:border-amber-400"
          />
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="bg-white rounded-2xl p-12 text-center border border-slate-200 shadow-2xs">
      <div class="inline-block animate-spin w-8 h-8 border-3 border-amber-500 border-t-transparent rounded-full mb-3"></div>
      <p class="text-sm text-slate-500">加载笔记中...</p>
    </div>

    <!-- Empty -->
    <div v-else-if="notes.length === 0" class="bg-white rounded-2xl p-12 text-center border border-slate-200 shadow-2xs">
      <div class="w-16 h-16 bg-amber-50 text-amber-500 rounded-full flex items-center justify-center mx-auto mb-3">
        <Sparkles class="w-8 h-8" />
      </div>
      <h3 class="text-base font-bold text-slate-800">还没有记录任何笔记</h3>
      <p class="text-xs text-slate-500 mt-1">在刷题或错题本中点击“记笔记”，提炼属于你自己的高分必背点！</p>
    </div>

    <!-- Notes List -->
    <div v-else class="space-y-4">
      <div
        v-for="note in filteredNotes"
        :key="note.note_id"
        class="bg-white rounded-2xl p-4 sm:p-5 border border-slate-200 shadow-2xs hover:border-amber-200 transition"
      >
        <div class="flex items-center justify-between pb-2 border-b border-slate-100 gap-2">
          <div class="flex items-center gap-2">
            <span class="px-2 py-0.5 text-xs font-semibold rounded-md bg-amber-50 text-amber-700 border border-amber-200">
              {{ note.category }} · 第 {{ note.question_num }} 题
            </span>
            <span class="text-[11px] text-slate-400">
              {{ note.workbook_name }}
            </span>
          </div>

          <div class="flex items-center gap-1">
            <button
              @click="openEditModal(note)"
              class="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition cursor-pointer"
              title="编辑笔记"
            >
              <Edit3 class="w-4 h-4" />
            </button>
            <button
              @click="deleteNote(note)"
              class="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition cursor-pointer"
              title="删除笔记"
            >
              <Trash2 class="w-4 h-4" />
            </button>
          </div>
        </div>

        <!-- Note content -->
        <div class="mt-3 p-3 bg-amber-50/60 border border-amber-100/80 rounded-xl text-xs sm:text-sm text-amber-950 font-medium whitespace-pre-line leading-relaxed">
          {{ note.content }}
        </div>

        <!-- Original Question stem reference -->
        <div class="mt-3 text-xs text-slate-500 line-clamp-2">
          <strong class="text-slate-600">关联题目：</strong>{{ note.stem }}
        </div>
      </div>
    </div>

    <NoteModal 
      :show="showNoteModal"
      :question="activeNoteQuestion"
      @close="showNoteModal = false"
      @saved="loadNotes"
    />
  </div>
</template>
