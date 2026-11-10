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

// 全平台 100% 兼容的纯 JavaScript SHA-256 实现
// 解决在普通 HTTP 环境 (如直接使用 IP 访问 http://47.93.172.13:8000、手机浏览器或局域网访问) 下
// window.crypto.subtle 为 undefined 导致 "Cannot read properties of undefined (reading 'digest')" 的致命报错
function pureJsSha256(ascii) {
  function rightRotate(value, amount) {
    return (value >>> amount) | (value << (32 - amount));
  }
  var mathPow = Math.pow;
  var maxWord = mathPow(2, 32);
  var lengthProperty = 'length';
  var i, j;
  var result = '';

  var words = [];
  var hash = [];
  var k = [];
  var primeCounter = 0;

  var isComposite = {};
  for (var candidate = 2; primeCounter < 64; candidate++) {
    if (!isComposite[candidate]) {
      for (i = candidate * candidate; i < 312; i += candidate) {
        isComposite[i] = true;
      }
      hash[primeCounter] = (mathPow(candidate, 0.5) * maxWord) | 0;
      k[primeCounter++] = (mathPow(candidate, 1 / 3) * maxWord) | 0;
    }
  }

  ascii = unescape(encodeURIComponent(ascii || ''));
  var asciiBitLength = ascii[lengthProperty] * 8;
  ascii += '\x80';
  while (ascii[lengthProperty] % 64 - 56) ascii += '\x00';
  for (i = 0; i < ascii[lengthProperty]; i++) {
    j = ascii.charCodeAt(i);
    words[i >> 2] |= j << ((3 - i) % 4) * 8;
  }
  words[words[lengthProperty]] = (asciiBitLength / maxWord) | 0;
  words[words[lengthProperty]] = asciiBitLength;

  for (j = 0; j < words[lengthProperty];) {
    var w = words.slice(j, j += 16);
    var oldHash = hash;
    hash = hash.slice(0, 8);

    for (i = 0; i < 64; i++) {
      var w15 = w[i - 15], w2 = w[i - 2];
      var s0 = rightRotate(w15, 7) ^ rightRotate(w15, 18) ^ (w15 >>> 3);
      var s1 = rightRotate(w2, 17) ^ rightRotate(w2, 19) ^ (w2 >>> 10);
      var ch = (hash[4] & hash[5]) ^ (~hash[4] & hash[6]);
      var maj = (hash[0] & hash[1]) ^ (hash[0] & hash[2]) ^ (hash[1] & hash[2]);
      var temp1 = hash[7] + (rightRotate(hash[4], 6) ^ rightRotate(hash[4], 11) ^ rightRotate(hash[4], 25)) + ch + k[i] + (w[i] = (i < 16) ? w[i] : (w[i - 16] + s0 + w[i - 7] + s1) | 0);
      var temp2 = (rightRotate(hash[0], 2) ^ rightRotate(hash[0], 13) ^ rightRotate(hash[0], 22)) + maj;

      hash = [(temp1 + temp2) | 0].concat(hash);
      hash[4] = (hash[4] + temp1) | 0;
    }

    for (i = 0; i < 8; i++) {
      hash[i] = (hash[i] + oldHash[i]) | 0;
    }
  }

  for (i = 0; i < 8; i++) {
    for (j = 3; j >= 0; j--) {
      var b = (hash[i] >> (8 * j)) & 255;
      result += (b < 16 ? '0' : '') + b.toString(16);
    }
  }
  return result;
}

// 统一对外异步/同步兼容接口（优先 Web Crypto，非安全 HTTP 下自动无缝降级为 pureJsSha256）
async function sha256Hex(str) {
  try {
    if (typeof crypto !== 'undefined' && crypto && crypto.subtle && typeof crypto.subtle.digest === 'function') {
      const enc = new TextEncoder();
      const data = enc.encode(str);
      const hashBuf = await crypto.subtle.digest('SHA-256', data);
      return Array.from(new Uint8Array(hashBuf))
        .map(b => b.toString(16).padStart(2, '0'))
        .join('');
    }
  } catch (e) {
    // 降级使用纯 JS 实现
  }
  return pureJsSha256(str);
}

// 用户账号云端存储 Key 生成（哈希转义，防止特殊字符）
async function getUserCloudKey(username) {
  const clean = username.trim().toLowerCase();
  const hex = await sha256Hex(clean);
  return `pm_u_${hex.slice(0, 24)}`;
}

// 获取当前后端服务器地址
function getBackendBaseUrl() {
  if (customServerUrl.value) {
    return customServerUrl.value.replace(/\/+$/, '');
  }
  if (typeof window !== 'undefined' && window.location && window.location.origin) {
    if (window.location.origin.startsWith('http')) {
      return window.location.origin;
    }
  }
  return '';
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

  // 设置云端独立服务器地址（选填，留空即默认使用当前服务器或内置云端）
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
    const salt = Math.random().toString(36).slice(2) + Date.now().toString(36);
    const pwdHash = await sha256Hex(cleanPwd + ':' + salt);

    const localExport = localStore.exportData();
    const studyLogs = JSON.parse(localStorage.getItem('policy_study_logs') || '{}');

    // 1. 如果有后端服务器（如当前访问云服务器），优先向后端注册
    let backendSuccess = false;
    const backendBase = getBackendBaseUrl();
    if (backendBase) {
      try {
        const bRes = await fetch(`${backendBase}/api/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            username: cleanUser,
            password: cleanPwd,
            nickname: cleanNick
          })
        });
        if (bRes.ok) {
          const bData = await bRes.json();
          if (bData.token) {
            authToken.value = bData.token;
            localStorage.setItem('policy_auth_token', bData.token);
            backendSuccess = true;
          }
        } else {
          const errData = await bRes.json().catch(() => ({}));
          if (errData.detail && (errData.detail.includes('已被注册') || errData.detail.includes('已存在'))) {
            throw new Error(errData.detail);
          }
        }
      } catch (e) {
        if (e.message && (e.message.includes('已被注册') || e.message.includes('已存在'))) {
          throw e;
        }
      }
    }

    // 2. 检查 KVDB 公网云端是否已存在
    try {
      const checkRes = await fetch(cloudUrl, { method: 'GET', cache: 'no-cache' });
      if (checkRes.ok) {
        throw new Error('该用户名已被注册，请直接登录或换一个用户名');
      }
    } catch (e) {
      if (e.message.includes('已被注册')) throw e;
    }

    // 3. 写入 KVDB (全天候免开机公网同步备份)
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

    try {
      await fetch(cloudUrl, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(userData)
      });
    } catch (e) {
      console.warn('KVDB 云备份暂缓:', e);
      if (!backendSuccess) {
        throw new Error('连接云端失败，请检查网络连接');
      }
    }

    // 4. 保存本地会话
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

    let loggedIn = false;
    let userData = null;

    // 1. 优先尝试本地/云服务器后端登录
    const backendBase = getBackendBaseUrl();
    if (backendBase) {
      try {
        const bRes = await fetch(`${backendBase}/api/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            username: cleanUser,
            password: cleanPwd
          })
        });
        if (bRes.ok) {
          const bData = await bRes.json();
          if (bData.token && bData.user) {
            authToken.value = bData.token;
            localStorage.setItem('policy_auth_token', bData.token);
            userData = {
              username: bData.user.username,
              nickname: bData.user.nickname || bData.user.username,
              records: (bData.cloud_data && bData.cloud_data.records) || {},
              stats: (bData.cloud_data && bData.cloud_data.stats) || {}
            };
            loggedIn = true;
          }
        } else {
          const errData = await bRes.json().catch(() => ({}));
          if (errData.detail && (errData.detail.includes('密码') || errData.detail.includes('不正确'))) {
            throw new Error(errData.detail);
          }
        }
      } catch (e) {
        if (e.message && (e.message.includes('密码') || e.message.includes('不正确'))) {
          throw e;
        }
      }
    }

    // 2. 如果后端未登录成功（或纯静态页无后端），从公网 KVDB 获取验证
    if (!loggedIn) {
      const res = await fetch(cloudUrl, { method: 'GET', cache: 'no-cache' });
      if (res.status === 404) {
        throw new Error('账号不存在，请先切换到「注册新账号」进行创建');
      }
      if (!res.ok) {
        throw new Error(`连接云端失败 (HTTP ${res.status})，请检查网络`);
      }

      userData = await res.json();
      const calcHash = await sha256Hex(cleanPwd + ':' + (userData.salt || ''));
      if (calcHash !== userData.pwdHash) {
        throw new Error('用户名或密码不正确，请重新输入');
      }
      loggedIn = true;
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
    this.saveSession(userData, userData.pwdHash || '', userData.salt || '');

    // 5. 双向对齐：静默把两端合并后的最全数据推回云端与服务器
    try {
      await this.syncNow();
    } catch (e) {
      console.warn('同步对齐暂缓:', e);
    }
    return currentUser.value;
  },

  saveSession(userData, pwdHash, salt) {
    currentUser.value = {
      username: userData.username,
      nickname: userData.nickname || userData.username
    };
    if (pwdHash) {
      authToken.value = pwdHash;
      localStorage.setItem('policy_auth_pwd', pwdHash);
    }
    if (salt) {
      localStorage.setItem('policy_auth_salt', salt);
    }
    localStorage.setItem('policy_auth_user', JSON.stringify(currentUser.value));
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
    localStorage.removeItem('policy_auth_token');
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

      const localExport = localStore.exportData();
      const localLogs = JSON.parse(localStorage.getItem('policy_study_logs') || '{}');

      // 1. 如果有后端 Token，同步到后端服务器 SQLite
      const backendBase = getBackendBaseUrl();
      if (backendBase && authToken.value) {
        try {
          const sRes = await fetch(`${backendBase}/api/auth/sync`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${authToken.value}`
            },
            body: JSON.stringify({
              client_records: localExport.records || {},
              client_stats: localLogs || {}
            })
          });
          if (sRes.ok) {
            const sData = await sRes.json();
            if (sData.server_records) {
              localStore.importData({
                records: sData.server_records,
                stats: sData.server_stats || {}
              }, 'merge');
            }
          }
        } catch (e) {
          console.warn('服务器后端同步暂缓:', e);
        }
      }

      // 2. 同时双向同步到 KVDB (确保 GitHub Pages / 手机数据无缝互通)
      try {
        const res = await fetch(`${cloudUrl}?t=${Date.now()}`, { method: 'GET', cache: 'no-cache' });
        let cloudData = {};
        if (res.ok) {
          cloudData = await res.json();
        }

        const currentLocal = localStore.exportData();
        const currentLogs = JSON.parse(localStorage.getItem('policy_study_logs') || '{}');

        const mergedRecords = smartMergeRecords(cloudData.records || {}, currentLocal.records || {});
        const mergedStats = smartMergeStats(cloudData.stats || {}, currentLogs || {});

        cloudData.username = currentUser.value.username;
        cloudData.nickname = currentUser.value.nickname || currentUser.value.username;
        cloudData.records = mergedRecords;
        cloudData.stats = mergedStats;
        cloudData.last_sync = new Date().toISOString();

        await fetch(cloudUrl, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(cloudData)
        });

        localStore.importData({
          records: mergedRecords,
          stats: mergedStats
        }, 'merge');
      } catch (e) {
        console.warn('KVDB 同步暂缓:', e);
      }

      syncStatus.value = 'synced';
      const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      lastSyncTime.value = timeStr;
      localStorage.setItem('policy_last_sync_time', timeStr);
      return true;
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
