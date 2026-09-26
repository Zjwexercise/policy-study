<script setup>
import { ref, onMounted } from 'vue';
import { api } from '../api';
import { 
  BarChart3, 
  CheckCircle2, 
  AlertCircle, 
  HelpCircle, 
  FileText, 
  TrendingUp, 
  Award,
  Lightbulb,
  Swords
} from 'lucide-vue-next';

const stats = ref(null);
const loading = ref(true);

const loadStats = async () => {
  loading.value = true;
  try {
    const data = await api.getStats();
    stats.value = data;
  } catch (err) {
    console.error('获取统计失败', err);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  loadStats();
});
</script>

<template>
  <div class="max-w-4xl mx-auto px-3 sm:px-6 py-4 pb-24 lg:pb-12">
    <!-- Header -->
    <div class="bg-white rounded-2xl p-4 sm:p-5 border border-slate-200 shadow-2xs mb-4">
      <div class="flex items-center gap-2.5">
        <div class="p-2.5 bg-indigo-50 text-indigo-600 rounded-xl">
          <BarChart3 class="w-5 h-5" />
        </div>
        <div>
          <h2 class="text-base sm:text-lg font-bold text-slate-800">学习统计与考情分析</h2>
          <p class="text-xs text-slate-500">实时追踪考研政治刷题进度与各学科掌握程度</p>
        </div>
      </div>
    </div>

    <div v-if="loading" class="bg-white rounded-2xl p-12 text-center border border-slate-200 shadow-2xs">
      <div class="inline-block animate-spin w-8 h-8 border-3 border-indigo-500 border-t-transparent rounded-full mb-3"></div>
      <p class="text-sm text-slate-500">统计分析中...</p>
    </div>

    <div v-else-if="stats" class="space-y-4">
      <!-- 5 Summary Cards -->
      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 sm:gap-4">
        <!-- Card 1: Total Completed -->
        <div class="bg-white p-4 rounded-2xl border border-slate-200 shadow-2xs">
          <div class="flex items-center justify-between text-slate-400 mb-2">
            <span class="text-xs font-medium">总刷题量</span>
            <TrendingUp class="w-4 h-4 text-blue-500" />
          </div>
          <div class="text-2xl font-bold text-slate-800">
            {{ stats.overview.total_answered || 0 }}
            <span class="text-xs font-normal text-slate-400">/ {{ stats.overview.total_questions || 0 }}</span>
          </div>
        </div>

        <!-- Card 2: Accuracy Rate -->
        <div class="bg-white p-4 rounded-2xl border border-slate-200 shadow-2xs">
          <div class="flex items-center justify-between text-slate-400 mb-2">
            <span class="text-xs font-medium">综合正确率</span>
            <Award class="w-4 h-4 text-emerald-500" />
          </div>
          <div class="text-2xl font-bold text-emerald-600">
            {{ stats.overview.total_answered > 0 ? ((stats.overview.total_correct / stats.overview.total_answered) * 100).toFixed(1) : 0 }}%
          </div>
        </div>

        <!-- Card 3: Wrong Questions -->
        <div class="bg-white p-4 rounded-2xl border border-slate-200 shadow-2xs">
          <div class="flex items-center justify-between text-slate-400 mb-2">
            <span class="text-xs font-medium">待攻克错题</span>
            <AlertCircle class="w-4 h-4 text-rose-500" />
          </div>
          <div class="text-2xl font-bold text-rose-600">
            {{ stats.overview.total_wrong || 0 }}
            <span class="text-xs font-normal text-slate-400">题</span>
          </div>
        </div>

        <!-- Card 4: Killed Questions -->
        <div class="bg-white p-4 rounded-2xl border border-slate-200 shadow-2xs">
          <div class="flex items-center justify-between text-slate-400 mb-2">
            <span class="text-xs font-medium">已斩熟题</span>
            <Swords class="w-4 h-4 text-rose-700" />
          </div>
          <div class="text-2xl font-bold text-rose-700">
            {{ stats.overview.total_killed || 0 }}
            <span class="text-xs font-normal text-slate-400">题</span>
          </div>
        </div>

        <!-- Card 5: Notes & Stars -->
        <div class="bg-white p-4 rounded-2xl border border-slate-200 shadow-2xs col-span-2 sm:col-span-1">
          <div class="flex items-center justify-between text-slate-400 mb-2">
            <span class="text-xs font-medium">专属考点笔记</span>
            <FileText class="w-4 h-4 text-amber-500" />
          </div>
          <div class="text-2xl font-bold text-amber-600">
            {{ stats.overview.total_notes || 0 }}
            <span class="text-xs font-normal text-slate-400">篇</span>
          </div>
        </div>
      </div>

      <!-- Category Breakdown -->
      <div class="bg-white rounded-2xl p-5 border border-slate-200 shadow-2xs">
        <h3 class="font-bold text-slate-800 text-sm sm:text-base mb-4">政治各科目正确率与进度</h3>

        <div class="space-y-4">
          <div 
            v-for="cat in stats.categories" 
            :key="cat.category"
            class="p-3.5 bg-slate-50 border border-slate-100 rounded-xl"
          >
            <div class="flex items-center justify-between mb-1.5">
              <span class="font-bold text-xs sm:text-sm text-slate-800">{{ cat.category }}</span>
              <div class="text-xs">
                <span class="text-slate-500">已做 {{ cat.answered }} / {{ cat.total }} 题 · </span>
                <span class="font-bold font-mono" :class="cat.accuracy >= 70 ? 'text-emerald-600' : 'text-rose-600'">
                  正确率 {{ cat.accuracy }}%
                </span>
              </div>
            </div>

            <!-- Progress bar -->
            <div class="w-full bg-slate-200/80 rounded-full h-2 overflow-hidden">
              <div 
                class="bg-indigo-600 h-full rounded-full transition-all duration-300"
                :style="{ width: `${cat.total > 0 ? (cat.answered / cat.total * 100) : 0}%` }"
              ></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Tips Box -->
      <div class="bg-amber-50/70 border border-amber-200/80 rounded-2xl p-4 sm:p-5 text-amber-950 text-xs sm:text-sm leading-relaxed">
        <div class="flex items-center gap-2 font-bold text-amber-900 mb-2">
          <Lightbulb class="w-4 h-4 text-amber-600" />
          <span>考研政治名师备考心法与提分建议：</span>
        </div>
        <ul class="list-disc list-inside space-y-1.5 text-xs text-amber-900/90">
          <li><strong>“得选择题者得天下”：</strong>考研政治选择题总分 50 分（单选 16 分，多选 34 分）。目标 70+ 分的同学，选择题至少要拿到 40 分以上！</li>
          <li><strong>多选题是核心拉分项：</strong>多选题多选、少选、错选均不得分。练习时注意排除“表述本身错误”和“表述正确但与题干无关”的干扰项。</li>
          <li><strong>善用【斩题】提高效率：</strong>滚瓜烂熟的常识题或简单题，果断点击【斩题】，系统自动跳过不再重复刷，把宝贵备考精力 100% 留给高频错题和真题难点！随时可在【斩题本】复活题目。</li>
          <li><strong>二刷、三刷非常关键：</strong>第一遍刷题重在扫清盲区，第二遍通过重置进度重刷巩固，重点利用【错题本】消灭顽固错题。</li>
          <li><strong>考前反复翻看【考点笔记】：</strong>把做题时易混淆的关键词、帽子题（如“根本保证”、“根本动力”、“核心”）记录并反复回看。</li>
        </ul>
      </div>
    </div>
  </div>
</template>
