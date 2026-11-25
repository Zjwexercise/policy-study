import { ref, computed } from 'vue';

// 当前选择的语言：'zh' (中文) 或 'th' (ไทย / ภาษาไทย)
const savedLang = localStorage.getItem('policy_lang') || 'zh';
export const currentLang = ref(savedLang);

export const setLanguage = (lang) => {
  if (['zh', 'th'].includes(lang)) {
    currentLang.value = lang;
    try {
      localStorage.setItem('policy_lang', lang);
      document.documentElement.lang = lang;
    } catch (e) {}
  }
};

export const isThai = computed(() => currentLang.value === 'th');

export const translations = {
  zh: {
    // 顶部导航与通用
    brand_name: '考研政治掌上宝',
    brand_sub: '2027 考研冲刺',
    nav_welcome: '欢迎首页',
    nav_practice: '答题练习',
    nav_practice_short: '答题',
    nav_wrong: '错题本',
    nav_wrong_short: '错题本',
    nav_killed: '熟题斩杀',
    nav_notes: '考点笔记',
    nav_workbooks: '试卷题库',
    nav_workbooks_short: '题库',
    nav_stats: '数据统计',
    nav_stats_short: '统计',
    nav_admin: '管理后台',
    nav_login: '登录',
    nav_syncing: '同步中',
    nav_synced: '已同步',
    back_to_stats: '返回统计',
    nav_mobile_qr: '手机做题',
    nav_cloud_sync: '云端同步',
    nav_theme_dark: '夜间模式',
    nav_theme_light: '浅色模式',
    nav_lang: '语言 / ภาษา',
    lang_zh: '🇨🇳 中文 (简体)',
    lang_th: '🇹🇭 ไทย (ภาษาไทย)',

    // 答题练习顶栏
    practicing: '正在练习：',
    total_q_count: '共 {n} 题',
    reset_wb_btn: '重新刷本卷',
    reset_wb_confirm: '确定要重置【{name}】的全部做题记录吗？\n\n这套试卷的所有已选答案、对错状态与错题将被清空，并回到第 1 题，方便你开启全新一轮二刷！\n（注：考点笔记和收藏夹仍会安全保留）',
    reset_wb_toast: '🎉【{name}】已成功重置！已回到第 1 题，开启全新二刷！',
    switch_1000_btn: '🎯 一键刷1000题',
    switch_subject_btn: '📚 换其它科目',
    random_box_btn: '🎲 盲盒抽题',
    auto_submit_on: '单选即判',
    auto_submit_off: '单选按确认',
    hide_killed_label: '隐藏已斩熟题',
    show_killed_label: '显示已斩熟题',
    answer_sheet_btn: '答题卡',
    redo_wrong_banner: '错题专项重练模式',
    redo_wrong_desc: '历史选项已自动为你清空，请全新作答测试！',
    clear_redo_wrong_btn: '清空重做错题',

    // 题目卡片
    question_single: '单选题 (1分)',
    question_multiple: '多选题 (2分)',
    submit_practice_btn: '确认作答',
    submit_hint: '已选：{ans}（支持按 Enter 回车键快捷提交作答）',
    submit_hint_empty: '已选：未选（支持按 Enter 回车键快捷提交作答）',
    drill_btn: '自测重练',
    exit_drill_btn: '退出自测',
    remove_wrong_btn: '移出错题',
    removed_wrong_btn: '已移出',
    star_btn: '收藏本题',
    note_btn: '记录考点笔记',
    translate_btn: '🌐 泰语翻译',
    translating_btn: '正在翻译...',
    hide_trans_btn: '隐藏翻译',
    thai_stem_title: '🇹🇭 คำแปลภาษาไทย (โจทย์ข้อสอบ):',
    thai_exp_title: '🇹🇭 คำแปลคำอธิบายเฉลย (ภาษาไทย):',
    auto_trans_label: '自动翻译新题',
    prev_q: '上一题',
    next_q: '下一题',
    shortcut_hint: '键盘快捷键：A/B/C/D 选答案 · Enter 提交/下一题 · ←/→ 翻题',

    // 作答判定
    ans_correct: '回答正确！🎉 考点掌握非常扎实',
    ans_wrong: '回答有偏差，已为你标注正确答案与解析',
    your_answer: '你的作答：',
    correct_answer: '正确答案：',
    formal_record: '📖 正式答卷曾选：',
    exp_heading: '【考点深度深度精析】',
    copy_exp_btn: '复制解析',
    copy_q_btn: '复制试题',

    // 试卷库
    wb_banner_title: '考研政治试卷与练习册库',
    wb_banner_sub: '支持每本习题集单独刷题、单独二刷重置与全科目统计',
    wb_re_practice: '重新刷',
    wb_continue: '继续练习',
    wb_start: '开始刷题',
    wb_accuracy: '正确率',
    wb_answered: '已刷',

    // 错题本
    wb_title: '错题本',
    wb_reset_redo: '清空自测作答',
    wb_mode_quiz: '自测重练模式',
    wb_mode_review: '解析背诵模式',
    wb_sort_ebbinghaus: '艾宾浩斯记忆遗忘曲线',
    wb_sort_wrong: '高频错误优先',
    wb_sort_recent: '最新做错优先',

    // 答题卡弹窗
    sheet_title: '答题卡',
    sheet_legend_correct: '正确',
    sheet_legend_wrong: '错误',
    sheet_legend_unanswered: '未答',
    sheet_legend_star: '收藏',
    sheet_legend_killed: '已斩',
    sheet_legend_note: '有笔记',
    sheet_redo_btn: '二刷重置本卷',

    // 科目分类
    cat_all: '全部',
    cat_my: '马原',
    cat_mzt: '毛中特',
    cat_xsx: '习思想',
    cat_sg: '史纲',
    cat_sx: '思修',
    cat_sz: '时政'
  },
  th: {
    // 顶部导航与通用
    brand_name: 'คลังข้อสอบการเมือง ป.โท',
    brand_sub: 'เตรียมสอบ 2027',
    nav_welcome: 'หน้าแรก',
    nav_practice: 'ฝึกทำข้อสอบ',
    nav_practice_short: 'ฝึกทำ',
    nav_wrong: 'สมุดข้อผิด',
    nav_wrong_short: 'ข้อผิด',
    nav_killed: 'ข้อที่จำได้แล้ว',
    nav_notes: 'สมุดโน้ต',
    nav_workbooks: 'คลังข้อสอบ',
    nav_workbooks_short: 'คลังข้อสอบ',
    nav_stats: 'สถิติการเรียน',
    nav_stats_short: 'สถิติ',
    nav_admin: 'ระบบจัดการ',
    nav_login: 'เข้าสู่ระบบ',
    nav_syncing: 'ซิงค์...',
    nav_synced: 'ซิงค์แล้ว',
    back_to_stats: 'กลับไปสถิติ',
    nav_mobile_qr: 'ทำบนมือถือ',
    nav_cloud_sync: 'ซิงค์ข้อมูล',
    nav_theme_dark: 'โหมดมืด',
    nav_theme_light: 'โหมดสว่าง',
    nav_lang: 'ภาษา / Language',
    lang_zh: '🇨🇳 中文 (简体)',
    lang_th: '🇹🇭 ไทย (ภาษาไทย)',

    // 答题练习顶栏
    practicing: 'กำลังทำชุด:',
    total_q_count: 'ทั้งหมด {n} ข้อ',
    reset_wb_btn: 'ทำชุดนี้ใหม่',
    reset_wb_confirm: 'คุณแน่ใจหรือไม่ว่าต้องการรีเซ็ต【{name}】?\n\nคำตอบและข้อผิดของชุดนี้จะถูกล้างทั้งหมด และจะกลับไปเริ่มที่ข้อ 1 เพื่อให้คุณเริ่มทำรอบใหม่ได้อย่างสมบูรณ์!\n(หมายเหตุ: โน้ตและข้อที่บันทึกไว้จะยังคงอยู่อย่างปลอดภัย)',
    reset_wb_toast: '🎉 รีเซ็ต【{name}】สำเร็จแล้ว! กลับไปที่ข้อ 1 พร้อมเริ่มทำรอบใหม่!',
    switch_1000_btn: '🎯 ทำชุด 1000 ข้อ',
    switch_subject_btn: '📚 เปลี่ยนวิชา',
    random_box_btn: '🎲 สุ่มข้อสอบ',
    auto_single: 'ตรวจทันที',
    auto_single_off: 'กดยืนยันคำตอบ',
    hide_killed_label: 'ซ่อนข้อที่จำได้แล้ว',
    show_killed_label: 'แสดงข้อที่จำได้แล้ว',
    answer_sheet_btn: 'กระดาษคำตอบ',
    redo_wrong_banner: 'โหมดเน้นทำซ้ำข้อที่ผิด',
    redo_wrong_desc: 'คำตอบเดิมถูกล้างออกแล้ว กรุณาทดสอบทำใหม่อีกครั้ง!',
    clear_redo_wrong_btn: 'ล้างคำตอบข้อผิด',

    // 题目卡片
    question_single: 'ปรนัย 1 คำตอบ (1 คะแนน)',
    question_multiple: 'ปรนัยหลายคำตอบ (2 คะแนน)',
    submit_practice_btn: 'ยืนยันส่งคำตอบ',
    submit_hint: 'เลือกแล้ว: {ans} (กดปุ่ม Enter เพื่อส่งคำตอบได้อย่างรวดเร็ว)',
    submit_hint_empty: 'เลือกแล้ว: ยังไม่ได้เลือก (กด Enter เพื่อส่งคำตอบ)',
    drill_btn: 'ทดสอบตัวเอง',
    exit_drill_btn: 'ออกจากการทดสอบ',
    remove_wrong_btn: 'ลบออกจากข้อผิด',
    removed_wrong_btn: 'ลบออกแล้ว',
    star_btn: 'บันทึกข้อนี้',
    note_btn: 'จดบันทึกเนื้อหา',
    translate_btn: '🌐 แปลภาษาไทย',
    translating_btn: 'กำลังแปลภาษา...',
    hide_trans_btn: 'ซ่อนคำแปล',
    thai_stem_title: '🇹🇭 คำแปลภาษาไทย (โจทย์ข้อสอบ):',
    thai_exp_title: '🇹🇭 คำแปลคำอธิบายเฉลย (ภาษาไทย):',
    auto_trans_label: 'แปลข้อสอบอัตโนมัติ',
    prev_q: 'ข้อก่อนหน้า',
    next_q: 'ข้อถัดไป',
    shortcut_hint: 'คีย์ลัด: A/B/C/D เลือกคำตอบ · Enter ส่งคำตอบ/ข้อถัดไป · ←/→ เปลี่ยนข้อ',

    // 作答判定
    ans_correct: 'ตอบถูกต้อง! 🎉 มีความเข้าใจจุดสำคัญของเนื้อหาเป็นอย่างดี',
    ans_wrong: 'คำตอบยังไม่ถูกต้อง ระบบได้แสดงคำตอบที่ถูกต้องพร้อมเฉลยแล้ว',
    your_answer: 'คำตอบของคุณ:',
    correct_answer: 'คำตอบที่ถูกต้อง:',
    formal_record: '📖 คำตอบที่เคยส่ง:',
    exp_heading: '【วิเคราะห์เฉลยข้อสอบอย่างละเอียด】',
    copy_exp_btn: 'คัดลอกเฉลย',
    copy_q_btn: 'คัดลอกโจทย์',

    // 试卷库
    wb_banner_title: 'คลังข้อสอบและชุดฝึกหัดการเมือง',
    wb_banner_sub: 'รองรับการฝึกทำทีละชุด รีเซ็ตทำใหม่รอบสอง และรวมสถิติทุกวิชา',
    wb_re_practice: 'ทำใหม่',
    wb_continue: 'ทำต่อ',
    wb_start: 'เริ่มทำ',
    wb_accuracy: 'ความถูกต้อง',
    wb_answered: 'ทำแล้ว',

    // 错题本
    wb_title: 'สมุดข้อที่ทำผิด',
    wb_reset_redo: 'ล้างผลทดสอบทั้งหมด',
    wb_mode_quiz: 'โหมดทดสอบทำซ้ำ',
    wb_mode_review: 'โหมดท่องจำพร้อมเฉลย',
    wb_sort_ebbinghaus: 'ตามเส้นโค้งการลืม Ebbinghaus',
    wb_sort_wrong: 'ข้อที่ผิดบ่อยที่สุด',
    wb_sort_recent: 'ข้อที่ผิดล่าสุด',

    // 答题卡弹窗
    sheet_title: 'กระดาษคำตอบ',
    sheet_legend_correct: 'ถูกต้อง',
    sheet_legend_wrong: 'ผิด',
    sheet_legend_unanswered: 'ยังไม่ทำ',
    sheet_legend_star: 'บันทึกไว้',
    sheet_legend_killed: 'จำได้แล้ว',
    sheet_legend_note: 'มีโน้ต',
    sheet_redo_btn: 'รีเซ็ตทำชุดนี้ใหม่',

    // 科目分类
    cat_all: 'ทั้งหมด',
    cat_my: 'มาร์กซิสต์',
    cat_mzt: 'ทฤษฎีเหมาฯ',
    cat_xsx: 'แนวคิดสี จิ้นผิง',
    cat_sg: 'ประวัติศาสตร์พรรค',
    cat_sx: 'คุณธรรมและกฎหมาย',
    cat_sz: 'การเมืองปัจจุบัน'
  }
};

export const t = (key, params = {}) => {
  const langDict = translations[currentLang.value] || translations['zh'];
  let text = langDict[key] || translations['zh'][key] || key;
  if (params && typeof params === 'object') {
    Object.keys(params).forEach(k => {
      text = text.replace(new RegExp(`\\{${k}\\}`, 'g'), params[k]);
    });
  }
  return text;
};
