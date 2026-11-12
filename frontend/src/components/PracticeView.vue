<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import { api } from '../api';
import confetti from 'canvas-confetti';
import { 
  Check, 
  X, 
  Star, 
  FileText, 
  ChevronLeft, 
  ChevronRight, 
  RotateCcw, 
  Shuffle, 
  LayoutGrid, 
  HelpCircle,
  Eye,
  Send,
  Sparkles,
  BookOpen,
  Swords,
  CheckSquare,
  CheckCircle2,
  Brain,
  Dices
} from 'lucide-vue-next';
import AnswerSheetModal from './AnswerSheetModal.vue';
import NoteModal from './NoteModal.vue';

const props = defineProps({
  workbookId: {
    type: [Number, String],
    default: null
  },
  workbooks: {
    type: Array,
    default: () => []
  },
  initialStatus: {
    type: String,
    default: 'all'
  },
  initialRedo: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['switch-tab', 'switch-workbook']);

const questions = ref([]);
const loading = ref(false);
const currentIndex = ref(0);
const selectedOptions = ref([]); // For multiple choice
const showAnswerSheet = ref(false);
const showNoteModal = ref(false);
const hideKilled = ref(true); // 隐藏已斩熟题（熟题不再重复刷）
const toastMsg = ref('');

const showToast = (msg) => {
  toastMsg.value = msg;
  setTimeout(() => {
    if (toastMsg.value === msg) {
      toastMsg.value = '';
    }
  }, 2200);
};

// 单选题作答模式：false 为按 Enter/确认作答提交 (防手抖误触，支持改选)；true 为即选即判
const singleAutoSubmit = ref(localStorage.getItem('policy_single_auto_submit') === 'true');
const toggleSingleAutoSubmit = () => {
  singleAutoSubmit.value = !singleAutoSubmit.value;
  localStorage.setItem('policy_single_auto_submit', String(singleAutoSubmit.value));
  showToast(singleAutoSubmit.value ? '已切换为：单选题点击立即判题' : '已切换为：单选题按Enter确认提交');
};

// 当前练习册名称与是否属于1000题
const currentWorkbookName = computed(() => {
  if (props.workbookId === 'all') return '🌟 全部题库大综合';
  if (props.workbookId === 'random') return '🎲 跨题库·盲盒随机抽题';
  const wb = props.workbooks.find(w => w.id === props.workbookId || String(w.id) === String(props.workbookId));
  return wb ? wb.name : '练习题库';
});

const is1000Workbook = computed(() => {
  if (props.workbookId === 'all') return false;
  const name = currentWorkbookName.value;
  return name.includes('1000题') || (typeof props.workbookId === 'number' && props.workbookId >= 34 && props.workbookId <= 39);
});

// 模式：study (即时解析背题), recall (艾宾浩斯主动回忆模式), exam (模考模式)
const practiceMode = ref(localStorage.getItem('policy_practice_mode') || 'study'); 

// ========================================================
// 1. 艾宾浩斯主动回忆模式独立状态隔离
// 格式: { [qid]: { revealed: bool, selected: string[], isSubmitted: bool, isCorrect: bool, userAns: '' } }
// 铁律：每题进入回忆模式独立遮罩，作答后判题，绝不篡改正式练习答题卡 user_progress！
// ========================================================
const recallStates = ref({});
const getRecallState = (qid) => {
  if (!qid) return { revealed: false, selected: [], isSubmitted: false, isCorrect: null, userAns: '' };
  if (!recallStates.value[qid]) {
    recallStates.value[qid] = {
      revealed: false,
      selected: [],
      isSubmitted: false,
      isCorrect: null,
      userAns: ''
    };
  }
  return recallStates.value[qid];
};

// ========================================================
// 2. 独立挑战自测状态隔离 (Drill Session)
// 用于：每日推荐一题自测、跨题库抽题自测、错题专攻演练与单题随时重新自测
// 铁律：自测作答独立判题对比，绝不清空原试卷历史做题记录！
// ========================================================
const drillStates = ref({});
const getDrillState = (qid) => {
  if (!qid) return { active: false, selected: [], isSubmitted: false, isCorrect: null, userAns: '' };
  if (!drillStates.value[qid]) {
    drillStates.value[qid] = {
      active: false,
      selected: [],
      isSubmitted: false,
      isCorrect: null,
      userAns: ''
    };
  }
  return drillStates.value[qid];
};

const setPracticeMode = (mode) => {
  practiceMode.value = mode;
  localStorage.setItem('policy_practice_mode', mode);
  if (mode === 'recall') {
    showToast('🧠 已开启【回忆模式】：先在心中主动回忆考点，按空格或点击揭晓作答！');
  } else if (mode === 'study') {
    showToast('📝 已切换为【即时背题模式】：作答后立即展示考点精解与正式记录');
  }
};

const isRandomOrder = ref(false);

// 每日推荐一题
const dailyQuestion = ref(null);
const showDailyBanner = ref(true);

const initDailyQuestion = () => {
  if (questions.value.length === 0) return;
  try {
    const today = new Date().toISOString().slice(0, 10);
    const savedDate = localStorage.getItem('policy_daily_date');
    const savedQid = localStorage.getItem('policy_daily_qid');

    if (savedDate === today && savedQid) {
      const found = questions.value.find(q => String(q.id) === String(savedQid));
      if (found) {
        dailyQuestion.value = found;
        return;
      }
    }

    // 智能选取今日一题：优先选急需复习的错题，其次选未答核心题
    const wrongList = questions.value.filter(q => q.wrong_count > 0 && !q.is_mastered);
    let picked = null;
    if (wrongList.length > 0) {
      picked = wrongList[Math.floor(Math.random() * wrongList.length)];
    } else {
      const unattempted = questions.value.filter(q => !q.user_answer);
      if (unattempted.length > 0) {
        picked = unattempted[Math.floor(Math.random() * unattempted.length)];
      } else {
        picked = questions.value[Math.floor(Math.random() * questions.value.length)];
      }
    }

    if (picked) {
      dailyQuestion.value = picked;
      localStorage.setItem('policy_daily_date', today);
      localStorage.setItem('policy_daily_qid', String(picked.id));
    }
  } catch (e) {
    console.warn('初始化每日推荐失败', e);
  }
};

const jumpToDailyQuestion = () => {
  if (!dailyQuestion.value) return;
  const idx = questions.value.findIndex(q => q.id === dailyQuestion.value.id);
  if (idx !== -1) {
    currentIndex.value = idx;
    // 若该题历史做过，自动开启今日独立挑战自测，绝不直接剧透红绿选项
    if (questions.value[idx].user_answer) {
      const ds = getDrillState(questions.value[idx].id);
      ds.active = true;
      ds.selected = [];
      ds.isSubmitted = false;
      ds.isCorrect = null;
      ds.userAns = '';
      showToast(`🎯 今日精选推荐：第 ${dailyQuestion.value.question_num} 题已开启全新挑战自测！`);
    } else {
      showToast(`🎯 已载入今日推荐题：第 ${dailyQuestion.value.question_num} 题！`);
    }
  }
};

const changeDailyQuestion = () => {
  if (questions.value.length <= 1) return;
  const pool = questions.value.filter(q => !dailyQuestion.value || q.id !== dailyQuestion.value.id);
  const picked = pool[Math.floor(Math.random() * pool.length)];
  if (picked) {
    dailyQuestion.value = picked;
    const today = new Date().toISOString().slice(0, 10);
    localStorage.setItem('policy_daily_date', today);
    localStorage.setItem('policy_daily_qid', String(picked.id));
    showToast('🎲 已更换今日推荐题目！');
  }
};

// 跨题库全局随机盲盒抽题
const triggerGlobalRandomQuestion = async () => {
  emit('switch-workbook', 'all');
  isRandomOrder.value = true;
  await loadQuestions();
  if (questions.value.length > 0) {
    const rIdx = Math.floor(Math.random() * questions.value.length);
    currentIndex.value = rIdx;
    const q = questions.value[rIdx];
    // 盲盒抽题：若该题已作答，开启独立挑战自测，让考生真正能动脑挑战
    if (q && q.user_answer) {
      const ds = getDrillState(q.id);
      ds.active = true;
      ds.selected = [];
      ds.isSubmitted = false;
      ds.isCorrect = null;
      ds.userAns = '';
    }
    showToast(`🎲 全真盲盒抽题：已为你随机抽取【${q.workbook_name || '全真合集'}】第 ${q.question_num} 题！`);
  }
};

// 筛选条件
const selectedCategory = ref('全部');
const selectedType = ref('全部');
const selectedStatus = ref(props.initialStatus || 'all'); // all, unattempted, wrong, starred
const redoWrongMode = ref(props.initialRedo || false);

watch(() => props.initialStatus, (newVal) => {
  if (newVal) selectedStatus.value = newVal;
});

watch(() => props.initialRedo, (newVal) => {
  redoWrongMode.value = !!newVal;
});

const categories = ['全部', '马原', '毛中特', '习思想', '史纲', '思修', '时政'];
const types = [
  { id: '全部', label: '全部题型' },
  { id: 'single', label: '单选题' },
  { id: 'multiple', label: '多选题' }
];

const currentQuestion = computed(() => {
  if (questions.value.length === 0) return null;
  return questions.value[currentIndex.value] || null;
});

const hasAnsweredCurrent = computed(() => {
  if (!currentQuestion.value) return false;
  return currentQuestion.value.user_answer !== null && 
         currentQuestion.value.user_answer !== undefined && 
         currentQuestion.value.user_answer !== '';
});

// 加载题目
const loadQuestions = async () => {
  if (!props.workbookId) return;
  loading.value = true;
  try {
    const isRandomWb = props.workbookId === 'random';
    const targetWbId = isRandomWb ? 'all' : props.workbookId;
    if (isRandomWb) {
      isRandomOrder.value = true;
    }

    const params = {};
    if (selectedCategory.value !== '全部') params.category = selectedCategory.value;
    if (selectedType.value !== '全部') params.question_type = selectedType.value;
    if (selectedStatus.value !== 'all') params.status = selectedStatus.value;
    if (redoWrongMode.value) {
      params.redo = true;
    }
    params.hide_killed = hideKilled.value;

    let data = await api.getQuestions(targetWbId, params);
    // 仅当用户明确点击“清空重做”触发 redoWrongMode 时，才清空前端回填选项
    if (redoWrongMode.value) {
      data = data.map(q => ({
        ...q,
        user_answer: null,
        is_correct: null
      }));
    }
    if (isRandomOrder.value) {
      data = [...data].sort(() => Math.random() - 0.5);
    }
    questions.value = data;
    initDailyQuestion();

    // 记忆题号位置：优先恢复上次停留在该练习册的具体题号，刷新不再被动重置到第1题
    const savedIdx = Number(localStorage.getItem(`policy_cur_idx_${props.workbookId}`) || 0);
    if (savedIdx >= 0 && savedIdx < data.length) {
      currentIndex.value = savedIdx;
    } else {
      currentIndex.value = 0;
    }
    isRecallRevealed.value = false;
    resetSelection();
  } catch (err) {
    console.error('加载题目失败', err);
  } finally {
    loading.value = false;
  }
};

// 监听题号切换
watch(currentIndex, (newIdx) => {
  localStorage.setItem(`policy_cur_idx_${props.workbookId}`, String(newIdx));
  isRecallRevealed.value = false;
  resetSelection();
});

const resetSelection = () => {
  selectedOptions.value = [];
  if (currentQuestion.value && currentQuestion.value.user_answer) {
    selectedOptions.value = currentQuestion.value.user_answer.split('');
  }
};

// 监听练习册或筛选改变
watch(() => props.workbookId, () => {
  loadQuestions();
});

watch([selectedCategory, selectedType, selectedStatus, isRandomOrder, hideKilled], () => {
  loadQuestions();
});

// 当前题目的独立回忆与自测计算属性
const currentRecall = computed(() => getRecallState(currentQuestion.value?.id));
const currentDrill = computed(() => getDrillState(currentQuestion.value?.id));

// 当前模式下题目是否已处于揭晓/判定状态
const isCurrentQuestionResolved = computed(() => {
  if (!currentQuestion.value) return false;
  if (practiceMode.value === 'recall') {
    return getRecallState(currentQuestion.value.id).isSubmitted;
  }
  const ds = getDrillState(currentQuestion.value.id);
  if (ds.active) {
    return ds.isSubmitted;
  }
  return hasAnsweredCurrent.value;
});

// 当前模式下的判题结果与作答文字
const currentEvalResult = computed(() => {
  if (!currentQuestion.value) return { isCorrect: false, userAns: '' };
  if (practiceMode.value === 'recall') {
    const s = getRecallState(currentQuestion.value.id);
    return {
      isCorrect: s.isCorrect,
      userAns: s.userAns
    };
  }
  const ds = getDrillState(currentQuestion.value.id);
  if (ds.active && ds.isSubmitted) {
    return {
      isCorrect: ds.isCorrect,
      userAns: ds.userAns
    };
  }
  return {
    isCorrect: currentQuestion.value.is_correct,
    userAns: currentQuestion.value.user_answer
  };
});

// 当前待提交的选项集合（支持普通模式、回忆模式、挑战自测模式）
const currentPendingSelection = computed(() => {
  if (!currentQuestion.value) return [];
  if (practiceMode.value === 'recall') {
    return getRecallState(currentQuestion.value.id).selected;
  }
  const ds = getDrillState(currentQuestion.value.id);
  if (ds.active) {
    return ds.selected;
  }
  return selectedOptions.value;
});

// 计算选项的独立呈现状态（彻底解耦各大模式冲突）
const getOptionStatus = (optKey) => {
  if (!currentQuestion.value) return { isSelected: false, isCorrect: false, isWrong: false, isResolved: false };

  const stdAns = currentQuestion.value.answer || '';

  // 1. 回忆模式
  if (practiceMode.value === 'recall') {
    const s = getRecallState(currentQuestion.value.id);
    if (!s.isSubmitted) {
      return {
        isSelected: s.selected.includes(optKey),
        isCorrect: false,
        isWrong: false,
        isResolved: false
      };
    }
    return {
      isSelected: s.selected.includes(optKey),
      isCorrect: stdAns.includes(optKey),
      isWrong: s.userAns.includes(optKey) && !stdAns.includes(optKey),
      isResolved: true
    };
  }

  // 2. 独立自测挑战模式
  const ds = getDrillState(currentQuestion.value.id);
  if (ds.active) {
    if (!ds.isSubmitted) {
      return {
        isSelected: ds.selected.includes(optKey),
        isCorrect: false,
        isWrong: false,
        isResolved: false
      };
    }
    return {
      isSelected: ds.selected.includes(optKey),
      isCorrect: stdAns.includes(optKey),
      isWrong: ds.userAns.includes(optKey) && !stdAns.includes(optKey),
      isResolved: true
    };
  }

  // 3. 正式题库刷题模式
  if (hasAnsweredCurrent.value) {
    const userAns = currentQuestion.value.user_answer || '';
    return {
      isSelected: userAns.includes(optKey),
      isCorrect: stdAns.includes(optKey),
      isWrong: userAns.includes(optKey) && !stdAns.includes(optKey),
      isResolved: true
    };
  }

  return {
    isSelected: selectedOptions.value.includes(optKey),
    isCorrect: false,
    isWrong: false,
    isResolved: false
  };
};

// 点击选项
const handleOptionClick = (key) => {
  if (!currentQuestion.value) return;

  // 1. 回忆模式
  if (practiceMode.value === 'recall') {
    const s = getRecallState(currentQuestion.value.id);
    if (!s.revealed) {
      revealRecall();
      return;
    }
    if (s.isSubmitted) return;

    const isMulti = currentQuestion.value.question_type === 'multiple';
    if (!isMulti) {
      s.selected = [key];
      if (singleAutoSubmit.value) {
        submitRecall();
      }
    } else {
      const idx = s.selected.indexOf(key);
      if (idx > -1) s.selected.splice(idx, 1);
      else {
        s.selected.push(key);
        s.selected.sort();
      }
    }
    return;
  }

  // 2. 独立挑战自测模式
  const ds = getDrillState(currentQuestion.value.id);
  if (ds.active) {
    if (ds.isSubmitted) return;
    const isMulti = currentQuestion.value.question_type === 'multiple';
    if (!isMulti) {
      ds.selected = [key];
      if (singleAutoSubmit.value) {
        submitDrill();
      }
    } else {
      const idx = ds.selected.indexOf(key);
      if (idx > -1) ds.selected.splice(idx, 1);
      else {
        ds.selected.push(key);
        ds.selected.sort();
      }
    }
    return;
  }

  // 3. 正式题库刷题模式
  if (hasAnsweredCurrent.value) {
    return;
  }

  const isMulti = currentQuestion.value.question_type === 'multiple';
  if (!isMulti) {
    if (singleAutoSubmit.value) {
      selectedOptions.value = [key];
      doSubmit(key);
    } else {
      selectedOptions.value = [key];
    }
  } else {
    const idx = selectedOptions.value.indexOf(key);
    if (idx > -1) {
      selectedOptions.value.splice(idx, 1);
    } else {
      selectedOptions.value.push(key);
      selectedOptions.value.sort();
    }
  }
};

// 手动提交答案（单选或多选通用）
const submitAnswerManual = () => {
  if (!currentQuestion.value) return;

  if (practiceMode.value === 'recall') {
    const s = getRecallState(currentQuestion.value.id);
    if (!s.revealed) {
      revealRecall();
      return;
    }
    if (s.selected.length === 0) {
      showToast('请先选择回忆答案后再确认作答');
      return;
    }
    submitRecall();
    return;
  }

  const ds = getDrillState(currentQuestion.value.id);
  if (ds.active) {
    if (ds.selected.length === 0) {
      showToast('请先选择答案后再确认作答');
      return;
    }
    submitDrill();
    return;
  }

  if (selectedOptions.value.length === 0) {
    showToast('请先选择答案后再确认作答');
    return;
  }
  const ans = selectedOptions.value.join('');
  doSubmit(ans);
};

// 提交多选题答案（向后兼容）
const submitMultiple = () => {
  submitAnswerManual();
};

// 回忆模式专用交互函数
const revealRecall = () => {
  if (!currentQuestion.value) return;
  const s = getRecallState(currentQuestion.value.id);
  s.revealed = true;
  showToast('✨ 选项已揭晓，请选择你的回忆答案！');
};

const submitRecall = () => {
  if (!currentQuestion.value) return;
  const s = getRecallState(currentQuestion.value.id);
  const userAns = s.selected.join('');
  const cleanUser = Array.from(userAns.toUpperCase()).sort().join('');
  const cleanStd = Array.from(currentQuestion.value.answer.toUpperCase()).sort().join('');
  const isCorrect = cleanUser === cleanStd;

  s.isSubmitted = true;
  s.userAns = userAns;
  s.isCorrect = isCorrect;

  if (isCorrect) {
    confetti({
      particleCount: 25,
      spread: 40,
      origin: { y: 0.8 }
    });
    showToast('🧠 回忆正确！考点记忆非常牢固！');
  } else {
    showToast('❌ 回忆有偏差，请对照考点精析强化复习！');
  }
};

const resetRecallOnCurrent = () => {
  if (!currentQuestion.value) return;
  const s = getRecallState(currentQuestion.value.id);
  s.revealed = false;
  s.selected = [];
  s.isSubmitted = false;
  s.isCorrect = null;
  s.userAns = '';
  showToast('🧠 已重新遮罩，请重新尝试主动回忆！');
};

// 独立挑战自测专用函数
const submitDrill = () => {
  if (!currentQuestion.value) return;
  const ds = getDrillState(currentQuestion.value.id);
  const userAns = ds.selected.join('');
  const cleanUser = Array.from(userAns.toUpperCase()).sort().join('');
  const cleanStd = Array.from(currentQuestion.value.answer.toUpperCase()).sort().join('');
  const isCorrect = cleanUser === cleanStd;

  ds.isSubmitted = true;
  ds.userAns = userAns;
  ds.isCorrect = isCorrect;

  if (isCorrect) {
    confetti({
      particleCount: 25,
      spread: 40,
      origin: { y: 0.8 }
    });
    showToast('🎯 挑战成功！回答正确！');
  } else {
    showToast('❌ 挑战未通过，建议查看解析复习！');
  }
};

const startDrillOnCurrent = () => {
  if (!currentQuestion.value) return;
  const ds = getDrillState(currentQuestion.value.id);
  ds.active = true;
  ds.selected = [];
  ds.isSubmitted = false;
  ds.isCorrect = null;
  ds.userAns = '';
  showToast('🎯 已开启独立自测：请重新作答（原试卷记录安全完好）');
};

const exitDrillOnCurrent = () => {
  if (!currentQuestion.value) return;
  const ds = getDrillState(currentQuestion.value.id);
  ds.active = false;
  resetSelection();
  showToast('已返回正式答卷视图');
};

const syncDrillToOfficial = async () => {
  if (!currentQuestion.value) return;
  const ds = getDrillState(currentQuestion.value.id);
  if (!ds.userAns) return;
  await doSubmit(ds.userAns);
  ds.active = false;
  showToast('✅ 已将本次自测结果同步为正式答卷记录！');
};

// 提交核心逻辑（正式题库刷题）
const doSubmit = async (answer) => {
  if (!currentQuestion.value) return;
  try {
    const targetWbId = currentQuestion.value.workbook_id || props.workbookId;
    const res = await api.submitAnswer(
      targetWbId, 
      currentQuestion.value.id, 
      answer
    );
    currentQuestion.value.user_answer = answer;
    currentQuestion.value.is_correct = res.is_correct;
    
    // 如果回答正确，触发小烟花
    if (res.is_correct && practiceMode.value === 'study') {
      confetti({
        particleCount: 25,
        spread: 40,
        origin: { y: 0.8 }
      });
    }
  } catch (err) {
    alert('提交答案失败: ' + err.message);
  }
};

// 错题专攻：开启当前练习列表中所有错题的全新自测轮次（绝不抹除正式答卷数据）
const handleResetWrongPractice = () => {
  if (!confirm('确定开启错题全新挑战演练吗？\n\n所有错题将进入独立重测模式，供你全新作答！\n（安全保障：原练习册正式答题记录与答卷完整保留）')) return;
  for (const q of questions.value) {
    const ds = getDrillState(q.id);
    ds.active = true;
    ds.selected = [];
    ds.isSubmitted = false;
    ds.isCorrect = null;
    ds.userAns = '';
  }
  currentIndex.value = 0;
  resetSelection();
  showToast('✨ 错题挑战演练已开启，请开始全新作答！');
};

// 收藏切换
const toggleStar = async () => {
  if (!currentQuestion.value) return;
  const nextVal = !currentQuestion.value.is_starred;
  try {
    const targetWbId = currentQuestion.value.workbook_id || props.workbookId;
    await api.toggleStar(targetWbId, currentQuestion.value.id, nextVal);
    currentQuestion.value.is_starred = nextVal;
  } catch (err) {
    console.error('收藏失败', err);
  }
};

// 斩杀/复活熟题切换
const toggleKill = async () => {
  if (!currentQuestion.value) return;
  const nextVal = !currentQuestion.value.is_killed;
  try {
    const targetWbId = currentQuestion.value.workbook_id || props.workbookId;
    await api.toggleKillQuestion(targetWbId, currentQuestion.value.id, nextVal);
    currentQuestion.value.is_killed = nextVal ? 1 : 0;
    if (nextVal) {
      showToast('⚔️ 熟题已斩杀！后续刷题将自动跳过此题');
    } else {
      showToast('🛡️ 题目已复活，已重新加入练习题库');
    }
  } catch (err) {
    console.error('斩题操作失败', err);
    showToast('操作失败，请重试');
  }
};

// 移出错题本 / 重新收录
const toggleMasterFromPractice = async () => {
  if (!currentQuestion.value) return;
  const nextStatus = !currentQuestion.value.is_mastered;
  try {
    await api.toggleMasterWrong(currentQuestion.value.id, nextStatus);
    currentQuestion.value.is_mastered = nextStatus;
    showToast(nextStatus ? '🏆 已成功移出错题集！' : '已重新收录进错题集');
  } catch (err) {
    showToast('操作失败: ' + err.message);
  }
};

// 切换上/下一题
const prevQuestion = () => {
  if (document.activeElement && typeof document.activeElement.blur === 'function') {
    document.activeElement.blur();
  }
  if (currentIndex.value > 0) {
    currentIndex.value--;
  }
};

const nextQuestion = () => {
  if (document.activeElement && typeof document.activeElement.blur === 'function') {
    document.activeElement.blur();
  }
  if (currentIndex.value < questions.value.length - 1) {
    currentIndex.value++;
  }
};

// 快捷键支持
const handleKeyDown = (e) => {
  if (showNoteModal.value || showAnswerSheet.value) return;
  
  // 排除输入框内的按键
  if (['INPUT', 'TEXTAREA'].includes(e.target.tagName)) return;

  // 回忆模式下按空格键揭晓选项
  if (practiceMode.value === 'recall' && !currentRecall.value.revealed) {
    if (e.code === 'Space' || e.key === ' ') {
      e.preventDefault();
      revealRecall();
      return;
    }
  }

  const key = e.key.toUpperCase();
  if (['A', 'B', 'C', 'D'].includes(key)) {
    e.preventDefault();
    handleOptionClick(key);
  } else if (['1', '2', '3', '4'].includes(e.key)) {
    e.preventDefault();
    const map = { '1': 'A', '2': 'B', '3': 'C', '4': 'D' };
    handleOptionClick(map[e.key]);
  } else if (e.key === 'Enter') {
    // 阻止浏览器把 Enter 转发给焦点按钮（防止误触发下一题跳题）
    e.preventDefault();
    e.stopPropagation();
    if (document.activeElement && typeof document.activeElement.blur === 'function') {
      document.activeElement.blur();
    }

    if (!isCurrentQuestionResolved.value) {
      // 1. 本题在当前模式下未提交：执行提交（停留在本题，显示判题结果与考点精析，绝不跳题）
      submitAnswerManual();
    } else {
      // 2. 本题已作答且已显示解析：再次按 Enter 顺畅进入下一题
      if (currentIndex.value < questions.value.length - 1) {
        nextQuestion();
      } else {
        showToast('已经是最后一题了');
      }
    }
  } else if (e.key === 'ArrowLeft' || e.key === 'j') {
    e.preventDefault();
    prevQuestion();
  } else if (e.key === 'ArrowRight' || e.key === 'k') {
    e.preventDefault();
    nextQuestion();
  }
};

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown);
  loadQuestions();
});

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown);
});
</script>

<template>
  <div class="max-w-4xl mx-auto px-3 sm:px-6 py-4 pb-24 lg:pb-12">
    <!-- 艾宾浩斯·每日精选一题横幅 -->
    <div 
      v-if="showDailyBanner && dailyQuestion"
      class="bg-gradient-to-r from-amber-500/10 via-rose-500/10 to-indigo-500/10 border border-amber-200/90 rounded-2xl p-3 sm:p-4 mb-4 flex items-center justify-between gap-3 shadow-2xs backdrop-blur-xs animate-in fade-in duration-300"
    >
      <div class="flex items-center gap-2.5 min-w-0">
        <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-amber-500 to-rose-500 text-white flex items-center justify-center shrink-0 shadow-xs font-bold text-sm">
          🌟
        </div>
        <div class="min-w-0">
          <div class="flex items-center gap-2 flex-wrap">
            <span class="text-xs font-bold text-slate-800">艾宾浩斯 · 每日精选一题</span>
            <span class="px-2 py-0.5 text-[10px] font-bold rounded-md bg-amber-100 text-amber-800 border border-amber-200">
              {{ dailyQuestion.category }} · {{ dailyQuestion.question_type === 'multiple' ? '多选题' : '单选题' }}
            </span>
            <span v-if="dailyQuestion.user_answer" class="px-1.5 py-0.5 text-[10px] font-semibold rounded bg-emerald-100 text-emerald-700">
              ✓ 今日已完成
            </span>
          </div>
          <p class="text-xs text-slate-600 truncate mt-0.5 max-w-xl">
            {{ dailyQuestion.stem }}
          </p>
        </div>
      </div>

      <div class="flex items-center gap-2 shrink-0">
        <button
          @click="jumpToDailyQuestion"
          class="px-3 py-1.5 bg-gradient-to-r from-rose-600 to-rose-700 hover:from-rose-700 hover:to-rose-800 text-white text-xs font-semibold rounded-xl shadow-xs transition cursor-pointer flex items-center gap-1 active:scale-95"
        >
          <span>{{ dailyQuestion.user_answer ? '查看回顾' : '立即挑战' }}</span>
        </button>
        <button
          @click="changeDailyQuestion"
          class="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition cursor-pointer"
          title="换一题推荐"
        >
          <RotateCcw class="w-3.5 h-3.5" />
        </button>
        <button
          @click="showDailyBanner = false"
          class="p-1 text-slate-300 hover:text-slate-500 rounded transition cursor-pointer"
          title="关闭"
        >
          <X class="w-3.5 h-3.5" />
        </button>
      </div>
    </div>

    <!-- Filter and Toolbar Area -->
    <div class="bg-white rounded-2xl p-3 sm:p-4 border border-slate-200 shadow-2xs mb-4">
      <!-- 当前练习册与快捷切换 1000 题 -->
      <div class="flex items-center justify-between pb-2.5 mb-2.5 border-b border-slate-100 flex-wrap gap-2">
        <div class="flex items-center gap-1.5 min-w-0">
          <BookOpen class="w-4 h-4 text-rose-600 shrink-0" />
          <span class="text-xs font-semibold text-slate-500">正在练习：</span>
          <span class="text-xs sm:text-sm font-bold text-slate-900 truncate">
            {{ currentWorkbookName }}
          </span>
          <span class="px-1.5 py-0.2 text-[10px] rounded-md font-bold bg-slate-100 text-slate-600 shrink-0">
            共 {{ questions.length }} 题
          </span>
        </div>

        <div class="flex items-center gap-2">
          <!-- 快捷一键切换至1000题 -->
          <button
            v-if="!is1000Workbook"
            @click="emit('switch-workbook', 39)"
            class="px-2.5 py-1 text-xs font-bold rounded-lg bg-rose-50 hover:bg-rose-100 active:bg-rose-200 text-rose-700 border border-rose-200 transition flex items-center gap-1 cursor-pointer shadow-2xs"
            title="一键切换至2027精雕细刻1000题全科目精选合集"
          >
            <span>🎯 一键刷1000题</span>
          </button>
          <button
            v-else
            @click="emit('switch-tab', 'workbooks')"
            class="px-2.5 py-1 text-xs font-bold rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 transition flex items-center gap-1 cursor-pointer"
            title="前往练习册中心切换分科"
          >
            <span>📚 换其它科目</span>
          </button>
        </div>
      </div>

      <div class="flex flex-wrap items-center justify-between gap-3">
        <!-- 学科分类过滤 -->
        <div class="flex items-center gap-1 overflow-x-auto py-0.5 no-scrollbar">
          <button
            v-for="cat in categories"
            :key="cat"
            @click="selectedCategory = cat"
            class="px-2.5 py-1 text-xs font-medium rounded-lg shrink-0 transition cursor-pointer"
            :class="[
              selectedCategory === cat 
                ? 'bg-rose-600 text-white shadow-2xs font-semibold' 
                : 'text-slate-600 hover:bg-slate-100'
            ]"
          >
            {{ cat }}
          </button>
        </div>

        <!-- 模式与辅助按钮 -->
        <div class="flex items-center gap-2 flex-wrap">
          <!-- 模式切换：即时背题 vs 艾宾浩斯主动回忆 -->
          <div class="bg-slate-100 p-0.5 rounded-lg flex items-center text-xs">
            <button
              @click="setPracticeMode('study')"
              class="px-2 py-1 rounded-md transition cursor-pointer flex items-center gap-1 font-medium"
              :class="practiceMode === 'study' ? 'bg-white text-slate-800 font-bold shadow-2xs' : 'text-slate-600 hover:text-slate-900'"
              title="即时背题模式：选择选项后直接展示考点精解"
            >
              <span>📝 背题</span>
            </button>
            <button
              @click="setPracticeMode('recall')"
              class="px-2.5 py-1 rounded-md transition cursor-pointer flex items-center gap-1 font-medium"
              :class="practiceMode === 'recall' ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-bold shadow-2xs' : 'text-slate-600 hover:text-indigo-600'"
              title="艾宾浩斯主动回忆模式：选项默认遮蔽，先在心中主动回忆考点，再揭晓作答！"
            >
              <Brain class="w-3.5 h-3.5" />
              <span>🧠 回忆模式</span>
            </button>
          </div>

          <!-- 跨题库随机盲盒抽题 -->
          <button
            @click="triggerGlobalRandomQuestion"
            class="px-2.5 py-1.5 rounded-lg border text-xs font-semibold flex items-center gap-1 transition cursor-pointer bg-gradient-to-r from-indigo-50 to-purple-50 hover:from-indigo-100 hover:to-purple-100 border-indigo-200 text-indigo-700 active:scale-95 shadow-2xs select-none"
            title="打破题库限制，在全国真题与10套卷共528题大题库中随机盲盒抽题"
          >
            <Dices class="w-3.5 h-3.5 text-indigo-600" />
            <span class="hidden sm:inline">跨库抽题</span>
          </button>

          <!-- 刷题范围：全部、错题、未做、收藏 -->
          <select 
            v-model="selectedStatus"
            class="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2 py-1 text-slate-700 cursor-pointer font-medium"
            :class="selectedStatus === 'wrong' ? 'border-rose-400 bg-rose-50 text-rose-700 font-bold' : ''"
          >
            <option value="all">全部题目</option>
            <option value="wrong">🎯 错题专攻</option>
            <option value="unattempted">未答题目</option>
            <option value="starred">⭐ 我的收藏</option>
          </select>

          <!-- 题型筛选 -->
          <select 
            v-model="selectedType"
            class="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2 py-1 text-slate-700 cursor-pointer"
          >
            <option v-for="t in types" :key="t.id" :value="t.id">{{ t.label }}</option>
          </select>

          <!-- 乱序开关 -->
          <button
            @click="isRandomOrder = !isRandomOrder"
            class="p-1.5 rounded-lg border text-xs font-medium flex items-center gap-1 transition cursor-pointer"
            :class="[
              isRandomOrder 
                ? 'bg-indigo-50 border-indigo-200 text-indigo-700' 
                : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100'
            ]"
            title="开启/关闭随机乱序"
          >
            <Shuffle class="w-3.5 h-3.5" />
            <span class="hidden sm:inline">乱序</span>
          </button>

          <!-- 隐藏已斩熟题开关 -->
          <button
            @click="hideKilled = !hideKilled"
            class="px-2.5 py-1.5 rounded-lg border text-xs font-medium flex items-center gap-1 transition cursor-pointer select-none"
            :class="[
              hideKilled 
                ? 'bg-rose-50 border-rose-200 text-rose-700 font-semibold' 
                : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100'
            ]"
            :title="hideKilled ? '已开启熟题过滤：斩杀的熟题不会再出现' : '已关闭熟题过滤：所有题目均会出现'"
          >
            <Swords class="w-3.5 h-3.5" :class="{ 'text-rose-600': hideKilled }" />
            <span>{{ hideKilled ? '已隐藏熟题' : '显示熟题' }}</span>
          </button>

          <!-- 单选作答模式切换 (Enter确认提交 vs 即选即判) -->
          <button
            @click="toggleSingleAutoSubmit"
            class="px-2.5 py-1.5 rounded-lg border text-xs font-medium flex items-center gap-1 transition cursor-pointer select-none"
            :class="[
              singleAutoSubmit 
                ? 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100' 
                : 'bg-emerald-50 border-emerald-200 text-emerald-700 font-semibold'
            ]"
            :title="singleAutoSubmit ? '当前模式：单选点击选项立即判题（点击可切换为Enter确认提交）' : '当前模式：单选按Enter确认提交（支持选定、改选，按Enter才提交，点击可切换为即选即判）'"
          >
            <CheckSquare class="w-3.5 h-3.5" :class="{ 'text-emerald-600': !singleAutoSubmit }" />
            <span class="hidden sm:inline">{{ singleAutoSubmit ? '单选即选即答' : '单选Enter提交' }}</span>
            <span class="sm:hidden">{{ singleAutoSubmit ? '即答' : 'Enter' }}</span>
          </button>

          <!-- 答题卡抽屉触发 -->
          <button
            @click="showAnswerSheet = true"
            class="px-2.5 py-1.5 rounded-lg border border-slate-200 bg-slate-50 hover:bg-slate-100 text-slate-700 text-xs font-medium flex items-center gap-1 transition cursor-pointer"
          >
            <LayoutGrid class="w-3.5 h-3.5 text-slate-500" />
            <span>答题卡</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 错题专项重做横幅提示 -->
    <div 
      v-if="selectedStatus === 'wrong' && questions.length > 0"
      class="bg-gradient-to-r from-rose-50 via-rose-50/80 to-amber-50/40 border border-rose-200 rounded-2xl p-3 sm:p-4 mb-4 flex items-center justify-between gap-3 shadow-2xs"
    >
      <div class="flex items-center gap-2.5 text-rose-950 text-xs sm:text-sm">
        <span class="text-lg">🎯</span>
        <div>
          <div class="font-bold flex items-center gap-2">
            <span>错题专项重练模式</span>
            <span class="px-2 py-0.5 rounded-full text-xs bg-rose-100 text-rose-700 font-bold">
              共 {{ questions.length }} 题
            </span>
          </div>
          <p class="text-xs text-rose-700 mt-0.5">历史选项已自动为你清空，请全新作答测试！</p>
        </div>
      </div>
      <button
        @click="handleResetWrongPractice"
        class="px-3 py-1.5 bg-white hover:bg-rose-50 border border-rose-300 text-rose-700 text-xs font-semibold rounded-xl transition cursor-pointer flex items-center gap-1 shrink-0 shadow-2xs active:scale-95"
        title="清空当前所有错题的历史作答状态"
      >
        <RotateCcw class="w-3.5 h-3.5" />
        <span>清空重做错题</span>
      </button>
    </div>

    <!-- Main Question Box -->
    <div v-if="loading" class="bg-white rounded-2xl p-12 text-center border border-slate-200 shadow-2xs">
      <div class="inline-block animate-spin w-8 h-8 border-3 border-rose-500 border-t-transparent rounded-full mb-3"></div>
      <p class="text-sm text-slate-500">正在调取题目，准备刷题...</p>
    </div>

    <div v-else-if="!currentQuestion" class="bg-white rounded-2xl p-12 text-center border border-slate-200 shadow-2xs">
      <BookOpen class="w-12 h-12 text-slate-300 mx-auto mb-3" />
      <h3 class="text-base font-bold text-slate-700">暂无符合条件的题目</h3>
      <p class="text-xs text-slate-400 mt-1">请尝试切换分类或导入新的政治练习册PDF</p>
      <button 
        @click="emit('switch-tab', 'workbooks')"
        class="mt-4 px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold rounded-xl transition cursor-pointer"
      >
        前往上传练习册
      </button>
    </div>

    <div v-else class="space-y-4">
      <!-- Question Card -->
      <div class="bg-white rounded-2xl p-4 sm:p-6 border border-slate-200 shadow-2xs relative">
        <!-- Question Meta Info -->
        <div class="flex items-center justify-between pb-3 mb-4 border-b border-slate-100 gap-2">
          <div class="flex items-center gap-2 flex-wrap">
            <span class="text-xs font-bold text-slate-400">
              第 {{ currentIndex + 1 }} / {{ questions.length }} 题
            </span>
            <!-- 来源练习册标签（综合练习模式下格外清晰） -->
            <span 
              v-if="currentQuestion.workbook_name"
              class="px-2 py-0.5 text-xs font-semibold rounded-md bg-purple-50 text-purple-700 border border-purple-200 shrink-0"
            >
              📖 {{ currentQuestion.workbook_name }}
            </span>
            <span class="px-2 py-0.5 text-xs font-semibold rounded-md bg-blue-50 text-blue-700 border border-blue-100">
              {{ currentQuestion.category }}
            </span>
            <span 
              class="px-2 py-0.5 text-xs font-semibold rounded-md"
              :class="[
                currentQuestion.question_type === 'multiple' 
                  ? 'bg-amber-50 text-amber-700 border border-amber-200' 
                  : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
              ]"
            >
              {{ currentQuestion.question_type === 'multiple' ? '多选题 (2分)' : '单选题 (1分)' }}
            </span>
          </div>

          <!-- Question Actions -->
          <div class="flex items-center gap-1.5">
            <!-- 独立自测重练触发按钮 (保护正式答卷) -->
            <button
              v-if="practiceMode === 'study' && hasAnsweredCurrent && !currentDrill.active"
              @click="startDrillOnCurrent"
              class="px-2 sm:px-2.5 py-1.5 rounded-lg border border-slate-200 text-xs font-medium text-slate-600 hover:text-indigo-600 hover:bg-indigo-50 hover:border-indigo-200 transition cursor-pointer flex items-center gap-1"
              title="在不改变原试卷正式答卷的前提下，独立重新做本题测试自己"
            >
              <RotateCcw class="w-3.5 h-3.5 text-indigo-500" />
              <span class="hidden sm:inline">自测重练</span>
            </button>
            <button
              v-else-if="practiceMode === 'study' && currentDrill.active"
              @click="exitDrillOnCurrent"
              class="px-2 sm:px-2.5 py-1.5 rounded-lg border border-indigo-200 bg-indigo-50 text-xs font-medium text-indigo-700 transition cursor-pointer flex items-center gap-1"
              title="退出自测模式，返回原试卷答卷记录"
            >
              <span>退出自测</span>
            </button>

            <!-- 错题专攻/错题移除按钮 -->
            <button
              v-if="currentQuestion.wrong_count > 0 || selectedStatus === 'wrong' || currentQuestion.is_mastered"
              @click="toggleMasterFromPractice"
              class="px-2 sm:px-2.5 py-1.5 rounded-lg border text-xs font-medium flex items-center gap-1 transition cursor-pointer active:scale-95"
              :class="[
                currentQuestion.is_mastered 
                  ? 'bg-emerald-50 border-emerald-300 text-emerald-700 font-semibold' 
                  : 'border-slate-200 text-slate-600 hover:text-rose-700 hover:bg-rose-50 hover:border-rose-200'
              ]"
              :title="currentQuestion.is_mastered ? '已移出错题集，点击可重新收录' : '已攻克？点击直接移出错题集'"
            >
              <CheckCircle2 class="w-3.5 h-3.5" :class="currentQuestion.is_mastered ? 'text-emerald-600' : 'text-slate-400'" />
              <span class="hidden sm:inline">{{ currentQuestion.is_mastered ? '已移出错题' : '移出错题' }}</span>
            </button>

            <!-- 斩杀熟题按钮 -->
            <button
              @click="toggleKill"
              class="px-2 sm:px-2.5 py-1.5 rounded-lg border text-xs font-medium flex items-center gap-1 transition cursor-pointer"
              :class="[
                currentQuestion.is_killed 
                  ? 'bg-rose-900 border-rose-900 text-rose-100 shadow-2xs font-semibold' 
                  : 'border-slate-200 text-slate-500 hover:text-rose-700 hover:bg-rose-50 hover:border-rose-200'
              ]"
              :title="currentQuestion.is_killed ? '已斩杀！点击可复活' : '已熟练掌握？点击斩杀，后续刷题不再出现'"
            >
              <Swords class="w-3.5 h-3.5" :class="currentQuestion.is_killed ? 'text-rose-200' : 'text-slate-400'" />
              <span class="hidden sm:inline">{{ currentQuestion.is_killed ? '已斩熟题' : '斩熟题' }}</span>
            </button>

            <button
              @click="toggleStar"
              class="p-1.5 rounded-lg border transition cursor-pointer"
              :class="[
                currentQuestion.is_starred 
                  ? 'bg-amber-50 border-amber-200 text-amber-500' 
                  : 'border-slate-200 text-slate-400 hover:text-slate-600 hover:bg-slate-50'
              ]"
              title="收藏本题"
            >
              <Star class="w-4 h-4" :class="{ 'fill-amber-500': currentQuestion.is_starred }" />
            </button>
            <button
              @click="showNoteModal = true"
              class="p-1.5 rounded-lg border transition cursor-pointer"
              :class="[
                currentQuestion.has_note || currentQuestion.note_content
                  ? 'bg-blue-50 border-blue-200 text-blue-600'
                  : 'border-slate-200 text-slate-400 hover:text-slate-600 hover:bg-slate-50'
              ]"
              title="记录考点笔记"
            >
              <FileText class="w-4 h-4" />
            </button>
          </div>
        </div>

        <!-- Question Stem (题干) -->
        <div class="text-base sm:text-lg font-medium text-slate-900 leading-relaxed tracking-wide">
          <span class="font-bold text-rose-600 mr-1.5">{{ currentQuestion.question_num }}.</span>
          <span>{{ currentQuestion.stem }}</span>
        </div>

        <!-- 回忆模式：未展开时的遮罩挑战卡片（每题独立隔离，绝不受历史作答干扰） -->
        <div 
          v-if="practiceMode === 'recall' && !currentRecall.revealed"
          class="mt-6 p-6 sm:p-7 bg-gradient-to-br from-indigo-50/90 via-purple-50/70 to-pink-50/50 border-2 border-indigo-200/90 rounded-2xl text-center shadow-xs animate-in fade-in zoom-in-95 duration-200"
        >
          <div class="w-12 h-12 bg-white text-indigo-600 rounded-2xl flex items-center justify-center mx-auto mb-3 shadow-2xs border border-indigo-100">
            <Brain class="w-6 h-6 animate-pulse text-indigo-600" />
          </div>
          <h4 class="text-base font-bold text-slate-800 flex items-center justify-center gap-1.5">
            <span>🧠 艾宾浩斯 · 主动回忆挑战</span>
          </h4>
          <p class="text-xs sm:text-sm text-slate-600 mt-2 max-w-lg mx-auto leading-relaxed">
            <strong class="text-indigo-900">请先勿看选项！</strong> 尝试在脑海中回忆该考点的核心概念、关键词或推导结论。心理学证实：先闭眼回忆再揭晓选项，记忆留存率提升 3 倍！
          </p>

          <div class="flex items-center justify-center gap-3 mt-5 flex-wrap">
            <button
              @click="revealRecall"
              class="px-5 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-bold text-xs sm:text-sm rounded-xl shadow-xs transition cursor-pointer flex items-center gap-2 active:scale-95"
            >
              <Sparkles class="w-4 h-4 text-amber-300" />
              <span>想好了，揭晓选项作答 (按 Space 空格键)</span>
            </button>
            <button
              @click="revealRecall"
              class="px-4 py-2.5 bg-white hover:bg-slate-100 border border-slate-200 text-slate-600 text-xs sm:text-sm font-medium rounded-xl transition cursor-pointer active:scale-95"
            >
              <span>毫无头绪，直接看选项</span>
            </button>
          </div>
        </div>

        <!-- Options List (多模式完全解耦：独立高亮与独立判定) -->
        <div v-else class="mt-6 space-y-3 animate-in fade-in duration-200">
          <div
            v-for="opt in currentQuestion.options"
            :key="opt.key"
            @click="handleOptionClick(opt.key)"
            class="group p-3.5 sm:p-4 rounded-xl border-2 transition-all flex items-start gap-3 cursor-pointer select-none"
            :class="[
              getOptionStatus(opt.key).isResolved
                ? (
                    getOptionStatus(opt.key).isCorrect
                      ? 'border-emerald-500 bg-emerald-50/70 text-emerald-950 font-medium'
                      : (getOptionStatus(opt.key).isWrong
                          ? 'border-rose-500 bg-rose-50/70 text-rose-950'
                          : 'border-slate-200/80 bg-slate-50/50 text-slate-400 opacity-60')
                  )
                : (
                    getOptionStatus(opt.key).isSelected
                      ? 'border-rose-500 bg-rose-50/40 text-slate-900 shadow-xs'
                      : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50 text-slate-800'
                  )
            ]"
          >
            <!-- Option Key Badge (A, B, C, D) -->
            <div
              class="w-7 h-7 rounded-lg flex items-center justify-center font-bold text-sm shrink-0 transition"
              :class="[
                getOptionStatus(opt.key).isResolved
                  ? (
                      getOptionStatus(opt.key).isCorrect
                        ? 'bg-emerald-600 text-white'
                        : (getOptionStatus(opt.key).isWrong
                            ? 'bg-rose-600 text-white'
                            : 'bg-slate-200 text-slate-600')
                    )
                  : (
                      getOptionStatus(opt.key).isSelected
                        ? 'bg-rose-600 text-white'
                        : 'bg-slate-100 group-hover:bg-slate-200 text-slate-700'
                    )
              ]"
            >
              <span>{{ opt.key }}</span>
            </div>

            <!-- Option Text -->
            <div class="text-sm sm:text-base leading-relaxed pt-0.5 flex-1">
              {{ opt.value }}
            </div>

            <!-- Feedback Icon -->
            <div v-if="getOptionStatus(opt.key).isResolved" class="shrink-0 pt-0.5">
              <Check v-if="getOptionStatus(opt.key).isCorrect" class="w-5 h-5 text-emerald-600 font-bold" />
              <X v-else-if="getOptionStatus(opt.key).isWrong" class="w-5 h-5 text-rose-600 font-bold" />
            </div>
          </div>
        </div>

        <!-- Submit Button (提交作答按钮：多选题 或 单选确认模式) -->
        <div 
          v-if="!isCurrentQuestionResolved && (currentQuestion.question_type === 'multiple' || !singleAutoSubmit)"
          class="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between gap-3"
        >
          <div class="text-xs text-slate-500">
            已选：<span class="font-bold text-rose-600 font-mono text-sm">{{ currentPendingSelection.join('') || '未选' }}</span>
            <span class="hidden sm:inline text-slate-400 ml-2">（支持按 Enter 回车键快捷提交作答）</span>
          </div>
          <button
            @click="(e) => { e.currentTarget.blur(); submitAnswerManual(); }"
            :disabled="currentPendingSelection.length === 0"
            class="px-5 py-2.5 bg-rose-600 hover:bg-rose-700 active:bg-rose-800 disabled:opacity-40 disabled:pointer-events-none text-white font-semibold text-sm rounded-xl shadow-xs flex items-center gap-1.5 transition cursor-pointer"
          >
            <Send class="w-4 h-4" />
            <span>确认作答</span>
          </button>
        </div>
      </div>

      <!-- Navigation Bar (Previous / Next Buttons - 位于解析上方，答完可直接无须滚动切题) -->
      <div class="flex items-center justify-between gap-3 pt-1">
        <button
          @click="(e) => { e.currentTarget.blur(); prevQuestion(); }"
          :disabled="currentIndex === 0"
          class="flex-1 sm:flex-none px-5 py-2.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-40 disabled:pointer-events-none text-slate-700 text-sm font-medium flex items-center justify-center gap-1.5 shadow-2xs transition cursor-pointer"
        >
          <ChevronLeft class="w-4 h-4" />
          <span>上一题</span>
        </button>

        <!-- 中间进度指示与快捷键 -->
        <div class="hidden sm:flex items-center gap-2 text-xs text-slate-500">
          <span>键盘快捷键：A/B/C/D 选答案 · Enter 提交/下一题 · Space 揭晓回忆 · ←/→ 翻题</span>
        </div>

        <button
          @click="(e) => { e.currentTarget.blur(); nextQuestion(); }"
          :disabled="currentIndex >= questions.length - 1"
          class="flex-1 sm:flex-none px-5 py-2.5 rounded-xl text-white text-sm font-semibold flex items-center justify-center gap-1.5 shadow-2xs transition cursor-pointer disabled:opacity-40 disabled:pointer-events-none"
          :class="[
            isCurrentQuestionResolved 
              ? 'bg-rose-600 hover:bg-rose-700 active:bg-rose-800 shadow-rose-200 ring-2 ring-rose-200' 
              : 'bg-slate-900 hover:bg-slate-800 active:bg-slate-950'
          ]"
        >
          <span>下一题</span>
          <ChevronRight class="w-4 h-4" />
        </button>
      </div>

      <!-- Result & Explanation Box (即时解析区域) -->
      <div 
        v-if="isCurrentQuestionResolved"
        class="bg-white rounded-2xl p-4 sm:p-6 border border-slate-200 shadow-2xs animate-in slide-in-from-bottom-2 duration-300"
      >
        <!-- Result Banner (根据模式独立展示判题与历史答卷比对) -->
        <div 
          class="p-4 rounded-xl flex items-center justify-between gap-3 mb-4"
          :class="[
            currentEvalResult.isCorrect 
              ? 'bg-emerald-50 border border-emerald-200 text-emerald-800' 
              : 'bg-rose-50 border border-rose-200 text-rose-800'
          ]"
        >
          <div class="flex items-center gap-2.5">
            <div 
              class="w-8 h-8 rounded-full flex items-center justify-center font-bold text-white shrink-0"
              :class="currentEvalResult.isCorrect ? 'bg-emerald-600' : 'bg-rose-600'"
            >
              <Check v-if="currentEvalResult.isCorrect" class="w-5 h-5" />
              <X v-else class="w-5 h-5" />
            </div>
            <div>
              <div class="font-bold text-sm sm:text-base">
                <span v-if="practiceMode === 'recall'">
                  {{ currentEvalResult.isCorrect ? '🧠 回忆挑战成功！知识点记忆非常牢固 🎉' : '💡 回忆稍有偏差，已为你高亮核心考点' }}
                </span>
                <span v-else-if="currentDrill.active">
                  {{ currentEvalResult.isCorrect ? '🎯 独立自测成功！回答正确 🎉' : '🎯 本次自测未通过，已为你生成对比解析' }}
                </span>
                <span v-else>
                  {{ currentQuestion.is_correct ? '回答正确！' : '回答错误！已自动收录到错题本' }}
                </span>
              </div>
              <div class="text-xs mt-0.5 opacity-90 flex items-center gap-3 flex-wrap">
                <span>{{ practiceMode === 'recall' ? '本次回忆：' : (currentDrill.active ? '本次自测：' : '你的作答：') }}<strong class="font-mono text-sm underline">{{ currentEvalResult.userAns || '未选' }}</strong></span>
                <span>正确答案：<strong class="font-mono text-sm underline">{{ currentQuestion.answer }}</strong></span>
                <span v-if="(practiceMode === 'recall' || currentDrill.active) && currentQuestion.user_answer" class="text-slate-600 bg-white/80 px-2 py-0.5 rounded border border-slate-200/80 font-medium">
                  📖 正式答卷曾选：<strong class="font-mono">{{ currentQuestion.user_answer }}</strong> ({{ currentQuestion.is_correct ? '当时答对' : '当时错选' }})
                </span>
              </div>
            </div>
          </div>

          <div class="flex items-center gap-1.5 shrink-0 flex-wrap justify-end">
            <!-- 回忆模式专用按钮 -->
            <button
              v-if="practiceMode === 'recall'"
              @click="resetRecallOnCurrent"
              class="px-2.5 py-1 text-xs font-medium rounded-lg bg-white/90 hover:bg-white text-indigo-700 border border-indigo-200 transition cursor-pointer flex items-center gap-1 shadow-2xs"
              title="重新隐藏选项，再次检验主动回忆"
            >
              <RotateCcw class="w-3.5 h-3.5" />
              <span>重新回忆</span>
            </button>

            <!-- 自测挑战模式专用按钮 -->
            <template v-else-if="currentDrill.active">
              <button
                @click="startDrillOnCurrent"
                class="px-2 py-1 text-xs font-medium rounded-lg bg-white/90 hover:bg-white text-slate-700 border border-slate-200 transition cursor-pointer flex items-center gap-1"
                title="清空自测选项，重新再测一次"
              >
                <RotateCcw class="w-3.5 h-3.5" />
                <span>再测一次</span>
              </button>
              <button
                @click="syncDrillToOfficial"
                class="px-2.5 py-1 text-xs font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white shadow-2xs transition cursor-pointer flex items-center gap-1"
                title="将本次自测的答案覆盖同步为正式答题卡记录"
              >
                <CheckCircle2 class="w-3.5 h-3.5" />
                <span>更新为正式答卷</span>
              </button>
              <button
                @click="exitDrillOnCurrent"
                class="px-2 py-1 text-xs font-medium rounded-lg bg-white/90 hover:bg-white text-slate-600 border border-slate-200 transition cursor-pointer"
                title="退出自测模式，返回原试卷记录"
              >
                <span>退出自测</span>
              </button>
            </template>

            <!-- 正式题库刷题模式专用按钮 -->
            <template v-else>
              <!-- 斩熟题快捷按钮 -->
              <button
                @click="toggleKill"
                class="px-2.5 py-1 text-xs font-medium rounded-lg transition cursor-pointer flex items-center gap-1 border shadow-2xs"
                :class="[
                  currentQuestion.is_killed
                    ? 'bg-rose-900 text-white border-rose-900 font-semibold'
                    : 'bg-white/90 hover:bg-white text-slate-700 border-slate-200 hover:text-rose-700 hover:border-rose-200'
                ]"
                :title="currentQuestion.is_killed ? '已斩杀，点击可复活' : '完全熟练？一键斩杀不再重复刷此题'"
              >
                <Swords class="w-3.5 h-3.5" :class="currentQuestion.is_killed ? 'text-rose-200' : 'text-rose-600'" />
                <span>{{ currentQuestion.is_killed ? '已斩熟题' : '斩掉此题' }}</span>
              </button>

              <!-- 独立自测本题 (不破坏历史记录) -->
              <button
                @click="startDrillOnCurrent"
                class="px-2.5 py-1 text-xs font-medium rounded-lg bg-white/80 hover:bg-white text-slate-700 border border-slate-200 transition cursor-pointer flex items-center gap-1"
                title="不破坏当前正式答卷记录的前提下，重新自测本题"
              >
                <RotateCcw class="w-3.5 h-3.5" />
                <span>重新自测本题</span>
              </button>
            </template>

            <!-- 答案栏内直达下一题按钮 -->
            <button
              @click="(e) => { e.currentTarget.blur(); nextQuestion(); }"
              :disabled="currentIndex >= questions.length - 1"
              class="px-3 py-1 text-xs font-semibold rounded-lg bg-slate-900 hover:bg-slate-800 text-white shadow-2xs transition cursor-pointer flex items-center gap-1 disabled:opacity-40"
              title="直接进入下一题"
            >
              <span>下一题</span>
              <ChevronRight class="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        <!-- 详细考点解析 -->
        <div class="space-y-2">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-slate-700 flex items-center gap-1">
              <Sparkles class="w-3.5 h-3.5 text-amber-500" /> 考点精析
            </span>
            <button
              @click="showNoteModal = true"
              class="text-xs text-rose-600 hover:text-rose-700 font-medium flex items-center gap-1 cursor-pointer"
            >
              <FileText class="w-3.5 h-3.5" />
              <span>{{ currentQuestion.has_note ? '编辑笔记' : '添加笔记' }}</span>
            </button>
          </div>
          <div class="p-3.5 bg-slate-50 border border-slate-100 rounded-xl text-xs sm:text-sm text-slate-700 leading-relaxed whitespace-pre-line font-normal">
            {{ currentQuestion.explanation || '暂无针对本题的详细解析' }}
          </div>
        </div>

        <!-- 笔记预览（若有） -->
        <div v-if="currentQuestion.note_content" class="mt-3 p-3 bg-amber-50/70 border border-amber-200/80 rounded-xl text-xs text-amber-900">
          <div class="font-bold flex items-center gap-1 mb-1 text-amber-800">
            <FileText class="w-3.5 h-3.5" /> 我的备考笔记：
          </div>
          <p class="whitespace-pre-line">{{ currentQuestion.note_content }}</p>
        </div>

        <!-- 底部快捷跳转（阅读完长解析后直接前往下一题，避免向上滚动） -->
        <div class="pt-3 mt-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
          <button
            @click="(e) => { e.currentTarget.blur(); prevQuestion(); }"
            :disabled="currentIndex === 0"
            class="px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-40 text-slate-600 flex items-center gap-1 cursor-pointer"
          >
            <ChevronLeft class="w-3.5 h-3.5" />
            <span>上一题</span>
          </button>
          <button
            @click="(e) => { e.currentTarget.blur(); nextQuestion(); }"
            :disabled="currentIndex >= questions.length - 1"
            class="px-4 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 active:bg-slate-950 disabled:opacity-40 text-white font-medium flex items-center gap-1 shadow-2xs cursor-pointer"
          >
            <span>下一题</span>
            <ChevronRight class="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>

    <!-- Modals -->
    <AnswerSheetModal 
      :show="showAnswerSheet"
      :questions="questions"
      :current-index="currentIndex"
      @close="showAnswerSheet = false"
      @jump="currentIndex = $event"
    />

    <NoteModal 
      :show="showNoteModal"
      :question="currentQuestion"
      @close="showNoteModal = false"
      @saved="currentQuestion.note_content = $event.content; currentQuestion.has_note = true;"
    />

    <!-- Floating Toast Notification -->
    <transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="transform -translate-y-2 opacity-0"
      enter-to-class="transform translate-y-0 opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="transform translate-y-0 opacity-100"
      leave-to-class="transform -translate-y-2 opacity-0"
    >
      <div 
        v-if="toastMsg"
        class="fixed top-18 left-1/2 -translate-x-1/2 z-50 bg-slate-900/95 backdrop-blur-md text-white text-xs sm:text-sm font-semibold px-4 py-2.5 rounded-xl shadow-xl border border-slate-700/80 flex items-center gap-2 pointer-events-none"
      >
        <span>{{ toastMsg }}</span>
      </div>
    </transition>
  </div>
</template>
