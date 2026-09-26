<script setup>
import { X, Check, AlertCircle, Star, FileText, Swords } from 'lucide-vue-next';

defineProps({
  show: Boolean,
  questions: {
    type: Array,
    default: () => []
  },
  currentIndex: {
    type: Number,
    default: 0
  }
});

const emit = defineEmits(['close', 'jump']);
</script>

<template>
  <div v-if="show" class="fixed inset-0 z-50 flex items-end sm:items-center justify-center sm:p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-200">
    <div class="bg-white rounded-t-3xl sm:rounded-2xl max-w-xl w-full p-5 sm:p-6 shadow-2xl relative border border-slate-100 flex flex-col max-h-[85vh] sm:max-h-[80vh]">
      <!-- Header -->
      <div class="flex items-center justify-between pb-3 border-b border-slate-100">
        <div>
          <h3 class="font-bold text-slate-800 text-base">答题卡</h3>
          <p class="text-xs text-slate-500 mt-0.5">共 {{ questions.length }} 题，点击题号快速跳转</p>
        </div>
        <button 
          @click="emit('close')"
          class="p-1.5 text-slate-400 hover:text-slate-600 rounded-full hover:bg-slate-100 transition cursor-pointer"
        >
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Legend -->
      <div class="flex items-center gap-3 py-2.5 text-xs text-slate-500 border-b border-slate-100 shrink-0 flex-wrap">
        <div class="flex items-center gap-1.5">
          <div class="w-3.5 h-3.5 rounded-md bg-emerald-500"></div>
          <span>正确</span>
        </div>
        <div class="flex items-center gap-1.5">
          <div class="w-3.5 h-3.5 rounded-md bg-rose-500"></div>
          <span>错误</span>
        </div>
        <div class="flex items-center gap-1.5">
          <div class="w-3.5 h-3.5 rounded-md bg-slate-100 border border-slate-300"></div>
          <span>未答</span>
        </div>
        <div class="flex items-center gap-1.5">
          <Star class="w-3.5 h-3.5 text-amber-500 fill-amber-500" />
          <span>收藏</span>
        </div>
        <div class="flex items-center gap-1.5">
          <Swords class="w-3.5 h-3.5 text-rose-800" />
          <span>已斩</span>
        </div>
        <div class="flex items-center gap-1.5">
          <FileText class="w-3.5 h-3.5 text-blue-500" />
          <span>有笔记</span>
        </div>
      </div>

      <!-- Grid of Questions -->
      <div class="overflow-y-auto py-4 flex-1 pr-1">
        <div class="grid grid-cols-5 sm:grid-cols-8 gap-2.5">
          <button
            v-for="(q, idx) in questions"
            :key="q.id"
            @click="emit('jump', idx); emit('close');"
            class="relative h-11 rounded-xl flex items-center justify-center font-bold text-sm transition transform active:scale-95 cursor-pointer"
            :class="[
              currentIndex === idx ? 'ring-2 ring-rose-500 ring-offset-2' : '',
              q.user_answer !== null && q.user_answer !== undefined && q.user_answer !== ''
                ? (q.is_correct 
                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-300 font-semibold' 
                    : 'bg-rose-50 text-rose-700 border border-rose-300 font-semibold')
                : 'bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200'
            ]"
          >
            <span>{{ q.question_num }}</span>

            <!-- Swords icon badge -->
            <Swords 
              v-if="q.is_killed" 
              class="w-2.5 h-2.5 text-rose-800 absolute top-1 left-1" 
            />

            <!-- Star icon badge -->
            <Star 
              v-if="q.is_starred" 
              class="w-2.5 h-2.5 text-amber-500 fill-amber-500 absolute top-1 right-1" 
            />

            <!-- Note icon badge -->
            <FileText 
              v-if="q.has_note || q.note_content" 
              class="w-2.5 h-2.5 text-blue-500 absolute bottom-1 right-1" 
            />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
