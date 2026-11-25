<script setup>
import { ref, computed, onMounted } from 'vue';
import { 
  Users, 
  UserCheck, 
  UserX, 
  ShieldCheck, 
  ShieldAlert, 
  BookOpen, 
  BarChart3, 
  RefreshCw, 
  Search, 
  Trash2, 
  Ban, 
  CheckCircle2, 
  AlertTriangle, 
  ArrowLeft,
  Key,
  Lock,
  Unlock,
  Sliders,
  Check,
  AlertCircle
} from 'lucide-vue-next';
import { api } from '../api';
import { auth } from '../auth';

const emit = defineEmits(['switch-tab']);

const loading = ref(false);
const actionLoading = ref(false);
const toastMsg = ref('');
const toastType = ref('success'); // 'success' | 'error'

const stats = ref({
  total_users: 0,
  active_users: 0,
  banned_users: 0,
  total_questions: 3004,
  total_workbooks: 24,
  total_answers: 0
});

const settings = ref({
  allow_registration: true,
  invite_code_enabled: true,
  invite_code: '2027kaoyan'
});

const users = ref([]);
const searchQuery = ref('');
const statusFilter = ref('all'); // 'all' | 'active' | 'banned'

const showDeleteConfirm = ref(false);
const userToDelete = ref(null);

const showToast = (msg, type = 'success') => {
  toastMsg.value = msg;
  toastType.value = type;
  setTimeout(() => {
    toastMsg.value = '';
  }, 3500);
};

const loadData = async () => {
  loading.value = true;
  try {
    const [statsRes, settingsRes, usersRes] = await Promise.all([
      api.getAdminStats(),
      api.getAdminSettings(),
      api.getAdminUsers()
    ]);
    if (statsRes && statsRes.stats) stats.value = statsRes.stats;
    if (settingsRes && settingsRes.settings) settings.value = settingsRes.settings;
    if (usersRes && usersRes.users) users.value = usersRes.users;
  } catch (err) {
    showToast(err.message || '加载后台数据失败，请确认是否具备超级管理员权限', 'error');
  } finally {
    loading.value = false;
  }
};

const handleSaveSettings = async () => {
  actionLoading.value = true;
  try {
    const res = await api.updateAdminSettings({
      allow_registration: !!settings.value.allow_registration,
      invite_code_enabled: !!settings.value.invite_code_enabled,
      invite_code: settings.value.invite_code.trim()
    });
    showToast(res.message || '全站安全与注册配置保存成功！');
  } catch (err) {
    showToast(err.message || '保存配置失败', 'error');
  } finally {
    actionLoading.value = false;
  }
};

const handleToggleStatus = async (user) => {
  if (user.is_current_admin) {
    showToast('不能对当前登录的超级管理员账号进行封禁操作', 'error');
    return;
  }

  const nextStatus = user.is_active === 1 ? 0 : 1;
  const actionText = nextStatus === 0 ? '封禁该账号（立刻吊销其Token并强制踢下线）' : '解封该账号（恢复正常登录与刷题）';

  if (!confirm(`确定要${actionText}【${user.username}】吗？`)) {
    return;
  }

  actionLoading.value = true;
  try {
    const res = await api.updateUserStatus(user.id, nextStatus);
    user.is_active = nextStatus;
    showToast(res.message || '操作成功');
    // 重新拉取统计数据
    const statsRes = await api.getAdminStats();
    if (statsRes && statsRes.stats) stats.value = statsRes.stats;
  } catch (err) {
    showToast(err.message || '操作失败', 'error');
  } finally {
    actionLoading.value = false;
  }
};

const confirmDeleteUser = (user) => {
  if (user.is_current_admin) {
    showToast('不能删除当前登录的管理员账号', 'error');
    return;
  }
  userToDelete.value = user;
  showDeleteConfirm.value = true;
};

const handleSyncKvdb = async () => {
  actionLoading.value = true;
  try {
    const res = await api.syncKvdbUsers();
    showToast(res.message || '已成功与公网云端合流注册考生！');
    await loadData();
  } catch (err) {
    showToast(err.message || '同步公网用户失败', 'error');
  } finally {
    actionLoading.value = false;
  }
};

const executeDeleteUser = async () => {
  if (!userToDelete.value) return;
  actionLoading.value = true;
  try {
    const res = await api.deleteUser(userToDelete.value.id);
    users.value = users.value.filter(u => u.id !== userToDelete.value.id);
    showToast(res.message || '用户已彻底删除');
    showDeleteConfirm.value = false;
    userToDelete.value = null;
    const statsRes = await api.getAdminStats();
    if (statsRes && statsRes.stats) stats.value = statsRes.stats;
  } catch (err) {
    showToast(err.message || '删除用户失败', 'error');
  } finally {
    actionLoading.value = false;
  }
};

const filteredUsers = computed(() => {
  return users.value.filter(u => {
    // 状态过滤
    if (statusFilter.value === 'active' && u.is_active !== 1) return false;
    if (statusFilter.value === 'banned' && u.is_active !== 0) return false;
    // 关键词搜索
    if (searchQuery.value.trim()) {
      const q = searchQuery.value.trim().toLowerCase();
      const matchUser = (u.username || '').toLowerCase().includes(q);
      const matchNick = (u.nickname || '').toLowerCase().includes(q);
      const matchId = String(u.id).includes(q);
      return matchUser || matchNick || matchId;
    }
    return true;
  });
});

onMounted(() => {
  loadData();
});
</script>

<template>
  <div class="max-w-7xl mx-auto px-3 sm:px-6 py-4 sm:py-6 pb-24 sm:pb-28 space-y-6">
    <!-- Toast 通知 -->
    <div 
      v-if="toastMsg" 
      class="fixed top-5 right-5 z-50 flex items-center gap-2.5 px-4 py-3 rounded-xl shadow-lg border text-sm font-medium animate-in fade-in slide-in-from-top-4 duration-200"
      :class="toastType === 'error' ? 'bg-rose-50 text-rose-800 border-rose-200' : 'bg-emerald-50 text-emerald-800 border-emerald-200'"
    >
      <AlertCircle v-if="toastType === 'error'" class="w-4 h-4 text-rose-600 shrink-0" />
      <CheckCircle2 v-else class="w-4 h-4 text-emerald-600 shrink-0" />
      <span>{{ toastMsg }}</span>
    </div>

    <!-- 顶部导航与操作栏 -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white p-4 sm:p-5 rounded-2xl border border-slate-200 shadow-2xs">
      <div class="flex items-center space-x-3">
        <div class="w-10 h-10 sm:w-12 sm:h-12 bg-linear-to-tr from-amber-500 to-orange-500 rounded-xl flex items-center justify-center text-white text-xl shadow-md font-bold">
          👑
        </div>
        <div>
          <div class="flex items-center gap-2">
            <h1 class="text-lg sm:text-xl font-bold text-slate-800">系统管理后台与安全防火墙</h1>
            <span class="px-2 py-0.5 text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-300 rounded-full">
              超级管理员
            </span>
          </div>
          <p class="text-xs sm:text-sm text-slate-500 mt-0.5">
            监控注册考生、封禁恶意注水账号、配置全站注册安全验证与专属口令
          </p>
        </div>
      </div>

      <div class="flex items-center gap-2">
        <button
          @click="loadData"
          :disabled="loading"
          class="flex items-center space-x-1.5 px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs sm:text-sm font-semibold rounded-xl transition cursor-pointer disabled:opacity-50"
        >
          <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': loading }" />
          <span>刷新</span>
        </button>

        <button
          @click="emit('switch-tab', 'practice')"
          class="flex items-center space-x-1.5 px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white text-xs sm:text-sm font-semibold rounded-xl transition cursor-pointer shadow-xs"
        >
          <ArrowLeft class="w-4 h-4" />
          <span>返回刷题中心</span>
        </button>
      </div>
    </div>

    <!-- 数据核心统计看板 -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
      <!-- 注册总人数 -->
      <div class="bg-white p-4 sm:p-5 rounded-2xl border border-slate-200 shadow-2xs flex items-center justify-between">
        <div>
          <p class="text-xs font-medium text-slate-500">全站注册用户</p>
          <p class="text-2xl sm:text-3xl font-extrabold text-slate-800 mt-1">{{ stats.total_users }}</p>
          <p class="text-[11px] text-slate-400 mt-0.5">总注册账号数</p>
        </div>
        <div class="w-11 h-11 bg-blue-50 text-blue-600 rounded-xl flex items-center justify-center">
          <Users class="w-6 h-6" />
        </div>
      </div>

      <!-- 活跃正常账号 -->
      <div class="bg-white p-4 sm:p-5 rounded-2xl border border-slate-200 shadow-2xs flex items-center justify-between">
        <div>
          <p class="text-xs font-medium text-slate-500">正常活跃状态</p>
          <p class="text-2xl sm:text-3xl font-extrabold text-emerald-600 mt-1">{{ stats.active_users }}</p>
          <p class="text-[11px] text-emerald-600/80 mt-0.5">具备正常答题权限</p>
        </div>
        <div class="w-11 h-11 bg-emerald-50 text-emerald-600 rounded-xl flex items-center justify-center">
          <UserCheck class="w-6 h-6" />
        </div>
      </div>

      <!-- 已封禁账号 -->
      <div class="bg-white p-4 sm:p-5 rounded-2xl border border-slate-200 shadow-2xs flex items-center justify-between">
        <div>
          <p class="text-xs font-medium text-slate-500">已封禁拦截账号</p>
          <p class="text-2xl sm:text-3xl font-extrabold text-rose-600 mt-1">{{ stats.banned_users }}</p>
          <p class="text-[11px] text-rose-500 mt-0.5">已被限制禁止登录</p>
        </div>
        <div class="w-11 h-11 bg-rose-50 text-rose-600 rounded-xl flex items-center justify-center">
          <UserX class="w-6 h-6" />
        </div>
      </div>

      <!-- 全站题库与作答总量 -->
      <div class="bg-white p-4 sm:p-5 rounded-2xl border border-slate-200 shadow-2xs flex items-center justify-between">
        <div>
          <p class="text-xs font-medium text-slate-500">题库与全站作答量</p>
          <p class="text-2xl sm:text-3xl font-extrabold text-indigo-600 mt-1">{{ stats.total_questions }}</p>
          <p class="text-[11px] text-indigo-500 mt-0.5">累计答题 {{ stats.total_answers }} 条记录</p>
        </div>
        <div class="w-11 h-11 bg-indigo-50 text-indigo-600 rounded-xl flex items-center justify-center">
          <BookOpen class="w-6 h-6" />
        </div>
      </div>
    </div>

    <!-- 防恶意注册防火墙与系统配置卡片 -->
    <div class="bg-white p-5 sm:p-6 rounded-2xl border border-slate-200 shadow-2xs space-y-5">
      <div class="flex items-center justify-between border-b border-slate-100 pb-3">
        <div class="flex items-center space-x-2.5">
          <div class="w-8 h-8 rounded-lg bg-rose-100 text-rose-700 flex items-center justify-center font-bold">
            <ShieldCheck class="w-5 h-5 text-rose-600" />
          </div>
          <div>
            <h2 class="text-base font-bold text-slate-800">防恶意刷号防火墙与注册控制</h2>
            <p class="text-xs text-slate-500">配置新用户注册门槛，抵御爬虫脚本暴力灌水，保护服务器数据库安全</p>
          </div>
        </div>
        <span class="px-2.5 py-1 bg-emerald-50 text-emerald-700 text-xs font-bold rounded-lg border border-emerald-200 flex items-center gap-1">
          <Check class="w-3.5 h-3.5" /> 防护运行中 (同IP限速3次/分)
        </span>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <!-- 控制项 1: 全站注册总开关 -->
        <div class="p-4 bg-slate-50 rounded-xl border border-slate-200/80 space-y-2">
          <div class="flex items-center justify-between">
            <span class="text-sm font-bold text-slate-800">全站开放新用户注册</span>
            <label class="relative inline-flex items-center cursor-pointer">
              <input 
                type="checkbox" 
                v-model="settings.allow_registration" 
                class="sr-only peer"
              />
              <div class="w-11 h-6 bg-slate-300 peer-focus:outline-hidden rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-500"></div>
            </label>
          </div>
          <p class="text-xs text-slate-500 leading-relaxed">
            关闭后全站立即暂停任何新账号注册，已有注册考生仍可正常登录刷题。
          </p>
        </div>

        <!-- 控制项 2: 邀请码验证总开关 -->
        <div class="p-4 bg-slate-50 rounded-xl border border-slate-200/80 space-y-2">
          <div class="flex items-center justify-between">
            <span class="text-sm font-bold text-slate-800">强制要求专属邀请码</span>
            <label class="relative inline-flex items-center cursor-pointer">
              <input 
                type="checkbox" 
                v-model="settings.invite_code_enabled" 
                class="sr-only peer"
              />
              <div class="w-11 h-6 bg-slate-300 peer-focus:outline-hidden rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-500"></div>
            </label>
          </div>
          <p class="text-xs text-slate-500 leading-relaxed">
            开启后注册必须输入正确口令。关闭则所有人均可免邀请码注册。
          </p>
        </div>

        <!-- 控制项 3: 自定义专属注册口令 -->
        <div class="p-4 bg-slate-50 rounded-xl border border-slate-200/80 space-y-2">
          <label class="block text-sm font-bold text-slate-800">当前专属注册口令</label>
          <div class="relative">
            <input 
              v-model="settings.invite_code"
              type="text"
              placeholder="例如: 2027kaoyan"
              class="w-full pl-8 pr-3 py-1.5 text-sm bg-white border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-rose-500/20 focus:border-rose-500 font-mono"
            />
            <Key class="w-4 h-4 text-slate-400 absolute left-2.5 top-2.5" />
          </div>
          <p class="text-xs text-slate-500">
            可任意更改为您的专属考研群/自习室暗号口令。
          </p>
        </div>
      </div>

      <div class="flex justify-end pt-1">
        <button
          @click="handleSaveSettings"
          :disabled="actionLoading"
          class="flex items-center space-x-1.5 px-5 py-2.5 bg-linear-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white font-bold text-sm rounded-xl shadow-sm transition cursor-pointer disabled:opacity-50"
        >
          <RefreshCw v-if="actionLoading" class="w-4 h-4 animate-spin" />
          <CheckCircle2 v-else class="w-4 h-4" />
          <span>保存防火墙与安全配置</span>
        </button>
      </div>
    </div>

    <!-- 用户管理与防滥用列表 -->
    <div class="bg-white rounded-2xl border border-slate-200 shadow-2xs overflow-hidden">
      <!-- 列表标题与搜索过滤 -->
      <div class="p-4 sm:p-5 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div class="flex items-center space-x-2">
          <Users class="w-5 h-5 text-slate-600" />
          <h2 class="text-base font-bold text-slate-800">注册考生账号管理</h2>
          <span class="text-xs text-slate-400 font-medium">(共 {{ filteredUsers.length }} 位)</span>
        </div>

        <div class="flex flex-wrap items-center gap-2">
          <!-- 状态筛选按纽组 -->
          <div class="flex items-center bg-slate-100 p-0.5 rounded-lg text-xs font-semibold">
            <button
              @click="statusFilter = 'all'"
              class="px-2.5 py-1 rounded-md transition cursor-pointer"
              :class="statusFilter === 'all' ? 'bg-white text-slate-800 shadow-xs' : 'text-slate-500 hover:text-slate-800'"
            >
              全部
            </button>
            <button
              @click="statusFilter = 'active'"
              class="px-2.5 py-1 rounded-md transition cursor-pointer"
              :class="statusFilter === 'active' ? 'bg-white text-emerald-700 shadow-xs' : 'text-slate-500 hover:text-slate-800'"
            >
              正常
            </button>
            <button
              @click="statusFilter = 'banned'"
              class="px-2.5 py-1 rounded-md transition cursor-pointer"
              :class="statusFilter === 'banned' ? 'bg-white text-rose-700 shadow-xs' : 'text-slate-500 hover:text-slate-800'"
            >
              已封禁
            </button>
          </div>

          <!-- 搜索输入框 -->
          <div class="relative w-full sm:w-48">
            <input 
              v-model="searchQuery"
              type="text"
              placeholder="搜索账号 / 昵称 / ID / 手机"
              class="w-full pl-8 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-rose-500/20 focus:border-rose-500"
            />
            <Search class="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
          </div>

          <!-- 同步公网注册考生按钮 -->
          <button
            @click="handleSyncKvdb"
            :disabled="actionLoading"
            class="px-2.5 py-1.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 text-xs font-semibold rounded-lg flex items-center gap-1 cursor-pointer transition shadow-2xs"
            title="合流 GitHub Pages / 手机网页端注册的考生与答题进度"
          >
            <RefreshCw class="w-3.5 h-3.5" :class="{ 'animate-spin': actionLoading }" />
            <span>合流公网考生</span>
          </button>
        </div>
      </div>

      <!-- 表格内容 -->
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs sm:text-sm">
          <thead class="bg-slate-50/80 text-slate-500 font-semibold border-b border-slate-100 uppercase text-[11px] tracking-wider">
            <tr>
              <th class="px-4 py-3">ID</th>
              <th class="px-4 py-3">用户与昵称</th>
              <th class="px-4 py-3">角色权限</th>
              <th class="px-4 py-3">账号状态</th>
              <th class="px-4 py-3">做题数据</th>
              <th class="px-4 py-3">注册 / 最后登录</th>
              <th class="px-4 py-3 text-right">安全操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 text-slate-700">
            <tr v-if="filteredUsers.length === 0">
              <td colspan="7" class="px-4 py-12 text-center text-slate-400">
                <Users class="w-8 h-8 mx-auto mb-2 text-slate-300" />
                <span>没有匹配的注册用户</span>
              </td>
            </tr>

            <tr 
              v-for="user in filteredUsers" 
              :key="user.id"
              class="hover:bg-slate-50/70 transition"
              :class="{ 'bg-amber-50/30': user.is_current_admin }"
            >
              <!-- ID -->
              <td class="px-4 py-3 font-mono font-bold text-slate-500">
                #{{ user.id }}
              </td>

              <!-- 用户与昵称 -->
              <td class="px-4 py-3">
                <div class="flex items-center gap-2">
                  <div 
                    class="w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs text-white shadow-2xs"
                    :class="user.role === 'admin' ? 'bg-amber-500' : 'bg-slate-400'"
                  >
                    {{ (user.nickname || user.username || '用').slice(0, 1) }}
                  </div>
                  <div>
                    <div class="font-bold text-slate-800 flex items-center gap-1">
                      <span>{{ user.nickname || user.username }}</span>
                      <span v-if="user.is_current_admin" class="text-[10px] text-amber-600 bg-amber-100 px-1 py-0.2 rounded font-bold">我</span>
                    </div>
                    <div class="text-[11px] text-slate-400">@{{ user.username }}</div>
                    <div v-if="user.phone" class="text-[10px] text-emerald-600 font-mono font-medium">📱 {{ user.phone }}</div>
                  </div>
                </div>
              </td>

              <!-- 角色权限 -->
              <td class="px-4 py-3">
                <span 
                  v-if="user.role === 'admin'"
                  class="px-2 py-0.5 text-xs font-bold bg-amber-100 text-amber-800 border border-amber-300 rounded-md inline-flex items-center gap-1"
                >
                  👑 超级管理员
                </span>
                <span 
                  v-else
                  class="px-2 py-0.5 text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200 rounded-md inline-flex items-center"
                >
                  考生学员
                </span>
              </td>

              <!-- 账号状态 -->
              <td class="px-4 py-3">
                <span 
                  v-if="user.is_active === 1"
                  class="px-2 py-0.5 text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-md inline-flex items-center gap-1"
                >
                  <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                  正常
                </span>
                <span 
                  v-else
                  class="px-2 py-0.5 text-xs font-bold bg-rose-50 text-rose-700 border border-rose-200 rounded-md inline-flex items-center gap-1"
                >
                  <span class="w-1.5 h-1.5 rounded-full bg-rose-500"></span>
                  已封禁
                </span>
              </td>

              <!-- 做题记录 -->
              <td class="px-4 py-3">
                <div class="text-xs">
                  <span class="font-bold text-slate-800">{{ user.records_count || 0 }}</span> 题
                  <span class="text-slate-400 text-[11px] ml-1">({{ user.notes_count || 0 }}条笔记)</span>
                </div>
              </td>

              <!-- 时间 -->
              <td class="px-4 py-3 text-[11px] text-slate-500">
                <div>注册: {{ user.created_at ? user.created_at.slice(0, 16) : '未知' }}</div>
                <div class="text-slate-400">最后登录: {{ user.last_login ? user.last_login.slice(0, 16) : '未登录' }}</div>
              </td>

              <!-- 操作 -->
              <td class="px-4 py-3 text-right">
                <div class="flex items-center justify-end gap-1.5">
                  <!-- 封禁 / 解封按钮 -->
                  <button
                    @click="handleToggleStatus(user)"
                    :disabled="user.is_current_admin || actionLoading"
                    class="px-2.5 py-1 text-xs font-semibold rounded-lg border transition cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
                    :class="[
                      user.is_active === 1
                        ? 'text-rose-600 bg-rose-50 hover:bg-rose-100 border-rose-200'
                        : 'text-emerald-700 bg-emerald-50 hover:bg-emerald-100 border-emerald-200'
                    ]"
                    :title="user.is_current_admin ? '无法封禁当前登录的管理员' : ''"
                  >
                    {{ user.is_active === 1 ? '封禁' : '解封' }}
                  </button>

                  <!-- 彻底注销删除按钮 -->
                  <button
                    @click="confirmDeleteUser(user)"
                    :disabled="user.is_current_admin || actionLoading"
                    class="px-2 py-1 text-xs font-medium text-slate-500 hover:text-rose-700 hover:bg-rose-50 border border-slate-200 hover:border-rose-200 rounded-lg transition cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
                    title="彻底物理删除此账号及其全站历史数据"
                  >
                    <Trash2 class="w-3.5 h-3.5" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 删除二次确认弹窗 -->
    <div 
      v-if="showDeleteConfirm" 
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in"
      @click.self="showDeleteConfirm = false"
    >
      <div class="bg-white rounded-2xl shadow-2xl border border-slate-100 w-full max-w-sm p-5 space-y-4">
        <div class="flex items-center gap-3 text-rose-600">
          <div class="w-10 h-10 rounded-full bg-rose-100 flex items-center justify-center shrink-0">
            <AlertTriangle class="w-5 h-5 text-rose-600" />
          </div>
          <div>
            <h3 class="font-bold text-slate-800 text-base">彻底删除此用户？</h3>
            <p class="text-xs text-slate-500">此操作不可撤销</p>
          </div>
        </div>

        <p class="text-xs text-slate-600 leading-relaxed bg-slate-50 p-3 rounded-xl border border-slate-200">
          确认删除用户 <strong class="text-rose-600 font-bold">@{{ userToDelete?.username }}</strong> 吗？<br />
          该用户的账号密码、登录令牌以及全部云端刷题记录将被永久从数据库物理抹除。
        </p>

        <div class="flex items-center justify-end gap-2 pt-2">
          <button 
            @click="showDeleteConfirm = false"
            class="px-3.5 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl transition cursor-pointer"
          >
            取消
          </button>
          <button 
            @click="executeDeleteUser"
            :disabled="actionLoading"
            class="px-4 py-2 text-xs font-bold bg-rose-600 hover:bg-rose-700 text-white rounded-xl shadow-xs transition cursor-pointer disabled:opacity-50"
          >
            {{ actionLoading ? '正在注销...' : '确定彻底删除' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
