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
      const noteContent = localStorage.getItem(`policy_note_${qid}`) || '';

      return {
        ...q,
        user_answer: userAns !== null ? userAns : null,
        is_correct: isCorrect !== null ? (isCorrect === '1' ? 1 : 0) : null,
        is_starred: isStarred ? 1 : 0,
        wrong_count: wrongCnt,
        is_mastered: isMastered ? 1 : 0,
        note_content: noteContent
      };
    });

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

  // 统计面板
  async getStats() {
    const all = await this.getQuestions('all');
    const total = all.length;
    let answered = 0;
    let correct = 0;
    let wrong = 0;
    let starred = 0;

    all.forEach(q => {
      if (q.user_answer !== null) answered++;
      if (q.is_correct === 1) correct++;
      if (q.wrong_count > 0 && q.is_mastered === 0) wrong++;
      if (q.is_starred === 1) starred++;
    });

    const accuracy = answered > 0 ? Math.round((correct / answered) * 1000) / 10 : 0;

    return {
      total_questions: total,
      answered_count: answered,
      correct_count: correct,
      wrong_count: wrong,
      starred_count: starred,
      accuracy
    };
  }
};
