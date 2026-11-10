import { ref, reactive } from 'vue';
import { localStore } from './localStore';

// 认证状态与云端同步响应式对象
const currentUser = ref(null);
const authToken = ref(localStorage.getItem('policy_auth_token') || '');
const customServerUrl = ref(localStorage.getItem('policy_custom_server_url') || '');
const syncStatus = ref('idle'); // 'idle' | 'syncing' | 'synced' | 'error'
const lastSyncTime = ref(localStorage.getItem('policy_last_sync_time') || '');
const syncError = ref('');

// 初始化已缓存的用户信息
try {
  const cachedUser = localStorage.getItem('policy_auth_user');
  if (cachedUser) {
    currentUser.value = JSON.parse(cachedUser);
  }
} catch (e) {
  currentUser.value = null;
}

// 计算当前实际生效的 API 基础路径
function getEffectiveApiBase() {
  let url = (customServerUrl.value || '').trim();
  if (url) {
    url = url.replace(/\/+$/, '');
    if (!url.endsWith('/api')) {
      url += '/api';
    }
    return url;
  }

  // 默认为相对路径 /api (适用于本地 Vite 代理、本地 FastAPI 托管、或同源云服务器)
  return '/api';
}

let autoSyncTimer = null;

export const auth = {
  currentUser,
  authToken,
  customServerUrl,
  syncStatus,
  lastSyncTime,
  syncError,

  getEffectiveApiBase,

  // 设置云端独立服务器地址（如 Render / Zeabur / 局域网IP）
  setCustomServerUrl(url) {
    const clean = (url || '').trim();
    customServerUrl.value = clean;
    if (clean) {
      localStorage.setItem('policy_custom_server_url', clean);
    } else {
      localStorage.removeItem('policy_custom_server_url');
    }
  },

  // 注册新用户
  async register(username, password, nickname = '') {
    const apiBase = getEffectiveApiBase();
    syncError.value = '';

    const res = await fetch(`${apiBase}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: username.trim(),
        password: password.trim(),
        nickname: nickname.trim() || username.trim()
      })
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || '注册失败，请稍后重试');
    }

    // 注册成功，自动登录并建立本地会话
    this.handleAuthSuccess(data);

    // 立即执行一次同步，把当前设备的已有刷题成果推送到新账号
    await this.syncNow();
    return data.user;
  },

  // 账号登录
  async login(username, password) {
    const apiBase = getEffectiveApiBase();
    syncError.value = '';

    const res = await fetch(`${apiBase}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: username.trim(),
        password: password.trim()
      })
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || '登录失败，请检查账号密码');
    }

    this.handleAuthSuccess(data);

    // 登录成功后，若云端有历史数据，自动无损合并到本地
    if (data.cloud_data && data.cloud_data.records && Object.keys(data.cloud_data.records).length > 0) {
      try {
        localStore.importData(data.cloud_data, 'merge');
      } catch (e) {
        console.warn('云端记录合并警告:', e);
      }
    }

    // 双向对齐：再将两端合并后的最全数据推回云端，保证云端也是最新的
    await this.syncNow();
    return data.user;
  },

  handleAuthSuccess(data) {
    authToken.value = data.token;
    currentUser.value = data.user;
    localStorage.setItem('policy_auth_token', data.token);
    localStorage.setItem('policy_auth_user', JSON.stringify(data.user));
    syncStatus.value = 'synced';
    lastSyncTime.value = new Date().toLocaleTimeString();
    localStorage.setItem('policy_last_sync_time', lastSyncTime.value);
  },

  // 退出登录
  async logout() {
    const apiBase = getEffectiveApiBase();
    if (authToken.value) {
      try {
        await fetch(`${apiBase}/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${authToken.value}`
          }
        });
      } catch (e) {
        // 忽略网络断开导致的注销失败
      }
    }

    authToken.value = '';
    currentUser.value = null;
    syncStatus.value = 'idle';
    syncError.value = '';
    localStorage.removeItem('policy_auth_token');
    localStorage.removeItem('policy_auth_user');
  },

  // 立即执行一次云端数据双向同步
  async syncNow() {
    if (!authToken.value || !currentUser.value) return;

    const apiBase = getEffectiveApiBase();
    syncStatus.value = 'syncing';
    syncError.value = '';

    try {
      // 提取本机所有的做题记录和学习统计
      const localExport = localStore.exportData();
      const studyLogs = JSON.parse(localStorage.getItem('policy_study_logs') || '{}');

      const res = await fetch(`${apiBase}/auth/sync`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken.value}`
        },
        body: JSON.stringify({
          client_records: localExport.records || {},
          client_stats: studyLogs || {}
        })
      });

      if (res.status === 401) {
        // Token 过期失效
        this.logout();
        throw new Error('登录凭据已过期，请重新登录');
      }

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || '云端同步失败');
      }

      // 将服务端合并后的最新记录更新回本地
      if (data.merged_records && Object.keys(data.merged_records).length > 0) {
        localStore.importData({
          records: data.merged_records,
          stats: data.merged_stats || {}
        }, 'merge');
      }

      syncStatus.value = 'synced';
      const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      lastSyncTime.value = timeStr;
      localStorage.setItem('policy_last_sync_time', timeStr);
      return data;
    } catch (e) {
      syncStatus.value = 'error';
      syncError.value = e.message || '网络连接超时';
      throw e;
    }
  },

  // 防抖静默触发自动云同步（刷完一道题、斩杀、收藏或记笔记后调用）
  triggerAutoSync(delay = 3000) {
    if (!authToken.value || !currentUser.value) return;

    if (autoSyncTimer) {
      clearTimeout(autoSyncTimer);
    }

    autoSyncTimer = setTimeout(async () => {
      try {
        await this.syncNow();
      } catch (e) {
        console.warn('静默自动云同步暂缓（网络离线或稍后重试）:', e);
      }
    }, delay);
  },

  // 检查当前凭据与静默同步初始化
  async initAuth() {
    if (!authToken.value) return;
    const apiBase = getEffectiveApiBase();

    try {
      const res = await fetch(`${apiBase}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${authToken.value}`
        }
      });

      if (res.ok) {
        const data = await res.json();
        currentUser.value = data.user;
        localStorage.setItem('policy_auth_user', JSON.stringify(data.user));
        // 开机或进页面时自动拉取最新云端记录进行合并
        await this.syncNow();
      } else if (res.status === 401) {
        // Token 失效
        this.logout();
      }
    } catch (e) {
      // 离线状态暂不强退
      console.warn('云端鉴权离线，继续以本地缓存账号运行');
    }
  }
};
