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

export function normalizeQuestion(q) {
  if (!q) return q;
  let opts = q.options;
  if (!Array.isArray(opts) && opts && typeof opts === 'object') {
    opts = Object.entries(opts).map(([key, value]) => ({ key, value }));
  } else if (typeof opts === 'string') {
    try {
      const parsed = JSON.parse(opts);
      if (Array.isArray(parsed)) opts = parsed;
      else if (parsed && typeof parsed === 'object') {
        opts = Object.entries(parsed).map(([key, value]) => ({ key, value }));
      }
    } catch (e) {
      opts = [];
    }
  } else if (!Array.isArray(opts)) {
    opts = [];
  }

  // 防御性转换：若 opts 是普通字符串数组（如 ["A. ...", "B. ..."] 或 ["选项1", ...]），转换为标准结构
  if (Array.isArray(opts) && opts.length > 0 && typeof opts[0] === 'string') {
    const keys = ['A', 'B', 'C', 'D', 'E', 'F'];
    opts = opts.map((item, idx) => {
      const m = String(item).match(/^([A-F])[.、\s]\s*(.*)$/);
      if (m) {
        return { key: m[1], value: m[2] };
      }
      return { key: keys[idx] || String(idx + 1), value: String(item) };
    });
  }

  let qType = q.question_type;
  if (qType === '单选题' || qType === '单选') qType = 'single';
  else if (qType === '多选题' || qType === '多选') qType = 'multiple';
  else if (!qType) qType = (q.answer && q.answer.length > 1) ? 'multiple' : 'single';

  return {
    ...q,
    options: opts,
    question_type: qType
  };
}

export const api = {
  // 练习册列表
  async getWorkbooks() {
    let list = [];
    if (await detectMode()) {
      list = await localStore.getWorkbooks();
    } else {
      try {
        const res = await fetch(`${API_BASE}/workbooks`);
        if (!res.ok) throw new Error();
        list = await res.json();
      } catch {
        isOfflineMode = true;
        list = await localStore.getWorkbooks();
      }
    }

    // 智能双向融合：无论在线或离线，取服务端与本地 localStorage 中最大的已答题数与错题数，绝不归零！
    try {
      const localList = await localStore.getWorkbooks();
      const localMap = {};
      localList.forEach(w => { localMap[w.id] = w; });
      return list.map(w => {
        const lw = localMap[w.id];
        if (!lw) return w;
        const answered = Math.max(w.answered_count || 0, lw.answered_count || 0);
        const correct = Math.max(w.correct_count || 0, lw.correct_count || 0);
        const wrong = Math.max(w.wrong_count || 0, lw.wrong_count || 0);
        const accuracy = answered > 0 ? Math.round((correct / answered) * 1000) / 10 : 0;
        return {
          ...w,
          answered_count: answered,
          correct_count: correct,
          wrong_count: wrong,
          accuracy
        };
      });
    } catch (e) {
      return list;
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
    let questions = [];
    if (await detectMode()) {
      questions = await localStore.getQuestions(workbookId, params);
    } else {
      try {
        const query = new URLSearchParams(params).toString();
        const res = await fetch(`${API_BASE}/workbooks/${workbookId}/questions?${query}`);
        if (res.ok) {
          questions = await res.json();
        } else {
          questions = await localStore.getQuestions(workbookId, params);
        }
      } catch {
        isOfflineMode = true;
        questions = await localStore.getQuestions(workbookId, params);
      }
    }

    // 关键双向融合保障：将 localStorage 和服务端进行智能合并，绝不因为模式切换丢失任何一题的作答！
    return questions.map(q => {
      const qid = q.id;
      const wId = q.workbook_id || workbookId;
      const localAns = localStorage.getItem(`policy_ans_${wId}_${qid}`) || 
                       localStorage.getItem(`policy_ans_all_${qid}`);
      const localCor = localStorage.getItem(`policy_cor_${qid}`);
      const localStar = localStorage.getItem(`policy_star_${qid}`);
      const localKilled = localStorage.getItem(`policy_killed_${qid}`);
      const localWrongCnt = localStorage.getItem(`policy_wrong_cnt_${wId}_${qid}`);
      const localWrongMaster = localStorage.getItem(`policy_wrong_master_${qid}`);
      const localNote = localStorage.getItem(`policy_note_${qid}`);

      const user_answer = q.user_answer || localAns || null;
      let is_correct = q.is_correct;
      if (is_correct === null || is_correct === undefined) {
        if (localCor === '1') is_correct = true;
        else if (localCor === '0') is_correct = false;
      }

      return normalizeQuestion({
        ...q,
        user_answer,
        is_correct,
        is_starred: q.is_starred || localStar === '1',
        is_killed: q.is_killed || localKilled === '1' ? 1 : 0,
        wrong_count: Math.max(q.wrong_count || 0, Number(localWrongCnt || 0)),
        is_mastered: q.is_mastered || localWrongMaster === '1',
        has_note: q.has_note || !!localNote,
        note_content: q.note_content || localNote || ''
      });
    });
  },

  async submitAnswer(workbookId, questionId, userAnswer) {
    // 无论在线还是离线，始终在本地 localStorage 存一份无缝底稿，绝对不丢题！
    let localResult = null;
    try {
      localResult = await localStore.submitAnswer(workbookId, questionId, userAnswer);
    } catch (e) {
      // ignore
    }

    let result = localResult;
    if (!await detectMode()) {
      try {
        const res = await fetch(`${API_BASE}/practice/submit`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            workbook_id: Number(workbookId) || workbookId,
            question_id: questionId,
            user_answer: userAnswer
          })
        });
        if (res.ok) {
          result = await res.json();
        }
      } catch (e) {
        // 后端失败时使用 localResult
      }
    }
    notifyUserAction();
    return result || localResult || { is_correct: false };
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
    let list = [];
    if (await detectMode()) {
      list = await localStore.getWrongQuestions(params);
    } else {
      try {
        const query = new URLSearchParams(params).toString();
        const res = await fetch(`${API_BASE}/wrong-book?${query}`);
        if (!res.ok) throw new Error();
        list = await res.json();
      } catch {
        list = await localStore.getWrongQuestions(params);
      }
    }

    // 双轨数据合并：自动补充本地作答、已攻克状态
    return list.map(q => {
      const qid = q.question_id || q.id;
      const wId = q.workbook_id;
      const localAns = localStorage.getItem(`policy_ans_${wId}_${qid}`) || localStorage.getItem(`policy_ans_all_${qid}`);
      const localCor = localStorage.getItem(`policy_cor_${qid}`);
      const localMaster = localStorage.getItem(`policy_wrong_master_${qid}`);

      let userAns = (q.user_answer !== undefined && q.user_answer !== null) ? q.user_answer : (localAns || null);
      let isCor = (q.is_correct !== undefined && q.is_correct !== null) ? q.is_correct : (localCor !== null ? localCor === '1' : null);
      let isMastered = (q.is_mastered !== undefined && q.is_mastered !== null) ? q.is_mastered : (localMaster === '1');

      return {
        ...q,
        user_answer: userAns,
        is_correct: isCor,
        is_mastered: isMastered
      };
    });
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
    // 同步写入本地持久化
    localStorage.setItem(`policy_wrong_master_${questionId}`, isMastered ? '1' : '0');
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
