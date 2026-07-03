// ===== Mock 数据层 V2.0 =====
// 基于《开发计划书 V2.0》重构
// 模拟所有后端 API 返回结构

// ========== 用户 ==========
export const mockUsers = [
  { id: "u1", username: "admin", full_name: "系统管理员", email: "admin@gc-aic.com", role: "admin", project_permissions: ["p1","p2","p3","p4","p5"], status: "active", last_login: "2026-06-30 08:30" },
  { id: "u2", username: "zhangwei", full_name: "张工", email: "zhangwei@example.com", role: "project_manager", project_permissions: ["p1","p3"], status: "active", last_login: "2026-06-30 14:00" },
  { id: "u3", username: "liming", full_name: "李工", email: "liming@example.com", role: "auditor", project_permissions: ["p1","p2"], status: "active", last_login: "2026-06-29 16:30" },
  { id: "u4", username: "wangfang", full_name: "王工", email: "wangfang@example.com", role: "operator", project_permissions: ["p1","p3"], status: "active", last_login: "2026-06-28 09:00" },
  { id: "u5", username: "zhaoqiang", full_name: "赵工", email: "zhaoqiang@example.com", role: "viewer", project_permissions: ["p2","p4"], status: "inactive", last_login: "2026-06-15 10:00" },
];

// ========== 项目 ==========
export const mockProjects = [
  { id: "p1", project_name: "1-6号粮仓新建工程", project_code: "GC-2025-001", construction_scale: "6座5000吨级平房仓", total_investment: 125000000, owner_unit: "中央储备粮集团", supervisor_unit: "建科监理公司", design_unit: "粮食设计院", constructor_unit: "中建三局", project_manager: "张工", project_location: "河南省郑州市", planned_start_date: "2025-06-01", planned_end_date: "2027-03-31", status: "construction", progress: 72, description: "新建6座5000吨级平房仓及配套设施" },
  { id: "p2", project_name: "7-12号粮仓改造工程", project_code: "GC-2025-002", construction_scale: "6座仓房智能化改造", total_investment: 82000000, owner_unit: "地方储备粮公司", supervisor_unit: "市政监理公司", design_unit: "建筑设计院", constructor_unit: "市政建设公司", project_manager: "李工", project_location: "河南省洛阳市", planned_start_date: "2025-09-15", planned_end_date: "2026-12-30", status: "construction", progress: 45, description: "对现有6座仓房进行智能化通风系统改造" },
  { id: "p3", project_name: "智能通风系统安装", project_code: "GC-2026-001", construction_scale: "48座仓房通风设备安装", total_investment: 36000000, owner_unit: "科技采购中心", supervisor_unit: "信息监理公司", design_unit: "智能设备研究院", constructor_unit: "智能设备公司", project_manager: "王工", project_location: "河南省周口市", planned_start_date: "2026-03-01", planned_end_date: "2026-08-30", status: "construction", progress: 88, description: "为48座仓房安装智能温湿度监控通风系统" },
  { id: "p4", project_name: "中心粮库扩建", project_code: "GC-2026-002", construction_scale: "新增10座立筒仓", total_investment: 158000000, owner_unit: "省级储备粮集团", supervisor_unit: "省监理公司", design_unit: "省级设计院", constructor_unit: "中建四局", project_manager: "孙工", project_location: "河南省南阳市", planned_start_date: "2026-06-01", planned_end_date: "2028-12-31", status: "preparation", progress: 5, description: "新建10座10000吨级立筒仓" },
  { id: "p5", project_name: "粮库信息化平台建设", project_code: "GC-2026-003", construction_scale: "全库区信息化改造", total_investment: 18000000, owner_unit: "粮食局信息中心", supervisor_unit: "信息化监理公司", design_unit: "软件设计院", constructor_unit: "华信科技", project_manager: "张工", project_location: "河南省开封市", planned_start_date: "2026-04-01", planned_end_date: "2027-03-31", status: "construction", progress: 35, description: "粮库全流程信息化管理平台建设" },
];

// ========== 项目里程碑 ==========
export interface ProjectMilestone {
  id: string; project_id: string; seq: number; name: string;
  planned_date: string; actual_date: string | null;
  status: "completed" | "in_progress" | "pending";
  description: string;
}
export const mockMilestones: ProjectMilestone[] = [
  { id: "ms1", project_id: "p1", seq: 1, name: "合同签订", planned_date: "2025-05-15", actual_date: "2025-05-15", status: "completed", description: "施工总承包合同" },
  { id: "ms2", project_id: "p1", seq: 2, name: "开工", planned_date: "2025-06-01", actual_date: "2025-06-01", status: "completed", description: "" },
  { id: "ms3", project_id: "p1", seq: 3, name: "地基完成", planned_date: "2025-12-31", actual_date: "2025-12-28", status: "completed", description: "6座仓房基础全部完成" },
  { id: "ms4", project_id: "p1", seq: 4, name: "主体封顶", planned_date: "2026-06-30", actual_date: null, status: "in_progress", description: "当前进度 72%" },
  { id: "ms5", project_id: "p1", seq: 5, name: "装修完成", planned_date: "2026-12-31", actual_date: null, status: "pending", description: "" },
  { id: "ms6", project_id: "p1", seq: 6, name: "竣工验收", planned_date: "2027-03-31", actual_date: null, status: "pending", description: "" },
];

// ========== 进度填报 ==========
export interface ProgressReport {
  id: string; project_id: string; reporter_name: string;
  unit_type: "constructor" | "supervisor" | "designer" | "owner";
  content: { items: { name: string; progress: number; note: string }[] };
  report_date: string;
}
export const mockProgressReports: ProgressReport[] = [
  { id: "pr1", project_id: "p1", reporter_name: "中建三局-王工", unit_type: "constructor",
    content: { items: [{ name: "土建工程", progress: 72, note: "主体结构施工中" }, { name: "安装工程", progress: 65, note: "通风管道预埋" }, { name: "装饰工程", progress: 30, note: "内墙抹灰开始" }] },
    report_date: "2026-06-30" },
  { id: "pr2", project_id: "p1", reporter_name: "建科监理-李工", unit_type: "supervisor",
    content: { items: [{ name: "旁站监理", progress: 100, note: "全覆盖" }, { name: "材料检验", progress: 95, note: "钢筋批次检验" }, { name: "质量验收", progress: 70, note: "主体结构验收中" }] },
    report_date: "2026-06-30" },
  { id: "pr3", project_id: "p1", reporter_name: "粮食设计院-陈工", unit_type: "designer",
    content: { items: [{ name: "施工图设计", progress: 100, note: "已交付" }, { name: "设计变更", progress: 60, note: "3项变更处理中" }, { name: "现场服务", progress: 80, note: "定期巡场" }] },
    report_date: "2026-06-30" },
  { id: "pr4", project_id: "p1", reporter_name: "中央储备粮-赵工", unit_type: "owner",
    content: { items: [{ name: "资金到位率", progress: 100, note: "全额到位" }, { name: "审批进度", progress: 85, note: "2项待批" }, { name: "资料归档", progress: 60, note: "阶段性归档" }] },
    report_date: "2026-06-30" },
];

// ========== Dashboard ==========
export const mockDashboardStats = { active_projects: 4, monthly_output: 38600000, pending_audits: 2, completed_reports: 28 };
export const mockWeeklyReportStatus = { draft: 1, pending_review: 2, published: 25 };
export const mockSCurveMini = { months: ["1月","2月","3月","4月","5月","6月"], planned: [15,25,35,45,55,65], actual: [12,22,32,42,52,60] };
export const mockInvestmentMini = { months: ["1月","2月","3月","4月","5月","6月"], monthly: [650,720,980,850,1100,1200], cumulative: [650,1370,2350,3200,4300,5500] };
export const mockAISummary = [
  { level: "warning", content: "1-6号粮仓工程进度偏差-3%，在可控范围内，需关注7月雨季影响" },
  { level: "info", content: "7-12号粮仓改造累计付款占合同44.9%，进度45%，付款比例基本合理" },
  { level: "danger", content: "3号粮仓（玉米仓）温度26.5℃超警戒线，需立即排查" },
  { level: "warning", content: "智能通风系统项目本周无进度报告上传，可能数据缺失" },
];
export const mockTodos = [
  { type: "batch", title: "批次 BT-20260630-001 待确认入库", target: "/data/batches/1", urgency: "high" },
  { type: "report", title: "6月粮仓温湿度月报 待审批", target: "/reports/1/edit", urgency: "medium" },
  { type: "audit", title: "第8期进度款审核 待处理", target: "/audits/1", urgency: "high" },
  { type: "report", title: "第26周质量检验周报 待发布", target: "/reports/2/edit", urgency: "low" },
];
export const mockWeather = { city: "郑州", temp: 32, humidity: 65, condition: "多云",
  forecast: [
    { day: "今天", temp_high: 33, temp_low: 25, condition: "多云" }, { day: "明天", temp_high: 35, temp_low: 26, condition: "晴" },
    { day: "后天", temp_high: 34, temp_low: 24, condition: "小雨" }, { day: "周四", temp_high: 31, temp_low: 23, condition: "阴" },
    { day: "周五", temp_high: 30, temp_low: 22, condition: "多云" }, { day: "周六", temp_high: 32, temp_low: 24, condition: "晴" },
    { day: "周日", temp_high: 33, temp_low: 25, condition: "晴" },
  ],
};

// ========== 批次 ==========
export const mockBatches = [
  { id: "1", batch_no: "BT-20260630-001", original_filename: "6月第4周工程量清单.xlsx", project_id: "p1", project_name: "1-6号粮仓新建工程", status: "validated", file_format: "xlsx", total_rows: 156, parsed_rows: 150, error_count: 6, quality_score: 92, period_type: "weekly", period_start: "2026-06-24", period_end: "2026-06-30", uploader_name: "王工", upload_time: "2026-06-30 14:30", mapping_name: "Excel 工程量清单" },
  { id: "2", batch_no: "BT-20260628-001", original_filename: "6月监理月报数据.xlsx", project_id: "p1", status: "committed", file_format: "xlsx", total_rows: 88, parsed_rows: 88, error_count: 0, quality_score: 98, period_type: "monthly", period_start: "2026-06-01", period_end: "2026-06-30", uploader_name: "王工", upload_time: "2026-06-28 09:15", mapping_name: "监理月报" },
  { id: "3", batch_no: "BT-20260625-001", original_filename: "第8期进度款申报.xlsx", project_id: "p2", project_name: "7-12号粮仓改造工程", status: "pending", file_format: "xlsx", total_rows: 45, parsed_rows: 0, error_count: 0, quality_score: 0, period_type: "payment", period_start: "2026-06-18", period_end: "2026-06-25", uploader_name: "王工", upload_time: "2026-06-25 16:00", mapping_name: "进度款申报" },
  { id: "4", batch_no: "BT-20260620-001", original_filename: "智能通风设备清单.xlsx", project_id: "p3", project_name: "智能通风系统安装", status: "rolled_back", file_format: "xlsx", total_rows: 120, parsed_rows: 118, error_count: 2, quality_score: 85, period_type: "other", period_start: "2026-06-01", period_end: "2026-06-20", uploader_name: "王工", upload_time: "2026-06-20 10:00", mapping_name: "Excel 工程量清单" },
];

// ========== 数据行 ==========
export const mockDataRows = Array.from({ length: 156 }, (_, i) => ({
  id: `${i + 1}`,
  batch_id: "1",
  row_number: i + 1,
  data_date: `2026-06-${24 + (i % 7)}`,
  category: ["土建工程","安装工程","装饰工程","其他"][i % 4],
  item_name: ["C30混凝土浇筑","HRB400钢筋","土方开挖","模板工程","脚手架搭设","砌体工程","防水工程","钢结构安装","电气安装","给排水"][i % 10],
  planned_quantity: Math.round((100 + Math.random() * 500)),
  actual_quantity: Math.round((100 + Math.random() * 500)),
  unit: ["m³","t","m³","m²","m²","m³","m²","t","套","m"][i % 10],
  unit_price: Math.round((50 + Math.random() * 800) * 100),
  amount: Math.round((5000 + Math.random() * 50000) * 100),
  cost_type: ["direct","indirect","material","labor","equipment"][i % 5],
  source_doc: "6月第4周工程量清单.xlsx",
  source_type: "excel",
  is_confirmed: i < 140,
  confirmed_by: i < 140 ? "王工" : null,
  confirmed_at: i < 140 ? "2026-06-30 16:30" : null,
  validation_flag: i % 20 === 0 ? "error" : i % 10 === 0 ? "warning" : "ok",
  error_description: i % 20 === 0 ? "金额超出合理范围" : i % 10 === 0 ? "数据精度待确认" : null,
  raw_payload: { 原始列A: "值A", 原始列B: 123, 原始列C: "2026/6/25" },
}));

// ========== 报告 ==========
export const mockReports = [
  { id: "1", title: "6月粮仓温湿度月报", project_id: "p1", project_name: "1-6号粮仓新建工程", type: "monthly", period: "2026-06", status: "pending_review", template_name: "月报标准模板", creator_name: "王工", created_at: "2026-06-30 16:00" },
  { id: "2", title: "第26周质量检验周报", project_id: "p1", project_name: "1-6号粮仓新建工程", type: "weekly", period: "2026-W26", status: "published", template_name: "周报标准模板", creator_name: "王工", created_at: "2026-06-28 10:00" },
  { id: "3", title: "6月30日粮情日报", project_id: "p1", project_name: "1-6号粮仓新建工程", type: "daily", period: "2026-06-30", status: "published", template_name: "日报模板", creator_name: "系统自动", created_at: "2026-06-30 08:00" },
  { id: "4", title: "3号粮仓异常分析报告", project_id: "p1", project_name: "1-6号粮仓新建工程", type: "special", period: "2026-06-29", status: "pending_review", template_name: "异常报告模板", creator_name: "李工", created_at: "2026-06-29 15:00" },
  { id: "5", title: "6月库存盘点报告", project_id: "p1", project_name: "1-6号粮仓新建工程", type: "monthly", period: "2026-06", status: "published", template_name: "月报标准模板", creator_name: "王工", created_at: "2026-06-30 11:00" },
];

// ========== 报告模板 ==========
export const mockReportTemplates = [
  { id: "t1", name: "周报标准模板", type: "weekly", version: 3, field_count: 12, status: "active", creator_name: "管理员", created_at: "2026-05-01",
    schema: { fields: [
      { key: "week_no", label: "周次", type: "text", required: true, ai_suggest: false },
      { key: "completed_value", label: "本周完成产值", type: "number", unit: "fen", required: true, ai_suggest: false },
      { key: "cumulative_value", label: "累计完成产值", type: "formula", formula: "prev.cumulative + this.completed", required: true, ai_suggest: false },
      { key: "progress_desc", label: "本周进度描述", type: "text", required: true, ai_suggest: true },
      { key: "next_plan", label: "下周计划", type: "text", required: true, ai_suggest: true },
      { key: "quality_desc", label: "质量情况", type: "text", required: false, ai_suggest: false },
      { key: "safety_desc", label: "安全情况", type: "text", required: false, ai_suggest: false },
    ]},
  },
  { id: "t2", name: "月报标准模板", type: "monthly", version: 5, field_count: 18, status: "active", creator_name: "管理员", created_at: "2026-05-01" },
  { id: "t3", name: "日报模板", type: "daily", version: 2, field_count: 8, status: "active", creator_name: "管理员", created_at: "2026-05-01" },
  { id: "t4", name: "异常报告模板", type: "special", version: 1, field_count: 6, status: "active", creator_name: "管理员", created_at: "2026-06-01" },
];

// ========== 审核 ==========
export const mockAudits = [
  { id: "1", project_id: "p1", project_name: "1-6号粮仓新建工程", contract_name: "施工总承包合同", contract_version: "V3",
    period: "第12期", constructor_unit: "中建三局", apply_amount: 580000000, ai_suggest_amount: 552000000, final_amount: null,
    deduct_amount: null, deduct_rate: null, anomaly_count: 2, status: "pending_audit",
    submitted_at: "2026-06-20", auditor_name: null,
    ai_findings: [
      { id: "f1", type: "重复计量", item: "土方开挖", suggest_deduct: 12000000, reason: "土方开挖申报数量(3200m³)超出图纸计算量(3105m³)约3.1%，请核实实际土方量" },
      { id: "f2", type: "单价异常", item: "脚手架", suggest_deduct: 8000000, reason: "脚手架与第7期存在重复计量嫌疑（第7期已计1200m²），请核实是否重复申报" },
    ],
    items: [
      { id: "ai1", name: "土方开挖", unit: "m³", apply_qty: 3200, apply_price: 2800, apply_amount: 8960000, audit_qty: 3100, audit_price: 2800, audit_amount: 8680000, deduct: 280000, anomaly: "超量" },
      { id: "ai2", name: "C30混凝土", unit: "m³", apply_qty: 450, apply_price: 68000, apply_amount: 30600000, audit_qty: 445, audit_price: 68000, audit_amount: 30260000, deduct: 340000, anomaly: null },
      { id: "ai3", name: "HRB400钢筋", unit: "t", apply_qty: 120, apply_price: 520000, apply_amount: 62400000, audit_qty: 118, audit_price: 520000, audit_amount: 61360000, deduct: 1040000, anomaly: null },
      { id: "ai4", name: "模板工程", unit: "m²", apply_qty: 2800, apply_price: 8500, apply_amount: 23800000, audit_qty: 2750, audit_price: 8500, audit_amount: 23375000, deduct: 425000, anomaly: null },
      { id: "ai5", name: "脚手架", unit: "m²", apply_qty: 3500, apply_price: 3500, apply_amount: 12250000, audit_qty: 3500, audit_price: 3500, audit_amount: 12250000, deduct: 0, anomaly: "重复" },
    ],
  },
  { id: "2", project_id: "p1", project_name: "1-6号粮仓新建工程", contract_name: "施工总承包合同", contract_version: "V3",
    period: "第11期", constructor_unit: "中建三局", apply_amount: 620000000, ai_suggest_amount: 595000000, final_amount: 595000000,
    deduct_amount: 25000000, deduct_rate: 4.03, anomaly_count: 1, status: "paid", submitted_at: "2026-05-18", auditor_name: "李工",
    items: [], ai_findings: [],
  },
  { id: "3", project_id: "p2", project_name: "7-12号粮仓改造工程", contract_name: "智能化改造合同", contract_version: "V2",
    period: "第8期", constructor_unit: "市政建设公司", apply_amount: 320000000, ai_suggest_amount: null, final_amount: null,
    deduct_amount: null, deduct_rate: null, anomaly_count: 0, status: "pending_audit", submitted_at: "2026-06-22", auditor_name: null,
    items: [], ai_findings: [],
  },
];

// ========== 二类费用：费用类型（用户可自定义） ==========
export const mockFeeTypes = ["监理", "设计", "检测", "咨询", "其他"];

// ========== 二类费用：支付节点 ==========
export interface PaymentNode {
  id: string; contract_id: string; seq: number;
  name: string; trigger: string;
  formula_expr: string;
  offset_days: number;
  amount: number;
  planned_date: string;
  actual_date: string | null;
  status: "paid" | "overdue" | "pending";
  paid_amount: number;
}
export const mockPaymentNodes: Record<string, PaymentNode[]> = {
  sc1: [
    { id: "n1", contract_id: "sc1", seq: 1, name: "合同签订", trigger: "合同双方盖章生效", formula_expr: "=合同金额*0.15", offset_days: 0, amount: 42000000, planned_date: "2025-06-15", actual_date: "2025-06-15", status: "paid", paid_amount: 42000000 },
    { id: "n2", contract_id: "sc1", seq: 2, name: "进场", trigger: "监理工程师进场确认", formula_expr: "=合同金额*0.15", offset_days: 0, amount: 42000000, planned_date: "2025-07-01", actual_date: "2025-07-03", status: "paid", paid_amount: 42000000 },
    { id: "n3", contract_id: "sc1", seq: 3, name: "中期监理费", trigger: "主体结构完成50%", formula_expr: "=合同金额*0.30", offset_days: 0, amount: 84000000, planned_date: "2026-03-01", actual_date: null, status: "overdue", paid_amount: 0 },
    { id: "n4", contract_id: "sc1", seq: 4, name: "完工验收", trigger: "竣工验收通过", formula_expr: "=合同金额*0.25", offset_days: 0, amount: 70000000, planned_date: "2027-03-31", actual_date: null, status: "pending", paid_amount: 0 },
    { id: "n5", contract_id: "sc1", seq: 5, name: "质保期满", trigger: "竣工验收通过后2年", formula_expr: "=合同金额*0.15", offset_days: 730, amount: 42000000, planned_date: "2029-03-31", actual_date: null, status: "pending", paid_amount: 0 },
  ],
  sc2: [
    { id: "n6", contract_id: "sc2", seq: 1, name: "方案设计", trigger: "方案设计完成交付", formula_expr: "=合同金额*0.20", offset_days: 0, amount: 30000000, planned_date: "2025-03-15", actual_date: "2025-03-10", status: "paid", paid_amount: 30000000 },
    { id: "n7", contract_id: "sc2", seq: 2, name: "初步设计", trigger: "初步设计通过评审", formula_expr: "=合同金额*0.20", offset_days: 0, amount: 30000000, planned_date: "2025-06-01", actual_date: "2025-06-05", status: "paid", paid_amount: 30000000 },
    { id: "n8", contract_id: "sc2", seq: 3, name: "施工图设计", trigger: "施工图交付", formula_expr: "=合同金额*0.40", offset_days: 0, amount: 60000000, planned_date: "2025-09-01", actual_date: null, status: "pending", paid_amount: 0 },
    { id: "n9", contract_id: "sc2", seq: 4, name: "现场服务", trigger: "竣工验收通过", formula_expr: "=合同金额*0.20", offset_days: 90, amount: 30000000, planned_date: "2027-06-30", actual_date: null, status: "pending", paid_amount: 0 },
  ],
  sc3: [
    { id: "n10", contract_id: "sc3", seq: 1, name: "进场检测", trigger: "检测合同签订", formula_expr: "=合同金额*0.30", offset_days: 0, amount: 18000000, planned_date: "2025-10-15", actual_date: "2025-10-10", status: "paid", paid_amount: 18000000 },
    { id: "n11", contract_id: "sc3", seq: 2, name: "中期检测", trigger: "主体结构完成", formula_expr: "=合同金额*0.40", offset_days: 0, amount: 24000000, planned_date: "2026-06-01", actual_date: null, status: "pending", paid_amount: 0 },
    { id: "n12", contract_id: "sc3", seq: 3, name: "完工检测", trigger: "竣工验收通过", formula_expr: "=合同金额*0.30", offset_days: 30, amount: 18000000, planned_date: "2027-04-30", actual_date: null, status: "pending", paid_amount: 0 },
  ],
  sc4: [
    { id: "n13", contract_id: "sc4", seq: 1, name: "前期咨询", trigger: "咨询合同签订", formula_expr: "=合同金额*0.30", offset_days: 0, amount: 13500000, planned_date: "2026-03-15", actual_date: "2026-03-15", status: "paid", paid_amount: 13500000 },
    { id: "n14", contract_id: "sc4", seq: 2, name: "中期咨询", trigger: "中期报告提交", formula_expr: "=合同金额*0.40", offset_days: 0, amount: 18000000, planned_date: "2026-06-01", actual_date: null, status: "pending", paid_amount: 0 },
  ],
};

// ========== 二类费用合同 ==========
export const mockSecondaryContracts = [
  { id: "sc1", contract_name: "监理服务合同", project_id: "p1", project_name: "1-6号粮仓新建工程", fee_type: "监理", contractor: "建科监理公司", contract_amount: 280000000, start_date: "2025-06-01", end_date: "2027-03-31", status: "active" as const, notes: "含5个支付节点" },
  { id: "sc2", contract_name: "设计服务合同", project_id: "p1", project_name: "1-6号粮仓新建工程", fee_type: "设计", contractor: "粮食设计院", contract_amount: 150000000, start_date: "2025-03-01", end_date: "2027-06-30", status: "active" as const, notes: "含现场服务期" },
  { id: "sc3", contract_name: "质量检测合同", project_id: "p2", project_name: "7-12号粮仓改造工程", fee_type: "检测", contractor: "省检测中心", contract_amount: 60000000, start_date: "2025-10-01", end_date: "2026-12-31", status: "active" as const, notes: "" },
  { id: "sc4", contract_name: "造价咨询合同", project_id: "p3", project_name: "智能通风系统安装", fee_type: "咨询", contractor: "造价咨询公司", contract_amount: 45000000, start_date: "2026-03-01", end_date: "2026-08-30", status: "terminated" as const, notes: "合同已终止" },
];

// ========== 二类费用：节点模板 ==========
export interface NodeTemplate {
  id: string; name: string; fee_type: string; is_builtin: boolean; status: string;
  nodes_def: { seq: number; name: string; trigger: string; ratio: number; offset_days: number }[];
}
export const mockNodeTemplates: NodeTemplate[] = [
  { id: "nt1", name: "监理费用模板", fee_type: "监理", is_builtin: true, status: "active",
    nodes_def: [
      { seq: 1, name: "合同签订", trigger: "双方盖章生效", ratio: 15, offset_days: 0 },
      { seq: 2, name: "进场", trigger: "监理进场确认", ratio: 15, offset_days: 30 },
      { seq: 3, name: "中期监理", trigger: "主体完成50%", ratio: 30, offset_days: 270 },
      { seq: 4, name: "完工验收", trigger: "竣工验收通过", ratio: 25, offset_days: 670 },
      { seq: 5, name: "质保期满", trigger: "竣工验收后2年", ratio: 15, offset_days: 730 },
    ],
  },
  { id: "nt2", name: "设计费用模板", fee_type: "设计", is_builtin: true, status: "active",
    nodes_def: [
      { seq: 1, name: "方案设计", trigger: "方案交付", ratio: 20, offset_days: 0 },
      { seq: 2, name: "初步设计", trigger: "评审通过", ratio: 20, offset_days: 60 },
      { seq: 3, name: "施工图设计", trigger: "施工图交付", ratio: 40, offset_days: 150 },
      { seq: 4, name: "现场服务", trigger: "竣工验收", ratio: 20, offset_days: 700 },
    ],
  },
  { id: "nt3", name: "检测费用模板", fee_type: "检测", is_builtin: true, status: "active",
    nodes_def: [
      { seq: 1, name: "进场检测", trigger: "检测进场", ratio: 30, offset_days: 0 },
      { seq: 2, name: "中期检测", trigger: "主体完成", ratio: 40, offset_days: 180 },
      { seq: 3, name: "完工检测", trigger: "竣工验收", ratio: 30, offset_days: 600 },
    ],
  },
];

// ========== 知识库 ==========
export const mockKnowledgeDocs = [
  { id: "kd1", doc_name: "施工总承包合同.pdf", project_id: "p1", doc_type: "合同", file_size: 2540000, chunk_count: 48, parse_status: "completed", summary: "1-6号粮仓新建工程施工总承包合同", uploader_name: "王工", upload_time: "2025-06-15" },
  { id: "kd2", doc_name: "粮仓建筑设计图纸.pdf", project_id: "p1", doc_type: "图纸", file_size: 12800000, chunk_count: 120, parse_status: "completed", summary: "全套施工图纸", uploader_name: "张工", upload_time: "2025-05-20" },
];

// ========== AI ==========
export const mockAISessions = [
  { id: "cs1", title: "3号粮仓温度问题分析", project_id: "p1", created_at: "2026-06-30 14:30" },
];
export const mockTrendData = {
  months: ["1月","2月","3月","4月","5月","6月"],
  indicators: [
    { name: "完成产值(万元)", data: [750, 880, 1150, 1050, 1250, 1400] },
    { name: "累计完成率(%)", data: [15, 28, 45, 58, 72, 87] },
  ],
  conclusion: "近期完成产值6月达1400万元，整体趋势向上，累计完成率87%。",
};
export const mockRisks = [
  { id: "r1", level: "high", type: "进度风险", description: "1-6号粮仓工程实际72%低于计划75%，偏差-3%", target: "1-6号粮仓", suggestion: "增加施工作业面，关注7月雨季", status: "unprocessed" },
  { id: "r2", level: "medium", type: "资料缺失", description: "智能通风项目本周无进度报告", target: "智能通风系统", suggestion: "催促施工单位补充", status: "processing" },
];

// ========== 驾驶舱 ==========
export const mockCockpitOverview = {
  active_projects: 4, total_investment: 401000000, total_paid: 248000000,
  avg_progress: 49, monthly_output: 38600000, pending_audits: 2,
  risk_count: 2, data_completeness: 78,
  project_distribution: [
    { province: "河南省-郑州", count: 2, lat: 34.75, lng: 113.62 },
    { province: "河南省-洛阳", count: 1, lat: 34.62, lng: 112.45 },
    { province: "河南省-周口", count: 1, lat: 33.62, lng: 114.65 },
    { province: "河南省-南阳", count: 1, lat: 32.99, lng: 112.53 },
  ],
  status_pie: [
    { name: "在建", value: 3, color: "#1677ff" },
    { name: "筹备中", value: 1, color: "#999" },
    { name: "已完工", value: 1, color: "#52c41a" },
  ],
};

export const mockSCurveData = {
  months: ["2025-06","2025-08","2025-10","2025-12","2026-02","2026-04","2026-06","2026-08","2026-10","2026-12","2027-02","2027-03"],
  planned: [5,12,22,35,48,58,65,72,80,88,95,100],
  actual: [5,11,20,32,45,55,60,0,0,0,0,0],
  cumulative_planned: [5,12,22,35,48,58,65,72,80,88,95,100],
  cumulative_actual: [5,11,20,32,45,55,60,0,0,0,0,0],
};

export const mockInvestmentData = {
  months: ["1月","2月","3月","4月","5月","6月"],
  contract_total: 125000000,
  completed: 90000000,
  paid: 75000000,
  pending_audit: 15000000,
  unpaid: 35000000,
  monthly_investment: [650, 720, 980, 850, 1100, 1200],
  cumulative_investment: [650, 1370, 2350, 3200, 4300, 5500],
  forecast: [1250, 1300, 1350],
};

// ========== 字段映射 ==========
export const mockFieldMappings = [
  { id: "m1", name: "Excel 工程量清单", project_id: null, file_format: "xlsx", header_row: 1, sheet_index: 0, status: "active", creator_name: "管理员", created_at: "2026-05-01",
    rules: [
      { user_header: "施工日期", system_field: "data_date", converter: "iso_date" },
      { user_header: "分部工程", system_field: "category", converter: "category_alias_to_canonical" },
      { user_header: "分项名称", system_field: "item_name", converter: "passthrough" },
      { user_header: "完成数量", system_field: "actual_quantity", converter: "passthrough" },
      { user_header: "单价(元)", system_field: "unit_price", converter: "yuan_to_fen" },
      { user_header: "合价(元)", system_field: "amount", converter: "yuan_to_fen" },
      { user_header: "单位", system_field: "unit", converter: "passthrough" },
      { user_header: "费用类别", system_field: "cost_type", converter: "category_alias_to_canonical" },
    ],
  },
  { id: "m2", name: "监理月报", project_id: null, file_format: "xlsx", header_row: 1, sheet_index: 0, status: "active", creator_name: "管理员", created_at: "2026-05-15", rules: [] },
  { id: "m3", name: "进度款申报", project_id: null, file_format: "xlsx", header_row: 1, sheet_index: 0, status: "active", creator_name: "管理员", created_at: "2026-05-20", rules: [] },
];

// ========== 系统字段列表（后端预置） ==========
export const SYSTEM_FIELDS = [
  { value: "data_date", label: "数据日期 (data_date)" },
  { value: "category", label: "分部类别 (category)" },
  { value: "item_name", label: "分项名称 (item_name)" },
  { value: "planned_quantity", label: "计划工程量 (planned_quantity)" },
  { value: "actual_quantity", label: "实际工程量 (actual_quantity)" },
  { value: "unit", label: "单位 (unit)" },
  { value: "unit_price", label: "单价 (unit_price)" },
  { value: "amount", label: "金额 (amount)" },
  { value: "cost_type", label: "费用类型 (cost_type)" },
  { value: "source_doc", label: "来源文档 (source_doc)" },
  { value: "source_type", label: "来源类型 (source_type)" },
];

// ========== 转换器列表（后端预置） ==========
export const CONVERTERS = [
  { value: "passthrough", label: "直通 (passthrough)" },
  { value: "yuan_to_fen", label: "元→分 (yuan_to_fen)" },
  { value: "wan_yuan_to_fen", label: "万元→分 (wan_yuan_to_fen)" },
  { value: "chinese_date_to_iso", label: "中文日期→ISO (chinese_date_to_iso)" },
  { value: "excel_serial_to_date", label: "Excel序列→日期 (excel_serial_to_date)" },
  { value: "iso_date", label: "ISO日期 (iso_date)" },
  { value: "decimal_to_base_unit:ton", label: "小数→基本单位:t (decimal_to_base_unit:ton)" },
  { value: "category_alias_to_canonical", label: "类别别名→标准 (category_alias_to_canonical)" },
  { value: "trim", label: "去空格 (trim)" },
  { value: "lowercase", label: "转小写 (lowercase)" },
];

// ========== 提醒设置 ==========
export const mockReminderSettings = {
  default_days: 7,
  channels: ["站内信"],
  remind_time: "09:00",
  contract_overrides: [
    { contract_id: "sc1", contract_name: "监理服务合同", days: 14, channels: ["站内信", "邮件"] },
  ],
  history: [
    { id: "rh1", time: "2026-06-30 09:00", node_name: "中期监理费", contract_name: "监理服务合同", channel: "站内信", status: "已发送" },
    { id: "rh2", time: "2026-06-23 09:00", node_name: "中期检测", contract_name: "质量检测合同", channel: "站内信", status: "已发送" },
  ],
};

// ========== 工具函数 ==========
export const formatYuan = (fen: number) => (fen / 100).toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
export const yuanToFen = (yuan: number) => Math.round(yuan * 100);
