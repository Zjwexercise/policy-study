// 前端智能多语言翻译服务（支持后端持久缓存与离线本地缓存）

const API_BASE = '/api';

/**
 * 翻译单段文本
 */
export async function translateText(text, targetLang = 'th', sourceLang = 'zh-CN') {
  if (!text || !text.trim()) return '';

  const cacheKey = `policy_trans_${targetLang}_${encodeURIComponent(text.slice(0, 40))}`;
  const localCached = localStorage.getItem(cacheKey);
  if (localCached) return localCached;

  try {
    // 优先调用后端翻译并读取 SQLite 缓存
    const res = await fetch(`${API_BASE}/translate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, target_lang: targetLang, source_lang: sourceLang })
    });
    if (res.ok) {
      const data = await res.json();
      if (data && data.translated_text) {
        localStorage.setItem(cacheKey, data.translated_text);
        return data.translated_text;
      }
    }
  } catch (e) {
    // 后端离线或异常，回退至客户端直接请求公共服务
  }

  // 客户端直连回退
  try {
    const url = `https://api.mymemory.translated.net/get?q=${encodeURIComponent(text)}&langpair=${sourceLang}|${targetLang}`;
    const resp = await fetch(url);
    if (resp.ok) {
      const d = await resp.json();
      const directTrans = d?.responseData?.translatedText || text;
      localStorage.setItem(cacheKey, directTrans);
      return directTrans;
    }
  } catch (err) {
    console.warn('客户端直连翻译失败:', err);
  }

  return text;
}

/**
 * 翻译整道题目（包含题干、选项 A/B/C/D 与考点深度解析）
 */
export async function translateQuestion(question, targetLang = 'th') {
  if (!question) return null;

  const qid = question.id || question.question_id;
  const storageKey = `policy_q_trans_${targetLang}_${qid}`;

  // 1. 本地缓存速读（0ms 响应）
  const saved = localStorage.getItem(storageKey);
  if (saved) {
    try {
      return JSON.parse(saved);
    } catch (e) {}
  }

  // 2. 格式化选项数据
  let optionsList = [];
  if (Array.isArray(question.options)) {
    optionsList = question.options.map((opt, idx) => {
      const key = opt && typeof opt === 'object' ? opt.key : String.fromCharCode(65 + idx);
      const val = opt && typeof opt === 'object' ? opt.value : String(opt);
      return { key, value: val };
    });
  }

  // 3. 发送给后端集中翻译与持久入库
  try {
    const res = await fetch(`${API_BASE}/translate/question`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question_id: qid,
        stem: question.stem || '',
        options: optionsList,
        explanation: question.explanation || '',
        target_lang: targetLang
      })
    });

    if (res.ok) {
      const data = await res.json();
      if (data && (data.stem || data.options)) {
        try {
          localStorage.setItem(storageKey, JSON.stringify(data));
        } catch (e) {}
        return data;
      }
    }
  } catch (e) {
    console.warn('请求后端题目翻译异常，执行前端分段回退:', e);
  }

  // 4. 离线/直连回退分段翻译
  try {
    const [stemTrans, expTrans] = await Promise.all([
      translateText(question.stem, targetLang),
      question.explanation ? translateText(question.explanation, targetLang) : Promise.resolve('')
    ]);

    const optionsTrans = {};
    for (const opt of optionsList) {
      optionsTrans[opt.key] = await translateText(opt.value, targetLang);
    }

    const fallbackResult = {
      stem: stemTrans,
      options: optionsTrans,
      explanation: expTrans
    };

    try {
      localStorage.setItem(storageKey, JSON.stringify(fallbackResult));
    } catch (e) {}

    return fallbackResult;
  } catch (err) {
    console.error('整题翻译失败:', err);
    return null;
  }
}
