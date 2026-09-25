<script setup>
import { ref, onMounted } from 'vue';
import { api } from '../api';
import { X, Smartphone, Wifi, Copy, Check } from 'lucide-vue-next';

defineProps({
  show: Boolean
});

const emit = defineEmits(['close']);

const loading = ref(true);
const networkInfo = ref(null);
const copied = ref(false);

const loadInfo = async () => {
  loading.value = true;
  try {
    const data = await api.getNetworkInfo();
    networkInfo.value = data;
  } catch (err) {
    console.error('加载网络信息失败', err);
  } finally {
    loading.value = false;
  }
};

const copyUrl = () => {
  if (!networkInfo.value?.mobile_url) return;
  navigator.clipboard.writeText(networkInfo.value.mobile_url);
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

      <div class="text-center mb-4">
        <div class="inline-flex p-3 bg-rose-50 text-rose-600 rounded-2xl mb-2">
          <Smartphone class="w-6 h-6" />
        </div>
        <h3 class="text-lg font-bold text-slate-900">手机扫码刷题</h3>
        <p class="text-xs text-slate-500 mt-1">在床上、自习室随时用手机复习考研政治</p>
      </div>

      <!-- QR Code Container -->
      <div class="flex flex-col items-center justify-center bg-slate-50 border border-slate-200 rounded-xl p-4 my-3">
        <div v-if="loading" class="py-12 text-sm text-slate-400 animate-pulse">
          正在检测局域网并生成二维码...
        </div>
        <template v-else-if="networkInfo?.qr_code">
          <img 
            :src="networkInfo.qr_code" 
            alt="手机扫码二维码"
            class="w-48 h-48 rounded-lg shadow-xs bg-white p-1"
          />
          <div class="mt-3 text-center">
            <span class="inline-flex items-center gap-1 text-[11px] text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full font-medium">
              <Wifi class="w-3 h-3" /> 手机和电脑连同一 Wi-Fi 或手机热点即可
            </span>
          </div>
        </template>
        <div v-else class="text-xs text-rose-500 py-6">
          无法获取网络信息，请确保服务已启动
        </div>
      </div>

      <!-- URL Copy -->
      <div v-if="networkInfo" class="mt-4">
        <label class="block text-xs font-medium text-slate-600 mb-1">手机浏览器直接输入网址：</label>
        <div class="flex items-center gap-1.5 bg-slate-100 rounded-lg p-1.5 border border-slate-200">
          <input 
            type="text" 
            readonly 
            :value="networkInfo.mobile_url"
            class="text-xs text-slate-700 font-mono px-2 py-1 bg-transparent w-full focus:outline-hidden"
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

      <div class="mt-5 text-center">
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
