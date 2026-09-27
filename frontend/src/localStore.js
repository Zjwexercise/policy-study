/**
 * localStore.js - 离线/静态优先模式本地存储引擎 (GitHub Pages 0 元终极运行核心)
 * 具备完整的题目加载、答题判定、答题记录、错题本、考点笔记和学习统计功能。
 */

// 缓存加载的题目数据
const cache = {
  workbooks: null,
  questionsByWb: {},
  allQuestions: null
};

// 辅助：从 ./data 获取静态 JSON
async function fetchStatic(path) {
  // 适配 Vite base './' 路径
  const base = import.meta.env.BASE_URL || './';
  const cleanBase = base.endsWith('/') ? base : base + '/';
  // 增加时间戳与 no-cache，确保用户在手机/电脑刷新后立即获取校准后的最新题目
  const url = `${cleanBase}data/${path}?v=${Date.now()}`;
  const res = await fetch(url, { cache: 'no-cache' });
  if (!res.ok) throw new Error(`加载离线数据失败: ${path}`);
  return res.json();
}


export const localStore = {
  // 获取练习册列表
  async getWorkbooks() {
    if (!cache.workbooks) {
      cache.workbooks = await fetchStatic('workbooks.json');
    }

    return cache.workbooks.map(wb => {
      const total = wb.total_questions || 0;
      // 从 localStorage 统计该练习册的答题数和正确数
      let answered = 0;
      let correct = 0;
      let wrong = 0;

      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key.startsWith(`policy_ans_${wb.id}_`)) {
          answered++;
          const qid = key.split('_')[3];
          if (localStorage.getItem(`policy_cor_${qid}`) === '1') {
            correct++;
          }
        }
        if (key.startsWith(`policy_wrong_cnt_${wb.id}_`)) {
          const qid = key.split('_')[4];
          if (localStorage.getItem(`policy_wrong_master_${qid}`) !== '1') {
            wrong++;
          }
        }
      }

      const accuracy = answered > 0 ? Math.round((correct / answered) * 1000) / 10 : 0;

      return {
        ...wb,
        answered_count: answered,
        correct_count: correct,
        wrong_count: wrong,
        accuracy
      };
    });
  },

  // 获取单个练习册详情
  async getWorkbook(id) {
    const wbs = await this.getWorkbooks();
    const wb = wbs.find(w => String(w.id) === String(id));
    if (!wb) throw new Error('练习册不存在');
    return wb;
  },

  // 获取题目列表（支持题型、分类、状态筛选）
  async getQuestions(workbookId, params = {}) {
    const isAll = String(workbookId).toLowerCase() === 'all' || workbookId === 0 || workbookId === -1;
    let questions = [];

    if (isAll) {
      if (!cache.allQuestions) {
        cache.allQuestions = await fetchStatic('all_questions.json');
      }
      questions = cache.allQuestions;
    } else {
      if (!cache.questionsByWb[workbookId]) {
        cache.questionsByWb[workbookId] = await fetchStatic(`questions_${workbookId}.json`);
      }
      questions = cache.questionsByWb[workbookId];
    }

    // 注入本地用户进度
    let result = questions.map(q => {
      const qid = q.id;
      const wId = q.workbook_id;
      const userAns = localStorage.getItem(`policy_ans_${wId}_${qid}`);
      const isCorrect = localStorage.getItem(`policy_cor_${qid}`);
      const isStarred = localStorage.getItem(`policy_star_${qid}`) === '1';
      const wrongCnt = Number(localStorage.getItem(`policy_wrong_cnt_${wId}_${qid}`) || 0);
      const isMastered = localStorage.getItem(`policy_wrong_master_${qid}`) === '1';
      const isKilled = localStorage.getItem(`policy_killed_${qid}`) === '1';
      const killedAt = localStorage.getItem(`policy_killed_at_${qid}`) || null;
      const noteContent = localStorage.getItem(`policy_note_${qid}`) || '';

      return {
        ...q,
        user_answer: userAns !== null ? userAns : null,
        is_correct: isCorrect !== null ? (isCorrect === '1' ? 1 : 0) : null,
        is_starred: isStarred ? 1 : 0,
        is_killed: isKilled ? 1 : 0,
        killed_at: killedAt,
        wrong_count: wrongCnt,
        is_mastered: isMastered ? 1 : 0,
        note_content: noteContent
      };
    });

    // 斩杀过滤：如果开启了 hide_killed，则排除已斩杀题目
    if (params.hide_killed) {
      result = result.filter(q => q.is_killed !== 1);
    }

    // 筛选
    if (params.category && params.category !== '全部') {
      result = result.filter(q => q.category === params.category);
    }
    if (params.question_type && params.question_type !== '全部') {
      result = result.filter(q => q.question_type === params.question_type);
    }
    if (params.status) {
      if (params.status === 'unattempted') {
        result = result.filter(q => q.user_answer === null);
      } else if (params.status === 'wrong') {
        result = result.filter(q => q.is_correct === 0);
      } else if (params.status === 'correct') {
        result = result.filter(q => q.is_correct === 1);
      } else if (params.status === 'starred') {
        result = result.filter(q => q.is_starred === 1);
      } else if (params.status === 'killed') {
        result = result.filter(q => q.is_killed === 1);
      }
    }

    return result;
  },

  // 提交答案
  async submitAnswer(workbookId, questionId, userAnswer) {
    // 寻找题目
    let targetQ = null;
    if (cache.allQuestions) {
      targetQ = cache.allQuestions.find(q => String(q.id) === String(questionId));
    }
    if (!targetQ && cache.questionsByWb[workbookId]) {
      targetQ = cache.questionsByWb[workbookId].find(q => String(q.id) === String(questionId));
    }
    if (!targetQ) {
      const all = await fetchStatic('all_questions.json');
      cache.allQuestions = all;
      targetQ = all.find(q => String(q.id) === String(questionId));
    }

    if (!targetQ) throw new Error('题目不存在');

    // 判定正确与否（支持单选与多选，排序后严格比对）
    const cleanUser = Array.from(userAnswer.toUpperCase()).sort().join('');
    const cleanStd = Array.from(targetQ.answer.toUpperCase()).sort().join('');
    const isCorrect = cleanUser === cleanStd;

    // 写入 localStorage
    localStorage.setItem(`policy_ans_${workbookId}_${questionId}`, userAnswer);
    localStorage.setItem(`policy_cor_${questionId}`, isCorrect ? '1' : '0');

    if (!isCorrect) {
      const curWrong = Number(localStorage.getItem(`policy_wrong_cnt_${workbookId}_${questionId}`) || 0);
      localStorage.setItem(`policy_wrong_cnt_${workbookId}_${questionId}`, String(curWrong + 1));
      localStorage.setItem(`policy_wrong_master_${questionId}`, '0');
    }

    return {
      is_correct: isCorrect,
      correct_answer: targetQ.answer,
      explanation: targetQ.explanation || '【解析】详见题干与选项考点解析。'
    };
  },

  // 收藏/取消收藏
  async toggleStar(workbookId, questionId, isStarred) {
    if (isStarred) {
      localStorage.setItem(`policy_star_${questionId}`, '1');
    } else {
      localStorage.removeItem(`policy_star_${questionId}`);
    }
    return { success: true, is_starred: isStarred };
  },

  // 获取错题本
  async getWrongQuestions(params = {}) {
    const all = await this.getQuestions('all');
    let wrongList = all.filter(q => q.wrong_count > 0);

    if (params.workbook_id && params.workbook_id !== 'all') {
      wrongList = wrongList.filter(q => String(q.workbook_id) === String(params.workbook_id));
    }
    if (params.category && params.category !== '全部') {
      wrongList = wrongList.filter(q => q.category === params.category);
    }
    if (params.is_mastered !== undefined && params.is_mastered !== 'all') {
      const targetMaster = String(params.is_mastered) === '1' || params.is_mastered === true ? 1 : 0;
      wrongList = wrongList.filter(q => q.is_mastered === targetMaster);
    }

    return wrongList;
  },

  // 标记错题已掌握
  async toggleMasterWrong(questionId, isMastered) {
    localStorage.setItem(`policy_wrong_master_${questionId}`, isMastered ? '1' : '0');
    return { success: true, is_mastered: isMastered };
  },

  // 清空错题记录
  async clearWrongBook(workbookId) {
    const keysToRemove = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (workbookId) {
        if (key.startsWith(`policy_wrong_cnt_${workbookId}_`)) {
          keysToRemove.push(key);
          const qid = key.split('_')[4];
          keysToRemove.push(`policy_wrong_master_${qid}`);
        }
      } else {
        if (key.startsWith('policy_wrong_cnt_') || key.startsWith('policy_wrong_master_')) {
          keysToRemove.push(key);
        }
      }
    }
    keysToRemove.forEach(k => localStorage.removeItem(k));
    return { success: true };
  },

  // 获取笔记
  async getNotes(workbookId) {
    const all = await this.getQuestions('all');
    let notes = all.filter(q => q.note_content && q.note_content.trim().length > 0);
    if (workbookId) {
      notes = notes.filter(q => String(q.workbook_id) === String(workbookId));
    }
    return notes.map(q => ({
      question_id: q.id,
      workbook_id: q.workbook_id,
      workbook_name: q.workbook_name,
      question_num: q.question_num,
      category: q.category,
      stem: q.stem,
      content: q.note_content,
      updated_at: '本地保存'
    }));
  },

  // 保存笔记
  async saveNote(questionId, content) {
    if (!content || !content.trim()) {
      localStorage.removeItem(`policy_note_${questionId}`);
    } else {
      localStorage.setItem(`policy_note_${questionId}`, content);
    }
    return { success: true, content };
  },

  // 重置单本进度
  async resetWorkbook(id) {
    const keysToRemove = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key.startsWith(`policy_ans_${id}_`)) {
        keysToRemove.push(key);
        const qid = key.split('_')[3];
        keysToRemove.push(`policy_cor_${qid}`);
      }
    }
    keysToRemove.forEach(k => localStorage.removeItem(k));
    return { success: true, message: '练习进度已重置' };
  },

  // 斩杀/撤销斩杀熟题
  async toggleKillQuestion(workbookId, questionId, isKilled) {
    if (isKilled) {
      localStorage.setItem(`policy_killed_${questionId}`, '1');
      localStorage.setItem(`policy_killed_at_${questionId}`, new Date().toISOString());
      // 熟练斩杀同时在错题本中标记为已掌握
      localStorage.setItem(`policy_wrong_master_${questionId}`, '1');
    } else {
      localStorage.removeItem(`policy_killed_${questionId}`);
      localStorage.removeItem(`policy_killed_at_${questionId}`);
    }
    return { success: true, is_killed: isKilled };
  },

  // 获取已斩杀题目列表
  async getKilledQuestions(params = {}) {
    const all = await this.getQuestions('all');
    let killedList = all.filter(q => q.is_killed === 1);

    if (params.workbook_id && params.workbook_id !== 'all') {
      killedList = killedList.filter(q => String(q.workbook_id) === String(params.workbook_id));
    }
    if (params.category && params.category !== '全部') {
      killedList = killedList.filter(q => q.category === params.category);
    }
    if (params.keyword && params.keyword.trim()) {
      const kw = params.keyword.trim().toLowerCase();
      killedList = killedList.filter(q => (q.stem && q.stem.toLowerCase().includes(kw)) || (q.explanation && q.explanation.toLowerCase().includes(kw)));
    }

    // 默认按斩杀时间倒序排列
    killedList.sort((a, b) => {
      const ta = a.killed_at ? new Date(a.killed_at).getTime() : 0;
      const tb = b.killed_at ? new Date(b.killed_at).getTime() : 0;
      return tb - ta;
    });

    return killedList;
  },

  // 清空斩题本（一键全部复活题目）
  async clearKilledQuestions(workbookId) {
    const keysToRemove = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith('policy_killed_')) {
        const qid = key.replace('policy_killed_at_', '').replace('policy_killed_', '');
        if (workbookId && workbookId !== 'all') {
          if (cache.allQuestions) {
            const q = cache.allQuestions.find(item => String(item.id) === String(qid));
            if (q && String(q.workbook_id) === String(workbookId)) {
              keysToRemove.push(key);
            }
          }
        } else {
          keysToRemove.push(key);
        }
      }
    }
    keysToRemove.forEach(k => localStorage.removeItem(k));
    return { success: true };
  },

  // 统计面板
  async getStats() {
    const all = await this.getQuestions('all');
    const total = all.length;
    let answered = 0;
    let correct = 0;
    let wrong = 0;
    let starred = 0;
    let killed = 0;
    let notesCount = 0;

    const catStats = {};

    all.forEach(q => {
      if (q.user_answer !== null) answered++;
      if (q.is_correct === 1) correct++;
      if (q.wrong_count > 0 && q.is_mastered === 0) wrong++;
      if (q.is_starred === 1) starred++;
      if (q.is_killed === 1) killed++;
      if (q.note_content && q.note_content.trim().length > 0) notesCount++;

      const c = q.category || '综合';
      if (!catStats[c]) {
        catStats[c] = { total: 0, answered: 0, correct: 0 };
      }
      catStats[c].total++;
      if (q.user_answer !== null) catStats[c].answered++;
      if (q.is_correct === 1) catStats[c].correct++;
    });

    const accuracy = answered > 0 ? Math.round((correct / answered) * 1000) / 10 : 0;
    const catList = Object.keys(catStats).map(c => {
      const item = catStats[c];
      const catAcc = item.answered > 0 ? Math.round((item.correct / item.answered) * 100) : 0;
      return {
        category: c,
        total: item.total,
        answered: item.answered,
        correct: item.correct,
        accuracy: catAcc
      };
    });

    const overview = {
      total_questions: total,
      total_answered: answered,
      total_correct: correct,
      total_wrong: wrong,
      total_starred: starred,
      total_killed: killed,
      total_notes: notesCount,
      accuracy
    };

    return {
      ...overview,
      overview,
      categories: catList
    };
  },

  // 跨端数据同步：导出所有刷题进度数据
  exportData() {
    const data = {
      version: 1,
      exported_at: new Date().toISOString(),
      platform: 'policy-study',
      stats: {},
      records: {}
    };

    let answered = 0;
    let correct = 0;
    let wrong = 0;
    let killed = 0;
    let notes = 0;
    let starred = 0;

    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith('policy_')) {
        const val = localStorage.getItem(key);
        data.records[key] = val;

        if (key.startsWith('policy_ans_')) answered++;
        if (key.startsWith('policy_cor_') && val === '1') correct++;
        if (key.startsWith('policy_wrong_cnt_')) wrong++;
        if (key.startsWith('policy_killed_') && !key.startsWith('policy_killed_at_') && val === '1') killed++;
        if (key.startsWith('policy_note_') && val && val.trim().length > 0) notes++;
        if (key.startsWith('policy_star_') && val === '1') starred++;
      }
    }

    data.stats = {
      answered,
      correct,
      wrong,
      killed,
      notes,
      starred,
      accuracy: answered > 0 ? Math.round((correct / answered) * 1000) / 10 : 0,
      total_keys: Object.keys(data.records).length
    };

    return data;
  },

  // 跨端数据同步：导出为压缩同步口令文本
  exportDataAsCode() {
    const data = this.exportData();
    const jsonStr = JSON.stringify(data);
    const b64 = btoa(encodeURIComponent(jsonStr).replace(/%([0-9A-F]{2})/g, (match, p1) => {
      return String.fromCharCode('0x' + p1);
    }));
    return `POLICY_SYNC#${b64}#END`;
  },

  // 解析同步输入（支持口令文本、JSON字符串、对象）
  parseSyncInput(input) {
    if (!input) throw new Error('同步内容为空，请粘贴口令或选择备份文件');

    let raw = input;
    if (typeof input === 'object' && input !== null) {
      if (input.records && typeof input.records === 'object') return input;
      throw new Error('无效的备份数据格式');
    }

    raw = String(raw).trim();
    if (!raw) throw new Error('同步内容为空');

    // 尝试作为普通 JSON 解析
    if (raw.startsWith('{') && raw.endsWith('}')) {
      try {
        const parsed = JSON.parse(raw);
        if (parsed.records) return parsed;
        if (Object.keys(parsed).some(k => k.startsWith('policy_'))) {
          return { records: parsed, stats: {} };
        }
      } catch (e) {
        // 继续尝试 base64
      }
    }

    // 尝试去除口令前缀后缀
    let cleanB64 = raw;
    if (cleanB64.includes('POLICY_SYNC#')) {
      const parts = cleanB64.split('POLICY_SYNC#');
      cleanB64 = parts[1].split('#END')[0].trim();
    } else if (cleanB64.startsWith('POLICY_SYNC_V1#')) {
      const parts = cleanB64.split('POLICY_SYNC_V1#');
      cleanB64 = parts[1].split('#END')[0].trim();
    }

    try {
      const decodedJson = decodeURIComponent(Array.prototype.map.call(atob(cleanB64), (c) => {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
      }).join(''));
      const parsed = JSON.parse(decodedJson);
      if (parsed.records) return parsed;
      if (Object.keys(parsed).some(k => k.startsWith('policy_'))) {
        return { records: parsed, stats: {} };
      }
    } catch (e) {
      throw new Error('同步口令格式错误或已损坏，请重新在另一端复制完整口令');
    }

    throw new Error('未能识别出有效的刷题数据');
  },

  // 跨端数据同步：导入数据（支持智能合并或完全覆盖）
  importData(input, mode = 'merge') {
    const data = this.parseSyncInput(input);
    const records = data.records || {};
    const keys = Object.keys(records);

    if (keys.length === 0) {
      throw new Error('备份数据中没有包含任何刷题记录');
    }

    let mergedCount = 0;
    let answerMerged = 0;
    let wrongMerged = 0;
    let killedMerged = 0;
    let notesMerged = 0;
    let starsMerged = 0;

    if (mode === 'overwrite') {
      // 覆盖模式：清空现有全部 policy_ 数据
      const keysToRemove = [];
      for (let i = 0; i < localStorage.length; i++) {
        const k = localStorage.key(i);
        if (k && k.startsWith('policy_')) {
          keysToRemove.push(k);
        }
      }
      keysToRemove.forEach(k => localStorage.removeItem(k));

      // 写入全部导入数据
      for (const [key, val] of Object.entries(records)) {
        if (key.startsWith('policy_')) {
          localStorage.setItem(key, String(val));
          mergedCount++;
          if (key.startsWith('policy_ans_')) answerMerged++;
          if (key.startsWith('policy_wrong_cnt_')) wrongMerged++;
          if (key.startsWith('policy_killed_') && !key.startsWith('policy_killed_at_') && val === '1') killedMerged++;
          if (key.startsWith('policy_note_')) notesMerged++;
          if (key.startsWith('policy_star_') && val === '1') starsMerged++;
        }
      }
    } else {
      // 智能合并模式（默认且推荐）：保留两端刷题成果，绝不丢失任何一边的记录！
      for (const [key, incomingVal] of Object.entries(records)) {
        if (!key.startsWith('policy_')) continue;
        const localVal = localStorage.getItem(key);

        if (key.startsWith('policy_ans_')) {
          if (localVal === null) {
            // 本地未做该题，采纳导入答案
            localStorage.setItem(key, String(incomingVal));
            answerMerged++;
          } else {
            // 两端都做过：若导入的答案已答对，而本地是错的，升级为正确答案
            const qid = key.split('_')[3];
            const localCor = localStorage.getItem(`policy_cor_${qid}`);
            const incomingCor = records[`policy_cor_${qid}`];
            if (incomingCor === '1' && localCor !== '1') {
              localStorage.setItem(key, String(incomingVal));
              localStorage.setItem(`policy_cor_${qid}`, '1');
              answerMerged++;
            }
          }
        } else if (key.startsWith('policy_cor_')) {
          if (localVal === null || (incomingVal === '1' && localVal !== '1')) {
            localStorage.setItem(key, String(incomingVal));
          }
        } else if (key.startsWith('policy_wrong_cnt_')) {
          const lNum = Number(localVal || 0);
          const inNum = Number(incomingVal || 0);
          const maxCnt = Math.max(lNum, inNum);
          if (maxCnt > 0) {
            localStorage.setItem(key, String(maxCnt));
            if (lNum === 0 && inNum > 0) wrongMerged++;
          }
        } else if (key.startsWith('policy_wrong_master_')) {
          if (localVal === null || incomingVal === '1') {
            localStorage.setItem(key, String(incomingVal));
          }
        } else if (key.startsWith('policy_killed_') && !key.startsWith('policy_killed_at_')) {
          if (localVal === null || incomingVal === '1') {
            localStorage.setItem(key, String(incomingVal));
            if (localVal !== '1' && incomingVal === '1') killedMerged++;
          }
        } else if (key.startsWith('policy_killed_at_')) {
          if (localVal === null) {
            localStorage.setItem(key, String(incomingVal));
          } else if (incomingVal) {
            const tLocal = new Date(localVal).getTime();
            const tIn = new Date(incomingVal).getTime();
            if (tIn > tLocal) localStorage.setItem(key, String(incomingVal));
          }
        } else if (key.startsWith('policy_note_')) {
          if (!localVal || !localVal.trim()) {
            if (incomingVal && incomingVal.trim()) {
              localStorage.setItem(key, String(incomingVal));
              notesMerged++;
            }
          } else if (incomingVal && incomingVal.trim() && localVal.trim() !== incomingVal.trim()) {
            if (incomingVal.includes(localVal)) {
              localStorage.setItem(key, String(incomingVal));
            } else if (!localVal.includes(incomingVal)) {
              localStorage.setItem(key, `${localVal}\n\n[同步合并笔记]:\n${incomingVal}`);
            }
            notesMerged++;
          }
        } else if (key.startsWith('policy_star_')) {
          if (localVal === null || incomingVal === '1') {
            localStorage.setItem(key, String(incomingVal));
            if (localVal !== '1' && incomingVal === '1') starsMerged++;
          }
        } else {
          if (localVal === null) {
            localStorage.setItem(key, String(incomingVal));
          }
        }
        mergedCount++;
      }
    }

    return {
      success: true,
      mode,
      stats: {
        merged_total_keys: mergedCount,
        answer_count: answerMerged,
        wrong_count: wrongMerged,
        killed_count: killedMerged,
        notes_count: notesMerged,
        stars_count: starsMerged
      }
    };
  },

  // 清空当前设备所有刷题数据
  clearAllUserData() {
    const keysToRemove = [];
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i);
      if (k && k.startsWith('policy_')) {
        keysToRemove.push(k);
      }
    }
    keysToRemove.forEach(k => localStorage.removeItem(k));
    return { success: true, cleared_count: keysToRemove.length };
  }
};

