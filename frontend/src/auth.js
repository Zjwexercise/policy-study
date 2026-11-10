import { ref } from 'vue';
import { localStore } from './localStore';

// 永久免费免开机公网云端数据库 (24小时全天候在线，手机4G/5G、自习室、电脑关机均可秒级直连)
const CLOUD_BUCKET = 'GoHbGrRznWpJGpLFkLSwRZ';
const CLOUD_BASE_URL = `https://kvdb.io/${CLOUD_BUCKET}`;

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

// 纯浏览器 Web Crypto SHA-256 哈希计算
async function sha256Hex(str) {
  const enc = new TextEncoder();
  const data = enc.encode(str);
  const hashBuf = await crypto.subtle.digest('SHA-256', data);
  return Array.from(new Uint8Array(hashBuf))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');
}

// 用户账号云端存储 Key 生成（哈希转义，防止特殊字符）
async function getUserCloudKey(username) {
  const clean = username.trim().toLowerCase();
  const hex = await sha256Hex(clean);
  return `pm_u_${hex.slice(0, 24)}`;
}

// 智能无损双向合并算法
function smartMergeRecords(targetRecords, incomingRecords) {
  const merged = { ...targetRecords };
  for (const [k, inVal] of Object.entries(incomingRecords || {})) {
    if (!k.startsWith('policy_')) continue;
    const curVal = merged[k];

    if (k.startsWith('policy_ans_')) {
      if (curVal === undefined) {
        merged[k] = inVal;
      } else {
        const qid = k.split('_')[3];
        const curCor = merged[`policy_cor_${qid}`];
        const inCor = incomingRecords[`policy_cor_${qid}`];
        if (inCor === '1' && curCor !== '1') {
          merged[k] = inVal;
          merged[`policy_cor_${qid}`] = '1';
        }
      }
    } else if (k.startsWith('policy_cor_')) {
      if (curVal === undefined || (inVal === '1' && curVal !== '1')) {
        merged[k] = inVal;
      }
    } else if (k.startsWith('policy_wrong_cnt_')) {
      const curNum = Number(curVal || 0);
      const inNum = Number(inVal || 0);
      merged[k] = String(Math.max(curNum, inNum));
    } else if (k.startsWith('policy_wrong_master_')) {
      if (curVal === undefined || inVal === '1') {
        merged[k] = inVal;
      }
    } else if (k.startsWith('policy_killed_') && !k.startsWith('policy_killed_at_')) {
      if (curVal === undefined || inVal === '1') {
        merged[k] = inVal;
      }
    } else if (k.startsWith('policy_killed_at_')) {
      if (curVal === undefined) {
        merged[k] = inVal;
      } else if (inVal) {
        const tCur = new Date(curVal).getTime();
        const tIn = new Date(inVal).getTime();
        if (tIn > tCur) merged[k] = inVal;
      }
    } else if (k.startsWith('policy_star_')) {
      if (curVal === undefined || inVal === '1') {
        merged[k] = inVal;
      }
    } else if (k.startsWith('policy_note_')) {
      const cStr = String(curVal || '').trim();
      const inStr = String(inVal || '').trim();
      if (!cStr) {
        if (inStr) merged[k] = inStr;
      } else if (inStr && cStr !== inStr) {
        if (!cStr.includes(inStr)) {
          merged[k] = `${cStr}\n\n[云端合并笔记]:\n${inStr}`;
        }
      }
    } else {
      if (curVal === undefined) {
        merged[k] = inVal;
      }
    }
  }
  return merged;
}

function smartMergeStats(targetStats, incomingStats) {
  const merged = { ...targetStats };
  for (const [dateKey, inStat] of Object.entries(incomingStats || {})) {
    if (!merged[dateKey]) {
      merged[dateKey] = inStat;
    } else {
      const curSec = merged[dateKey].duration_seconds || 0;
      const inSec = inStat.duration_seconds || 0;
      merged[dateKey].duration_seconds = Math.max(curSec, inSec);

      const curCnt = merged[dateKey].question_count || 0;
      const inCnt = inStat.question_count || 0;
      merged[dateKey].question_count = Math.max(curCnt, inCnt);
    }
  }
  return merged;
}

let autoSyncTimer = null;

export const auth = {
  currentUser,
  authToken,
  customServerUrl,
  syncStatus,
  lastSyncTime,
  syncError,

  // 设置云端独立服务器地址（选填，留空即默认使用内置24小时免开机云端）
  setCustomServerUrl(url) {
    const clean = (url || '').trim();
    customServerUrl.value = clean;
    if (clean) {
      localStorage.setItem('policy_custom_server_url', clean);
    } else {
      localStorage.removeItem('policy_custom_server_url');
    }
  },

  // 注册新账号（免开机、免Wi-Fi、手机电脑全网通用）
  async register(username, password, nickname = '') {
    const cleanUser = username.trim();
    const cleanPwd = password.trim();
    const cleanNick = (nickname || '').trim() || cleanUser;

    if (cleanUser.length < 2) throw new Error('用户名不能少于2个字符');
    if (cleanPwd.length < 4) throw new Error('密码长度不能少于4位');

    syncError.value = '';
    const userKey = await getUserCloudKey(cleanUser);
    const cloudUrl = `${CLOUD_BASE_URL}/${userKey}`;

    // 1. 检查用户名在云端是否已存在
    try {
      const checkRes = await fetch(cloudUrl, { method: 'GET', cache: 'no-cache' });
      if (checkRes.ok) {
        throw new Error('该用户名已被注册，请直接登录或换一个用户名');
      }
    } catch (e) {
      if (e.message.includes('已被注册')) throw e;
      // 404 或网络通过，继续注册
    }

    // 2. 加盐哈希密码
    const salt = Math.random().toString(36).slice(2) + Date.now().toString(36);
    const pwdHash = await sha256Hex(cleanPwd + ':' + salt);

    // 3. 提取本地当前已做的题，作为初始云端数据
    const localExport = localStore.exportData();
    const studyLogs = JSON.parse(localStorage.getItem('policy_study_logs') || '{}');

    const userData = {
      username: cleanUser,
      nickname: cleanNick,
      salt,
      pwdHash,
      created_at: new Date().toISOString(),
      last_sync: new Date().toISOString(),
      records: localExport.records || {},
      stats: studyLogs || {}
    };

    // 4. 写入 24 小时公网云数据库 (免开机)
    const putRes = await fetch(cloudUrl, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData)
    });

    if (!putRes.ok) {
      throw new Error(`连接云端失败 (HTTP ${putRes.status})，请检查手机网络`);
    }

    // 5. 保存本地登录会话
    this.saveSession(userData, pwdHash, salt);
    return currentUser.value;
  },

  // 账号登录（免开机、免Wi-Fi、跨设备恢复）
  async login(username, password) {
    const cleanUser = username.trim();
    const cleanPwd = password.trim();

    if (!cleanUser) throw new Error('请输入用户名');
    if (!cleanPwd) throw new Error('请输入密码');

    syncError.value = '';
    const userKey = await getUserCloudKey(cleanUser);
    const cloudUrl = `${CLOUD_BASE_URL}/${userKey}?t=${Date.now()}`;

    // 1. 从公网云端获取用户信息
    const res = await fetch(cloudUrl, { method: 'GET', cache: 'no-cache' });
    if (res.status === 404) {
      throw new Error('账号不存在，请先切换到「注册新账号」进行创建');
    }
    if (!res.ok) {
      throw new Error(`连接云端失败 (HTTP ${res.status})，请检查网络`);
    }

    const userData = await res.json();

    // 2. 校验加盐哈希密码
    const calcHash = await sha256Hex(cleanPwd + ':' + (userData.salt || ''));
    if (calcHash !== userData.pwdHash) {
      throw new Error('密码错误，请重新输入');
    }

    // 3. 登录成功：智能无损合并云端历史记录到本地
    if (userData.records && Object.keys(userData.records).length > 0) {
      try {
        localStore.importData({
          records: userData.records,
          stats: userData.stats || {}
        }, 'merge');
      } catch (e) {
        console.warn('本地合并云端记录提示:', e);
      }
    }

    // 4. 保存本地会话
    this.saveSession(userData, userData.pwdHash, userData.salt);

    // 5. 双向对齐：立即把两端合并后的最全数据推回云端
    await this.syncNow();
    return currentUser.value;
  },

  saveSession(userData, pwdHash, salt) {
    currentUser.value = {
      username: userData.username,
      nickname: userData.nickname || userData.username
    };
    authToken.value = pwdHash;
    localStorage.setItem('policy_auth_user', JSON.stringify(currentUser.value));
    localStorage.setItem('policy_auth_pwd', pwdHash);
    localStorage.setItem('policy_auth_salt', salt);
    syncStatus.value = 'synced';
    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    lastSyncTime.value = timeStr;
    localStorage.setItem('policy_last_sync_time', timeStr);
  },

  // 退出登录
  async logout() {
    currentUser.value = null;
    authToken.value = '';
    syncStatus.value = 'idle';
    syncError.value = '';
    localStorage.removeItem('policy_auth_user');
    localStorage.removeItem('policy_auth_pwd');
    localStorage.removeItem('policy_auth_salt');
  },

  // 立即执行一次公网云端双向静默同步
  async syncNow() {
    if (!currentUser.value) return;

    syncStatus.value = 'syncing';
    syncError.value = '';

    try {
      const userKey = await getUserCloudKey(currentUser.value.username);
      const cloudUrl = `${CLOUD_BASE_URL}/${userKey}`;

      // 1. 获取云端当前存档
      const res = await fetch(`${cloudUrl}?t=${Date.now()}`, { method: 'GET', cache: 'no-cache' });
      if (!res.ok) {
        throw new Error(`连接云端失败 (HTTP ${res.status})`);
      }
      const cloudData = await res.json();

      // 2. 提取本地最新做题记录与学习时长
      const localExport = localStore.exportData();
      const localLogs = JSON.parse(localStorage.getItem('policy_study_logs') || '{}');

      // 3. 智能双向无损合并
      const mergedRecords = smartMergeRecords(cloudData.records || {}, localExport.records || {});
      const mergedStats = smartMergeStats(cloudData.stats || {}, localLogs || {});

      cloudData.records = mergedRecords;
      cloudData.stats = mergedStats;
      cloudData.last_sync = new Date().toISOString();

      // 4. 推送合并结果回云端
      const putRes = await fetch(cloudUrl, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(cloudData)
      });

      if (!putRes.ok) {
        throw new Error(`同步更新失败 (HTTP ${putRes.status})`);
      }

      // 5. 更新本地存储，确保本地包含云端的最新刷题记录
      localStore.importData({
        records: mergedRecords,
        stats: mergedStats
      }, 'merge');

      syncStatus.value = 'synced';
      const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      lastSyncTime.value = timeStr;
      localStorage.setItem('policy_last_sync_time', timeStr);
      return cloudData;
    } catch (e) {
      syncStatus.value = 'error';
      syncError.value = e.message || '网络连接超时';
      throw e;
    }
  },

  // 防抖静默触发自动云同步（每当答题、斩题、收藏、写笔记后自动调用）
  triggerAutoSync(delay = 3000) {
    if (!currentUser.value) return;

    if (autoSyncTimer) {
      clearTimeout(autoSyncTimer);
    }

    autoSyncTimer = setTimeout(async () => {
      try {
        await this.syncNow();
      } catch (e) {
        console.warn('后台自动云同步暂缓（网络离线或稍后重试）:', e);
      }
    }, delay);
  },

  // 页面加载时自动静默与云端同步
  async initAuth() {
    if (!currentUser.value) return;
    try {
      await this.syncNow();
    } catch (e) {
      console.warn('离线初始化，继续以本地缓存账号运行');
    }
  }
};
