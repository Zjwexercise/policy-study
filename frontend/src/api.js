const API_BASE = '/api';

export const api = {
  // 练习册
  async getWorkbooks() {
    const res = await fetch(`${API_BASE}/workbooks`);
    if (!res.ok) throw new Error('获取练习册列表失败');
    return res.json();
  },

  async getWorkbook(id) {
    const res = await fetch(`${API_BASE}/workbooks/${id}`);
    if (!res.ok) throw new Error('获取练习册详情失败');
    return res.json();
  },

  async uploadPdf(file, name) {
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
    const res = await fetch(`${API_BASE}/workbooks/${id}/reset`, {
      method: 'POST'
    });
    if (!res.ok) throw new Error('重置练习进度失败');
    return res.json();
  },

  async deleteWorkbook(id) {
    const res = await fetch(`${API_BASE}/workbooks/${id}`, {
      method: 'DELETE'
    });
    if (!res.ok) throw new Error('删除练习册失败');
    return res.json();
  },

  // 题目与刷题
  async getQuestions(workbookId, params = {}) {
    const query = new URLSearchParams(params).toString();
    const res = await fetch(`${API_BASE}/workbooks/${workbookId}/questions?${query}`);
    if (!res.ok) throw new Error('获取题目失败');
    return res.json();
  },

  async submitAnswer(workbookId, questionId, userAnswer) {
    const res = await fetch(`${API_BASE}/practice/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        workbook_id: workbookId,
        question_id: questionId,
        user_answer: userAnswer
      })
    });
    if (!res.ok) throw new Error('提交答案失败');
    return res.json();
  },

  async toggleStar(workbookId, questionId, isStarred) {
    const res = await fetch(`${API_BASE}/practice/star`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        workbook_id: workbookId,
        question_id: questionId,
        is_starred: isStarred
      })
    });
    if (!res.ok) throw new Error('收藏题目失败');
    return res.json();
  },

  async updateQuestion(questionId, data) {
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
    const query = new URLSearchParams(params).toString();
    const res = await fetch(`${API_BASE}/wrong-book?${query}`);
    if (!res.ok) throw new Error('获取错题失败');
    return res.json();
  },

  async toggleMasterWrong(questionId, isMastered) {
    const res = await fetch(`${API_BASE}/wrong-book/${questionId}/master`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_mastered: isMastered })
    });
    if (!res.ok) throw new Error('更新错题状态失败');
    return res.json();
  },

  async clearWrongBook(workbookId) {
    const url = workbookId ? `${API_BASE}/wrong-book/clear?workbook_id=${workbookId}` : `${API_BASE}/wrong-book/clear`;
    const res = await fetch(url, { method: 'DELETE' });
    if (!res.ok) throw new Error('清空错题记录失败');
    return res.json();
  },

  // 考点笔记
  async getNotes(workbookId) {
    const url = workbookId ? `${API_BASE}/notes?workbook_id=${workbookId}` : `${API_BASE}/notes`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('获取笔记失败');
    return res.json();
  },

  async saveNote(questionId, content) {
    const res = await fetch(`${API_BASE}/notes/${questionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content })
    });
    if (!res.ok) throw new Error('保存笔记失败');
    return res.json();
  },

  // 统计与系统
  async getStats() {
    const res = await fetch(`${API_BASE}/practice/stats`);
    if (!res.ok) throw new Error('获取学习统计失败');
    return res.json();
  },

  async getNetworkInfo() {
    const res = await fetch(`${API_BASE}/system/network-info`);
    if (!res.ok) throw new Error('获取网络信息失败');
    return res.json();
  }
};
