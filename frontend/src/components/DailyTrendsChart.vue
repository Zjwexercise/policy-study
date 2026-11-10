<script setup>
import { ref, computed } from 'vue';
import { 
  TrendingUp, 
  Clock, 
  Award, 
  Calendar,
  Sparkles,
  Flame,
  BarChart2
} from 'lucide-vue-next';

const props = defineProps({
  dailyTrends: {
    type: Array,
    default: () => []
  }
});

// 当前展示指标：'answered' (刷题量), 'study_minutes' (学习时长), 'accuracy' (正确率)
const activeMetric = ref('answered');
// 展示时间跨度：7, 14, 30
const selectedRange = ref(14);
// 悬浮/触摸激活的数据点索引
const activePointIndex = ref(null);

// 根据时间跨度切片数据
const filteredData = computed(() => {
  if (!props.dailyTrends || props.dailyTrends.length === 0) return [];
  const range = Math.min(selectedRange.value, props.dailyTrends.length);
  return props.dailyTrends.slice(-range);
});

// 指标配置
const metricConfig = computed(() => {
  switch (activeMetric.value) {
    case 'study_minutes':
      return {
        key: 'study_minutes',
        label: '学习时长',
        unit: '分钟',
        color: '#4f46e5', // indigo-600
        gradientStart: 'rgba(79, 70, 229, 0.35)',
        gradientEnd: 'rgba(79, 70, 229, 0.02)',
        badgeBg: 'bg-indigo-50',
        badgeText: 'text-indigo-700'
      };
    case 'accuracy':
      return {
        key: 'accuracy',
        label: '做题正确率',
        unit: '%',
        color: '#059669', // emerald-600
        gradientStart: 'rgba(5, 150, 105, 0.35)',
        gradientEnd: 'rgba(5, 150, 105, 0.02)',
        badgeBg: 'bg-emerald-50',
        badgeText: 'text-emerald-700'
      };
    case 'answered':
    default:
      return {
        key: 'answered',
        label: '每日刷题量',
        unit: '题',
        color: '#e11d48', // rose-600
        gradientStart: 'rgba(225, 29, 72, 0.35)',
        gradientEnd: 'rgba(225, 29, 72, 0.02)',
        badgeBg: 'bg-rose-50',
        badgeText: 'text-rose-700'
      };
  }
});

// 统计摘要
const summaryStats = computed(() => {
  const data = filteredData.value;
  if (data.length === 0) return { totalAnswered: 0, totalMinutes: 0, avgAnswered: 0, maxAnswered: 0 };
  
  const totalAnswered = data.reduce((sum, d) => sum + (d.answered || 0), 0);
  const totalMinutes = Math.round(data.reduce((sum, d) => sum + (d.study_minutes || 0), 0) * 10) / 10;
  const avgAnswered = Math.round(totalAnswered / data.length);
  const maxAnswered = Math.max(...data.map(d => d.answered || 0));
  
  return {
    totalAnswered,
    totalMinutes,
    avgAnswered,
    maxAnswered
  };
});

// SVG 图表坐标计算 (SVG 宽 650, 高 220)
const SVG_WIDTH = 650;
const SVG_HEIGHT = 200;
const PADDING = { top: 25, right: 30, bottom: 35, left: 45 };

const chartWidth = SVG_WIDTH - PADDING.left - PADDING.right;
const chartHeight = SVG_HEIGHT - PADDING.top - PADDING.bottom;

// 计算 Y 轴最大值
const yMaxValue = computed(() => {
  const data = filteredData.value;
  if (data.length === 0) return 10;
  const key = metricConfig.value.key;
  const max = Math.max(...data.map(d => d[key] || 0));
  
  if (activeMetric.value === 'accuracy') {
    return 100;
  }
  if (max === 0) return activeMetric.value === 'study_minutes' ? 30 : 20;
  // 向上取整为美观的刻度值
  const step = max > 100 ? 50 : (max > 40 ? 20 : (max > 10 ? 10 : 5));
  return Math.ceil(max / step) * step;
});

// Y 轴刻度线 (4条)
const yTicks = computed(() => {
  const max = yMaxValue.value;
  return [
    { value: max, y: PADDING.top },
    { value: Math.round(max * 0.66), y: PADDING.top + chartHeight * 0.34 },
    { value: Math.round(max * 0.33), y: PADDING.top + chartHeight * 0.67 },
    { value: 0, y: PADDING.top + chartHeight }
  ];
});

// 各数据点坐标
const points = computed(() => {
  const data = filteredData.value;
  if (data.length === 0) return [];
  
  const key = metricConfig.value.key;
  const yMax = yMaxValue.value;
  const n = data.length;
  
  return data.map((d, i) => {
    const x = n > 1 
      ? PADDING.left + (i / (n - 1)) * chartWidth 
      : PADDING.left + chartWidth / 2;
    const val = d[key] || 0;
    const yRatio = yMax > 0 ? (val / yMax) : 0;
    const y = PADDING.top + chartHeight - (yRatio * chartHeight);
    return {
      x,
      y,
      data: d,
      value: val,
      index: i
    };
  });
});

// 生成三次贝塞尔平滑曲线路径
const pathD = computed(() => {
  const pts = points.value;
  if (pts.length === 0) return '';
  if (pts.length === 1) return `M ${pts[0].x} ${pts[0].y}`;

  let d = `M ${pts[0].x.toFixed(1)} ${pts[0].y.toFixed(1)}`;
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[i === 0 ? i : i - 1];
    const p1 = pts[i];
    const p2 = pts[i + 1];
    const p3 = pts[i + 2 < pts.length ? i + 2 : i + 1];

    const cp1x = p1.x + (p2.x - p0.x) / 6;
    const cp1y = p1.y + (p2.y - p0.y) / 6;
    const cp2x = p2.x - (p3.x - p1.x) / 6;
    const cp2y = p2.y - (p3.y - p1.y) / 6;

    d += ` C ${cp1x.toFixed(1)} ${cp1y.toFixed(1)}, ${cp2x.toFixed(1)} ${cp2y.toFixed(1)}, ${p2.x.toFixed(1)} ${p2.y.toFixed(1)}`;
  }
  return d;
});

// 面积图底部闭合路径
const areaD = computed(() => {
  const pts = points.value;
  if (pts.length < 2) return '';
  const first = pts[0];
  const last = pts[pts.length - 1];
  const baseline = PADDING.top + chartHeight;
  return `${pathD.value} L ${last.x.toFixed(1)} ${baseline} L ${first.x.toFixed(1)} ${baseline} Z`;
});

// 当前被激活的高亮数据点
const activePoint = computed(() => {
  if (activePointIndex.value === null) return null;
  return points.value[activePointIndex.value] || null;
});

// 触摸/鼠标交互
const handleMouseMove = (e) => {
  const svg = e.currentTarget;
  const rect = svg.getBoundingClientRect();
  const mouseX = ((e.clientX - rect.left) / rect.width) * SVG_WIDTH;
  
  // 寻找横坐标最近的数据点
  let closestIdx = 0;
  let minDiff = Infinity;
  points.value.forEach((pt, idx) => {
    const diff = Math.abs(pt.x - mouseX);
    if (diff < minDiff) {
      minDiff = diff;
      closestIdx = idx;
    }
  });
  activePointIndex.value = closestIdx;
};

const handleMouseLeave = () => {
  activePointIndex.value = null;
};
</script>

<template>
  <div class="bg-white rounded-2xl p-4 sm:p-5 border border-slate-200 shadow-2xs">
    <!-- Header with Controls -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
      <div class="flex items-center gap-2">
        <div 
          class="p-2 rounded-xl transition-colors"
          :class="metricConfig.badgeBg"
        >
          <BarChart2 class="w-4 h-4" :style="{ color: metricConfig.color }" />
        </div>
        <div>
          <h3 class="font-bold text-slate-800 text-sm sm:text-base flex items-center gap-1.5">
            <span>{{ metricConfig.label }}趋势折线图</span>
            <span class="text-[11px] font-normal text-slate-400">（支持切换指标与周期）</span>
          </h3>
        </div>
      </div>

      <!-- Controls: Metric + Range -->
      <div class="flex flex-wrap items-center gap-2">
        <!-- 指标切换 -->
        <div class="inline-flex bg-slate-100 p-0.5 rounded-xl border border-slate-200 text-xs">
          <button
            @click="activeMetric = 'answered'"
            class="px-2.5 py-1 rounded-lg font-medium transition cursor-pointer flex items-center gap-1"
            :class="activeMetric === 'answered' ? 'bg-white text-rose-600 shadow-2xs font-semibold' : 'text-slate-600 hover:text-slate-900'"
          >
            <TrendingUp class="w-3 h-3" />
            <span>刷题量</span>
          </button>
          <button
            @click="activeMetric = 'study_minutes'"
            class="px-2.5 py-1 rounded-lg font-medium transition cursor-pointer flex items-center gap-1"
            :class="activeMetric === 'study_minutes' ? 'bg-white text-indigo-600 shadow-2xs font-semibold' : 'text-slate-600 hover:text-slate-900'"
          >
            <Clock class="w-3 h-3" />
            <span>学习时长</span>
          </button>
          <button
            @click="activeMetric = 'accuracy'"
            class="px-2.5 py-1 rounded-lg font-medium transition cursor-pointer flex items-center gap-1"
            :class="activeMetric === 'accuracy' ? 'bg-white text-emerald-600 shadow-2xs font-semibold' : 'text-slate-600 hover:text-slate-900'"
          >
            <Award class="w-3 h-3" />
            <span>正确率</span>
          </button>
        </div>

        <!-- 周期切换 -->
        <div class="inline-flex bg-slate-100 p-0.5 rounded-xl border border-slate-200 text-xs">
          <button
            v-for="r in [7, 14, 30]"
            :key="r"
            @click="selectedRange = r"
            class="px-2 py-1 rounded-lg font-medium transition cursor-pointer"
            :class="selectedRange === r ? 'bg-white text-slate-800 shadow-2xs font-semibold' : 'text-slate-500 hover:text-slate-800'"
          >
            近{{ r }}天
          </button>
        </div>
      </div>
    </div>

    <!-- Mini Overview Badges -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-3 pb-2 text-xs">
      <div class="p-2.5 bg-slate-50 rounded-xl border border-slate-100">
        <span class="text-slate-400 block mb-0.5">近 {{ selectedRange }} 天总刷题</span>
        <span class="font-bold text-slate-800 text-sm font-mono">{{ summaryStats.totalAnswered }} 题</span>
      </div>
      <div class="p-2.5 bg-slate-50 rounded-xl border border-slate-100">
        <span class="text-slate-400 block mb-0.5">近 {{ selectedRange }} 天总时长</span>
        <span class="font-bold text-slate-800 text-sm font-mono">{{ summaryStats.totalMinutes }} 分钟</span>
      </div>
      <div class="p-2.5 bg-slate-50 rounded-xl border border-slate-100">
        <span class="text-slate-400 block mb-0.5">日均刷题效率</span>
        <span class="font-bold text-indigo-600 text-sm font-mono">{{ summaryStats.avgAnswered }} 题/天</span>
      </div>
      <div class="p-2.5 bg-slate-50 rounded-xl border border-slate-100">
        <span class="text-slate-400 block mb-0.5">单日最高产出</span>
        <span class="font-bold text-rose-600 text-sm font-mono">{{ summaryStats.maxAnswered }} 题/日</span>
      </div>
    </div>

    <!-- SVG Line Chart Area -->
    <div class="relative mt-2 select-none">
      <svg 
        :viewBox="`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`"
        class="w-full h-48 sm:h-56 touch-none"
        @mousemove="handleMouseMove"
        @touchmove="handleMouseMove"
        @mouseleave="handleMouseLeave"
        @touchend="handleMouseLeave"
      >
        <defs>
          <linearGradient id="trendGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" :stop-color="metricConfig.gradientStart" />
            <stop offset="100%" :stop-color="metricConfig.gradientEnd" />
          </linearGradient>
        </defs>

        <!-- Y-Axis Grid Lines & Labels -->
        <g class="grid-lines">
          <g v-for="t in yTicks" :key="t.value">
            <line 
              :x1="PADDING.left" 
              :y1="t.y" 
              :x2="SVG_WIDTH - PADDING.right" 
              :y2="t.y" 
              stroke="#e2e8f0" 
              stroke-width="1"
              stroke-dasharray="3,3"
            />
            <text 
              :x="PADDING.left - 8" 
              :y="t.y + 4" 
              fill="#94a3b8" 
              font-size="10" 
              text-anchor="end"
              font-family="monospace"
            >
              {{ t.value }}{{ activeMetric === 'accuracy' ? '%' : '' }}
            </text>
          </g>
        </g>

        <!-- Area Fill under curve -->
        <path 
          v-if="areaD"
          :d="areaD" 
          fill="url(#trendGradient)" 
        />

        <!-- Smooth Curve Line -->
        <path 
          v-if="pathD"
          :d="pathD" 
          fill="none" 
          :stroke="metricConfig.color" 
          stroke-width="3" 
          stroke-linecap="round"
          stroke-linejoin="round"
        />

        <!-- Active Point Crosshair & Tooltip Anchor -->
        <g v-if="activePoint">
          <!-- Vertical Guideline -->
          <line
            :x1="activePoint.x"
            :y1="PADDING.top"
            :x2="activePoint.x"
            :y2="PADDING.top + chartHeight"
            stroke="#cbd5e1"
            stroke-width="1.5"
            stroke-dasharray="2,2"
          />
          <!-- Outer Pulsing Ring -->
          <circle 
            :cx="activePoint.x" 
            :cy="activePoint.y" 
            r="8" 
            :fill="metricConfig.color" 
            opacity="0.25"
          />
        </g>

        <!-- Data Point Circles -->
        <g class="data-points">
          <circle
            v-for="pt in points"
            :key="pt.index"
            :cx="pt.x"
            :cy="pt.y"
            :r="activePointIndex === pt.index ? 5.5 : (selectedRange <= 14 ? 3.5 : 2.5)"
            :fill="metricConfig.color"
            stroke="#ffffff"
            :stroke-width="activePointIndex === pt.index ? 2.5 : 1.5"
            class="transition-all duration-150 cursor-pointer"
          />
        </g>

        <!-- X-Axis Labels (Dates) -->
        <g class="x-labels">
          <text
            v-for="(pt, idx) in points"
            :key="idx"
            v-show="selectedRange <= 7 || idx % (selectedRange > 14 ? 3 : 2) === 0 || idx === points.length - 1"
            :x="pt.x"
            :y="PADDING.top + chartHeight + 18"
            fill="#64748b"
            font-size="10"
            text-anchor="middle"
            font-family="monospace"
          >
            {{ pt.data.display_date }}
          </text>
        </g>
      </svg>

      <!-- Floating Tooltip Box -->
      <transition
        enter-active-class="transition duration-150 ease-out"
        enter-from-class="opacity-0 scale-95"
        enter-to-class="opacity-100 scale-100"
        leave-active-class="transition duration-100 ease-in"
        leave-from-class="opacity-100 scale-100"
        leave-to-class="opacity-0 scale-95"
      >
        <div
          v-if="activePoint"
          class="absolute z-20 pointer-events-none bg-slate-900/95 backdrop-blur-sm text-white px-3 py-2 rounded-xl shadow-lg border border-slate-700 text-xs w-48 -translate-x-1/2"
          :style="{
            left: `${(activePoint.x / SVG_WIDTH) * 100}%`,
            top: activePoint.y < 90 ? `${((activePoint.y + 25) / SVG_HEIGHT) * 100}%` : `${((activePoint.y - 75) / SVG_HEIGHT) * 100}%`
          }"
        >
          <div class="font-bold flex items-center justify-between border-b border-slate-700/80 pb-1 mb-1 text-slate-200">
            <span>{{ activePoint.data.date }} ({{ activePoint.data.day_name }})</span>
          </div>
          <div class="space-y-0.5">
            <div class="flex items-center justify-between">
              <span class="text-slate-400">当日刷题：</span>
              <span class="font-bold text-rose-400 font-mono">{{ activePoint.data.answered }} 题</span>
            </div>
            <div class="flex items-center justify-between text-[11px] text-slate-400">
              <span>正误对比：</span>
              <span class="font-mono text-emerald-400">对 {{ activePoint.data.correct }} / 错 {{ activePoint.data.wrong }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-slate-400">当日正确率：</span>
              <span class="font-bold text-emerald-400 font-mono">{{ activePoint.data.accuracy }}%</span>
            </div>
            <div class="flex items-center justify-between pt-0.5 border-t border-slate-800">
              <span class="text-slate-400">学习时长：</span>
              <span class="font-bold text-indigo-300 font-mono">{{ activePoint.data.study_minutes }} 分钟</span>
            </div>
          </div>
        </div>
      </transition>
    </div>

    <!-- Chart Footer Explanation -->
    <div class="mt-2 text-[11px] text-slate-400 flex items-center justify-between">
      <div class="flex items-center gap-1.5">
        <Sparkles class="w-3.5 h-3.5 text-amber-500" />
        <span>提示：手指滑动或鼠标悬停在折线上，可查看每一天的详细刷题正误与专注时长</span>
      </div>
      <div class="hidden sm:block">
        数据每日凌晨自动归档汇总
      </div>
    </div>
  </div>
</template>
