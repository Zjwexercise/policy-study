<script setup>
import { ref, computed, watch, onMounted } from 'vue';
import { api } from '../api';
import { 
  X, 
  RefreshCw, 
  Upload, 
  Download, 
  Copy, 
  Check, 
  Smartphone, 
  Laptop, 
  CheckCircle2, 
  AlertCircle, 
  HelpCircle, 
  ShieldCheck, 
  Trash2,
  FileText,
  Sparkles,
  Database,
  ArrowRight
} from 'lucide-vue-next';

const props = defineProps({
  show: Boolean
});

const emit = defineEmits(['close', 'synced']);

const activeTab = ref('export'); // 'export' | 'import' | 'cloud'
const localStats = ref(null);
const syncCode = ref('');
const codeCopied = ref(false);
const inputCode = ref('');
const importMode = ref('merge'); // 'merge' | 'overwrite'
const importing = ref(false);
const importResult = ref(null);
const importError = ref('');
const fileInput = ref(null);
const parsedPreview = ref(null);

// 清空确认
const showClearConfirm = ref(false);
const clearSuccess = ref(false);

const loadLocalData = () => {
  try {
    const data = api.exportData();
    localStats.value = data.stats || {};
    syncCode.value = api.exportDataAsCode();
  } catch (err) {
    console.error('加载本地数据失败', err);
  }
};

watch(() => props.show, (newVal) => {
  if (newVal) {
    loadLocalData();
    importResult.value = null;
    importError.value = '';
    showClearConfirm.value = false;
    clearSuccess.value = false;
  }
});

// 监听输入口令，实时解析预览
watch(inputCode, (val) => {
  importError.value = '';
  parsedPreview.value = null;
  if (!val || !val.trim()) return;
  try {
    const parsed = api.parseSyncInput(val);
    if (parsed) {
      let ans = 0, wrong = 0, killed = 0, notes = 0;
      const rec = parsed.records || {};
      for (const k of Object.keys(rec)) {
        if (k.startsWith('policy_ans_')) ans++;
        else if (k.startsWith('policy_wrong_cnt_')) wrong++;
        else if (k.startsWith('policy_killed_') && !k.startsWith('policy_killed_at_') && rec[k] === '1') killed++;
        else if (k.startsWith('policy_note_')) notes++;
      }
      parsedPreview.value = {
        total_keys: Object.keys(rec).length,
        ans,
        wrong,
        killed,
        notes,
        exported_at: parsed.exported_at ? new Date(parsed.exported_at).toLocaleString() : '未知'
      };
    }
  } catch (e) {
    // 尚未输入完毕或格式不符合，不打断用户输入
  }
});

// 复制口令
const copySyncCode = () => {
  if (!syncCode.value) return;
  navigator.clipboard.writeText(syncCode.value);
  codeCopied.value = true;
  setTimeout(() => {
    codeCopied.value = false;
  }, 2500);
};

// 下载 JSON 备份文件
const downloadBackupJson = () => {
  try {
    const data = api.exportData();
    const str = JSON.stringify(data, null, 2);
    const blob = new Blob([str], { type: 'application/json;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    const now = new Date();
    const timeStr = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}`;
    a.href = url;
    a.download = `考研政治刷题进度备份_${timeStr}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  } catch (err) {
    alert('下载备份失败: ' + err.message);
  }
};

// 触发选择文件上传
const triggerFileUpload = () => {
  if (fileInput.value) fileInput.value.click();
};

const handleFileChange = (e) => {
  const file = e.target.files?.[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = (event) => {
    inputCode.value = event.target?.result || '';
  };
  reader.readAsText(file);
};

// 执行导入同步
const handleImport = () => {
  if (!inputCode.value || !inputCode.value.trim()) {
    importError.value = '请先粘贴同步口令或选择备份文件！';
    return;
  }

  importing.value = true;
  importError.value = '';
  importResult.value = null;

  try {
    const res = api.importData(inputCode.value.trim(), importMode.value);
    importResult.value = res;
    // 延迟 1.5 秒刷新页面，确保状态全面重载
    setTimeout(() => {
      emit('synced');
      window.location.reload();
    }, 1500);
  } catch (err) {
    importError.value = err.message || '导入同步失败，请检查口令是否完整';
  } finally {
    importing.value = false;
  }
};

// 清空本机数据
const handleClearAll = () => {
  try {
    api.clearAllUserData();
    clearSuccess.value = true;
    showClearConfirm.value = false;
    setTimeout(() => {
      emit('synced');
      window.location.reload();
    }, 1200);
  } catch (err) {
    alert('清空失败: ' + err.message);
  }
};

onMounted(() => {
  if (props.show) loadLocalData();
});
</script>

<template>
  <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-200">
    <div class="bg-white rounded-2xl max-w-xl w-full p-4 sm:p-6 shadow-2xl relative border border-slate-100 max-h-[92vh] flex flex-col">
      <!-- Close button -->
      <button 
        @click="emit('close')"
        class="absolute top-4 right-4 p-1.5 text-slate-400 hover:text-slate-600 rounded-full hover:bg-slate-100 transition cursor-pointer"
      >
        <X class="w-5 h-5" />
      </button>

      <!-- Modal Header -->
      <div class="flex items-center gap-3 mb-4 shrink-0">
        <div class="w-10 h-10 rounded-xl bg-linear-to-tr from-indigo-600 to-blue-500 flex items-center justify-center text-white shadow-xs">
          <RefreshCw class="w-5 h-5" />
        </div>
        <div>
          <div class="flex items-center gap-2">
            <h3 class="text-base sm:text-lg font-bold text-slate-900">跨端数据同步与备份</h3>
            <span class="px-2 py-0.5 text-[10px] font-semibold bg-emerald-50 text-emerald-700 rounded-full border border-emerald-200">
              免登录 · 0 成本
            </span>
          </div>
          <p class="text-xs text-slate-500">手机与电脑进度互通 · 智能合并 · 绝不丢题</p>
        </div>
      </div>

      <!-- Navigation Tabs -->
      <div class="flex border-b border-slate-200 mb-4 shrink-0">
        <button
          @click="activeTab = 'export'"
          class="flex items-center gap-1.5 py-2 px-3 sm:px-4 text-xs sm:text-sm font-semibold border-b-2 transition cursor-pointer"
          :class="activeTab === 'export' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-slate-500 hover:text-slate-800'"
        >
          <Upload class="w-4 h-4" />
          <span>📤 导出进度 / 发到手机</span>
        </button>

        <button
          @click="activeTab = 'import'"
          class="flex items-center gap-1.5 py-2 px-3 sm:px-4 text-xs sm:text-sm font-semibold border-b-2 transition cursor-pointer"
          :class="activeTab === 'import' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-slate-500 hover:text-slate-800'"
        >
          <Download class="w-4 h-4" />
          <span>📥 导入进度 / 跨端合并</span>
        </button>

        <button
          @click="activeTab = 'cloud'"
          class="flex items-center gap-1.5 py-2 px-3 sm:px-4 text-xs sm:text-sm font-semibold border-b-2 transition cursor-pointer"
          :class="activeTab === 'cloud' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-slate-500 hover:text-slate-800'"
        >
          <HelpCircle class="w-4 h-4" />
          <span>☁️ 同步原理与账号说明</span>
        </button>
      </div>

      <!-- Tab Content Area (Scrollable) -->
      <div class="overflow-y-auto pr-1 flex-1 text-slate-700 text-xs sm:text-sm space-y-4">
        
        <!-- Tab 1: Export -->
        <div v-if="activeTab === 'export'" class="space-y-4">
          <!-- Current Stats Card -->
          <div class="bg-indigo-50/60 border border-indigo-100 rounded-xl p-3 sm:p-4">
            <div class="text-xs font-semibold text-indigo-900 mb-2 flex items-center justify-between">
              <span>当前设备记录概览：</span>
              <span class="text-[11px] font-normal text-indigo-600">共 {{ localStats?.total_keys || 0 }} 项本地数据</span>
            </div>
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center">
              <div class="bg-white/80 p-2 rounded-lg border border-indigo-50">
                <div class="text-xs text-slate-500">已做题</div>
                <div class="text-base font-bold text-slate-800 font-mono">{{ localStats?.answered || 0 }} 题</div>
              </div>
              <div class="bg-white/80 p-2 rounded-lg border border-indigo-50">
                <div class="text-xs text-slate-500">错题记录</div>
                <div class="text-base font-bold text-rose-600 font-mono">{{ localStats?.wrong || 0 }} 题</div>
              </div>
              <div class="bg-white/80 p-2 rounded-lg border border-indigo-50">
                <div class="text-xs text-slate-500">已斩熟题</div>
                <div class="text-base font-bold text-rose-700 font-mono">{{ localStats?.killed || 0 }} 题</div>
              </div>
              <div class="bg-white/80 p-2 rounded-lg border border-indigo-50">
                <div class="text-xs text-slate-500">考点笔记</div>
                <div class="text-base font-bold text-amber-600 font-mono">{{ localStats?.notes || 0 }} 条</div>
              </div>
            </div>
          </div>

          <!-- Method 1: Sync Code -->
          <div class="border border-slate-200 rounded-xl p-3.5 bg-slate-50/50">
            <div class="flex items-center justify-between mb-2">
              <div class="font-bold text-slate-800 text-xs sm:text-sm flex items-center gap-1.5">
                <Sparkles class="w-4 h-4 text-indigo-600" />
                <span>方式一：一键复制「同步口令」（最快最省心）</span>
              </div>
              <span class="text-[11px] text-emerald-600 font-medium bg-emerald-50 px-2 py-0.5 rounded-full">推荐</span>
            </div>
            <p class="text-xs text-slate-500 mb-2.5">
              点击下方按钮复制口令，通过微信「文件传输助手」或 QQ 发送给另一端，在另一端导入即可！
            </p>

            <div class="relative mb-2">
              <textarea
                readonly
                :value="syncCode"
                rows="2"
                class="w-full text-[11px] font-mono bg-white p-2.5 rounded-lg border border-slate-200 text-slate-600 focus:outline-hidden resize-none select-all"
                placeholder="同步口令生成中..."
              ></textarea>
            </div>

            <button
              @click="copySyncCode"
              class="w-full py-2.5 px-4 rounded-xl text-xs sm:text-sm font-semibold flex items-center justify-center gap-2 transition cursor-pointer shadow-xs"
              :class="codeCopied ? 'bg-emerald-600 text-white' : 'bg-indigo-600 hover:bg-indigo-700 text-white'"
            >
              <component :is="codeCopied ? Check : Copy" class="w-4 h-4" />
              <span>{{ codeCopied ? '已复制同步口令！请发至微信文件传输助手' : '一键复制完整同步口令' }}</span>
            </button>
          </div>

          <!-- Method 2: Download File -->
          <div class="border border-slate-200 rounded-xl p-3.5 bg-slate-50/50 flex items-center justify-between gap-3">
            <div>
              <div class="font-bold text-slate-800 text-xs sm:text-sm flex items-center gap-1.5">
                <Download class="w-4 h-4 text-slate-600" />
                <span>方式二：下载数据备份文件 (.json)</span>
              </div>
              <p class="text-xs text-slate-500 mt-0.5">
                下载到电脑或手机长期保存，防止清理浏览器缓存造成数据丢失。
              </p>
            </div>
            <button
              @click="downloadBackupJson"
              class="px-3 py-2 bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 rounded-xl text-xs font-semibold shrink-0 transition cursor-pointer shadow-2xs flex items-center gap-1.5"
            >
              <Download class="w-3.5 h-3.5" />
              <span>下载备份</span>
            </button>
          </div>

          <!-- Step Instructions -->
          <div class="p-3 bg-amber-50/70 border border-amber-200 rounded-xl text-xs text-amber-900 space-y-1">
            <div class="font-semibold text-amber-950 flex items-center gap-1">
              <span>💡 跨端同步 3 步走：</span>
            </div>
            <ol class="list-decimal list-inside space-y-0.5 text-amber-900/90 pl-1">
              <li>在电脑点击上方【一键复制完整同步口令】；</li>
              <li>微信发给自己的手机（发在文件传输助手）；</li>
              <li>手机浏览器打开本站，点击右上角【跨端同步】->【导入进度】，粘贴并点击【智能合并】！</li>
            </ol>
          </div>
        </div>

        <!-- Tab 2: Import -->
        <div v-if="activeTab === 'import'" class="space-y-4">
          <div>
            <div class="flex items-center justify-between mb-1.5">
              <label class="block text-xs font-bold text-slate-800">
                粘贴同步口令文本 或 上传备份文件：
              </label>
              <button
                @click="triggerFileUpload"
                class="text-xs text-indigo-600 hover:text-indigo-800 font-medium flex items-center gap-1 cursor-pointer"
              >
                <Upload class="w-3.5 h-3.5" />
                <span>选择 .json 文件</span>
              </button>
              <input 
                ref="fileInput" 
                type="file" 
                accept=".json,application/json" 
                @change="handleFileChange" 
                class="hidden" 
              />
            </div>

            <textarea
              v-model="inputCode"
              rows="4"
              class="w-full text-xs font-mono bg-slate-50 p-2.5 rounded-xl border border-slate-200 text-slate-800 focus:outline-hidden focus:ring-2 focus:ring-indigo-500/20 resize-none"
              placeholder="在此粘贴另一台设备复制的 POLICY_SYNC#... 口令，或粘贴备份的 JSON 文本"
            ></textarea>
          </div>

          <!-- Mode Selector -->
          <div class="space-y-2">
            <label class="block text-xs font-bold text-slate-800">选择同步合并方式：</label>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              <label 
                class="flex items-start gap-2.5 p-3 rounded-xl border cursor-pointer transition text-xs"
                :class="importMode === 'merge' ? 'border-indigo-600 bg-indigo-50/50 text-indigo-950 font-medium shadow-2xs' : 'border-slate-200 bg-slate-50/50 text-slate-600 hover:bg-slate-100'"
              >
                <input 
                  type="radio" 
                  name="importMode" 
                  value="merge" 
                  v-model="importMode" 
                  class="mt-0.5 text-indigo-600" 
                />
                <div>
                  <div class="font-bold flex items-center gap-1">
                    <span>智能合并两端进度</span>
                    <span class="text-[10px] bg-indigo-600 text-white px-1.5 py-0.2 rounded font-normal">推荐</span>
                  </div>
                  <div class="text-[11px] text-slate-500 mt-0.5 leading-tight">
                    保留两端做过的全部题目，错题与斩题自动汇总，绝不弄丢任何一边的刷题心血！
                  </div>
                </div>
              </label>

              <label 
                class="flex items-start gap-2.5 p-3 rounded-xl border cursor-pointer transition text-xs"
                :class="importMode === 'overwrite' ? 'border-rose-600 bg-rose-50/50 text-rose-950 font-medium shadow-2xs' : 'border-slate-200 bg-slate-50/50 text-slate-600 hover:bg-slate-100'"
              >
                <input 
                  type="radio" 
                  name="importMode" 
                  value="overwrite" 
                  v-model="importMode" 
                  class="mt-0.5 text-rose-600" 
                />
                <div>
                  <div class="font-bold">完全覆盖当前设备</div>
                  <div class="text-[11px] text-slate-500 mt-0.5 leading-tight">
                    用导入的数据完全替代当前设备记录，适合将电脑数据完全克隆到全新手机。
                  </div>
                </div>
              </label>
            </div>
          </div>

          <!-- Error Feedback -->
          <div v-if="importError" class="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-600 flex items-center gap-2">
            <AlertCircle class="w-4 h-4 shrink-0 text-rose-500" />
            <span>{{ importError }}</span>
          </div>

          <!-- Success Feedback -->
          <div v-if="importResult" class="p-3.5 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800 space-y-1 animate-in fade-in">
            <div class="font-bold flex items-center gap-1.5 text-emerald-900 text-sm">
              <CheckCircle2 class="w-4 h-4 text-emerald-600" />
              <span>同步成功！数据已更新！</span>
            </div>
            <p class="text-xs text-emerald-700">
              共合并导入记录项：新增/更新已答题 {{ importResult.stats?.answer_count }} 题、错题 {{ importResult.stats?.wrong_count }} 题、斩熟题 {{ importResult.stats?.killed_count }} 题、考点笔记 {{ importResult.stats?.notes_count }} 条！页面即将自动刷新...
            </p>
          </div>

          <!-- Action Button -->
          <button
            @click="handleImport"
            :disabled="importing || !inputCode.trim()"
            class="w-full py-2.5 px-4 rounded-xl text-xs sm:text-sm font-semibold flex items-center justify-center gap-2 transition cursor-pointer shadow-xs disabled:opacity-50 disabled:cursor-not-allowed bg-indigo-600 hover:bg-indigo-700 text-white"
          >
            <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': importing }" />
            <span>{{ importing ? '正在同步并校验数据...' : (importMode === 'merge' ? '立即智能合并同步' : '立即覆盖导入') }}</span>
          </button>
        </div>

        <!-- Tab 3: Cloud & Account Explanation -->
        <div v-if="activeTab === 'cloud'" class="space-y-4">
          <div class="bg-slate-50 border border-slate-200 rounded-xl p-3.5 space-y-2.5">
            <div class="flex items-center gap-2 font-bold text-slate-800 text-xs sm:text-sm">
              <Database class="w-4 h-4 text-indigo-600" />
              <span>为什么电脑和手机的做题记录一开始不一样？</span>
            </div>
            <p class="text-xs text-slate-600 leading-relaxed">
              为了实现<strong>「0 元终极运行、0 广告、永久免费且保护绝对隐私」</strong>，本项目目前托管在 GitHub Pages 上。所有答题进度、正确率、错题本、斩题本和考点笔记，均直接保存在您各自设备浏览器的本地安全沙箱（localStorage）中。
            </p>
            <p class="text-xs text-slate-600 leading-relaxed">
              因此，手机浏览器与电脑浏览器默认互不干通。通过本站配备的<strong>「同步口令」</strong>，您只需复制一次发给微信，两端即可在 5 秒内实现<strong>智能合并</strong>，绝不会让您多花一分钱！
            </p>
          </div>

          <div class="bg-indigo-50/60 border border-indigo-100 rounded-xl p-3.5 space-y-2">
            <div class="flex items-center gap-2 font-bold text-indigo-950 text-xs sm:text-sm">
              <ShieldCheck class="w-4 h-4 text-emerald-600" />
              <span>后续是否可以开通云端账号登录实时同步？</span>
            </div>
            <p class="text-xs text-indigo-900/80 leading-relaxed">
              <strong>完全支持！</strong> 本应用底层数据接口已全部标准化预留完毕。后续若您需要“输入账号密码登录、多端无感静默实时自动同步”，可以无缝接入免费的云端数据库（如 Supabase、LeanCloud 或 Cloudflare KV 等）。
            </p>
            <p class="text-xs text-indigo-900/80 leading-relaxed">
              目前采用的【口令智能合并】兼具<strong>免注册、保护隐私、随时多重备份防丢失</strong>等优势，深受考研同学喜爱。
            </p>
          </div>

          <!-- Advanced: Clear Data Option -->
          <div class="pt-3 border-t border-slate-200">
            <div class="flex items-center justify-between">
              <div>
                <span class="text-xs font-semibold text-slate-700">危险操作：清空本机刷题记录</span>
                <p class="text-[11px] text-slate-400">重置当前设备上的所有做题记录、错题本与笔记</p>
              </div>
              <button
                v-if="!showClearConfirm"
                @click="showClearConfirm = true"
                class="px-2.5 py-1 text-xs text-rose-600 hover:text-rose-700 hover:bg-rose-50 border border-rose-200 rounded-lg transition cursor-pointer"
              >
                清空本机数据
              </button>
            </div>

            <!-- Clear Confirm Box -->
            <div v-if="showClearConfirm" class="mt-2.5 p-3 bg-rose-50 border border-rose-200 rounded-xl space-y-2 text-xs text-rose-800">
              <p class="font-bold">⚠️ 确定要清空当前设备上的所有做题数据吗？此操作不可逆！</p>
              <div class="flex items-center gap-2">
                <button
                  @click="handleClearAll"
                  class="px-3 py-1.5 bg-rose-600 hover:bg-rose-700 text-white rounded-lg font-semibold transition cursor-pointer"
                >
                  确认清空并重置
                </button>
                <button
                  @click="showClearConfirm = false"
                  class="px-3 py-1.5 bg-white text-slate-700 border border-slate-200 rounded-lg hover:bg-slate-50 transition cursor-pointer"
                >
                  取消
                </button>
              </div>
            </div>

            <div v-if="clearSuccess" class="mt-2 text-xs text-emerald-600 font-semibold">
              已清空本机所有数据，即将重新载入...
            </div>
          </div>
        </div>

      </div>

      <!-- Modal Footer -->
      <div class="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between shrink-0">
        <span class="text-[11px] text-slate-400 flex items-center gap-1">
          <ShieldCheck class="w-3.5 h-3.5 text-emerald-500" /> 数据仅在您自己的设备间传输，安全无忧
        </span>
        <button 
          @click="emit('close')"
          class="px-4 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition cursor-pointer"
        >
          完成
        </button>
      </div>
    </div>
  </div>
</template>
