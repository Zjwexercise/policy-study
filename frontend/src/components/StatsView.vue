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
  Swords,
  RefreshCw,
  Clock,
  Timer
} from 'lucide-vue-next';
import DailyTrendsChart from './DailyTrendsChart.vue';

const emit = defineEmits(['open-sync']);

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

const formatSeconds = (sec) => {
  if (!sec || sec <= 0) return '0 分钟';
  const m = Math.floor(sec / 60);
  if (m < 60) {
    return `${m} 分钟`;
  }
  const h = Math.floor(m / 60);
  const remM = m % 60;
  return remM > 0 ? `${h} 小时 ${remM} 分` : `${h} 小时整`;
};

onMounted(() => {
  loadStats();
});
</script>

<template>
  <div class="max-w-4xl mx-auto px-3 sm:px-6 py-4 pb-24 lg:pb-12">
    <!-- Header -->
    <div class="bg-white rounded-2xl p-4 sm:p-5 border border-slate-200 shadow-2xs mb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
      <div class="flex items-center gap-2.5">
        <div class="p-2.5 bg-indigo-50 text-indigo-600 rounded-xl">
          <BarChart3 class="w-5 h-5" />
        </div>
        <div>
          <h2 class="text-base sm:text-lg font-bold text-slate-800">学习统计与考情分析</h2>
          <p class="text-xs text-slate-500">实时追踪考研政治刷题进度与各学科掌握程度</p>
        </div>
      </div>
      <button
        @click="emit('open-sync')"
        class="self-start sm:self-center px-3 py-1.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer shadow-2xs"
      >
        <RefreshCw class="w-3.5 h-3.5" />
        <span>跨端同步与备份</span>
      </button>
    </div>

    <div v-if="loading" class="bg-white rounded-2xl p-12 text-center border border-slate-200 shadow-2xs">
      <div class="inline-block animate-spin w-8 h-8 border-3 border-indigo-500 border-t-transparent rounded-full mb-3"></div>
      <p class="text-sm text-slate-500">统计分析中...</p>
    </div>

    <div v-else-if="stats" class="space-y-4">
      <!-- Summary Cards Grid -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
        <!-- Card 1: Today Study Time -->
        <div class="bg-white p-4 rounded-2xl border border-slate-200 shadow-2xs">
          <div class="flex items-center justify-between text-slate-400 mb-1.5">
            <span class="text-xs font-medium">今日专注时长</span>
            <Timer class="w-4 h-4 text-indigo-600" />
          </div>
          <div class="text-xl sm:text-2xl font-bold text-indigo-700 font-mono">
            {{ formatSeconds(stats.overview.today_study_seconds) }}
          </div>
          <div class="text-[11px] text-slate-400 mt-1">
            今日已刷 <strong class="text-slate-700 font-mono">{{ stats.overview.today_answered || 0 }}</strong> 题
          </div>
        </div>

        <!-- Card 2: Total Study Time -->
        <div class="bg-white p-4 rounded-2xl border border-slate-200 shadow-2xs">
          <div class="flex items-center justify-between text-slate-400 mb-1.5">
            <span class="text-xs font-medium">累计学习时长</span>
            <Clock class="w-4 h-4 text-sky-600" />
          </div>
          <div class="text-xl sm:text-2xl font-bold text-sky-700 font-mono">
            {{ formatSeconds(stats.overview.total_study_seconds) }}
          </div>
          <div class="text-[11px] text-slate-400 mt-1">
            实时专注计时统计
          </div>
        </div>

        <!-- Card 3: Total Completed -->
        <div class="bg-white p-4 rounded-2xl border border-slate-200 shadow-2xs">
          <div class="flex items-center justify-between text-slate-400 mb-1.5">
            <span class="text-xs font-medium">总做题进度</span>
            <TrendingUp class="w-4 h-4 text-blue-500" />
          </div>
          <div class="text-xl sm:text-2xl font-bold text-slate-800 font-mono">
            {{ stats.overview.total_answered || 0 }}
            <span class="text-xs font-normal text-slate-400 font-sans">/ {{ stats.overview.total_questions || 0 }}</span>
          </div>
          <div class="text-[11px] text-slate-400 mt-1">
            完成度 {{ stats.overview.total_questions > 0 ? ((stats.overview.total_answered / stats.overview.total_questions) * 100).toFixed(1) : 0 }}%
          </div>
        </div>

        <!-- Card 4: Accuracy Rate -->
        <div class="bg-white p-4 rounded-2xl border border-slate-200 shadow-2xs">
          <div class="flex items-center justify-between text-slate-400 mb-1.5">
            <span class="text-xs font-medium">综合正确率</span>
            <Award class="w-4 h-4 text-emerald-500" />
          </div>
          <div class="text-xl sm:text-2xl font-bold text-emerald-600 font-mono">
            {{ stats.overview.total_answered > 0 ? ((stats.overview.total_correct / stats.overview.total_answered) * 100).toFixed(1) : 0 }}%
          </div>
          <div class="text-[11px] text-slate-400 mt-1">
            答对 {{ stats.overview.total_correct || 0 }} 题
          </div>
        </div>
      </div>

      <!-- Secondary Metric Row -->
      <div class="grid grid-cols-3 gap-3 sm:gap-4">
        <!-- Card 5: Wrong Questions -->
        <div class="bg-white p-3.5 sm:p-4 rounded-2xl border border-slate-200 shadow-2xs">
          <div class="flex items-center justify-between text-slate-400 mb-1">
            <span class="text-xs font-medium">待攻克错题</span>
            <AlertCircle class="w-4 h-4 text-rose-500" />
          </div>
          <div class="text-lg sm:text-xl font-bold text-rose-600 font-mono">
            {{ stats.overview.total_wrong || 0 }} <span class="text-xs font-normal text-slate-400 font-sans">题</span>
          </div>
        </div>

        <!-- Card 6: Killed Questions -->
        <div class="bg-white p-3.5 sm:p-4 rounded-2xl border border-slate-200 shadow-2xs">
          <div class="flex items-center justify-between text-slate-400 mb-1">
            <span class="text-xs font-medium">已斩熟题</span>
            <Swords class="w-4 h-4 text-rose-700" />
          </div>
          <div class="text-lg sm:text-xl font-bold text-rose-700 font-mono">
            {{ stats.overview.total_killed || 0 }} <span class="text-xs font-normal text-slate-400 font-sans">题</span>
          </div>
        </div>

        <!-- Card 7: Notes -->
        <div class="bg-white p-3.5 sm:p-4 rounded-2xl border border-slate-200 shadow-2xs">
          <div class="flex items-center justify-between text-slate-400 mb-1">
            <span class="text-xs font-medium">专属考点笔记</span>
            <FileText class="w-4 h-4 text-amber-500" />
          </div>
          <div class="text-lg sm:text-xl font-bold text-amber-600 font-mono">
            {{ stats.overview.total_notes || 0 }} <span class="text-xs font-normal text-slate-400 font-sans">篇</span>
          </div>
        </div>
      </div>

      <!-- 每日刷题量与学习时长趋势折线图 -->
      <DailyTrendsChart :daily-trends="stats.daily_trends || []" />

      <!-- Cross-Device Sync & Data Backup Card -->
      <div class="bg-linear-to-r from-indigo-50/70 via-white to-sky-50/70 rounded-2xl p-4 sm:p-5 border border-indigo-150 shadow-2xs flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div class="flex items-start gap-3">
          <div class="p-2.5 bg-indigo-600 text-white rounded-xl shrink-0 mt-0.5 shadow-xs">
            <RefreshCw class="w-5 h-5" />
          </div>
          <div>
            <div class="flex items-center gap-2">
              <h3 class="font-bold text-slate-800 text-sm sm:text-base">跨设备数据同步与备份</h3>
              <span class="px-2 py-0.5 text-[10px] font-semibold bg-emerald-100 text-emerald-800 rounded-full">
                免登录 · 智能合并
              </span>
            </div>
            <p class="text-xs text-slate-500 mt-1 leading-relaxed">
              电脑和手机的刷题记录不一样？使用免登录【同步口令】或【备份文件】，一键将两端已做题目、错题与斩题智能合并，绝不丢失任何一边的刷题心血！
            </p>
          </div>
        </div>
        <div class="shrink-0 sm:self-center">
          <button
            @click="emit('open-sync')"
            class="w-full sm:w-auto px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs sm:text-sm font-semibold transition cursor-pointer shadow-xs flex items-center justify-center gap-1.5"
          >
            <RefreshCw class="w-4 h-4" />
            <span>进入同步中心</span>
          </button>
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
