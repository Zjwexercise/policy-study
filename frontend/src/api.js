import { localStore } from './localStore';
import { auth } from './auth';

const API_BASE = '/api';

// 状态：后端 API 是否可用
let isOfflineMode = null;

function notifyUserAction() {
  try {
    auth.triggerAutoSync(3000);
  } catch (e) {
    // 忽略静默同步调度错误
  }
}

async function detectMode() {
  if (isOfflineMode !== null) return isOfflineMode;
  try {
    const res = await fetch(`${API_BASE}/workbooks`, { 
      method: 'GET',
      signal: AbortSignal.timeout ? AbortSignal.timeout(1200) : undefined 
    });
    isOfflineMode = !res.ok;
  } catch (e) {
    isOfflineMode = true;
  }
  return isOfflineMode;
}

export const api = {
  // 练习册列表
  async getWorkbooks() {
    if (await detectMode()) return localStore.getWorkbooks();
    try {
      const res = await fetch(`${API_BASE}/workbooks`);
      if (!res.ok) throw new Error();
      return await res.json();
    } catch {
      isOfflineMode = true;
      return localStore.getWorkbooks();
    }
  },

  async getWorkbook(id) {
    if (await detectMode()) return localStore.getWorkbook(id);
    try {
      const res = await fetch(`${API_BASE}/workbooks/${id}`);
      if (!res.ok) throw new Error();
      return await res.json();
    } catch {
      isOfflineMode = true;
      return localStore.getWorkbook(id);
    }
  },

  async uploadPdf(file, name) {
    if (await detectMode()) {
      throw new Error('离线/静态托管模式下暂不支持上传解析新PDF，题目已全部内嵌 1521 题！');
    }
    const formData = new FormData();
    formData.append('file', file);
    if (name) formData.append('name', name);

    const res = await fetch(`${API_BASE}/workbooks/upload`, {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || '上传解析PDF失败');
    return data;
  },

  async resetWorkbook(id) {
    if (await detectMode()) return localStore.resetWorkbook(id);
    try {
      const res = await fetch(`${API_BASE}/workbooks/${id}/reset`, { method: 'POST' });
      if (!res.ok) throw new Error();
      return await res.json();
    } catch {
      return localStore.resetWorkbook(id);
    }
  },

  async deleteWorkbook(id) {
    if (await detectMode()) {
      throw new Error('默认真题集不可删除');
    }
    const res = await fetch(`${API_BASE}/workbooks/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('删除练习册失败');
    return res.json();
  },

  // 题目与刷题
  async getQuestions(workbookId, params = {}) {
    if (await detectMode()) return localStore.getQuestions(workbookId, params);
    try {
      const query = new URLSearchParams(params).toString();
      const res = await fetch(`${API_BASE}/workbooks/${workbookId}/questions?${query}`);
      if (!res.ok) throw new Error();
      return await res.json();
    } catch {
      isOfflineMode = true;
      return localStore.getQuestions(workbookId, params);
    }
  },

  async submitAnswer(workbookId, questionId, userAnswer) {
    let result;
    if (await detectMode()) {
      result = await localStore.submitAnswer(workbookId, questionId, userAnswer);
    } else {
      try {
        const res = await fetch(`${API_BASE}/practice/submit`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            workbook_id: workbookId,
            question_id: questionId,
            user_answer: userAnswer
          })
        });
        if (!res.ok) throw new Error();
        result = await res.json();
      } catch {
        result = await localStore.submitAnswer(workbookId, questionId, userAnswer);
      }
    }
    notifyUserAction();
    return result;
  },

  async toggleStar(workbookId, questionId, isStarred) {
    let result;
    if (await detectMode()) {
      result = await localStore.toggleStar(workbookId, questionId, isStarred);
    } else {
      try {
        const res = await fetch(`${API_BASE}/practice/star`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            workbook_id: workbookId,
            question_id: questionId,
            is_starred: isStarred
          })
        });
        if (!res.ok) throw new Error();
        result = await res.json();
      } catch {
        result = await localStore.toggleStar(workbookId, questionId, isStarred);
      }
    }
    notifyUserAction();
    return result;
  },

  // 斩杀熟题
  async toggleKillQuestion(workbookId, questionId, isKilled) {
    let result;
    if (await detectMode()) {
      result = await localStore.toggleKillQuestion(workbookId, questionId, isKilled);
    } else {
      try {
        const res = await fetch(`${API_BASE}/practice/kill`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            workbook_id: workbookId,
            question_id: questionId,
            is_killed: isKilled
          })
        });
        if (!res.ok) throw new Error();
        result = await res.json();
      } catch {
        result = await localStore.toggleKillQuestion(workbookId, questionId, isKilled);
      }
    }
    notifyUserAction();
    return result;
  },

  async getKilledQuestions(params = {}) {
    if (await detectMode()) return localStore.getKilledQuestions(params);
    try {
      const query = new URLSearchParams(params).toString();
      const res = await fetch(`${API_BASE}/practice/killed-questions?${query}`);
      if (!res.ok) throw new Error();
      return await res.json();
    } catch {
      return localStore.getKilledQuestions(params);
    }
  },

  async clearKilledQuestions(workbookId) {
    let result;
    if (await detectMode()) {
      result = await localStore.clearKilledQuestions(workbookId);
    } else {
      try {
        const url = workbookId ? `${API_BASE}/practice/killed-questions/clear?workbook_id=${workbookId}` : `${API_BASE}/practice/killed-questions/clear`;
        const res = await fetch(url, { method: 'DELETE' });
        if (!res.ok) throw new Error();
        result = await res.json();
      } catch {
        result = await localStore.clearKilledQuestions(workbookId);
      }
    }
    notifyUserAction();
    return result;
  },

  async updateQuestion(questionId, data) {
    if (await detectMode()) {
      return { success: true, message: '题目已保存在本地' };
    }
    const res = await fetch(`${API_BASE}/questions/${questionId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error('保存修改题目失败');
    return res.json();
  },

  // 错题本
  async getWrongQuestions(params = {}) {
    if (await detectMode()) return localStore.getWrongQuestions(params);
    try {
      const query = new URLSearchParams(params).toString();
      const res = await fetch(`${API_BASE}/wrong-book?${query}`);
      if (!res.ok) throw new Error();
      return await res.json();
    } catch {
      return localStore.getWrongQuestions(params);
    }
  },

  async toggleMasterWrong(questionId, isMastered) {
    let result;
    if (await detectMode()) {
      result = await localStore.toggleMasterWrong(questionId, isMastered);
    } else {
      try {
        const res = await fetch(`${API_BASE}/wrong-book/${questionId}/master`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ is_mastered: isMastered })
        });
        if (!res.ok) throw new Error();
        result = await res.json();
      } catch {
        result = await localStore.toggleMasterWrong(questionId, isMastered);
      }
    }
    notifyUserAction();
    return result;
  },

  async resetWrongAnswers(workbookId) {
    let result;
    if (await detectMode()) {
      result = await localStore.resetWrongAnswers(workbookId);
    } else {
      try {
        const res = await fetch(`${API_BASE}/wrong-book/reset-answers`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ workbook_id: (workbookId && workbookId !== 'all') ? Number(workbookId) : null })
        });
        if (!res.ok) throw new Error();
        result = await res.json();
      } catch {
        result = await localStore.resetWrongAnswers(workbookId);
      }
    }
    notifyUserAction();
    return result;
  },

  async resetQuestionAnswer(workbookId, questionId) {
    let result;
    if (await detectMode()) {
      result = await localStore.resetQuestionAnswer(workbookId, questionId);
    } else {
      try {
        const res = await fetch(`${API_BASE}/wrong-book/${questionId}/reset-answer`, {
          method: 'POST'
        });
        if (!res.ok) throw new Error();
        result = await res.json();
      } catch {
        result = await localStore.resetQuestionAnswer(workbookId, questionId);
      }
    }
    notifyUserAction();
    return result;
  },

  async clearWrongBook(workbookId) {
    let result;
    if (await detectMode()) {
      result = await localStore.clearWrongBook(workbookId);
    } else {
      try {
        const url = workbookId ? `${API_BASE}/wrong-book/clear?workbook_id=${workbookId}` : `${API_BASE}/wrong-book/clear`;
        const res = await fetch(url, { method: 'DELETE' });
        if (!res.ok) throw new Error();
        result = await res.json();
      } catch {
        result = await localStore.clearWrongBook(workbookId);
      }
    }
    notifyUserAction();
    return result;
  },

  // 考点笔记
  async getNotes(workbookId) {
    if (await detectMode()) return localStore.getNotes(workbookId);
    try {
      const url = workbookId ? `${API_BASE}/notes?workbook_id=${workbookId}` : `${API_BASE}/notes`;
      const res = await fetch(url);
      if (!res.ok) throw new Error();
      return await res.json();
    } catch {
      return localStore.getNotes(workbookId);
    }
  },

  async saveNote(questionId, content) {
    let result;
    if (await detectMode()) {
      result = await localStore.saveNote(questionId, content);
    } else {
      try {
        const res = await fetch(`${API_BASE}/notes/${questionId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ content })
        });
        if (!res.ok) throw new Error();
        result = await res.json();
      } catch {
        result = await localStore.saveNote(questionId, content);
      }
    }
    notifyUserAction();
    return result;
  },

  // 统计与系统
  async reportStudyTime(seconds) {
    let result;
    if (await detectMode()) {
      result = await localStore.reportStudyTime(seconds);
    } else {
      try {
        const res = await fetch(`${API_BASE}/practice/study-time`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ seconds })
        });
        if (!res.ok) throw new Error();
        result = await res.json();
      } catch {
        result = await localStore.reportStudyTime(seconds);
      }
    }
    notifyUserAction();
    return result;
  },

  async getStats() {
    if (await detectMode()) return localStore.getStats();
    try {
      const res = await fetch(`${API_BASE}/practice/stats`);
      if (!res.ok) throw new Error();
      return await res.json();
    } catch {
      return localStore.getStats();
    }
  },

  async getNetworkInfo() {
    if (await detectMode()) {
      return { local_ip: '127.0.0.1', is_cloud: true };
    }
    try {
      const res = await fetch(`${API_BASE}/system/network-info`);
      if (!res.ok) throw new Error();
      return await res.json();
    } catch {
      return { local_ip: '127.0.0.1', is_cloud: true };
    }
  },

  // 跨端数据同步与备份
  exportData() {
    return localStore.exportData();
  },

  exportDataAsCode() {
    return localStore.exportDataAsCode();
  },

  parseSyncInput(input) {
    return localStore.parseSyncInput(input);
  },

  importData(input, mode = 'merge') {
    return localStore.importData(input, mode);
  },

  clearAllUserData() {
    return localStore.clearAllUserData();
  }
};
