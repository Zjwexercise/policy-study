<script setup>
import { ref, onMounted, watch } from 'vue';
import { api } from '../api';
import { auth } from '../auth';
import QRCode from 'qrcode';
import { X, Smartphone, Wifi, Copy, Check, RefreshCw, Cloud, Globe, AlertTriangle } from 'lucide-vue-next';

const props = defineProps({
  show: Boolean
});

const emit = defineEmits(['close', 'open-sync']);

const activeTab = ref('server'); // 'server' | 'cloud' | 'lan'
const loading = ref(true);
const serverUrl = ref('http://47.93.172.13:8000');
const cloudUrl = ref('https://zjwexercise.github.io/policy-study/');
const lanUrl = ref('');
const qrDataUrl = ref('');
const copied = ref(false);

const getActiveUrl = () => {
  let base = serverUrl.value;
  if (activeTab.value === 'cloud') base = cloudUrl.value;
  else if (activeTab.value === 'lan') base = lanUrl.value || window.location.href;

  const u = auth.currentUser.value;
  const token = auth.authToken.value;
  if (u && u.username) {
    const sep = base.includes('?') ? '&' : '?';
    return `${base}${sep}u=${encodeURIComponent(u.username)}&t=${encodeURIComponent(token)}&sync=1`;
  }
  return base;
};

const updateQr = async () => {
  loading.value = true;
  try {
    const url = getActiveUrl();
    qrDataUrl.value = await QRCode.toDataURL(url, {
      width: 260,
      margin: 2,
      color: {
        dark: '#1e293b',
        light: '#ffffff'
      }
    });
  } catch (err) {
    console.error('生成二维码失败', err);
  } finally {
    loading.value = false;
  }
};

const loadInfo = async () => {
  try {
    const net = await api.getNetworkInfo();
    if (net && net.mobile_url && !net.is_cloud) {
      lanUrl.value = net.mobile_url;
    } else {
      lanUrl.value = 'http://192.168.1.20:8000';
    }
  } catch {
    lanUrl.value = 'http://192.168.1.20:8000';
  }
  await updateQr();
};

watch(activeTab, () => {
  updateQr();
});

watch(() => props.show, (newVal) => {
  if (newVal) {
    loadInfo();
  }
});

const copyUrl = (text) => {
  if (!text) return;
  navigator.clipboard.writeText(text);
  copied.value = true;
  setTimeout(() => {
    copied.value = false;
  }, 2000);
};

onMounted(() => {
  loadInfo();
});
</script>

<template>
  <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-200">
    <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl relative border border-slate-100 max-h-[92vh] overflow-y-auto">
      <!-- Close button -->
      <button 
        @click="emit('close')"
        class="absolute top-4 right-4 p-1.5 text-slate-400 hover:text-slate-600 rounded-full hover:bg-slate-100 transition cursor-pointer"
      >
        <X class="w-5 h-5" />
      </button>

      <div class="text-center mb-3">
        <div class="inline-flex p-3 bg-rose-50 text-rose-600 rounded-2xl mb-2">
          <Smartphone class="w-6 h-6" />
        </div>
        <h3 class="text-lg font-bold text-slate-900">手机扫码刷题</h3>
        <p class="text-xs text-slate-500 mt-0.5">选择适合你当前网络环境的打开方式</p>
      </div>

      <!-- 模式切换 Tab -->
      <div class="flex bg-slate-100 p-1 rounded-xl mb-3 text-xs font-semibold gap-1">
        <button 
          @click="activeTab = 'server'"
          class="flex-1 py-1.5 rounded-lg transition flex items-center justify-center gap-1 cursor-pointer"
          :class="activeTab === 'server' ? 'bg-white text-rose-600 shadow-xs' : 'text-slate-600 hover:text-slate-900'"
        >
          <span>🚀 云服务器 (推荐)</span>
        </button>
        <button 
          @click="activeTab = 'cloud'"
          class="flex-1 py-1.5 rounded-lg transition flex items-center justify-center gap-1 cursor-pointer"
          :class="activeTab === 'cloud' ? 'bg-white text-rose-600 shadow-xs' : 'text-slate-600 hover:text-slate-900'"
        >
          <Globe class="w-3.5 h-3.5" />
          <span>GitHub Pages</span>
        </button>
        <button 
          @click="activeTab = 'lan'"
          class="flex-1 py-1.5 rounded-lg transition flex items-center justify-center gap-1 cursor-pointer"
          :class="activeTab === 'lan' ? 'bg-white text-rose-600 shadow-xs' : 'text-slate-600 hover:text-slate-900'"
        >
          <Wifi class="w-3.5 h-3.5" />
          <span>同 Wi-Fi</span>
        </button>
      </div>

      <!-- 模式说明与注意事项 -->
      <div v-if="activeTab === 'server'" class="p-2.5 bg-rose-50/70 border border-rose-200 rounded-xl text-left text-xs space-y-1 text-rose-900">
        <div class="font-bold flex items-center gap-1 text-rose-700">
          <span>🚀 阿里云公网服务器直连：</span>
        </div>
        <p class="text-[11px] text-rose-800 leading-relaxed">
          手机用4G/5G流量或自习室Wi-Fi<strong>均可秒级直连</strong>！手机端注册、答题与电脑端后台数据<strong>100% 实时互通同步</strong>，管理后台秒级可见！
        </p>
      </div>

      <div v-else-if="activeTab === 'cloud'" class="p-2.5 bg-emerald-50/70 border border-emerald-200 rounded-xl text-left text-xs space-y-1 text-emerald-900">
        <div class="font-bold flex items-center gap-1 text-emerald-700">
          <Globe class="w-3.5 h-3.5" />
          <span>GitHub Pages 镜像特性：</span>
        </div>
        <p class="text-[11px] text-emerald-800 leading-relaxed">
          永久免费公网托管镜像，离线与本地刷题体验极佳。在此注册的考生也会在管理员后台自动合流同步！
        </p>
      </div>

      <div v-else class="p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-left text-xs space-y-1 text-slate-800">
        <div class="font-bold flex items-center gap-1 text-slate-700">
          <Wifi class="w-3.5 h-3.5" />
          <span>本地局域网特性：</span>
        </div>
        <p class="text-[11px] text-slate-600 leading-relaxed">
          电脑开机并在同一 Wi-Fi 下访问。适合电脑本地开发调试。
        </p>
      </div>

      <!-- QR Code Container -->
      <div class="flex flex-col items-center justify-center bg-slate-50 border border-slate-200 rounded-xl p-4 my-2.5">
        <div v-if="loading" class="py-12 text-sm text-slate-400 animate-pulse">
          正在生成手机访问二维码...
        </div>
        <template v-else-if="qrDataUrl">
          <img 
            :src="qrDataUrl" 
            alt="手机扫码二维码"
            class="w-44 h-44 rounded-lg shadow-xs bg-white p-1"
          />
          <div class="mt-2 text-center">
            <span class="inline-flex items-center gap-1 text-[11px] text-slate-600 bg-white border border-slate-200 px-2.5 py-0.5 rounded-full font-medium">
              手机相机或浏览器扫一扫直接打开
            </span>
          </div>
        </template>
        <div v-else class="text-xs text-rose-500 py-6">
          二维码生成失败，请直接复制下方网址
        </div>
      </div>

      <!-- URL Copy -->
      <div class="mt-2 text-left">
        <label class="block text-xs font-medium text-slate-600 mb-1">
          当前访问网址：
        </label>
        <div class="flex items-center gap-1.5 bg-slate-100 rounded-lg p-1.5 border border-slate-200">
          <input 
            type="text" 
            readonly 
            :value="getActiveUrl()"
            class="text-xs text-slate-700 font-mono px-2 py-1 bg-transparent w-full focus:outline-hidden select-all"
          />
          <button 
            @click="copyUrl(getActiveUrl())"
            class="px-2.5 py-1 text-xs font-medium rounded-md bg-white text-slate-700 border border-slate-200 hover:bg-slate-50 shrink-0 flex items-center gap-1 shadow-2xs transition cursor-pointer"
          >
            <component :is="copied ? Check : Copy" class="w-3 h-3 text-slate-500" />
            <span>{{ copied ? '已复制' : '复制' }}</span>
          </button>
        </div>
      </div>

      <div class="mt-3 text-center">
        <button 
          @click="emit('close')"
          class="w-full py-2 bg-slate-800 hover:bg-slate-900 text-white rounded-xl text-sm font-medium transition cursor-pointer"
        >
          关闭
        </button>
      </div>
    </div>
  </div>
</template>
