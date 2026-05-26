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
    compare: string;
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
    // Multi-outcome
    multiOutcomeTitle: string;
    multiOutcomeEnable: string;
    multiOutcomeHelp: string;
    multiOutcomeDisabled: string;
    outcomeBName: string;
    outcomeBDisplayName: string;
    outcomeBNamePlaceholder: string;
    outcomeBDisplayNamePlaceholder: string;
    runMultiOutcomePipelineBtn: string;
    multiOutcomeRunning: string;
    // Sample data
    sampleDataBtn: string;
    sampleDataTooltip: string;
    sampleLoaded: (n: number, domain: string) => string;
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
    exportDocx: string;
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
    // Cases tab
    tabCases: string;
    caseId: string;
    caseText: string;
    caseOutcome: string;
    caseSearch: string;
    caseFilterToggle: string;
    caseFilterMin: string;
    caseFilterMax: string;
    caseNoMatch: string;
    caseNoText: string;
    caseCount: (n: number) => string;
    caseExpandedLabel: (id: string) => string;
    saveSnapshotA: string;
    saveSnapshotB: string;
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
    bertModelSwitchWarning: string;
    bertModel: string;
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

  // ── Help Tooltips ──
  help: Record<string, string>;

  // ── Performance ──
  performance: {
    title: string;
    noData: string;
    avgInferenceTime: string;
    cacheHitRate: string;
    textsProcessed: string;
    lastBatchMs: string;
    activeModel: string;
    ms: string;
  };

  // ── Project Save/Load (P1-6) ──
  projectSave: {
    sectionTitle: string;
    sectionDesc: string;
    saveProjectBtn: string;
    saveProjectTooltip: string;
    saveProjectSuccess: (filename: string) => string;
    saveProjectNoData: string;
    loadProjectBtn: string;
    loadProjectTooltip: string;
    loadProjectSuccess: string;
    loadProjectError: string;
    loadProjectInvalid: string;
    autoRestoreBanner: (timestamp: string) => string;
    autoRestoreBtn: string;
    autoRestoreDismiss: string;
    validationMissingPipeline: string;
    validationMissingSettings: string;
  };

  // ── Compare (P1-7) ──
  compare: {
    title: string;
    subtitle: string;
    snapshotA: string;
    snapshotB: string;
    selectSnapshot: string;
    noSnapshots: string;
    noSnapshotsHint: string;
    swap: string;
    clear: string;
    paramDiffs: string;
    paramName: string;
    valueA: string;
    valueB: string;
    noDifferences: string;
    tabSolutions: string;
    tabTruthTable: string;
    tabNecessity: string;
    solutionsSame: string;
    solutionsDifferent: string;
    consistencyChange: string;
    coverageChange: string;
    exportReport: string;
    selectBothSnapshots: string;
    changed: string;
    unchanged: string;
    snapshotMeta: string;
    timestamp: string;
    conditions: string;
    cases: string;
  };

  // ── Templates (P1-13) ──
  templates: {
    libraryTitle: string;
    librarySubtitle: string;
    builtinLabel: string;
    importedLabel: string;
    useTemplate: string;
    viewDetails: string;
    conditionCount: string;
    noImportedTemplates: string;
    importFailed: string;
    shareLink: string;
    shareCopied: string;
    shareFailed: string;
    shareUrlTooLong: string;
    copyLink: string;
    generateShareLink: string;
    importFromLink: string;
    importTitle: string;
    importConfirm: string;
    importLoadAndGo: string;
    importDismiss: string;
    importSuccess: string;
    importErrorInvalid: string;
    importErrorIncomplete: string;
    importErrorVersion: string;
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
    compare: '参数比较',
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
    // Multi-outcome
    multiOutcomeTitle: '多结局分析',
    multiOutcomeEnable: '启用多结局比较',
    multiOutcomeHelp: '在同一条件集上分析两个结局并比较结果。',
    multiOutcomeDisabled: '需要先校准并运行至少一次分析才能开启多结局功能。',
    outcomeBName: '结局 B 变量名',
    outcomeBDisplayName: '结局 B 显示名称',
    outcomeBNamePlaceholder: '例如: outcome_b',
    outcomeBDisplayNamePlaceholder: '例如: 信任水平',
    runMultiOutcomePipelineBtn: '运行多结局分析管道',
    multiOutcomeRunning: '多结局分析运行中...',
    // Sample data
    sampleDataBtn: '加载 30 条样本数据',
    sampleDataTooltip: '从测试数据中加载 30 条样本（每领域 6 条）',
    sampleLoaded: (n: number, domain: string) => `已加载 ${n} 条样本数据。条件集：${domain}`,
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
    exportDocx: '导出 Word',
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
    // Cases tab
    tabCases: '案例详情',
    caseId: '案例ID',
    caseText: '原文',
    caseOutcome: '结果',
    caseSearch: '搜索文本...',
    caseFilterToggle: '筛选',
    caseFilterMin: '最小',
    caseFilterMax: '最大',
    caseNoMatch: '无匹配案例',
    caseNoText: '无文本',
    caseCount: (n: number) => `${n} 条案例`,
    caseExpandedLabel: (id: string) => `完整文本 (案例: ${id})`,
    saveSnapshotA: '保存为快照 A',
    saveSnapshotB: '保存为快照 B',
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
    bertModelSwitchWarning: '切换模型后需重新计算原型嵌入。',
    bertModel: 'BERT 模型',
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

  help: {
    temperatureTau: '控制相似度分数的区分程度。较高值（如10.0）会创建更接近二元的区分；较低值（如1.0）产生更平滑的边界。',
    calibrationMethod: 'Direct：分段线性映射。Indirect：Log-Odds 转换。Fuzzy Direct：fsQCA 文献中的逻辑公式。',
    aggregation: 'Centroid：所有原型嵌入的均值（标准原型理论）。Max：与任意单一原型的最高相似度（样例理论）。',
    scoring: 'Softmax：带温度的指数级 Softmax。Diff：归一化差值（备选）。',
    qcaVariant: 'fsQCA：模糊集分析（连续隶属度）。csQCA：清晰集分析（二分隶属度）。',
    prototypeText: '代表该条件的"典型示例"文本。BERT 将测量此原型与您的数据之间的语义相似度。',
    weight: '该原型对条件分数的贡献程度。较高权值增加影响力。',
    consistency: '条件-结果关系在案例间的一致性程度。通常认为高于0.8的值具有意义。',
    coverage: '该条件路径解释的结果比例。越高越好。',
    robustness: '在校准参数扰动下 QCA 解的稳定程度。',
  },
  performance: {
    title: 'BERT 性能',
    noData: '尚未执行推理',
    avgInferenceTime: '平均推理时间',
    cacheHitRate: '缓存命中率',
    textsProcessed: '已处理文本',
    lastBatchMs: '最近批次',
    activeModel: '当前模型',
    ms: 'ms',
  },

  projectSave: {
    sectionTitle: '项目管理',
    sectionDesc: '导出项目文件以便稍后恢复分析，或在其他浏览器中继续。',
    saveProjectBtn: '保存项目',
    saveProjectTooltip: '将当前管道状态、设置、文本语料和分析结果保存为 .qca 文件',
    saveProjectSuccess: (filename: string) => `项目已保存为 ${filename}`,
    saveProjectNoData: '请先定义条件集后再保存项目。',
    loadProjectBtn: '加载项目',
    loadProjectTooltip: '从 .qca 文件恢复之前保存的项目',
    loadProjectSuccess: '项目已成功加载。',
    loadProjectError: '加载项目文件失败：',
    loadProjectInvalid: '项目文件无效：',
    autoRestoreBanner: (timestamp: string) => `检测到 ${timestamp} 的自动保存。要恢复上次会话吗？`,
    autoRestoreBtn: '恢复',
    autoRestoreDismiss: '忽略',
    validationMissingPipeline: '缺少管道数据',
    validationMissingSettings: '缺少设置',
  },

  compare: {
    title: 'A/B 参数比较',
    subtitle: '比较两组分析参数的解、真值表和必要性差异',
    snapshotA: '快照 A',
    snapshotB: '快照 B',
    selectSnapshot: '选择快照...',
    noSnapshots: '请先在"分析结果"页面保存两个快照后再进行比较。',
    noSnapshotsHint: '运行分析后，点击"保存为快照 A/B"按钮来保存当前的参数和结果。',
    swap: '交换',
    clear: '清除',
    paramDiffs: '参数差异',
    paramName: '参数名称',
    valueA: '值 A',
    valueB: '值 B',
    noDifferences: '无差异 —— 两组参数完全相同',
    tabSolutions: '解',
    tabTruthTable: '真值表',
    tabNecessity: '必要性',
    solutionsSame: '解公式相同',
    solutionsDifferent: '解公式不同',
    consistencyChange: '一致性变化',
    coverageChange: '覆盖度变化',
    exportReport: '导出比较报告 (JSON)',
    selectBothSnapshots: '请选择两组快照进行对比',
    changed: '已变化',
    unchanged: '未变化',
    snapshotMeta: '快照元数据',
    timestamp: '时间戳',
    conditions: '个条件',
    cases: '条案例',
  },

  templates: {
    libraryTitle: '条件集模板库',
    librarySubtitle: '从内置领域模板开始，或导入分享的条件集配置。',
    builtinLabel: '内置',
    importedLabel: '已导入',
    useTemplate: '使用模板',
    viewDetails: '查看详情',
    conditionCount: '个条件',
    noImportedTemplates: '暂无导入的模板',
    importFailed: '模板加载失败',
    shareLink: '分享链接',
    shareCopied: '已复制！',
    shareFailed: '复制失败',
    shareUrlTooLong: '链接过长，无法分享',
    copyLink: '复制链接',
    generateShareLink: '生成分享链接',
    importFromLink: '从分享链接导入',
    importTitle: '导入条件集模板',
    importConfirm: '导入到库',
    importLoadAndGo: '导入并直接使用',
    importDismiss: '取消',
    importSuccess: '导入成功！',
    importErrorInvalid: '无效的分享链接',
    importErrorIncomplete: '分享数据不完整',
    importErrorVersion: '版本不兼容',
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
    compare: 'Compare',
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
    // Multi-outcome
    multiOutcomeTitle: 'Multi-Outcome Analysis',
    multiOutcomeEnable: 'Enable Multi-Outcome Comparison',
    multiOutcomeHelp: 'Analyze two outcomes on the same condition set and compare results.',
    multiOutcomeDisabled: 'Calibrate and run at least one analysis before enabling multi-outcome mode.',
    outcomeBName: 'Outcome B Variable Name',
    outcomeBDisplayName: 'Outcome B Display Name',
    outcomeBNamePlaceholder: 'e.g. outcome_b',
    outcomeBDisplayNamePlaceholder: 'e.g. Trust Level',
    runMultiOutcomePipelineBtn: 'Run Multi-Outcome Pipeline',
    multiOutcomeRunning: 'Multi-outcome analysis running...',
    // Sample data
    sampleDataBtn: 'Load 30 Sample Cases',
    sampleDataTooltip: 'Load 30 sample cases from the test fixture (6 per domain)',
    sampleLoaded: (n: number, domain: string) => `Loaded ${n} sample cases. Condition set: ${domain}`,
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
    exportDocx: 'Export Word',
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
    // Cases tab
    tabCases: 'Cases',
    caseId: 'Case ID',
    caseText: 'Text',
    caseOutcome: 'Outcome',
    caseSearch: 'Search text...',
    caseFilterToggle: 'Filters',
    caseFilterMin: 'Min',
    caseFilterMax: 'Max',
    caseNoMatch: 'No matching cases',
    caseNoText: 'No text',
    caseCount: (n: number) => `${n} cases`,
    caseExpandedLabel: (id: string) => `Full Text (Case: ${id})`,
    saveSnapshotA: 'Save as Snapshot A',
    saveSnapshotB: 'Save as Snapshot B',
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
    bertModelSwitchWarning: 'Switching models will require re-computing prototype embeddings.',
    bertModel: 'BERT Model',
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

  help: {
    temperatureTau: 'Controls how sharply similarity scores are separated. Higher values (e.g., 10.0) create more binary-like distinctions; lower values (e.g., 1.0) produce softer boundaries.',
    calibrationMethod: 'Direct: piecewise linear mapping. Indirect: log-odds transformation. Fuzzy Direct: logistic formula from fsQCA literature.',
    aggregation: 'Centroid: mean of all prototype embeddings (standard prototype theory). Max: highest similarity to any single prototype (exemplar theory).',
    scoring: 'Softmax: exponential softmax with temperature. Diff: normalized difference (fallback).',
    qcaVariant: 'fsQCA: fuzzy-set analysis with continuous membership. csQCA: crisp-set analysis with binary membership.',
    prototypeText: "A 'typical example' text that represents this condition. BERT will measure semantic similarity between this prototype and your data.",
    weight: 'How much this prototype contributes to the condition score. Higher weights increase influence.',
    consistency: 'How consistently the condition-outcome relationship holds across cases. Values above 0.8 are typically considered meaningful.',
    coverage: 'What proportion of the outcome is explained by this condition path. Higher is better.',
    robustness: 'How stable the QCA solution is under perturbations of calibration parameters.',
  },
  performance: {
    title: 'BERT Performance',
    noData: 'No inference performed yet',
    avgInferenceTime: 'Avg. Inference Time',
    cacheHitRate: 'Cache Hit Rate',
    textsProcessed: 'Texts Processed',
    lastBatchMs: 'Last Batch',
    activeModel: 'Active Model',
    ms: 'ms',
  },

  projectSave: {
    sectionTitle: 'Project',
    sectionDesc: 'Export your project file to restore later or continue in another browser.',
    saveProjectBtn: 'Save Project',
    saveProjectTooltip: 'Save current pipeline state, settings, text corpus, and analysis results as a .qca file',
    saveProjectSuccess: (filename: string) => `Project saved as ${filename}`,
    saveProjectNoData: 'Please define a condition set before saving the project.',
    loadProjectBtn: 'Load Project',
    loadProjectTooltip: 'Restore a previously saved project from a .qca file',
    loadProjectSuccess: 'Project loaded successfully.',
    loadProjectError: 'Failed to load project file: ',
    loadProjectInvalid: 'Invalid project file: ',
    autoRestoreBanner: (timestamp: string) => `An auto-save from ${timestamp} was found. Restore last session?`,
    autoRestoreBtn: 'Restore',
    autoRestoreDismiss: 'Dismiss',
    validationMissingPipeline: 'Missing pipeline data',
    validationMissingSettings: 'Missing settings',
  },

  compare: {
    title: 'Parameter Comparison (A/B)',
    subtitle: 'Compare solutions, truth tables, and necessity between two analysis parameter sets',
    snapshotA: 'Snapshot A',
    snapshotB: 'Snapshot B',
    selectSnapshot: 'Select a snapshot...',
    noSnapshots: 'Save two snapshots from the Results page before comparing.',
    noSnapshotsHint: 'After running an analysis, click "Save as Snapshot A/B" to save the current parameters and results.',
    swap: 'Swap',
    clear: 'Clear',
    paramDiffs: 'Parameter Differences',
    paramName: 'Parameter',
    valueA: 'Value A',
    valueB: 'Value B',
    noDifferences: 'No differences — both parameter sets are identical',
    tabSolutions: 'Solutions',
    tabTruthTable: 'Truth Table',
    tabNecessity: 'Necessity',
    solutionsSame: 'Solution formulas are identical',
    solutionsDifferent: 'Solution formulas differ',
    consistencyChange: 'Consistency change',
    coverageChange: 'Coverage change',
    exportReport: 'Export Comparison Report (JSON)',
    selectBothSnapshots: 'Please select two snapshots to compare',
    changed: 'Changed',
    unchanged: 'Unchanged',
    snapshotMeta: 'Snapshot Metadata',
    timestamp: 'Timestamp',
    conditions: 'conditions',
    cases: 'cases',
  },

  templates: {
    libraryTitle: 'Condition Set Template Library',
    librarySubtitle: 'Start from a built-in domain template or import a shared condition set configuration.',
    builtinLabel: 'Built-in',
    importedLabel: 'Imported',
    useTemplate: 'Use Template',
    viewDetails: 'View Details',
    conditionCount: 'conditions',
    noImportedTemplates: 'No imported templates yet',
    importFailed: 'Failed to load templates',
    shareLink: 'Share Link',
    shareCopied: 'Copied!',
    shareFailed: 'Copy failed',
    shareUrlTooLong: 'URL too long to share',
    copyLink: 'Copy Link',
    generateShareLink: 'Generate Share Link',
    importFromLink: 'Import from shared link',
    importTitle: 'Import Condition Set Template',
    importConfirm: 'Import to Library',
    importLoadAndGo: 'Import & Use Now',
    importDismiss: 'Dismiss',
    importSuccess: 'Import successful!',
    importErrorInvalid: 'Invalid share link',
    importErrorIncomplete: 'Shared data is incomplete',
    importErrorVersion: 'Incompatible version',
  },
};

export const translations: Record<Language, TranslationDict> = { zh, en };
