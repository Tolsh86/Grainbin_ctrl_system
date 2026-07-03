-- ============================================================
-- 粮仓过控平台 — 业务流程测试数据
-- 场景：川西现代粮食物流中心建设项目，2026年1月~7月
-- 目的：检验表结构、外键关系、字段设计是否合理
-- ============================================================

BEGIN;

-- ============================================================
-- 一、字典初始数据
-- ============================================================

INSERT INTO dict_project_nature (code, name, sort_order) VALUES
    ('functional', '功能性项目', 1),
    ('commercial', '商业性项目', 2);

INSERT INTO dict_invest_timing (code, name, sort_order) VALUES
    ('new', '新投项目', 1),
    ('continuing', '续投项目', 2);

INSERT INTO dict_invest_nature (code, name, sort_order) VALUES
    ('fixed_asset', '固定资产投资', 1),
    ('equity', '股权投资', 2),
    ('other', '其他投资', 3);

INSERT INTO dict_invest_structure (code, name, sort_order) VALUES
    ('infrastructure', '基础设施类', 1),
    ('livelihood', '民生和社会事业类', 2),
    ('eco_environment', '生态环保类', 3);

INSERT INTO dict_invest_field (code, name, sort_order) VALUES
    ('equipment_mfg', '装备制造', 1),
    ('food_beverage', '食品饮料', 2),
    ('material_chemical', '材料化工', 3);

INSERT INTO dict_project_level (code, name, sort_order) VALUES
    ('province_key', '省重点项目', 1),
    ('city_key', '市重点项目', 2),
    ('province_sub', '省重点项目子项', 3);

INSERT INTO dict_review_type (code, name, sort_order) VALUES
    ('equipment', '设备', 1),
    ('design', '设计', 2),
    ('construction', '施工', 3),
    ('supervision', '监理过控', 4);

INSERT INTO dict_location (code, name, sort_order) VALUES
    ('power_unit', '电力单位', 1),
    ('pile_unit', '桩基单位', 2),
    ('general_flat', '总平单位', 3),
    ('work_tower', '工作塔区域', 4),
    ('warehouse_5', '5#平房仓', 5),
    ('warehouse_6', '6#平房仓', 6),
    ('quality_bldg', '质检楼区域', 7),
    ('oil_tank', '油罐区', 8),
    ('shallow_silo', '浅圆仓', 9),
    ('wall_constr', '围墙施工', 10),
    ('crane', '塔吊工程', 11);

INSERT INTO dict_owner_unit (code, name, sort_order) VALUES
    ('chantou', '产投集团', 1),
    ('fazhan', '发展集团', 2),
    ('shangtou', '商投集团', 3),
    ('chengfa', '城发集团', 4),
    ('jiangong', '建工集团', 5);

INSERT INTO dict_supplier (code, name, sort_order) VALUES
    ('jixin', '四川锦鑫川荣工程咨询有限公司', 1),
    ('dazheng', '重庆大正建设工程经济技术有限公司', 2),
    ('zhongrui', '中资锐诚工程项目管理有限公司', 3),
    ('luojiang', '德阳市罗江区自然资源和规划局', 4),
    ('zhongchuliang', '中储粮成都储藏研究院有限公司', 5),
    ('doulin', '四川都林工程咨询有限公司', 6),
    ('zhuoli', '四川卓立建设工程咨询有限公司', 7),
    ('deyangjiangong', '德阳建设工程集团有限公司', 8),
    ('zhongjixie', '中国机械工业建设集团有限公司', 9),
    ('zhongkaijuncheng', '中凯俊成建设咨询有限公司', 10);

-- ============================================================
-- 二、用户数据
-- ============================================================

INSERT INTO t_users (id, username, password_hash, real_name, email, role) VALUES
    ('a0000000-0000-0000-0000-000000000001', 'admin',   '$2b$12$dummy', '系统管理员', 'admin@grainbin.com',   'admin'),
    ('a0000000-0000-0000-0000-000000000002', 'zhangwei','$2b$12$dummy', '张伟',       'zhangwei@grainbin.com', 'project_manager'),
    ('a0000000-0000-0000-0000-000000000003', 'liming',  '$2b$12$dummy', '李明',       'liming@grainbin.com',   'auditor'),
    ('a0000000-0000-0000-0000-000000000004', 'wangfang','$2b$12$dummy', '王芳',       'wangfang@grainbin.com', 'operator');

-- ============================================================
-- 三、项目数据（川西现代粮食物流中心）
-- ============================================================

INSERT INTO t_projects (id, project_name, project_code, project_nature, invest_timing,
    invest_nature, invest_structure, invest_field, implement_body, implement_period,
    business_class, region, importance, supervising_dept, project_level_remark,
    responsible_unit, construction_content, construction_scale, construction_period,
    planned_total_invest, planned_invest_2026, owner_unit, quality_target, safety_target,
    expected_return, project_status)
VALUES (
    'b0000000-0000-0000-0000-000000000001',
    '川西现代粮食物流中心建设项目',
    'XM-2025-001',
    '功能性项目',
    '续投项目',
    '固定资产投资',
    '民生和社会事业类',
    '/',
    '产投集团',
    '2025.12-2027.11',
    '主业',
    '市内',
    '▲',
    '德阳市发展与改革局',
    '市重点项目',
    '罗江区人民政府',
    '新建7.25万吨高标准粮仓，其中浅圆仓5.25万吨，低温平房仓2万吨，配套建设卸粮棚、工作塔、仓间罩棚；新建4600吨食用油罐，配套建设油泵房、发油棚；新建质检楼，配套建设附属总平工程；仓顶阳光及附属设施。',
    '平房仓共2栋；浅圆仓共7座；油罐共5座；质检综合楼1座；器材库（含机修间）、仓间罩棚、药品库、公厕、油泵房、大门、地磅、工作塔、卸粮棚、辅助用房等设备设施及总图的道路、消防、给排水以及供配电等工程',
    '600天',
    1932033000000,   -- 19320.33万元 → 分
    750000000000,    -- 7500万元 → 分
    '四川德阳省食油储备库',
    '合格',
    '不发生一般及以上的安全事故',
    '功能性项目：通过承担省市两级政府政策性粮食储备业务实现资金平衡',
    'constructing'
);

-- ============================================================
-- 四、合同 → 支付阶段 → 月度明细 → 支付记录
-- ============================================================

-- 4.1 合同1: CX005 设计合同（3阶段支付）
INSERT INTO t_contracts (id, project_id, seq, contract_no, supplier_name, contract_desc,
    sign_date, contract_amount, contract_type, status)
VALUES (
    'c0000000-0000-0000-0000-000000000001',
    'b0000000-0000-0000-0000-000000000001',
    5, 'CX005', '中储粮成都储藏研究院有限公司',
    '建设工程勘察、初设设计服务合同',
    '2025-08-11', 19371600000,  -- 193.716万元 = 设计合同
    'secondary', 'active'
);

-- CX005 支付阶段（4个阶段，stage_order=0 是汇总行）
INSERT INTO t_contract_payment_stages (contract_id, contract_no, stage_order, stage_name, payment_terms, cumulative_paid, remaining_unpaid, paid_ratio) VALUES
    ('c0000000-0000-0000-0000-000000000001', 'CX005', 0, '汇总', NULL, 38743200, 18984376800, 0.0020),
    ('c0000000-0000-0000-0000-000000000001', 'CX005', 1, '施工前阶段', '合同签订后30日内，支付合同暂定设计价的20%(预付款)', NULL, NULL, NULL),
    ('c0000000-0000-0000-0000-000000000001', 'CX005', 2, '施工中阶段', '提交方案设计资料并经过相关行政主管部门审批通过后15个工作日内，支付合同暂定设计价的30%', NULL, NULL, NULL),
    ('c0000000-0000-0000-0000-000000000001', 'CX005', 3, '竣工阶段', '提交初步设计资料并通过初设评审且取得第三方概算审核批复后的15工作日内，支付至合同金额的80%', NULL, NULL, NULL),
    ('c0000000-0000-0000-0000-000000000001', 'CX005', 4, '尾款阶段', '剩余尾款在项目竣工及财评审核后支付。设计费最终结算价不得超过签约合同价。', NULL, NULL, NULL);

-- CX005 逐笔支付记录
INSERT INTO t_contract_payments (contract_id, contract_no, payment_date, payment_amount, payment_voucher, payer, payee, remark) VALUES
    ('c0000000-0000-0000-0000-000000000001', 'CX005',
     '2026-01-15', 38743200, 'PAY-2026-001', '四川德阳省食油储备库', '中储粮成都储藏研究院有限公司',
     '第一期进度款-设计费20%');

-- CX005 月度明细（2026年1~6月）
INSERT INTO t_contract_monthly_detail (contract_id, contract_no, detail_month, payment_amount, output_amount, cumulative_completed) VALUES
    ('c0000000-0000-0000-0000-000000000001', 'CX005', '2026-01-01', 38743200, 38743200, 38743200),
    ('c0000000-0000-0000-0000-000000000001', 'CX005', '2026-02-01', 0, 0, 38743200),
    ('c0000000-0000-0000-0000-000000000001', 'CX005', '2026-03-01', 0, 0, 38743200),
    ('c0000000-0000-0000-0000-000000000001', 'CX005', '2026-04-01', 0, 0, 38743200),
    ('c0000000-0000-0000-0000-000000000001', 'CX005', '2026-05-01', 0, 0, 38743200),
    ('c0000000-0000-0000-0000-000000000001', 'CX005', '2026-06-01', 0, 0, 38743200);

-- 4.2 合同2: CX008 EPC施工合同（5阶段支付）
INSERT INTO t_contracts (id, project_id, seq, contract_no, supplier_name, contract_desc,
    sign_date, contract_amount, contract_type, status)
VALUES (
    'c0000000-0000-0000-0000-000000000002',
    'b0000000-0000-0000-0000-000000000001',
    8, 'CX008', '德阳建设工程集团有限公司',
    '建设安装工程',
    '2025-11-26', 1317298500000,  -- 13172.985万元
    'main', 'active'
);

INSERT INTO t_contract_payment_stages (contract_id, contract_no, stage_order, stage_name, payment_terms) VALUES
    ('c0000000-0000-0000-0000-000000000002', 'CX008', 1, '施工前阶段', NULL),
    ('c0000000-0000-0000-0000-000000000002', 'CX008', 2, '施工中阶段', '(1)按月进度支付，按每月已完成的实际产值的80%进行支付'),
    ('c0000000-0000-0000-0000-000000000002', 'CX008', 3, '竣工阶段', '工程竣工验收合格后30日内，支付至结算总价的90%'),
    ('c0000000-0000-0000-0000-000000000002', 'CX008', 4, '结算后阶段', '工程完成财务决算后，支付至决算金额的97%'),
    ('c0000000-0000-0000-0000-000000000002', 'CX008', 5, '质保尾款阶段', '剩余3%作为质保金，缺陷责任期满后无息支付');

-- CX008 月度明细（每月实际产值递增，模拟施工进度）
INSERT INTO t_contract_monthly_detail (contract_id, contract_no, detail_month, payment_amount, output_amount, cumulative_completed) VALUES
    ('c0000000-0000-0000-0000-000000000002', 'CX008', '2026-01-01', 10526301846, 15000000000, 15000000000),
    ('c0000000-0000-0000-0000-000000000002', 'CX008', '2026-02-01', 0, 15000000000, 30000000000),
    ('c0000000-0000-0000-0000-000000000002', 'CX008', '2026-03-01', 0, 30000000000, 60000000000),
    ('c0000000-0000-0000-0000-000000000002', 'CX008', '2026-04-01', 0, 50000000000, 110000000000),
    ('c0000000-0000-0000-0000-000000000002', 'CX008', '2026-05-01', 0, 80000000000, 190000000000),
    ('c0000000-0000-0000-0000-000000000002', 'CX008', '2026-06-01', 0, 80000000000, 270000000000);

INSERT INTO t_contract_payments (contract_id, contract_no, payment_date, payment_amount, payment_voucher, remark) VALUES
    ('c0000000-0000-0000-0000-000000000002', 'CX008', '2026-01-25', 10526301846, 'PAY-2026-002', '第一期进度款-含农民工工资2572409.12元');

-- ============================================================
-- 五、进度款审核链路（4 类审核各1条）
-- ============================================================

-- 5.1 设备单位审核
INSERT INTO t_progress_payment_review (project_id, contract_id, review_type, period_month, period_no,
    applicant_unit, contract_amount, cumulative_reported_output, payment_ratio,
    current_audited_output, cumulative_audited_output, cumulative_audited_payable,
    tax_rate, remark, audit_status, submit_date)
VALUES (
    'b0000000-0000-0000-0000-000000000001', NULL,
    '设备', '第一期/2026年01月', 1,
    '中国机械工业建设集团有限公司',
    325644300000,  -- 3256.443万元
    65128860000,   -- 651.2886万元
    0.20,
    65128860000,
    65128860000,
    65128860000,
    9.00,
    '以上金额均为含税金额，税率为9%',
    'audited', '2026-01-10'
);

-- 5.2 设计单位审核
INSERT INTO t_progress_payment_review (project_id, contract_id, review_type, period_month, period_no,
    applicant_unit, contract_amount, cumulative_reported_output, payment_ratio,
    current_audited_output, cumulative_audited_output, cumulative_audited_payable,
    tax_rate, remark, audit_status, submit_date)
VALUES (
    'b0000000-0000-0000-0000-000000000001', NULL,
    '设计', '第一期/2026年01月', 1,
    '中储粮成都储藏研究院有限公司',
    19371600000,
    3874320000,
    0.20,
    3874320000,
    3874320000,
    3874320000,
    6.00,
    '以上金额均为含税金额，税率为6%',
    'audited', '2026-01-10'
);

-- 5.3 施工单位审核（含建安费+安全文明费特有字段）
INSERT INTO t_progress_payment_review (project_id, contract_id, review_type, period_month, period_no,
    applicant_unit, contract_amount, cumulative_reported_output,
    constr_install_fee, safety_civil_fee,
    constr_install_pay_ratio, safety_civil_pay_ratio,
    current_audited_output, cumulative_audited_output, cumulative_audited_payable,
    tax_rate, remark, audit_status, submit_date)
VALUES (
    'b0000000-0000-0000-0000-000000000001', 'c0000000-0000-0000-0000-000000000002',
    '施工', '第一期/2026年01月', 1,
    '德阳建设工程集团有限公司',
    13172985000000,
    1052630184600,
    9722826000000,   -- 建筑安装工程费
    53565056400,     -- 安全文明施工费
    0.10, 0.50,
    1052630184600,
    1052630184600,
    1052630184600,
    9.00,
    '农民工工资专用账户：9187175.44*28%=2572409.12元；基本账户：7953892.73元',
    'audited', '2026-01-10'
);

-- 5.4 监理过控单位审核（含监理费+造价咨询费+结算费特有字段）
INSERT INTO t_progress_payment_review (project_id, contract_id, review_type, period_month, period_no,
    applicant_unit, contract_amount, cumulative_reported_output,
    supervision_fee, cost_consult_fee, settlement_fee,
    supervision_pay_ratio, cost_consult_pay_ratio, settlement_pay_ratio,
    current_audited_output, cumulative_audited_output, cumulative_audited_payable,
    tax_rate, remark, audit_status, submit_date)
VALUES (
    'b0000000-0000-0000-0000-000000000001', NULL,
    '监理过控', '第一期/2026年01月', 1,
    '中凯俊成建设咨询有限公司',
    30407400000,
    4576950000,
    18697500000,  -- 工程监理服务费
    8057700000,   -- 造价咨询服务费
    3652200000,   -- 竣工结算服务费
    0.10, 0.20, 0.30,
    4576950000,
    4576950000,
    4576950000,
    6.00,
    '以上金额均为含税金额，税率为6%',
    'audited', '2026-01-10'
);

-- ============================================================
-- 六、周报数据（2026年7月1日周报）
-- ============================================================

-- 6.1 形象进度（每个工程部位一行）
INSERT INTO t_weekly_progress_report (project_id, report_date, seq, location_name, weekly_progress_desc,
    weekly_output_reported, weekly_output_audited, cumulative_output_reported, cumulative_output_audited,
    type2_expense, total_amount, cumulative_progress_desc, review_date)
VALUES
    ('b0000000-0000-0000-0000-000000000001', '2026-07-01', 1, '电力单位',   '强电管线施工已完成90%，电缆敷设进行中', 0, 0, NULL, NULL, NULL, NULL, '电力工程总进度85%', '2026-07-01'),
    ('b0000000-0000-0000-0000-000000000001', '2026-07-01', 2, '桩基单位',   '101~204#浅圆仓桩基已全部完成，承载力检测合格', 0, 0, NULL, NULL, NULL, NULL, '桩基工程100%完成', '2026-07-01'),
    ('b0000000-0000-0000-0000-000000000001', '2026-07-01', 3, '总平单位',   '室外道路完成60%，围墙施工完成100%，给排水管线铺设70%', 0, 0, NULL, NULL, NULL, NULL, '总平工程进度60%', '2026-07-01'),
    ('b0000000-0000-0000-0000-000000000001', '2026-07-01', 4, '工作塔区域', '工作塔主体施工完成50%，卸粮棚基础完成100%', 0, 0, NULL, NULL, NULL, NULL, '工作塔区域进度50%', '2026-07-01'),
    ('b0000000-0000-0000-0000-000000000001', '2026-07-01', 5, '5#平房仓',   '基础混凝土浇筑完成100%，地面混凝土开始施工', 0, 0, NULL, NULL, NULL, NULL, '5#平房仓基础完成', '2026-07-01'),
    ('b0000000-0000-0000-0000-000000000001', '2026-07-01', 6, '6#平房仓',   '土方开挖完成100%，垫层完成80%，基础钢筋绑扎中', 0, 0, NULL, NULL, NULL, NULL, '6#平房仓基础施工中', '2026-07-01'),
    ('b0000000-0000-0000-0000-000000000001', '2026-07-01', 7, '质检楼区域', '质检楼主体完成100%，装饰装修完成30%', 0, 0, NULL, NULL, NULL, NULL, '质检楼主体封顶', '2026-07-01'),
    ('b0000000-0000-0000-0000-000000000001', '2026-07-01', 8, '油罐区',     '油泵房基础完成100%，油罐区土方完成100%', 0, 0, NULL, NULL, NULL, NULL, '油罐区基础完成', '2026-07-01'),
    ('b0000000-0000-0000-0000-000000000001', '2026-07-01', 9, '浅圆仓',     '101~103#筒体已完成，201~204#筒体施工50%', 0, 0, NULL, NULL, NULL, NULL, '浅圆仓筒体施工中', '2026-07-01'),
    ('b0000000-0000-0000-0000-000000000001', '2026-07-01', 10, '围墙施工',  '围墙施工已完成100%', 0, 0, NULL, NULL, NULL, NULL, '围墙施工完毕', '2026-07-01'),
    ('b0000000-0000-0000-0000-000000000001', '2026-07-01', 11, '塔吊工程',  '3台塔吊已全部安装完成并验收合格', 0, 0, NULL, NULL, NULL, NULL, '塔吊工程完成', '2026-07-01');

-- 6.2 投资指标（K-V结构，模拟7月1日周报的12个指标）
INSERT INTO t_weekly_progress_metrics (project_id, report_week, data_scope, metric_name, metric_value) VALUES
    ('b0000000-0000-0000-0000-000000000001', '2026-07-01', '标准口径', '项目总投资', 19320.33),
    ('b0000000-0000-0000-0000-000000000001', '2026-07-01', '标准口径', '2026年度计划投资', 7500),
    ('b0000000-0000-0000-0000-000000000001', '2026-07-01', '标准口径', '2026年度已完成投资', 2610),
    ('b0000000-0000-0000-0000-000000000001', '2026-07-01', '标准口径', '其中：建安工程费', 2365.4),
    ('b0000000-0000-0000-0000-000000000001', '2026-07-01', '标准口径', '其中：二类费用', 244.6),
    ('b0000000-0000-0000-0000-000000000001', '2026-07-01', '标准口径', '本周完成建安投资', 93.5),
    ('b0000000-0000-0000-0000-000000000001', '2026-07-01', '标准口径', '本周二类费用完成金额', 0),
    ('b0000000-0000-0000-0000-000000000001', '2026-07-01', '标准口径', '上周完成建安投资', 2271.9),
    ('b0000000-0000-0000-0000-000000000001', '2026-07-01', '标准口径', '上周二类费用完成金额', 244.6),
    ('b0000000-0000-0000-0000-000000000001', '2026-07-01', '标准口径', '本周建设安装工程完成本年度计划（百分比）', 0.01247),
    ('b0000000-0000-0000-0000-000000000001', '2026-07-01', '标准口径', '年度完成本年度计划投资（百分比）', 0.348),
    ('b0000000-0000-0000-0000-000000000001', '2026-07-01', '标准口径', '年度完成项目计划总投资（百分比）', 0.1351);

-- ============================================================
-- 七、月报数据（省市重点项目6月进度 + 月度目标计划 + 资金分解）
-- ============================================================

-- 7.1 省市重点项目6月进度（川西项目）
INSERT INTO t_monthly_province_progress (project_id, report_month, seq, project_name,
    construction_period, construction_scale,
    planned_total_invest, cumulative_invest_by_2025, planned_invest_2026,
    completed_invest_1_5m, completed_invest_6m, completed_invest_1_6m,
    completion_rate, progress_apr, progress_jun, progress_target_2026,
    owner_unit, responsible_unit, remark)
VALUES (
    'b0000000-0000-0000-0000-000000000001', '2026-06-01', 1,
    '川西现代粮食物流中心建设项目',
    '2025-2027年',
    '平房仓共2栋；浅圆仓共7座；油罐共5座；质检综合楼1座；器材库、仓间罩棚、药品库、公厕、油泵房、大门、地磅、工作塔、卸粮棚、辅助用房等',
    1932033000000,   -- 19320.33万元
    1000000000000,   -- 截至2025年底累计
    750000000000,    -- 2026年预计
    229101000000,    -- 1-5月完成
    50000000000,     -- 6月单月完成
    279101000000,    -- 1-6月累计
    0.3721,
    '1.工作塔桩完成100%；2.综合楼桩完成100%；3.101~103#基础完成；4.5#、6#平房仓基础完成100%',
    '1.5#、6#土方开挖完成100%；垫层完成80%；2.6#平房仓基础垫层浇筑完成90%，基础开始绑扎钢筋',
    '1.浅圆仓完成60%；2.质检楼主体完成100%，装饰装修完成30%；3.工作塔、卸粮棚、辅助用房完成60%',
    '四川德阳省食油储备库',
    '罗江区人民政府',
    '省重点项目'
);

-- 7.2 月度目标计划（1~6月）
INSERT INTO t_monthly_target_plan (project_id, plan_month, monthly_planned_invest, monthly_planned_progress) VALUES
    ('b0000000-0000-0000-0000-000000000001', '2026-01-01', 15000000000, '完成施工图预算编制；临时设施建设完成50%；电力工程施工；试桩完成3根'),
    ('b0000000-0000-0000-0000-000000000001', '2026-02-01', 15000000000, '试桩检测；临时设施完成100%；工作塔降水井70%；工作塔护壁桩100%'),
    ('b0000000-0000-0000-0000-000000000001', '2026-03-01', 30000000000, '工作塔降水井完成100%；综合楼降水井完成100%；101~103#浅圆仓桩完成100%'),
    ('b0000000-0000-0000-0000-000000000001', '2026-04-01', 50000000000, '工作塔土方开挖完成100%；5#6#平房仓土方完成100%；器材库土方开挖完成100%'),
    ('b0000000-0000-0000-0000-000000000001', '2026-05-01', 80000000000, '工作塔桩完成100%；综合楼桩完成100%；5#6#平房仓基础完成100%'),
    ('b0000000-0000-0000-0000-000000000001', '2026-06-01', 80000000000, '工作塔基础完成100%；综合楼基础完成100%；101~103#浅圆仓筒体完成');

-- 7.3 资金来源分解（总投资 + 2026年度计划）
INSERT INTO t_fund_breakdown (project_id, fund_year, fund_scope,
    central_province_fund, special_general_bond, national_bond_fund,
    self_owned_fund, financing_fund, other_fund,
    cumulative_completed_invest, annual_planned_invest)
VALUES
    ('b0000000-0000-0000-0000-000000000001', 2026, 'total',
     0, 0, 0, 1932033000000, 0, 0,  -- 总投资全部为自有资金
     279101000000, NULL),
    ('b0000000-0000-0000-0000-000000000001', 2026, 'annual_plan',
     0, 0, 0, 750000000000, 0, 0,   -- 年度计划全部为自有资金
     NULL, 750000000000);

-- ============================================================
-- 八、数据上传 → AI解析链路
-- ============================================================

-- 8.1 字段映射配置（预置：工程量清单模板）
INSERT INTO t_field_mappings (id, mapping_name, file_format, header_row, rules, is_active) VALUES (
    'd0000000-0000-0000-0000-000000000001',
    'Excel工程量清单标准表头', 'xlsx', 1,
    '[
        {"user_header": "序号",        "system_field": "seq",            "converter": null},
        {"user_header": "分项名称",    "system_field": "item_name",      "converter": null},
        {"user_header": "单位",        "system_field": "unit",           "converter": null},
        {"user_header": "计划数量",    "system_field": "planned_quantity","converter": null},
        {"user_header": "实际数量",    "system_field": "actual_quantity", "converter": null},
        {"user_header": "单价(元)",    "system_field": "unit_price",      "converter": "yuan_to_fen"},
        {"user_header": "合价(元)",    "system_field": "amount",          "converter": "yuan_to_fen"},
        {"user_header": "费用类型",    "system_field": "cost_type",       "converter": null}
    ]'::jsonb,
    true
);

-- 8.2 上传批次（模拟上传一份施工单位Excel）
INSERT INTO t_ingest_batches (id, project_id, source_doc, source_path, source_type, file_format,
    period_start, period_end, mapping_id, total_rows, parsed_rows, valid_rows, error_rows,
    quality_score, status, uploaded_by)
VALUES (
    'e0000000-0000-0000-0000-000000000001',
    'b0000000-0000-0000-0000-000000000001',
    '川西项目_2026年6月_建安产值上报.xlsx',
    'minio://grainbin/uploads/2026/06/chuanxi_jianan_202606.xlsx',
    'upload', 'xlsx',
    '2026-06-01', '2026-06-30',
    'd0000000-0000-0000-0000-000000000001',
    12, 12, 10, 2, 83.33,
    'review',
    'a0000000-0000-0000-0000-000000000004'
);

-- 8.3 清洗明细行（模拟AI解析后的行数据，含不同校验状态）
INSERT INTO t_ingest_rows (batch_id, row_no, raw_payload, normalized, mapped,
    project_id, data_date, category, item_name, planned_quantity, actual_quantity,
    unit, unit_price, amount, cost_type,
    validation_flags, validation_status, quality_score, is_valid)
VALUES
    -- 行1: 通过
    ('e0000000-0000-0000-0000-000000000001', 1,
     '{"序号":"1","分项":"混凝土C30","单位":"m³","数量":"500","单价":"450"}',
     '{"seq":1,"item":"混凝土C30","unit":"m³","qty":500,"price":450}',
     '{"item_name":"混凝土C30","unit":"m³","actual_quantity":500,"unit_price":45000,"amount":22500000}',
     'b0000000-0000-0000-0000-000000000001', '2026-06-30',
     '主体结构', '混凝土C30', 500, 500, 'm³', 4500000, 2250000000, '建安工程费',
     '[{"rule":"required_check","level":"info","message":"必填项全部通过"}]', 'normal', 100.00, true),
    -- 行2: 通过
    ('e0000000-0000-0000-0000-000000000001', 2,
     '{"序号":"2","分项":"钢筋HRB400","单位":"t","数量":"120","单价":"4200"}',
     '{"seq":2,"item":"钢筋HRB400","unit":"t","qty":120,"price":4200}',
     '{"item_name":"钢筋HRB400","unit":"t","actual_quantity":120,"unit_price":420000,"amount":50400000}',
     'b0000000-0000-0000-0000-000000000001', '2026-06-30',
     '主体结构', '钢筋HRB400', 120, 120, 't', 42000000, 5040000000, '建安工程费',
     '[{"rule":"required_check","level":"info","message":"必填项全部通过"}]', 'normal', 100.00, true),
    -- 行3: warning（金额超出合理范围）
    ('e0000000-0000-0000-0000-000000000001', 3,
     '{"序号":"3","分项":"钢结构安装","单位":"t","数量":"80","单价":"15000"}',
     '{"seq":3,"item":"钢结构安装","unit":"t","qty":80,"price":15000}',
     '{"item_name":"钢结构安装","unit":"t","actual_quantity":80,"unit_price":1500000,"amount":120000000}',
     'b0000000-0000-0000-0000-000000000001', '2026-06-30',
     '钢结构', '钢结构安装', 80, 80, 't', 150000000, 12000000000, '建安工程费',
     '[{"rule":"amount_range","level":"warning","message":"单价超出历史均值230%，请确认"}]', 'warning', 85.00, true),
    -- 行4: suspicious（AI置信度中等）
    ('e0000000-0000-0000-0000-000000000001', 4,
     '{"序号":"4","分项":"防水工程","单位":"m²","数量":"2000","单价":"35"}',
     '{"seq":4,"item":"防水工程","unit":"m²","qty":2000,"price":35}',
     '{"item_name":"防水工程","unit":"m²","actual_quantity":2000,"unit_price":3500,"amount":7000000}',
     'b0000000-0000-0000-0000-000000000001', '2026-06-30',
     '防水工程', '防水工程', 2000, 2000, 'm²', 350000, 700000000, '建安工程费',
     '[{"rule":"duplicate_check","level":"suspicious","message":"该分项名称与上期相似度92%，可能为连续施工，非重复"}]', 'suspicious', 60.00, false),
    -- 行5: error（必填缺失）
    ('e0000000-0000-0000-0000-000000000001', 5,
     '{"序号":"5","分项":"","单位":"","数量":"","单价":""}',
     '{"seq":5,"item":null,"unit":null,"qty":null,"price":null}',
     '{"item_name":null,"unit":null,"actual_quantity":null,"unit_price":null,"amount":null}',
     'b0000000-0000-0000-0000-000000000001', '2026-06-30',
     NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
     '[{"rule":"required_check","level":"error","message":"分项名称为空，必填缺失"}]', 'error', 0.00, false);

-- 8.4 错误明细（对应行3和行5的详细错误）
INSERT INTO t_ingest_errors (batch_id, row_id, error_stage, error_code, error_message, error_field, error_value, severity, resolved) VALUES
    ('e0000000-0000-0000-0000-000000000001',
     (SELECT id FROM t_ingest_rows WHERE batch_id = 'e0000000-0000-0000-0000-000000000001' AND row_no = 3),
     'validate', 'AMOUNT_OUT_OF_RANGE',
     '钢结构安装单价15000元/t超出同类项目历史均值6,500元/t的230%，请人工确认',
     'unit_price', '15000', 'warning', false),
    ('e0000000-0000-0000-0000-000000000001',
     (SELECT id FROM t_ingest_rows WHERE batch_id = 'e0000000-0000-0000-0000-000000000001' AND row_no = 5),
     'validate', 'REQUIRED_MISSING',
     '分项名称为空，无法匹配到系统字段 item_name',
     'item_name', '', 'error', false);

-- 8.5 确认入库的数据行（从batch中is_valid=true的行转换到t_data_rows）
INSERT INTO t_data_rows (project_id, data_date, category, item_name,
    planned_quantity, actual_quantity, unit, unit_price, amount, cost_type,
    source_doc, source_type, is_confirmed, raw_data)
VALUES
    ('b0000000-0000-0000-0000-000000000001', '2026-06-30', '主体结构', '混凝土C30',
     500, 500, 'm³', 4500000, 2250000000, '建安工程费',
     '川西项目_2026年6月_建安产值上报.xlsx', 'ai', true,
     '{"seq":1,"confidence":0.98,"ai_suggestion":"数值在合理范围内"}'),
    ('b0000000-0000-0000-0000-000000000001', '2026-06-30', '主体结构', '钢筋HRB400',
     120, 120, 't', 42000000, 5040000000, '建安工程费',
     '川西项目_2026年6月_建安产值上报.xlsx', 'ai', true,
     '{"seq":2,"confidence":0.97,"ai_suggestion":"数值在合理范围内"}'),
    ('b0000000-0000-0000-0000-000000000001', '2026-06-30', '钢结构', '钢结构安装',
     80, 80, 't', 150000000, 12000000000, '建安工程费',
     '川西项目_2026年6月_建安产值上报.xlsx', 'ai', true,
     '{"seq":3,"confidence":0.75,"ai_suggestion":"单价异常，需人工确认。已核:市场价12000~18000元/t，本次15000元/t在可接受范围。"}');

-- ============================================================
-- 九、审计日志
-- ============================================================

INSERT INTO t_audit_logs (table_name, record_id, field_name, old_value, new_value, operation_type, modified_by, source) VALUES
    ('t_data_rows', (SELECT id FROM t_data_rows WHERE item_name = '钢结构安装' LIMIT 1),
     'is_confirmed', 'false', 'true', 'CONFIRM',
     'a0000000-0000-0000-0000-000000000003', 'manual');

COMMIT;

-- ============================================================
-- 验证查询
-- ============================================================

-- 1. 合同-支付阶段-支付记录 三表联查
-- SELECT c.contract_no, c.supplier_name,
--        ps.stage_order, ps.stage_name, ps.payment_terms,
--        cp.payment_date, cp.payment_amount, cp.payment_voucher
-- FROM t_contracts c
-- JOIN t_contract_payment_stages ps ON ps.contract_id = c.id
-- LEFT JOIN t_contract_payments cp ON cp.contract_id = c.id
-- WHERE c.contract_no = 'CX005'
-- ORDER BY ps.stage_order;

-- 2. 月度产值汇总（已确认数据）
-- SELECT category, SUM(amount) AS total_amount
-- FROM t_data_rows
-- WHERE project_id = 'b0000000-0000-0000-0000-000000000001'
--   AND is_confirmed = true AND deleted_at IS NULL
-- GROUP BY category;

-- 3. 进度款审核按类型统计
-- SELECT review_type, COUNT(*) AS cnt,
--        SUM(contract_amount) AS total_contract,
--        SUM(cumulative_audited_payable) AS total_payable
-- FROM t_progress_payment_review
-- WHERE project_id = 'b0000000-0000-0000-0000-000000000001'
--   AND audit_status = 'audited'
-- GROUP BY review_type;

-- 4. 批次校验状态分布
-- SELECT validation_status, COUNT(*) AS cnt
-- FROM t_ingest_rows
-- WHERE batch_id = 'e0000000-0000-0000-0000-000000000001'
-- GROUP BY validation_status;

-- ============================================================
-- 十、边界测试数据：禁用字典 + 软删除样本
-- ============================================================

-- 10.1 各字典表插入一条已停用记录
INSERT INTO dict_project_nature (code, name, sort_order, is_active) VALUES
    ('demo_legacy', '历史遗留项目', 99, false);
INSERT INTO dict_invest_timing (code, name, sort_order, is_active) VALUES
    ('unknown', '未知（已废弃）', 99, false);
INSERT INTO dict_invest_nature (code, name, sort_order, is_active) VALUES
    ('deprecated', '已废弃类型', 99, false);
INSERT INTO dict_supplier (code, name, sort_order, is_active) VALUES
    ('old_company', '已注销的旧承包商', 99, false);
INSERT INTO dict_location (code, name, sort_order, is_active) VALUES
    ('old_zone', '已拆除旧区域', 99, false);
INSERT INTO dict_review_type (code, name, sort_order, is_active) VALUES
    ('legacy_audit', '旧版审核（已停用）', 99, false);

-- 10.2 软删除：已作废合同
INSERT INTO t_contracts (id, project_id, seq, contract_no, supplier_name, contract_desc,
    sign_date, contract_amount, contract_type, status, deleted_at)
VALUES (
    'c0000000-0000-0000-0000-000000000099',
    'b0000000-0000-0000-0000-000000000001',
    99, 'CX099', '已注销供应商',
    '已作废的旧合同（测试软删除过滤）',
    '2024-01-01', 0, 'secondary', 'terminated',
    NOW()
);

-- 10.3 软删除：已删除数据行
INSERT INTO t_data_rows (project_id, data_date, category, item_name,
    planned_quantity, actual_quantity, unit, unit_price, amount, cost_type,
    source_doc, source_type, is_confirmed, deleted_at)
VALUES (
    'b0000000-0000-0000-0000-000000000001', '2026-01-01',
    '已删除分类', '已删除分项',
    0, 0, '项', 0, 0, '其他',
    '旧文件.xlsx', 'system', false,
    NOW()
);
