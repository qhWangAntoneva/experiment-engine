/**
 * i18n translations: Chinese (zh) and English (en).
 *
 * Design principles:
 * - Methodological QCA terms (fsQCA, csQCA, consistency, coverage, etc.)
 *   display Chinese explanation with English term in parentheses.
 * - Technical terms stay accurate; no over-localization.
 * - Organized by page/section for maintainability.
 */

export type Language = 'zh' | 'en';

export interface TranslationDict {
  // ── Common / Global ──
  common: {
    reset: string;
    loading: string;
    exporting: string;
    error: string;
    yes: string;
    no: string;
    none: string;
    or: string;
    vs: string;
    differs: string;
    different: string;
    same: string;
    passed: string;
    unstable: string;
    notLoaded: string;
    active: string;
    idle: string;
    enabled: string;
    disabled: string;
  };

  // ── Sidebar ──
  sidebar: {
    appTitle: string;
    appSubtitle: string;
    version: string;
    engineLabel: string;
    dashboard: string;
    dataInput: string;
    results: string;
    settings: string;
  };

  // ── Dashboard ──
  dashboard: {
    title: string;
    subtitle: string;
    description: string;
    pyodideStatus: string;
    pipelineStage: string;
    casesAnalyzed: string;
    conditionsDefined: string;
    statusReady: string;
    statusLoading: string;
    statusNotLoaded: string;
    statusError: string;
    quickStart: string;
    step1Title: string;
    step1Desc: string;
    step1BtnReady: string;
    step1BtnLoading: string;
    step1BtnLoad: string;
    step1BtnError: string;
    step2Title: string;
    step2Desc: string;
    step2Btn: string;
    step3Title: string;
    step3Desc: string;
    step4Title: string;
    step4Desc: string;
    recentRuns: string;
    runId: string;
    runName: string;
    runStatus: string;
    runCases: string;
    runConditions: string;
    runDuration: string;
    runDate: string;
    emptyTitle: string;
    emptySubtitle: string;
    emptyAction: string;
    privacyTitle: string;
    privacyDesc: string;
    clearAllData: string;
    clearDataConfirm: string;
  };

  // ── Data Input ──
  dataInput: {
    title: string;
    subtitle: string;
    engineNotReady: string;
    // BERT
    bertModel: string;
    bertModelDesc: string;
    bertStatus: string;
    bertNotLoaded: string;
    bertLoadingProgress: (pct: number) => string;
    bertReady: string;
    bertError: string;
    bertCalibration: string;
    bertDescription: string;
    bertUnloaded: string;
    bertLoading: string;
    bertLoadingBtn: string;
    bertLoadedBtn: string;
    bertLoadBtn: string;
    bertCalibratingBtn: string;
    bertCalibrateBtn: string;
    bertNotReady: string;
    bertModelReady: string;
    bertLoadFailed: string;
    bertCalibrationComplete: string;
    bertCalibrationFailed: string;
    bertErrorUnknown: string;
    outcomeLabel: string;
    // Text corpus
    textCorpus: string;
    pasteText: string;
    uploadFile: string;
    format: string;
    formatPlainText: string;
    parseText: string;
    parseCsv: string;
    pastePlaceholderCsv: string;
    pastePlaceholderJson: string;
    pastePlaceholderTxt: string;
    dropHere: string;
    orClickBrowse: string;
    casesLoaded: string;
    id: string;
    textTruncated: string;
    andMoreCases: (n: number) => string;
    // Prototype
    prototypeTitle: string;
    prototypeFormatHelp: string;
    prototypePlaceholder: string;
    parseProtoCsv: string;
    dropProtoFile: string;
    parseProto: string;
    outcome0: string;
    outcome1: string;
    // Condition set YAML
    conditionSetYaml: string;
    domainPreset: string;
    // Prototype editor
    prototypeEditor: string;
    addCondition: string;
    prototypeHelp: string;
    conditionN: (n: number) => string;
    removeCondition: string;
    name: string;
    displayName: string;
    namePlaceholder: string;
    displayNamePlaceholder: string;
    prototypeTextsLabel: string;
    prototypeTextsPlaceholder: string;
    generatedConditionSet: string;
    conditionCount: (n: number) => string;
    prototypeCount: (n: number) => string;
    totalText: string;
    outcomePassthrough: string;
    // Domain labels
    domainLabels: Record<string, string>;
    // Actions
    calibrateBtn: string;
    calibrating: string;
    runPipelineBtn: string;
    running: string;
    resetBtn: string;
    // Messages
    noTextData: string;
    calibrationComplete: string;
    calibrationCompleteProto: (n: number) => string;
    calibrationFailed: string;
    analysisComplete: string;
    pipelineFailed: string;
    loadedCases: (n: number, name: string) => string;
    parsedCases: (n: number) => string;
    parseError: string;
    fileTooLarge: (size: string) => string;
    errorReadingFile: string;
    parsedProtoCases: (total: number, out0: number, out1: number) => string;
    loadedProtoCases: (total: number, out0: number, out1: number, name: string) => string;
    protoCsvParseError: string;
  };

  // ── Results ──
  results: {
    title: string;
    subtitle: string;
    noResults: string;
    noResultsHint: string;
    // View toggle
    rawText: string;
    prototype: string;
    compare: string;
    // Export
    exportCsv: string;
    exportJson: string;
    exportLatex: string;
    exportedAs: (format: string) => string;
    exportFailed: string;
    // Tabs
    tabSolutions: string;
    tabTruthTable: string;
    tabNecessity: string;
    tabRobustness: string;
    // Metrics
    cases: string;
    conditions: string;
    consistency: string;
    coverage: string;
    robustness: string;
    nA: string;
    // Necessity table
    necessityTitle: (threshold: number) => string;
    colCondition: string;
    colConsistency: string;
    colCoverage: string;
    colNecessary: string;
    // Robustness
    robustnessReport: string;
    overall: string;
    varying: string;
    stability: string;
    params: string;
    // Comparison
    comparisonTitle: string;
    consistencyCmp: string;
    coverageCmp: string;
    formulaMatchCmp: string;
    necessaryCondCmp: string;
    truthTableRowsCmp: string;
    solutionFormulaComparison: string;
    raw: string;
    // Compare view headers
    rawTextSolutions: string;
    protoSolutions: string;
    rawTruthTable: string;
    protoTruthTable: string;
    rawNecessity: string;
    protoNecessity: string;
    // Auto-interpretation
    autoInterpretation: string;
    expand: string;
    collapse: string;
    // QCA solution type labels (bilingual: Chinese + English parenthetical)
    solutionTypeComplex: string;
    solutionTypeParsimonious: string;
    solutionTypeIntermediate: string;
  };

  // ── Settings ──
  settings: {
    title: string;
    subtitle: string;
    // Sections
    calibrationDefaults: string;
    analysisThresholds: string;
    exportPreferences: string;
    engineStatus: string;
    about: string;
    // Setting field labels & descriptions
    fields: Record<string, { label: string; description: string }>;
    // Engine status
    pyodide: string;
    pythonVersion: string;
    packages: string;
    workerThread: string;
    // About
    aboutApp: string;
    aboutVersion: string;
    aboutFrontend: string;
    aboutPythonEngine: string;
    aboutAnalysisEngine: string;
    aboutVisualization: string;
    // Save
    saveBtn: string;
    saved: string;
    // BERT
    bertModelSection: string;
    bertStatusDesc: string;
    bertModelLabel: string;
    bertStatusLabel: string;
    bertDetailLabel: string;
    bertActionLabel: string;
    bertLoadModelBtn: string;
    // Export Dictionary
    exportDictSection: string;
    exportDictHelp: string;
    exportDictBtn: string;
    exportDictExporting: string;
    exportDictNoConditionSet: string;
    exportedDict: (count: number, format: string) => string;
    exportDictError: string;
    // Calibration Preview
    calibrationPreview: string;
    previewDistribution: string;
    distributionNormal: string;
    distributionUniform: string;
    distributionBimodal: string;
    previewHelp: string;
    previewMeanMembership: string;
    previewFullyOut: string;
    previewFullyIn: string;
    previewAtCrossover: string;
  };

  // ── Pipeline Status ──
  pipelineStatus: {
    stageLabels: Record<string, string>;
    reset: string;
  };
}

const zh: TranslationDict = {
  common: {
    reset: '重置',
    loading: '加载中...',
    exporting: '导出中...',
    error: '错误',
    yes: '是',
    no: '否',
    none: '无',
    or: '或',
    vs: '对比',
    differs: '不同',
    different: '不同',
    same: '相同',
    passed: '通过',
    unstable: '不稳定',
    notLoaded: '未加载',
    active: '运行中',
    idle: '空闲',
    enabled: '已启用',
    disabled: '已禁用',
  },

  sidebar: {
    appTitle: 'QCA 文本分析',
    appSubtitle: 'Pyodide + React',
    version: 'v0.2.0',
    engineLabel: 'QCA 引擎',
    dashboard: '首页',
    dataInput: '数据输入',
    results: '分析结果',
    settings: '设置',
  },

  dashboard: {
    title: '首页',
    subtitle: 'QCA 文本分析管道概览',
    description: '将公民反馈中文文本自动转化为模糊集 QCA 分析结果，支持关键词匹配与 BERT 原型校准两种方式。',
    pyodideStatus: 'Pyodide 状态',
    pipelineStage: '管道阶段',
    casesAnalyzed: '已分析案例',
    conditionsDefined: '已定义条件',
    statusReady: '就绪',
    statusLoading: '加载中...',
    statusNotLoaded: '未加载',
    statusError: '错误',
    quickStart: '快速开始',
    step1Title: '加载分析引擎',
    step1Desc: '启动 Pyodide（浏览器中的 Python）。首次加载约需 30 秒，后续加载使用缓存。',
    step1BtnReady: '引擎就绪',
    step1BtnLoading: '加载中...',
    step1BtnLoad: '加载引擎',
    step1BtnError: '重试（错误）',
    step2Title: '上传数据并定义条件',
    step2Desc: '上传中文文本语料（CSV/JSON/TXT）并定义模糊集校准条件。',
    step2Btn: '前往数据输入',
    step3Title: '运行 QCA 分析',
    step3Desc: '真值表构建、Quine-McCluskey 布尔最小化、必要性与充分性检验。',
    step4Title: '查看与导出结果',
    step4Desc: '查看真值表、解公式、必要性/充分性指标。导出为 CSV、JSON 或 LaTeX。',
    recentRuns: '最近分析记录',
    runId: '运行 ID',
    runName: '名称',
    runStatus: '状态',
    runCases: '案例数',
    runConditions: '条件数',
    runDuration: '用时',
    runDate: '日期',
    emptyTitle: '暂无分析记录。',
    emptySubtitle: '加载引擎并上传数据，开始您的首次 QCA 分析。',
    emptyAction: '上传数据并运行分析后，您的分析记录将显示在此处。',
    privacyTitle: '隐私与数据安全',
    privacyDesc:
      '所有分析数据仅在您的浏览器本地处理，不会上传至任何服务器。文本数据、校准结果和配置存储在浏览器 localStorage 中。',
    clearAllData: '清除所有本地数据',
    clearDataConfirm: '确认清除？此操作不可撤销，将删除所有本地存储的分析数据和设置。',
  },

  dataInput: {
    title: '数据输入',
    subtitle: '上传文本语料并定义 QCA 条件',
    engineNotReady: 'Pyodide 引擎尚未就绪。请前往首页点击"加载引擎"。',
    // BERT
    bertModel: 'BERT 模型',
    bertModelDesc: '用于原型语义匹配的嵌入模型',
    bertStatus: 'BERT 状态',
    bertNotLoaded: '未加载',
    bertLoadingProgress: (pct: number) => `下载模型中... ${pct}%`,
    bertReady: '就绪',
    bertError: '加载失败',
    bertCalibration: 'BERT 嵌入校准',
    bertDescription: '使用 BERT 嵌入余弦相似度替代关键词匹配进行原型校准。',
    bertUnloaded: '未加载',
    bertLoading: '加载中...',
    bertLoadingBtn: '加载中...',
    bertLoadedBtn: '已加载',
    bertLoadBtn: '加载 BERT 模型',
    bertCalibratingBtn: '校准中...',
    bertCalibrateBtn: '使用 BERT 嵌入校准',
    bertNotReady: '请先加载 BERT 模型',
    bertModelReady: 'BERT 模型加载成功。',
    bertLoadFailed: 'BERT 模型加载失败: ',
    bertCalibrationComplete: 'BERT 嵌入校准完成。',
    bertCalibrationFailed: 'BERT 嵌入校准失败: ',
    bertErrorUnknown: '未知 BERT 错误',
    outcomeLabel: '结果',
    // Text corpus
    textCorpus: '文本语料输入',
    pasteText: '粘贴文本',
    uploadFile: '上传文件',
    format: '格式：',
    formatPlainText: '纯文本',
    parseText: '解析文本',
    parseCsv: '解析 CSV',
    pastePlaceholderCsv: 'id,text\ncase_1,投诉内容...\ncase_2,建议内容...',
    pastePlaceholderJson: '[{"text_id": "1", "text": "投诉内容..."}]',
    pastePlaceholderTxt: '每条文本用空行分隔...',
    dropHere: '将 CSV、JSON、TXT 或 Excel 文件拖放到此处',
    orClickBrowse: '或点击浏览',
    casesLoaded: '条案例已加载',
    id: 'ID',
    textTruncated: '文本（截断）',
    andMoreCases: (n: number) => `... 还有 ${n} 条案例`,
    // Prototype
    prototypeTitle: '原型文本输入（含结果的 CSV）',
    prototypeFormatHelp:
      '格式：3 列 CSV，表头为 编号,文本内容,结果（或 id,text,outcome）。结果必须为 0 或 1。每行 = 一条文本案例。',
    prototypePlaceholder: '编号,文本内容,结果\ncase_1,服务态度非常差，等了很久没人理,0\ncase_2,问题已解决，效率很高很满意,1',
    parseProtoCsv: '解析 CSV',
    dropProtoFile: '将 CSV 文件拖放到此处（3 列：编号, 文本, 结果）',
    parseProto: '解析 CSV',
    outcome0: '结果=0',
    outcome1: '结果=1',
    // Condition set YAML
    conditionSetYaml: '条件集（YAML）',
    domainPreset: '领域预设：',
    // Prototype editor
    prototypeEditor: '原型编辑器（条件定义）',
    addCondition: '+ 添加条件',
    prototypeHelp:
      '为每个条件定义原型文本。使用 [1] 文本 表示成员原型，[0] 文本 表示非成员原型。无前缀的行默认为成员（1）。',
    conditionN: (n: number) => `条件 ${n}`,
    removeCondition: '移除',
    name: '名称',
    displayName: '显示名称',
    namePlaceholder: '例如: negative_affect',
    displayNamePlaceholder: '例如: 负面情感',
    prototypeTextsLabel: '原型文本（每行一条，前缀 [1] 或 [0]）',
    prototypeTextsPlaceholder: '[1] 非常不满，投诉多次无果\n[1] 严重扰民，无法忍受\n[0] 有点小问题但可以接受',
    generatedConditionSet: '生成的条件集：',
    conditionCount: (n: number) => `${n} 个条件`,
    prototypeCount: (n: number) => `${n} 个原型`,
    totalText: '共',
    outcomePassthrough: '结果列：passthrough（来自 CSV 结果列）',
    // Domain labels
    domainLabels: {
      dissatisfaction: '不满',
      policy_demand: '政策需求',
      co_production: '合产参与',
      trust: '信任',
      gov_responsiveness: '政府响应',
    },
    // Actions
    calibrateBtn: '校准（文本转模糊集）',
    calibrating: '校准中...',
    runPipelineBtn: '运行完整管道',
    running: '运行中...',
    resetBtn: '重置',
    // Messages
    noTextData: '未加载文本数据。请先上传或粘贴文本。',
    calibrationComplete: '校准完成。前往"分析结果"页面查看。',
    calibrationCompleteProto: (n: number) => `校准完成（含 ${n} 条原型案例）。前往"分析结果"页面查看。`,
    calibrationFailed: '校准失败：',
    analysisComplete: '分析完成！',
    pipelineFailed: '管道执行失败：',
    loadedCases: (n: number, name: string) => `已从 ${name} 加载 ${n} 条案例`,
    parsedCases: (n: number) => `已从粘贴文本解析 ${n} 条案例`,
    parseError: '解析错误：',
    fileTooLarge: (size: string) => `文件过大：${size} MB（上限 10 MB）`,
    errorReadingFile: '读取文件出错',
    parsedProtoCases: (total, out0, out1) =>
      `已解析 ${total} 条文本案例（结果=0: ${out0}, 结果=1: ${out1})`,
    loadedProtoCases: (total, out0, out1, name) =>
      `已从 ${name} 加载 ${total} 条文本案例（结果=0: ${out0}, 结果=1: ${out1})`,
    protoCsvParseError: '原型 CSV 解析错误：',
  },

  results: {
    title: '分析结果',
    subtitle: 'QCA 分析输出与可视化',
    noResults: '暂无分析结果。',
    noResultsHint: '前往"数据输入"页面上传文本并运行 QCA 管道。',
    // View toggle
    rawText: '原始文本',
    prototype: '原型',
    compare: '对比',
    // Export
    exportCsv: '导出 CSV',
    exportJson: '导出 JSON',
    exportLatex: '导出 LaTeX',
    exportedAs: (format: string) => `已导出为 ${format}`,
    exportFailed: '导出失败：',
    // Tabs
    tabSolutions: '解（Solutions）',
    tabTruthTable: '真值表（Truth Table）',
    tabNecessity: '必要性（Necessity）',
    tabRobustness: '稳健性（Robustness）',
    // Metrics
    cases: '案例数',
    conditions: '条件数',
    consistency: '一致性 (Consistency)',
    coverage: '覆盖度 (Coverage)',
    robustness: '稳健性 (Robustness)',
    nA: 'N/A',
    // Necessity table
    necessityTitle: (threshold: number) => `必要性分析（阈值 = ${threshold}）`,
    colCondition: '条件',
    colConsistency: '一致性',
    colCoverage: '覆盖度',
    colNecessary: '是否必要',
    // Robustness
    robustnessReport: '稳健性报告',
    overall: '总体：',
    varying: '变化参数：',
    stability: '稳定性：',
    params: '参数值：',
    // Comparison
    comparisonTitle: '原始文本 vs 原型 比较',
    consistencyCmp: '一致性',
    coverageCmp: '覆盖度',
    formulaMatchCmp: '公式匹配',
    necessaryCondCmp: '必要条件数',
    truthTableRowsCmp: '真值表行数',
    solutionFormulaComparison: '解公式比较',
    raw: '原始文本',
    // Compare view
    rawTextSolutions: '原始文本解',
    protoSolutions: '原型解',
    rawTruthTable: '原始文本真值表',
    protoTruthTable: '原型真值表',
    rawNecessity: '原始文本必要性',
    protoNecessity: '原型必要性',
    // Auto-interpretation
    autoInterpretation: '自动解读',
    expand: '展开',
    collapse: '收起',
    // QCA solution types
    solutionTypeComplex: '复杂解 (Complex Solution)',
    solutionTypeParsimonious: '精简解 (Parsimonious Solution)',
    solutionTypeIntermediate: '中间解 (Intermediate Solution)',
  },

  settings: {
    title: '设置',
    subtitle: 'QCA 管道配置与偏好',
    calibrationDefaults: '校准默认值',
    analysisThresholds: '分析阈值',
    exportPreferences: '导出偏好',
    engineStatus: '引擎状态',
    about: '关于',
    fields: {
      threshold_full_in: {
        label: '完全属于阈值 (Full-In)',
        description: '高于此隶属度的案例视为完全属于该集合（0.5-1.0）',
      },
      threshold_full_out: {
        label: '完全不属于阈值 (Full-Out)',
        description: '低于此隶属度的案例视为完全不属于该集合（0.0-0.5）',
      },
      crossover_point: {
        label: '交叉点 (Crossover)',
        description: '隶属度为 0.5 的分数值（最大模糊点）',
      },
      calibration_direction: {
        label: '默认方向',
        description: '分数越高对应越高隶属度（ascending）还是越低隶属度（descending）',
      },
      calibration_type: {
        label: '校准方法',
        description: 'Direct = 分段线性, Indirect = Log-Odds, Fuzzy Direct = Ragin 直接法',
      },
      qca_variant: {
        label: 'QCA 类型',
        description: 'fsQCA = 模糊集（连续隶属度 0-1）, csQCA = 清晰集（二分 0/1）',
      },
      consistency_threshold: {
        label: '一致性阈值 (Consistency)',
        description: '真值表行被分配结果=1 所需的最小子集一致性',
      },
      frequency_threshold: {
        label: '频次阈值 (Frequency)',
        description: '真值表配置被纳入的最小案例数',
      },
      necessity_threshold: {
        label: '必要性阈值 (Necessity)',
        description: '条件被视为必要条件的最小一致性（通常为 0.9）',
      },
      n_cut: {
        label: 'N-Cut（真值表截断）',
        description: '真值表行的频次截断。较高值减少噪音但需要更多案例。',
      },
      export_default_format: {
        label: '默认导出格式',
        description: '导出分析结果时的默认格式',
      },
      include_raw_data: {
        label: '导出中包含原始数据',
        description: '是否在导出文件中包含原始隶属度矩阵',
      },
      pretty_print_json: {
        label: 'JSON 格式化输出',
        description: '导出 JSON 时使用缩进格式',
      },
      bert_model: {
        label: 'BERT 模型',
        description: '用于原型语义相似度的 BERT 模型。切换模型后需重新计算嵌入。',
      },
    },
    pyodide: 'Pyodide',
    pythonVersion: 'Python 版本',
    packages: '已加载包',
    workerThread: 'Worker 线程',
    aboutApp: '应用名称',
    aboutVersion: '版本',
    aboutFrontend: '前端框架',
    aboutPythonEngine: 'Python 引擎',
    aboutAnalysisEngine: '分析引擎',
    aboutVisualization: '可视化',
    saveBtn: '保存设置',
    saved: '设置已保存。',
    // BERT
    bertModelSection: 'BERT 模型',
    bertStatusDesc: '当前 BERT 嵌入模型的加载状态',
    bertModelLabel: '模型选择',
    bertStatusLabel: '加载状态',
    bertDetailLabel: '详情',
    bertActionLabel: '操作',
    bertLoadModelBtn: '加载模型',
    // Export Dictionary
    exportDictSection: '导出关键词字典',
    exportDictHelp: '将当前条件集的关键词模式导出为文件。',
    exportDictBtn: '导出字典',
    exportDictExporting: '导出中...',
    exportDictNoConditionSet: '（暂无已定义的条件集）',
    exportedDict: (count: number, format: string) => `已导出 ${count} 个条件为 ${format} 格式`,
    exportDictError: '导出失败：',
    // Calibration Preview
    calibrationPreview: '校准预览',
    previewDistribution: '样本分布',
    distributionNormal: '正态分布',
    distributionUniform: '均匀分布',
    distributionBimodal: '双峰分布',
    previewHelp: '拖动上方校准参数，实时预览隶属度分布变化。使用合成样本数据展示校准效果。',
    previewMeanMembership: '平均隶属度',
    previewFullyOut: '完全不属于',
    previewFullyIn: '完全属于',
    previewAtCrossover: '交叉点',
  },

  pipelineStatus: {
    stageLabels: {
      idle: '就绪',
      'loading-pyodide': '加载引擎中...',
      'pyodide-ready': '引擎就绪',
      'loading-texts': '加载文本中...',
      calibrating: '校准中...',
      calibrated: '已校准',
      analyzing: '分析中...',
      analyzed: '已分析',
      'prototype-analyzing': '原型分析中...',
      'prototype-analyzed': '原型已分析',
      'running-robustness': '稳健性检验中...',
      'robustness-done': '稳健性检验完成',
      exporting: '导出中...',
      done: '完成',
      error: '错误',
    },
    reset: '重置',
  },
};

const en: TranslationDict = {
  common: {
    reset: 'Reset',
    loading: 'Loading...',
    exporting: 'Exporting...',
    error: 'Error',
    yes: 'Yes',
    no: 'No',
    none: '(none)',
    or: 'or',
    vs: 'vs',
    differs: 'differs',
    different: 'Different',
    same: 'Same',
    passed: 'PASSED',
    unstable: 'UNSTABLE',
    notLoaded: 'Not loaded',
    active: 'Active',
    idle: 'Idle',
    enabled: 'Enabled',
    disabled: 'Disabled',
  },

  sidebar: {
    appTitle: 'QCA Text',
    appSubtitle: 'Pyodide + React',
    version: 'v0.2.0',
    engineLabel: 'QCA Engine',
    dashboard: 'Dashboard',
    dataInput: 'Data Input',
    results: 'Results',
    settings: 'Settings',
  },

  dashboard: {
    title: 'Dashboard',
    subtitle: 'QCA Text Analysis Pipeline Overview',
    description: 'Automatically transforms Chinese-language citizen feedback into fuzzy-set QCA analysis results, supporting both keyword matching and BERT prototype calibration.',
    pyodideStatus: 'Pyodide Status',
    pipelineStage: 'Pipeline Stage',
    casesAnalyzed: 'Cases Analyzed',
    conditionsDefined: 'Conditions Defined',
    statusReady: 'Ready',
    statusLoading: 'Loading...',
    statusNotLoaded: 'Not Loaded',
    statusError: 'Error',
    quickStart: 'Quick Start',
    step1Title: 'Load Analysis Engine',
    step1Desc: 'Start Pyodide (Python in browser). First load takes ~30s. Subsequent loads are cached.',
    step1BtnReady: 'Engine Ready',
    step1BtnLoading: 'Loading...',
    step1BtnLoad: 'Load Engine',
    step1BtnError: 'Retry (Error)',
    step2Title: 'Upload Data & Define Conditions',
    step2Desc: 'Upload Chinese text corpus (CSV/JSON/TXT) and define fuzzy-set calibration conditions.',
    step2Btn: 'Go to Data Input',
    step3Title: 'Run QCA Analysis',
    step3Desc: 'Truth table construction, Quine-McCluskey minimization, necessity & sufficiency tests.',
    step4Title: 'Review & Export Results',
    step4Desc: 'View truth tables, solution formulas, necessity/sufficiency metrics. Export to CSV, JSON, or LaTeX.',
    recentRuns: 'Recent Analysis Runs',
    runId: 'Run ID',
    runName: 'Name',
    runStatus: 'Status',
    runCases: 'Cases',
    runConditions: 'Conditions',
    runDuration: 'Duration',
    runDate: 'Date',
    emptyTitle: 'No analysis runs yet.',
    emptySubtitle: 'Load the engine and upload data to start your first QCA analysis.',
    emptyAction: 'After uploading data and running an analysis, your recent runs will appear here.',
    privacyTitle: 'Privacy & Data Security',
    privacyDesc:
      'All analysis data is processed locally in your browser. No data is uploaded to any server. Text data, calibration results, and settings are stored in browser localStorage.',
    clearAllData: 'Clear All Local Data',
    clearDataConfirm: 'Confirm deletion? This cannot be undone. All locally stored analysis data and settings will be removed.',
  },

  dataInput: {
    title: 'Data Input',
    subtitle: 'Upload text corpus and define QCA conditions',
    engineNotReady: 'Pyodide engine is not ready. Go to Dashboard and click "Load Engine" first.',
    // BERT
    bertModel: 'BERT Model',
    bertModelDesc: 'Embedding model for prototype semantic matching',
    bertStatus: 'BERT Status',
    bertNotLoaded: 'Not loaded',
    bertLoadingProgress: (pct: number) => `Downloading model... ${pct}%`,
    bertReady: 'Ready',
    bertError: 'Load failed',
    bertCalibration: 'BERT Embedding Calibration',
    bertDescription: 'Use BERT embedding cosine similarity instead of keyword matching for prototype calibration.',
    bertUnloaded: 'Not loaded',
    bertLoading: 'Loading...',
    bertLoadingBtn: 'Loading...',
    bertLoadedBtn: 'Loaded',
    bertLoadBtn: 'Load BERT Model',
    bertCalibratingBtn: 'Calibrating...',
    bertCalibrateBtn: 'Calibrate with BERT Embeddings',
    bertNotReady: 'Please load BERT model first',
    bertModelReady: 'BERT model loaded successfully.',
    bertLoadFailed: 'BERT model load failed: ',
    bertCalibrationComplete: 'BERT embedding calibration complete.',
    bertCalibrationFailed: 'BERT embedding calibration failed: ',
    bertErrorUnknown: 'Unknown BERT error',
    outcomeLabel: 'Outcome',
    // Text corpus
    textCorpus: 'Text Corpus Input',
    pasteText: 'Paste Text',
    uploadFile: 'Upload File',
    format: 'Format:',
    formatPlainText: 'Plain Text',
    parseText: 'Parse Text',
    parseCsv: 'Parse CSV',
    pastePlaceholderCsv: 'id,text\ncase_1,投诉内容...\ncase_2,建议内容...',
    pastePlaceholderJson: '[{"text_id": "1", "text": "投诉内容..."}]',
    pastePlaceholderTxt: '每条文本用空行分隔...',
    dropHere: 'Drop a CSV, JSON, TXT, or Excel file here',
    orClickBrowse: 'or click to browse',
    casesLoaded: 'cases loaded',
    id: 'ID',
    textTruncated: 'Text (truncated)',
    andMoreCases: (n: number) => `... and ${n} more cases`,
    // Prototype
    prototypeTitle: 'Prototype Text Input (CSV with Outcomes)',
    prototypeFormatHelp:
      'Format: 3-column CSV with headers 编号,文本内容,结果 (or id,text,outcome). Outcome must be 0 or 1. Each row = one text case.',
    prototypePlaceholder:
      '编号,文本内容,结果\ncase_1,服务态度非常差，等了很久没人理,0\ncase_2,问题已解决，效率很高很满意,1',
    parseProtoCsv: 'Parse CSV',
    dropProtoFile: 'Drop a CSV file here (3 columns: id, text, outcome)',
    parseProto: 'Parse CSV',
    outcome0: 'Outcome 0',
    outcome1: 'Outcome 1',
    // Condition set YAML
    conditionSetYaml: 'Condition Set (YAML)',
    domainPreset: 'Domain Preset:',
    // Prototype editor
    prototypeEditor: 'Prototype Editor (Conditions)',
    addCondition: '+ Add Condition',
    prototypeHelp:
      "Define each condition's prototypes. Use [1] text for member prototypes and [0] text for non-member prototypes. Lines without a prefix default to member (1).",
    conditionN: (n: number) => `Condition ${n}`,
    removeCondition: 'Remove',
    name: 'Name',
    displayName: 'Display Name',
    namePlaceholder: 'e.g. negative_affect',
    displayNamePlaceholder: 'e.g. 负面情感',
    prototypeTextsLabel: 'Prototype Texts (one per line, prefix with [1] or [0])',
    prototypeTextsPlaceholder: '[1] 非常不满，投诉多次无果\n[1] 严重扰民，无法忍受\n[0] 有点小问题但可以接受',
    generatedConditionSet: 'Generated Condition Set:',
    conditionCount: (n: number) => `${n} condition(s)`,
    prototypeCount: (n: number) => `${n} prototype(s)`,
    totalText: 'total.',
    outcomePassthrough: 'Outcome: passthrough (from CSV output column).',
    // Domain labels
    domainLabels: {
      dissatisfaction: 'Dissatisfaction',
      policy_demand: 'Policy Demand',
      co_production: 'Co-Production',
      trust: 'Trust',
      gov_responsiveness: 'Gov Responsiveness',
    },
    // Actions
    calibrateBtn: 'Calibrate (Text to Fuzzy-Set)',
    calibrating: 'Calibrating...',
    runPipelineBtn: 'Run Full Pipeline',
    running: 'Running...',
    resetBtn: 'Reset',
    // Messages
    noTextData: 'No text data loaded. Upload or paste text first.',
    calibrationComplete: 'Calibration complete. Navigate to Results to analyze.',
    calibrationCompleteProto: (n: number) => `Calibration complete (with ${n} prototype cases). Navigate to Results to analyze.`,
    calibrationFailed: 'Calibration failed: ',
    analysisComplete: 'Analysis complete!',
    pipelineFailed: 'Pipeline failed: ',
    loadedCases: (n: number, name: string) => `Loaded ${n} cases from ${name}`,
    parsedCases: (n: number) => `Parsed ${n} cases from pasted text`,
    parseError: 'Parse error: ',
    fileTooLarge: (size: string) => `File too large: ${size} MB (max 10 MB)`,
    errorReadingFile: 'Error reading file',
    parsedProtoCases: (total, out0, out1) =>
      `Parsed ${total} text cases (outcome=0: ${out0}, outcome=1: ${out1})`,
    loadedProtoCases: (total, out0, out1, name) =>
      `Loaded ${total} text cases from ${name} (outcome=0: ${out0}, outcome=1: ${out1})`,
    protoCsvParseError: 'Prototype CSV parse error: ',
  },

  results: {
    title: 'Results',
    subtitle: 'QCA analysis output and visualizations',
    noResults: 'No analysis results yet.',
    noResultsHint: 'Go to Data Input to upload texts and run the QCA pipeline.',
    // View toggle
    rawText: 'Raw Text',
    prototype: 'Prototype',
    compare: 'Compare',
    // Export
    exportCsv: 'Export CSV',
    exportJson: 'Export JSON',
    exportLatex: 'Export LaTeX',
    exportedAs: (format: string) => `Exported as ${format}`,
    exportFailed: 'Export failed: ',
    // Tabs
    tabSolutions: 'Solutions',
    tabTruthTable: 'Truth Table',
    tabNecessity: 'Necessity',
    tabRobustness: 'Robustness',
    // Metrics
    cases: 'Cases',
    conditions: 'Conditions',
    consistency: 'Consistency',
    coverage: 'Coverage',
    robustness: 'Robustness',
    nA: 'N/A',
    // Necessity table
    necessityTitle: (threshold: number) => `Necessity Analysis (threshold = ${threshold})`,
    colCondition: 'Condition',
    colConsistency: 'Consistency',
    colCoverage: 'Coverage',
    colNecessary: 'Necessary?',
    // Robustness
    robustnessReport: 'Robustness Report',
    overall: 'Overall:',
    varying: 'Varying:',
    stability: 'Stability:',
    params: 'Params:',
    // Comparison
    comparisonTitle: 'Raw Text vs Prototype Comparison',
    consistencyCmp: 'Consistency',
    coverageCmp: 'Coverage',
    formulaMatchCmp: 'Formula Match',
    necessaryCondCmp: 'Necessary Cond.',
    truthTableRowsCmp: 'Truth Table Rows',
    solutionFormulaComparison: 'Solution Formula Comparison',
    raw: 'Raw',
    // Compare view
    rawTextSolutions: 'Raw Text Solutions',
    protoSolutions: 'Prototype Solutions',
    rawTruthTable: 'Raw Truth Table',
    protoTruthTable: 'Prototype Truth Table',
    rawNecessity: 'Raw Necessity',
    protoNecessity: 'Prototype Necessity',
    // Auto-interpretation
    autoInterpretation: 'Auto Interpretation',
    expand: 'Expand',
    collapse: 'Collapse',
    // QCA solution types
    solutionTypeComplex: 'Complex Solution',
    solutionTypeParsimonious: 'Parsimonious Solution',
    solutionTypeIntermediate: 'Intermediate Solution',
  },

  settings: {
    title: 'Settings',
    subtitle: 'QCA pipeline configuration and preferences',
    calibrationDefaults: 'Calibration Defaults',
    analysisThresholds: 'Analysis Thresholds',
    exportPreferences: 'Export Preferences',
    engineStatus: 'Engine Status',
    about: 'About',
    fields: {
      threshold_full_in: {
        label: 'Threshold Full-In',
        description: 'Membership score above which a case is fully in the set (0.5-1.0)',
      },
      threshold_full_out: {
        label: 'Threshold Full-Out',
        description: 'Membership score below which a case is fully out of the set (0.0-0.5)',
      },
      crossover_point: {
        label: 'Crossover Point',
        description: 'Score at which membership = 0.5 (maximum ambiguity)',
      },
      calibration_direction: {
        label: 'Default Direction',
        description: 'Whether higher raw scores mean higher membership (ascending) or lower (descending)',
      },
      calibration_type: {
        label: 'Calibration Method',
        description: 'Direct = piecewise linear, Indirect = log-odds, Fuzzy Direct = Ragins method',
      },
      qca_variant: {
        label: 'QCA Variant',
        description: 'fsQCA = fuzzy-set (continuous membership 0-1), csQCA = crisp-set (binary 0/1)',
      },
      consistency_threshold: {
        label: 'Consistency Threshold',
        description: 'Minimum subset consistency for a truth table row to be assigned outcome=1',
      },
      frequency_threshold: {
        label: 'Frequency Threshold',
        description: 'Minimum number of cases for a truth table configuration to be included',
      },
      necessity_threshold: {
        label: 'Necessity Threshold',
        description: 'Minimum consistency for a condition to be considered necessary (typically 0.9)',
      },
      n_cut: {
        label: 'N-Cut (Truth Table)',
        description: 'Frequency cutoff for truth table rows. Higher values reduce noise but require more cases.',
      },
      export_default_format: {
        label: 'Default Export Format',
        description: 'Default format when exporting analysis results',
      },
      include_raw_data: {
        label: 'Include Raw Data in Export',
        description: 'Whether to include the original membership matrix in exported files',
      },
      pretty_print_json: {
        label: 'Pretty-Print JSON',
        description: 'Use indented formatting when exporting JSON',
      },
      bert_model: {
        label: 'BERT Model',
        description: 'BERT model for prototype semantic similarity. Switching models requires re-computing embeddings.',
      },
    },
    pyodide: 'Pyodide',
    pythonVersion: 'Python Version',
    packages: 'Packages',
    workerThread: 'Worker Thread',
    aboutApp: 'Application',
    aboutVersion: 'Version',
    aboutFrontend: 'Frontend',
    aboutPythonEngine: 'Python Engine',
    aboutAnalysisEngine: 'Analysis Engine',
    aboutVisualization: 'Visualization',
    saveBtn: 'Save Settings',
    saved: 'Settings saved.',
    // BERT
    bertModelSection: 'BERT Model',
    bertStatusDesc: 'Current BERT embedding model loading status',
    bertModelLabel: 'Model',
    bertStatusLabel: 'Status',
    bertDetailLabel: 'Details',
    bertActionLabel: 'Action',
    bertLoadModelBtn: 'Load Model',
    // Export Dictionary
    exportDictSection: 'Export Keyword Dictionary',
    exportDictHelp: 'Export keyword patterns from the current condition set to a file.',
    exportDictBtn: 'Export Dictionary',
    exportDictExporting: 'Exporting...',
    exportDictNoConditionSet: ' (no condition set defined yet)',
    exportedDict: (count: number, format: string) => `Exported ${count} conditions as ${format}`,
    exportDictError: 'Export failed: ',
    // Calibration Preview
    calibrationPreview: 'Calibration Preview',
    previewDistribution: 'Sample Distribution',
    distributionNormal: 'Normal',
    distributionUniform: 'Uniform',
    distributionBimodal: 'Bimodal',
    previewHelp: 'Drag the calibration parameters above to preview membership distribution changes in real time. Uses synthetic sample data.',
    previewMeanMembership: 'Mean Membership',
    previewFullyOut: 'Fully Out',
    previewFullyIn: 'Fully In',
    previewAtCrossover: 'At Crossover',
  },

  pipelineStatus: {
    stageLabels: {
      idle: 'Ready',
      'loading-pyodide': 'Loading Engine...',
      'pyodide-ready': 'Engine Ready',
      'loading-texts': 'Loading Texts...',
      calibrating: 'Calibrating...',
      calibrated: 'Calibrated',
      analyzing: 'Analyzing...',
      analyzed: 'Analyzed',
      'prototype-analyzing': 'Analyzing Prototype...',
      'prototype-analyzed': 'Prototype Analyzed',
      'running-robustness': 'Robustness...',
      'robustness-done': 'Robustness Done',
      exporting: 'Exporting...',
      done: 'Complete',
      error: 'Error',
    },
    reset: 'Reset',
  },
};

export const translations: Record<Language, TranslationDict> = { zh, en };

/** Get the preferred language from browser locale, fallback to English. */
export function detectLanguage(): Language {
  try {
    const locale = navigator.language || (navigator as any).userLanguage || '';
    if (locale.toLowerCase().startsWith('zh')) return 'zh';
  } catch {}
  return 'en'; // default to English
}
