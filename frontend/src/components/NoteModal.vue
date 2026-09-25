<script setup>
import { ref, watch } from 'vue';
import { api } from '../api';
import { X, FileText, Check, Sparkles } from 'lucide-vue-next';

const props = defineProps({
  show: Boolean,
  question: {
    type: Object,
    default: null
  }
});

const emit = defineEmits(['close', 'saved']);

const content = ref('');
const saving = ref(false);
const saveSuccess = ref(false);

watch(() => props.question, (q) => {
  if (q) {
    content.value = q.note_content || '';
  }
}, { immediate: true });

const handleSave = async () => {
  if (!props.question) return;
  saving.value = true;
  try {
    await api.saveNote(props.question.id, content.value);
    props.question.note_content = content.value;
    props.question.has_note = !!content.value.trim();
    saveSuccess.value = true;
    emit('saved', { questionId: props.question.id, content: content.value });
    setTimeout(() => {
      saveSuccess.value = false;
      emit('close');
    }, 600);
  } catch (err) {
    alert('保存笔记失败: ' + err.message);
  } finally {
    saving.value = false;
  }
};

const insertTemplate = (prefix) => {
  if (content.value && !content.value.endsWith('\n')) {
    content.value += '\n';
  }
  content.value += prefix + ' ';
};
</script>

<template>
  <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-200">
    <div class="bg-white rounded-2xl max-w-lg w-full p-5 sm:p-6 shadow-2xl relative border border-slate-100 flex flex-col max-h-[90vh]">
      <!-- Header -->
      <div class="flex items-center justify-between pb-3 border-b border-slate-100">
        <div class="flex items-center gap-2">
          <div class="p-2 bg-amber-50 text-amber-600 rounded-xl">
            <FileText class="w-5 h-5" />
          </div>
          <div>
            <h3 class="font-bold text-slate-800 text-base">题目专属笔记</h3>
            <p class="text-xs text-slate-400">第 {{ question?.question_num }} 题 · 【{{ question?.category }}】</p>
          </div>
        </div>
        <button 
          @click="emit('close')"
          class="p-1.5 text-slate-400 hover:text-slate-600 rounded-full hover:bg-slate-100 transition cursor-pointer"
        >
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Question Preview Snippet -->
      <div class="mt-3 p-2.5 bg-slate-50 rounded-xl text-xs text-slate-600 line-clamp-2 border border-slate-100">
        <span class="font-semibold text-slate-700">题干：</span>{{ question?.stem }}
      </div>

      <!-- Quick Template Tags -->
      <div class="flex flex-wrap items-center gap-1.5 mt-3">
        <span class="text-[11px] text-slate-400 flex items-center gap-0.5">
          <Sparkles class="w-3 h-3 text-amber-500" /> 快捷模版：
        </span>
        <button 
          @click="insertTemplate('【核心考点】')"
          class="text-[11px] px-2 py-0.5 bg-slate-100 hover:bg-amber-50 hover:text-amber-700 text-slate-600 rounded-md border border-slate-200 transition cursor-pointer"
        >
          考点
        </button>
        <button 
          @click="insertTemplate('【避坑提醒】')"
          class="text-[11px] px-2 py-0.5 bg-slate-100 hover:bg-rose-50 hover:text-rose-700 text-slate-600 rounded-md border border-slate-200 transition cursor-pointer"
        >
          避坑
        </button>
        <button 
          @click="insertTemplate('【记忆口诀】')"
          class="text-[11px] px-2 py-0.5 bg-slate-100 hover:bg-emerald-50 hover:text-emerald-700 text-slate-600 rounded-md border border-slate-200 transition cursor-pointer"
        >
          口诀
        </button>
        <button 
          @click="insertTemplate('【真题联想】')"
          class="text-[11px] px-2 py-0.5 bg-slate-100 hover:bg-indigo-50 hover:text-indigo-700 text-slate-600 rounded-md border border-slate-200 transition cursor-pointer"
        >
          联想
        </button>
      </div>

      <!-- Textarea -->
      <div class="mt-3 flex-1 flex flex-col">
        <textarea
          v-model="content"
          placeholder="写下你的记忆理解、易混点辨析或老师强调的重点..."
          class="w-full h-44 p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-800 placeholder-slate-400 focus:outline-hidden focus:ring-2 focus:ring-amber-500/20 focus:border-amber-400 focus:bg-white resize-none transition"
        ></textarea>
      </div>

      <!-- Action buttons -->
      <div class="mt-4 flex items-center justify-between pt-3 border-t border-slate-100">
        <span class="text-[11px] text-slate-400">
          {{ content.length }} 字
        </span>
        <div class="flex items-center gap-2">
          <button
            @click="emit('close')"
            class="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg transition cursor-pointer"
          >
            取消
          </button>
          <button
            @click="handleSave"
            :disabled="saving"
            class="px-4 py-1.5 text-xs font-semibold text-white bg-amber-600 hover:bg-amber-700 rounded-lg shadow-xs flex items-center gap-1.5 transition disabled:opacity-50 cursor-pointer"
          >
            <component :is="saveSuccess ? Check : FileText" class="w-3.5 h-3.5" />
            <span>{{ saveSuccess ? '已保存！' : (saving ? '保存中...' : '保存笔记') }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
