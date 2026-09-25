<script setup>
import { ref } from 'vue';
import { api } from '../api';
import { 
  Upload, 
  FileUp, 
  Library, 
  Trash2, 
  RotateCcw, 
  BookOpen, 
  CheckCircle2, 
  AlertCircle, 
  Edit3,
  HelpCircle,
  FileCheck
} from 'lucide-vue-next';

const props = defineProps({
  workbooks: {
    type: Array,
    default: () => []
  },
  activeWorkbookId: {
    type: [Number, String],
    default: null
  }
});

const emit = defineEmits([
  'refresh-workbooks', 
  'select-workbook', 
  'start-practice'
]);

const fileInput = ref(null);
const selectedFile = ref(null);
const customName = ref('');
const uploading = ref(false);
const uploadError = ref('');
const uploadSuccess = ref('');

// 题目校对弹窗
const inspectingWorkbook = ref(null);
const questionsList = ref([]);
const loadingQuestions = ref(false);
const editingQuestion = ref(null);

const handleFileSelect = (e) => {
  const file = e.target.files[0];
  if (file) {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      alert('请选择 PDF 格式文件');
      return;
    }
    selectedFile.value = file;
    customName.value = file.name.replace(/\.pdf$/i, '');
    uploadError.value = '';
    uploadSuccess.value = '';
  }
};

const handleDrop = (e) => {
  e.preventDefault();
  const file = e.dataTransfer.files[0];
  if (file && file.name.toLowerCase().endsWith('.pdf')) {
    selectedFile.value = file;
    customName.value = file.name.replace(/\.pdf$/i, '');
    uploadError.value = '';
  }
};

const submitUpload = async () => {
  if (!selectedFile.value) return;
  uploading.value = true;
  uploadError.value = '';
  uploadSuccess.value = '';

  try {
    const res = await api.uploadPdf(selectedFile.value, customName.value.trim());
    uploadSuccess.value = res.message || '上传并解析成功！';
    selectedFile.value = null;
    customName.value = '';
    if (fileInput.value) fileInput.value.value = '';
    emit('refresh-workbooks');
  } catch (err) {
    uploadError.value = err.message || '上传解析失败';
  } finally {
    uploading.value = false;
  }
};

const handleReset = async (wb) => {
  if (!confirm(`确定要重置【${wb.name}】的刷题进度吗？\n所有已作答记录和错题将被清空，方便您开启全新一轮“二刷”！`)) return;
  try {
    await api.resetWorkbook(wb.id);
    alert('已成功重置刷题进度！');
    emit('refresh-workbooks');
  } catch (err) {
    alert('重置失败: ' + err.message);
  }
};

const handleDelete = async (wb) => {
  if (!confirm(`确定要删除【${wb.name}】及其所有题目吗？此操作不可撤销。`)) return;
  try {
    await api.deleteWorkbook(wb.id);
    emit('refresh-workbooks');
  } catch (err) {
    alert('删除失败: ' + err.message);
  }
};

// 打开校对题目弹窗
const openInspect = async (wb) => {
  inspectingWorkbook.value = wb;
  loadingQuestions.value = true;
  try {
    const list = await api.getQuestions(wb.id, {});
    questionsList.value = list;
  } catch (err) {
    alert('加载题目失败: ' + err.message);
  } finally {
    loadingQuestions.value = false;
  }
};

const saveQuestionEdit = async (q) => {
  try {
    await api.updateQuestion(q.id, {
      stem: q.stem,
      options: q.options,
      answer: q.answer,
      explanation: q.explanation,
      category: q.category,
      question_type: q.question_type
    });
    editingQuestion.value = null;
    alert('题目已更新！');
  } catch (err) {
    alert('保存失败: ' + err.message);
  }
};
</script>

<template>
  <div class="max-w-5xl mx-auto px-3 sm:px-6 py-4 pb-24 lg:pb-12">
    <!-- Section 1: Upload New PDF -->
    <div class="bg-white rounded-2xl p-4 sm:p-6 border border-slate-200 shadow-2xs mb-6">
      <div class="flex items-center gap-2.5 pb-3 border-b border-slate-100">
        <div class="p-2 bg-rose-50 text-rose-600 rounded-xl">
          <FileUp class="w-5 h-5" />
        </div>
        <div>
          <h2 class="text-base sm:text-lg font-bold text-slate-800">导入考研政治习题 PDF</h2>
          <p class="text-xs text-slate-500">自动智能识别分栏、题干、选项（A/B/C/D）、参考答案与解析</p>
        </div>
      </div>

      <!-- Drag & Drop Box -->
      <div 
        @dragover.prevent
        @drop="handleDrop"
        class="mt-4 border-2 border-dashed border-slate-200 hover:border-rose-400 rounded-2xl p-6 text-center transition bg-slate-50/50"
      >
        <input 
          ref="fileInput"
          type="file" 
          accept=".pdf"
          @change="handleFileSelect"
          class="hidden" 
          id="pdf-upload"
        />

        <label for="pdf-upload" class="cursor-pointer flex flex-col items-center">
          <div class="w-12 h-12 rounded-2xl bg-white shadow-2xs border border-slate-200 flex items-center justify-center text-rose-600 mb-2">
            <Upload class="w-6 h-6" />
          </div>
          <span class="text-sm font-semibold text-slate-700">
            {{ selectedFile ? selectedFile.name : '点击选择 PDF 或将文件拖拽至此处' }}
          </span>
          <span class="text-xs text-slate-400 mt-1">
            {{ selectedFile ? `大小: ${(selectedFile.size / 1024 / 1024).toFixed(2)} MB` : '支持肖秀荣1000题、优题库、冲刺卷等电子版文本PDF' }}
          </span>
        </label>

        <!-- Selected File Actions -->
        <div v-if="selectedFile" class="mt-4 max-w-md mx-auto space-y-3">
          <div class="text-left">
            <label class="block text-xs font-semibold text-slate-700 mb-1">练习册名称：</label>
            <input 
              type="text" 
              v-model="customName"
              placeholder="请输入练习册名称..."
              class="w-full text-xs sm:text-sm bg-white border border-slate-200 rounded-xl px-3 py-2 focus:ring-2 focus:ring-rose-500/20 focus:border-rose-400"
            />
          </div>

          <button
            @click="submitUpload"
            :disabled="uploading"
            class="w-full py-2.5 bg-rose-600 hover:bg-rose-700 active:bg-rose-800 disabled:opacity-50 text-white font-semibold text-xs sm:text-sm rounded-xl shadow-xs transition flex items-center justify-center gap-2 cursor-pointer"
          >
            <span v-if="uploading" class="inline-block animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full"></span>
            <span>{{ uploading ? '智能解析排版中，请稍候...' : '开始识别并导入题库' }}</span>
          </button>
        </div>

        <!-- Feedback Alert -->
        <div v-if="uploadSuccess" class="mt-3 p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800 flex items-center justify-center gap-1.5">
          <CheckCircle2 class="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{{ uploadSuccess }}</span>
        </div>
        <div v-if="uploadError" class="mt-3 p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 flex items-center justify-center gap-1.5">
          <AlertCircle class="w-4 h-4 text-rose-600 shrink-0" />
          <span>{{ uploadError }}</span>
        </div>
      </div>
    </div>

    <!-- Section 2: Workbooks List -->
    <div>
      <!-- 🌟 全库跨本综合练习卡片（合并模式） -->
      <div class="bg-linear-to-r from-rose-500 via-red-500 to-amber-500 rounded-3xl p-5 sm:p-6 text-white shadow-md mb-6 relative overflow-hidden">
        <div class="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div class="space-y-1.5 max-w-xl">
            <div class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-white/20 text-white text-xs font-semibold backdrop-blur-xs">
              <span>🌟 全库跨册大综合模式</span>
            </div>
            <h3 class="text-lg sm:text-xl font-extrabold tracking-wide">
              全部练习册合并综合练习
            </h3>
            <p class="text-xs sm:text-sm text-rose-50 leading-relaxed">
              汇集已导入的全部 3 本真题与习题集（共 {{ workbooks.reduce((s, w) => s + (w.total_questions || 0), 0) }} 道考研政治选择题），支持跨册混合大乱练、全学科综合模拟测试！
            </p>
          </div>

          <div class="flex items-center gap-2 shrink-0">
            <button
              @click="emit('select-workbook', 'all'); emit('start-practice');"
              class="w-full sm:w-auto px-5 py-2.5 bg-white hover:bg-rose-50 active:bg-rose-100 text-rose-700 font-bold text-xs sm:text-sm rounded-xl shadow-xs transition flex items-center justify-center gap-1.5 cursor-pointer"
            >
              <BookOpen class="w-4 h-4 text-rose-600" />
              <span>开启全库综合大乱练</span>
            </button>
          </div>
        </div>
      </div>

      <div class="flex items-center justify-between mb-4">
        <div>
          <h3 class="font-bold text-slate-800 text-base flex items-center gap-1.5">
            <Library class="w-4 h-4 text-rose-600" />
            <span>分册独立练习列表 (共 {{ workbooks.length }} 本)</span>
          </h3>
          <p class="text-xs text-slate-500 mt-0.5">每本习题集均可单独刷题、单独二刷重置与统计</p>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div
          v-for="wb in workbooks"
          :key="wb.id"
          class="bg-white rounded-2xl p-5 border transition shadow-2xs hover:shadow-sm flex flex-col justify-between"
          :class="[
            activeWorkbookId === wb.id ? 'border-rose-300 ring-2 ring-rose-500/10' : 'border-slate-200'
          ]"
        >
          <div>
            <!-- Title & Status -->
            <div class="flex items-start justify-between gap-2">
              <div>
                <h4 class="font-bold text-slate-900 text-base leading-snug">{{ wb.name }}</h4>
                <p class="text-xs text-slate-400 mt-0.5">创建于 {{ wb.created_at?.slice(0, 10) }}</p>
              </div>
              <span 
                v-if="activeWorkbookId === wb.id"
                class="px-2 py-0.5 text-[11px] font-bold bg-rose-50 text-rose-600 rounded-md border border-rose-200 shrink-0"
              >
                当前选择
              </span>
            </div>

            <!-- Stats Bar -->
            <div class="mt-4 grid grid-cols-3 gap-2 bg-slate-50 p-2.5 rounded-xl border border-slate-100 text-center">
              <div>
                <div class="text-[11px] text-slate-400">总题数</div>
                <div class="font-bold text-slate-800 text-sm mt-0.5">{{ wb.total_questions }}</div>
              </div>
              <div>
                <div class="text-[11px] text-slate-400">已作答</div>
                <div class="font-bold text-slate-800 text-sm mt-0.5">{{ wb.answered_count }}</div>
              </div>
              <div>
                <div class="text-[11px] text-slate-400">正确率</div>
                <div class="font-bold text-emerald-600 text-sm mt-0.5">{{ wb.accuracy }}%</div>
              </div>
            </div>

            <!-- Progress Bar -->
            <div class="mt-3">
              <div class="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                <div 
                  class="bg-rose-500 h-full rounded-full transition-all duration-300"
                  :style="{ width: `${wb.total_questions > 0 ? (wb.answered_count / wb.total_questions * 100) : 0}%` }"
                ></div>
              </div>
            </div>
          </div>

          <!-- Actions -->
          <div class="mt-5 pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
            <div class="flex items-center gap-1">
              <button
                @click="openInspect(wb)"
                class="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition cursor-pointer"
                title="校对/查看题目"
              >
                <FileCheck class="w-4 h-4" />
              </button>
              <button
                @click="handleReset(wb)"
                class="p-1.5 text-slate-400 hover:text-amber-600 hover:bg-amber-50 rounded-lg transition cursor-pointer"
                title="二刷重置练习进度"
              >
                <RotateCcw class="w-4 h-4" />
              </button>
              <button
                @click="handleDelete(wb)"
                class="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition cursor-pointer"
                title="删除此练习册"
              >
                <Trash2 class="w-4 h-4" />
              </button>
            </div>

            <button
              @click="emit('select-workbook', wb.id); emit('start-practice');"
              class="px-4 py-1.5 bg-rose-600 hover:bg-rose-700 active:bg-rose-800 text-white font-semibold text-xs rounded-xl shadow-2xs transition flex items-center gap-1 cursor-pointer"
            >
              <BookOpen class="w-3.5 h-3.5" />
              <span>开始刷题</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Question Inspect / Edit Modal -->
    <div v-if="inspectingWorkbook" class="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-200">
      <div class="bg-white rounded-2xl max-w-3xl w-full p-4 sm:p-6 shadow-2xl relative border border-slate-100 flex flex-col max-h-[90vh]">
        <div class="flex items-center justify-between pb-3 border-b border-slate-100">
          <div>
            <h3 class="font-bold text-slate-800 text-base">题目校对与浏览 - {{ inspectingWorkbook.name }}</h3>
            <p class="text-xs text-slate-400">共 {{ questionsList.length }} 题，支持快速修改由于PDF扫描导致的不规范字符</p>
          </div>
          <button 
            @click="inspectingWorkbook = null; editingQuestion = null;"
            class="text-slate-400 hover:text-slate-600 px-2 py-1 text-sm font-semibold rounded-lg hover:bg-slate-100"
          >
            关闭
          </button>
        </div>

        <div v-if="loadingQuestions" class="py-12 text-center text-slate-400">
          加载题目中...
        </div>

        <div v-else class="overflow-y-auto py-3 space-y-3 flex-1 pr-1">
          <div 
            v-for="q in questionsList"
            :key="q.id"
            class="p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs space-y-1.5"
          >
            <div class="flex items-center justify-between">
              <span class="font-bold text-slate-700">第 {{ q.question_num }} 题 · {{ q.category }} · {{ q.question_type === 'multiple' ? '多选题' : '单选题' }}</span>
              <span class="text-emerald-700 font-bold font-mono">答案: {{ q.answer }}</span>
            </div>
            <div class="text-slate-800">{{ q.stem }}</div>
            <div class="text-slate-500">
              <span v-for="opt in q.options" :key="opt.key" class="mr-3">
                <strong>{{ opt.key }}.</strong> {{ opt.value }}
              </span>
            </div>
            <div v-if="q.explanation" class="text-slate-400 border-t border-slate-200 pt-1">
              <strong>解析:</strong> {{ q.explanation }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
