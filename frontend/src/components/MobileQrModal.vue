<script setup>
import { ref, onMounted } from 'vue';
import { api } from '../api';
import QRCode from 'qrcode';
import { X, Smartphone, Wifi, Copy, Check, RefreshCw } from 'lucide-vue-next';

defineProps({
  show: Boolean
});

const emit = defineEmits(['close', 'open-sync']);

const loading = ref(true);
const targetUrl = ref('');
const qrDataUrl = ref('');
const copied = ref(false);

const loadInfo = async () => {
  loading.value = true;
  try {
    let url = window.location.href;
    try {
      const net = await api.getNetworkInfo();
      if (net && net.mobile_url && !net.is_cloud) {
        url = net.mobile_url;
      }
    } catch {
      // 降级使用当前浏览器地址
    }
    targetUrl.value = url;

    // 纯前端离线生成清晰二维码
    qrDataUrl.value = await QRCode.toDataURL(url, {
      width: 260,
      margin: 2,
      color: {
        dark: '#1e293b',
        light: '#ffffff'
      }
    });
  } catch (err) {
    console.error('加载二维码失败', err);
  } finally {
    loading.value = false;
  }
};

const copyUrl = () => {
  if (!targetUrl.value) return;
  navigator.clipboard.writeText(targetUrl.value);
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
    <div class="bg-white rounded-2xl max-w-sm w-full p-6 shadow-2xl relative border border-slate-100">
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
        <p class="text-xs text-slate-500 mt-0.5">自习室、地铁、床上随时手机复习考研政治</p>
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
            class="w-48 h-48 rounded-lg shadow-xs bg-white p-1"
          />
          <div class="mt-2.5 text-center">
            <span class="inline-flex items-center gap-1 text-[11px] text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full font-medium">
              <Wifi class="w-3 h-3" /> 微信、浏览器扫一扫即可直接打开
            </span>
          </div>
        </template>
        <div v-else class="text-xs text-rose-500 py-6">
          二维码生成失败，请直接复制下方网址
        </div>
      </div>

      <!-- URL Copy -->
      <div v-if="targetUrl" class="mt-3">
        <label class="block text-xs font-medium text-slate-600 mb-1">手机浏览器直接打开：</label>
        <div class="flex items-center gap-1.5 bg-slate-100 rounded-lg p-1.5 border border-slate-200">
          <input 
            type="text" 
            readonly 
            :value="targetUrl"
            class="text-xs text-slate-700 font-mono px-2 py-1 bg-transparent w-full focus:outline-hidden select-all"
          />
          <button 
            @click="copyUrl"
            class="px-2.5 py-1 text-xs font-medium rounded-md bg-white text-slate-700 border border-slate-200 hover:bg-slate-50 shrink-0 flex items-center gap-1 shadow-2xs transition cursor-pointer"
          >
            <component :is="copied ? Check : Copy" class="w-3 h-3 text-slate-500" />
            <span>{{ copied ? '已复制' : '复制' }}</span>
          </button>
        </div>
      </div>

      <!-- Cross-Device Sync Guidance Hint -->
      <div class="mt-3 p-2.5 bg-indigo-50/70 border border-indigo-150 rounded-xl text-left">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-1.5 text-indigo-900 font-medium text-xs">
            <RefreshCw class="w-3.5 h-3.5 text-indigo-600 shrink-0" />
            <span>想同步电脑和手机的做题记录？</span>
          </div>
          <button 
            @click="emit('open-sync'); emit('close');"
            class="text-[11px] text-indigo-600 hover:text-indigo-800 font-semibold underline underline-offset-2 cursor-pointer"
          >
            打开同步
          </button>
        </div>
        <p class="text-[11px] text-indigo-700/80 mt-1">
          使用【跨端同步】一键复制口令，微信发到手机即可合并两端题目！
        </p>
      </div>

      <div class="mt-4 text-center">
        <button 
          @click="emit('close')"
          class="w-full py-2 bg-slate-800 hover:bg-slate-900 text-white rounded-xl text-sm font-medium transition cursor-pointer"
        >
          我知道了
        </button>
      </div>
    </div>
  </div>
</template>
