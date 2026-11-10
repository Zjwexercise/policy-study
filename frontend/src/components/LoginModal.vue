<script setup>
import { ref, computed, watch } from 'vue';
import { 
  User, 
  Lock, 
  UserPlus, 
  LogIn, 
  LogOut, 
  Cloud, 
  RefreshCw, 
  CheckCircle2, 
  AlertCircle, 
  X, 
  Server, 
  ShieldCheck, 
  Smartphone,
  ChevronDown,
  ChevronUp
} from 'lucide-vue-next';
import { auth } from '../auth';

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['close', 'login-success']);

const activeTab = ref('login'); // 'login' | 'register'
const username = ref('');
const password = ref('');
const nickname = ref('');
const loading = ref(false);
const errorMsg = ref('');
const successMsg = ref('');
const showServerConfig = ref(false);
const serverUrlInput = ref(auth.customServerUrl.value || '');
const serverTesting = ref(false);
const serverTestResult = ref(null); // { success: boolean, msg: string }

// 监听弹窗打开，重置表单与消息
watch(() => props.show, (newVal) => {
  if (newVal) {
    errorMsg.value = '';
    successMsg.value = '';
    serverTestResult.value = null;
    serverUrlInput.value = auth.customServerUrl.value || '';
  }
});

const currentUser = computed(() => auth.currentUser.value);
const syncStatus = computed(() => auth.syncStatus.value);
const lastSyncTime = computed(() => auth.lastSyncTime.value);

const isStaticHosting = computed(() => {
  return window.location.hostname.includes('github.io') && !auth.customServerUrl.value;
});

const handleAuth = async () => {
  if (isStaticHosting.value) {
    errorMsg.value = '提示：当前为 GitHub Pages 免开机版，无云端数据库。您无需登录即可直接做题！若需账号登录，请连接同Wi-Fi电脑后台或在下方配置云端后台地址。';
    return;
  }

  if (!username.value.trim()) {
    errorMsg.value = '请输入用户名';
    return;
  }
  if (!password.value.trim()) {
    errorMsg.value = '请输入密码';
    return;
  }

  loading.value = true;
  errorMsg.value = '';
  successMsg.value = '';

  try {
    if (activeTab.value === 'register') {
      const u = await auth.register(username.value, password.value, nickname.value);
      successMsg.value = `注册成功！欢迎同学：${u.nickname || u.username}`;
    } else {
      const u = await auth.login(username.value, password.value);
      successMsg.value = `登录成功！已自动无损同步云端刷题记录。`;
    }

    emit('login-success', auth.currentUser.value);
    setTimeout(() => {
      emit('close');
    }, 900);
  } catch (err) {
    errorMsg.value = err.message || '操作失败，请检查网络或账号密码';
  } finally {
    loading.value = false;
  }
};

const handleManualSync = async () => {
  loading.value = true;
  errorMsg.value = '';
  successMsg.value = '';
  try {
    await auth.syncNow();
    successMsg.value = '云端数据双向同步完成！';
  } catch (err) {
    errorMsg.value = err.message || '同步失败，请检查网络';
  } finally {
    loading.value = false;
  }
};

const handleLogout = async () => {
  if (confirm('确认退出当前账号吗？（退出登录后，本地已刷题目记录仍会保留，重新登录即可再次云同步）')) {
    await auth.logout();
    successMsg.value = '已退出登录，当前为访客模式';
  }
};

const saveServerUrl = () => {
  auth.setCustomServerUrl(serverUrlInput.value);
  serverTestResult.value = { success: true, msg: '服务器地址已保存！' };
};

const testServerConnection = async () => {
  serverTesting.value = true;
  serverTestResult.value = null;
  const targetUrl = (serverUrlInput.value || '').trim() || auth.getEffectiveApiBase();
  let cleanUrl = targetUrl.replace(/\/+$/, '');
  if (!cleanUrl.endsWith('/api')) cleanUrl += '/api';

  try {
    const res = await fetch(`${cleanUrl}/auth/me`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
      signal: AbortSignal.timeout ? AbortSignal.timeout(3000) : undefined
    });
    // 401 说明服务端正常运行且路由存在（只是未带Token）
    if (res.status === 401 || res.status === 200) {
      serverTestResult.value = { success: true, msg: '连接成功！该服务器支持云端账号与同步。' };
    } else {
      serverTestResult.value = { success: false, msg: `连接响应异常 (HTTP ${res.status})` };
    }
  } catch (e) {
    serverTestResult.value = { 
      success: false, 
      msg: '连接超时或失败。若为手机跨设备访问，请确保电脑与手机在同一WiFi，或填写了公网云服务地址。' 
    };
  } finally {
    serverTesting.value = false;
  }
};
</script>

<template>
  <div 
    v-if="show" 
    class="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-900/60 backdrop-blur-xs transition-opacity animate-in fade-in duration-200"
    @click.self="emit('close')"
  >
    <div class="bg-white rounded-2xl shadow-2xl border border-slate-100 w-full max-w-md overflow-hidden flex flex-col max-h-[92vh]">
      <!-- 弹窗顶栏 -->
      <div class="px-5 py-4 bg-linear-to-r from-rose-500 to-red-600 text-white flex items-center justify-between shrink-0">
        <div class="flex items-center space-x-2.5">
          <div class="w-9 h-9 rounded-xl bg-white/20 backdrop-blur-md flex items-center justify-center text-white font-bold text-lg shadow-inner">
            <Cloud class="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 class="font-bold text-base sm:text-lg leading-tight">用户登录与多端云同步</h3>
            <p class="text-xs text-rose-100/90 leading-tight">手机与电脑登录同账号，做题记录实时互通</p>
          </div>
        </div>
        <button 
          @click="emit('close')" 
          class="p-1.5 rounded-lg hover:bg-white/20 text-rose-100 hover:text-white transition cursor-pointer"
        >
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- 弹窗主体内容 -->
      <div class="p-5 overflow-y-auto space-y-4">
        <!-- 成功提示 -->
        <div v-if="successMsg" class="p-3 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center gap-2.5 text-emerald-800 text-xs sm:text-sm animate-in fade-in">
          <CheckCircle2 class="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{{ successMsg }}</span>
        </div>

        <!-- 错误提示 -->
        <div v-if="errorMsg" class="p-3 bg-rose-50 border border-rose-200 rounded-xl flex items-center gap-2.5 text-rose-800 text-xs sm:text-sm animate-in fade-in">
          <AlertCircle class="w-4 h-4 text-rose-600 shrink-0" />
          <span>{{ errorMsg }}</span>
        </div>

        <!-- 状态A：用户已登录 -->
        <div v-if="currentUser" class="space-y-4">
          <!-- 用户名片 -->
          <div class="p-4 bg-slate-50 border border-slate-200 rounded-xl flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="w-12 h-12 rounded-full bg-linear-to-tr from-rose-500 to-amber-400 text-white font-bold text-lg flex items-center justify-center shadow-sm">
                {{ (currentUser.nickname || currentUser.username || '用').slice(0, 1) }}
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <span class="font-bold text-slate-800 text-base">{{ currentUser.nickname || currentUser.username }}</span>
                  <span class="px-1.5 py-0.5 text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 rounded">已登录</span>
                </div>
                <p class="text-xs text-slate-500">账号: @{{ currentUser.username }}</p>
              </div>
            </div>
            <button 
              @click="handleLogout"
              class="px-3 py-1.5 text-xs text-slate-600 hover:text-rose-600 hover:bg-rose-50 border border-slate-200 hover:border-rose-200 rounded-lg transition font-medium flex items-center gap-1 cursor-pointer"
            >
              <LogOut class="w-3.5 h-3.5" />
              退出
            </button>
          </div>

          <!-- 自动云同步状态卡 -->
          <div class="p-4 bg-indigo-50/60 border border-indigo-100 rounded-xl space-y-2.5">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2 text-indigo-900 font-semibold text-sm">
                <Cloud class="w-4 h-4 text-indigo-600" />
                <span>自动双向云同步状态</span>
              </div>
              <span 
                class="px-2 py-0.5 text-xs font-medium rounded-full flex items-center gap-1"
                :class="[
                  syncStatus === 'syncing' ? 'bg-amber-100 text-amber-800' :
                  syncStatus === 'synced' ? 'bg-emerald-100 text-emerald-800' :
                  syncStatus === 'error' ? 'bg-rose-100 text-rose-800' : 'bg-slate-100 text-slate-700'
                ]"
              >
                <RefreshCw v-if="syncStatus === 'syncing'" class="w-3 h-3 animate-spin" />
                <span v-if="syncStatus === 'syncing'">同步中...</span>
                <span v-else-if="syncStatus === 'synced'">已实时同步</span>
                <span v-else-if="syncStatus === 'error'">同步失败</span>
                <span v-else>待同步</span>
              </span>
            </div>

            <p class="text-xs text-indigo-700/80 leading-relaxed">
              ✨ <strong>无需每次手动同步</strong>：平时在手机或电脑答题、斩杀、收藏或写笔记，系统都会在后台自动双向同步！
            </p>

            <div class="text-[11px] text-slate-500 pt-1 flex items-center justify-between border-t border-indigo-100/60">
              <span>最后同步时间：{{ lastSyncTime || '刚刚' }}</span>
              <button 
                @click="handleManualSync" 
                :disabled="loading"
                class="text-indigo-600 hover:text-indigo-800 font-medium flex items-center gap-1 cursor-pointer hover:underline disabled:opacity-50"
              >
                <RefreshCw class="w-3 h-3" :class="{ 'animate-spin': loading }" />
                立即对齐同步
              </button>
            </div>
          </div>
        </div>

        <!-- 状态B：未登录，显示登录/注册表单 -->
        <div v-else class="space-y-4">
          <!-- GitHub Pages 静态免开机模式特别提示 -->
          <div v-if="isStaticHosting" class="p-3.5 bg-amber-50/90 border border-amber-200 rounded-xl text-xs space-y-1.5 text-amber-900 leading-relaxed">
            <div class="font-bold flex items-center gap-1.5 text-amber-800 text-sm">
              <span>💡 手机免开机刷题无需登录！</span>
            </div>
            <p>
              当前为 <strong>GitHub Pages 免开机版</strong>。你可以直接点击底部的【暂不登录 (访客模式)】，题目已全量离线内嵌，你做的每一题都会自动保存在手机中，电脑关机也不影响使用！
            </p>
            <p class="text-amber-700 text-[11px]">
              ⚠️ 若要使用账号登录并在电脑与手机间实时同步，请将手机连接同一 Wi-Fi 打开电脑局域网版（<code>http://192.168.1.20:8000</code>），或在下方展开【云端服务器配置】填入在线后台网址。
            </p>
          </div>

          <!-- 切换 Tab -->
          <div class="flex border-b border-slate-200">
            <button 
              @click="activeTab = 'login'; errorMsg = '';"
              class="flex-1 py-2 text-center text-sm font-semibold transition cursor-pointer border-b-2"
              :class="activeTab === 'login' ? 'border-rose-600 text-rose-600' : 'border-transparent text-slate-500 hover:text-slate-800'"
            >
              登录已有账号
            </button>
            <button 
              @click="activeTab = 'register'; errorMsg = '';"
              class="flex-1 py-2 text-center text-sm font-semibold transition cursor-pointer border-b-2"
              :class="activeTab === 'register' ? 'border-rose-600 text-rose-600' : 'border-transparent text-slate-500 hover:text-slate-800'"
            >
              注册新账号
            </button>
          </div>

          <!-- 表单字段 -->
          <form @submit.prevent="handleAuth" class="space-y-3.5">
            <div>
              <label class="block text-xs font-semibold text-slate-700 mb-1">用户名 / 账号</label>
              <div class="relative">
                <input 
                  v-model="username"
                  type="text"
                  required
                  placeholder="例如: zjw2027"
                  class="w-full pl-9 pr-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-rose-500/20 focus:border-rose-500"
                />
                <User class="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              </div>
            </div>

            <div v-if="activeTab === 'register'">
              <label class="block text-xs font-semibold text-slate-700 mb-1">用户昵称 (选填)</label>
              <div class="relative">
                <input 
                  v-model="nickname"
                  type="text"
                  placeholder="例如: 建威同学"
                  class="w-full pl-9 pr-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-rose-500/20 focus:border-rose-500"
                />
                <UserPlus class="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              </div>
            </div>

            <div>
              <label class="block text-xs font-semibold text-slate-700 mb-1">登录密码</label>
              <div class="relative">
                <input 
                  v-model="password"
                  type="password"
                  required
                  placeholder="输入不少于4位的密码"
                  class="w-full pl-9 pr-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-rose-500/20 focus:border-rose-500"
                />
                <Lock class="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              </div>
            </div>

            <button 
              type="submit" 
              :disabled="loading"
              class="w-full py-2.5 px-4 bg-linear-to-r from-rose-600 to-red-500 hover:from-rose-700 hover:to-red-600 text-white font-semibold text-sm rounded-xl shadow-md transition flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
            >
              <RefreshCw v-if="loading" class="w-4 h-4 animate-spin" />
              <LogIn v-else class="w-4 h-4" />
              <span>{{ activeTab === 'register' ? '立即注册并同步' : '立即登录并同步' }}</span>
            </button>
          </form>

          <p class="text-[11px] text-slate-400 text-center">
            登录后当前设备的做题数据将与云端智能合并，换手机/换电脑直接登录即可继续刷题。
          </p>
        </div>

        <!-- 高级设置：云端/后台服务地址 -->
        <div class="pt-2 border-t border-slate-100">
          <button 
            @click="showServerConfig = !showServerConfig"
            class="w-full flex items-center justify-between text-xs text-slate-500 hover:text-slate-800 py-1 cursor-pointer transition font-medium"
          >
            <span class="flex items-center gap-1.5">
              <Server class="w-3.5 h-3.5 text-slate-400" />
              <span>云端服务器配置 (电脑关机免开机支持)</span>
            </span>
            <component :is="showServerConfig ? ChevronUp : ChevronDown" class="w-3.5 h-3.5 text-slate-400" />
          </button>

          <div v-if="showServerConfig" class="mt-2.5 p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-2.5 text-xs text-slate-600 animate-in fade-in">
            <p class="text-[11px] leading-relaxed text-slate-500">
              默认连接本机后端（同Wi-Fi下自动识别）。若想在<strong>电脑关机</strong>时也能24小时随时在手机上跨网登录，可在此填入免费云服务器地址（如 Render / Zeabur 部署的后端地址）：
            </p>
            <div class="flex gap-2">
              <input 
                v-model="serverUrlInput"
                type="text"
                placeholder="留空即使用当前网页默认后台"
                class="flex-1 px-2.5 py-1.5 text-xs bg-white border border-slate-200 rounded-lg focus:outline-hidden focus:ring-1 focus:ring-rose-500"
              />
              <button 
                @click="saveServerUrl"
                class="px-2.5 py-1.5 bg-slate-200 hover:bg-slate-300 text-slate-700 font-semibold rounded-lg transition cursor-pointer"
              >
                保存
              </button>
            </div>

            <div class="flex items-center justify-between pt-1">
              <button 
                @click="testServerConnection"
                :disabled="serverTesting"
                class="text-[11px] text-indigo-600 hover:underline flex items-center gap-1 cursor-pointer disabled:opacity-50"
              >
                <RefreshCw class="w-3 h-3" :class="{ 'animate-spin': serverTesting }" />
                测试服务连通性
              </button>
            </div>

            <div v-if="serverTestResult" class="text-[11px] p-2 rounded-lg" :class="serverTestResult.success ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'">
              {{ serverTestResult.msg }}
            </div>
          </div>
        </div>
      </div>

      <!-- 弹窗底栏 -->
      <div class="px-5 py-3 bg-slate-50 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500 shrink-0">
        <span class="flex items-center gap-1">
          <ShieldCheck class="w-4 h-4 text-emerald-600" />
          <span>数据高强度PBKDF2加密储存</span>
        </span>
        <button 
          @click="emit('close')"
          class="px-3 py-1 bg-white hover:bg-slate-100 border border-slate-200 rounded-lg transition cursor-pointer font-medium text-slate-600"
        >
          暂不登录 (访客模式)
        </button>
      </div>
    </div>
  </div>
</template>
