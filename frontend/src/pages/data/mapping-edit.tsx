import { useState } from "react";
import { Card, Form, Input, Select, Button, Table, Space, message, Row, Col, InputNumber, Collapse, Tag, Typography } from "antd";
import { PlusOutlined, DeleteOutlined, UploadOutlined } from "@ant-design/icons";
import { SYSTEM_FIELDS, CONVERTERS } from "../../utils/mock";

const { Text } = Typography;

interface MappingRule {
  id: string;
  user_header: string;
  system_field: string;
  converter: string;
}

const defaultRules: MappingRule[] = [
  { id: "r1", user_header: "施工日期", system_field: "data_date", converter: "iso_date" },
  { id: "r2", user_header: "分部工程", system_field: "category", converter: "category_alias_to_canonical" },
  { id: "r3", user_header: "分项名称", system_field: "item_name", converter: "passthrough" },
  { id: "r4", user_header: "完成数量", system_field: "actual_quantity", converter: "passthrough" },
  { id: "r5", user_header: "单价(元)", system_field: "unit_price", converter: "yuan_to_fen" },
  { id: "r6", user_header: "合价(元)", system_field: "amount", converter: "yuan_to_fen" },
  { id: "r7", user_header: "单位", system_field: "unit", converter: "passthrough" },
  { id: "r8", user_header: "费用类别", system_field: "cost_type", converter: "category_alias_to_canonical" },
];

export default function MappingEdit() {
  const [rules, setRules] = useState<MappingRule[]>(defaultRules);
  const [mappingName, setMappingName] = useState("Excel 工程量清单");
  const [fileFormat, setFileFormat] = useState("xlsx");
  const [headerRow, setHeaderRow] = useState(1);
  const [sheetIndex, setSheetIndex] = useState(0);
  const [status, setStatus] = useState("active");
  const [projectScope, setProjectScope] = useState("global");

  const addRule = () => {
    setRules((prev) => [...prev, { id: `r${Date.now()}`, user_header: "", system_field: "", converter: "passthrough" }]);
  };

  const updateRule = (id: string, field: keyof MappingRule, value: string) => {
    setRules((prev) => prev.map((r) => (r.id === id ? { ...r, [field]: value } : r)));
  };

  const removeRule = (id: string) => {
    if (rules.length <= 1) { message.warning("至少保留一条映射规则"); return; }
    setRules((prev) => prev.filter((r) => r.id !== id));
  };

  const ruleColumns = [
    {
      title: "#", key: "idx", width: 40,
      render: (_: unknown, __: unknown, i: number) => <Text type="secondary">{i + 1}</Text>,
    },
    {
      title: "用户表头（Excel 列名）", dataIndex: "user_header", width: 200,
      render: (v: string, r: MappingRule) => (
        <Input value={v} onChange={(e) => updateRule(r.id, "user_header", e.target.value)}
          size="small" placeholder="如：施工日期" />
      ),
    },
    {
      title: "→ 系统字段", dataIndex: "system_field", width: 220,
      render: (v: string, r: MappingRule) => (
        <Select value={v || undefined} onChange={(val) => updateRule(r.id, "system_field", val)}
          size="small" style={{ width: "100%" }} placeholder="选择系统字段"
          options={SYSTEM_FIELDS} showSearch />
      ),
    },
    {
      title: "转换器", dataIndex: "converter", width: 220,
      render: (v: string, r: MappingRule) => (
        <Select value={v || undefined} onChange={(val) => updateRule(r.id, "converter", val)}
          size="small" style={{ width: "100%" }} placeholder="选择转换器"
          options={CONVERTERS} showSearch />
      ),
    },
    {
      title: "操作", width: 60, align: "center" as const,
      render: (_: unknown, r: MappingRule) => (
        <Button type="text" danger size="small" icon={<DeleteOutlined />}
          onClick={() => removeRule(r.id)} />
      ),
    },
  ];

  const handleSave = () => {
    if (!mappingName.trim()) { message.warning("请输入映射名称"); return; }
    const emptyRule = rules.find(r => !r.user_header || !r.system_field);
    if (emptyRule) { message.warning("请补全所有映射规则的「用户表头」和「系统字段」"); return; }
    message.success(`映射「${mappingName}」保存成功`);
  };

  // 预览数据
  const previewData = [
    { seq: 1, date: "2026-06-24", category: "土建工程", item: "C30混凝土浇筑", qty: 450, price: 680, amount: "306,000", unit: "m³" },
    { seq: 2, date: "2026-06-25", category: "土建工程", item: "HRB400钢筋", qty: 120, price: 5200, amount: "624,000", unit: "t" },
    { seq: 3, date: "2026-06-25", category: "安装工程", item: "钢结构安装", qty: 85, price: 12000, amount: "1,020,000", unit: "t" },
  ];

  return (
    <div>
      {/* 基本信息 */}
      <Card title="基本信息" size="small" style={{ marginBottom: 16 }}>
        <Row gutter={[16, 12]}>
          <Col xs={24} sm={12} md={8}>
            <div style={{ marginBottom: 4, fontWeight: 500 }}>映射名称 <span style={{ color: "#ff4d4f" }}>*</span></div>
            <Input value={mappingName} onChange={(e) => setMappingName(e.target.value)} placeholder="如：Excel 工程量清单" />
          </Col>
          <Col xs={24} sm={12} md={4}>
            <div style={{ marginBottom: 4, fontWeight: 500 }}>适用项目</div>
            <Select value={projectScope} onChange={setProjectScope} style={{ width: "100%" }}
              options={[{ value: "global", label: "通用（所有项目）" }, { value: "p1", label: "1-6号粮仓" }, { value: "p2", label: "7-12号粮仓改造" }]} />
          </Col>
          <Col xs={12} sm={6} md={3}>
            <div style={{ marginBottom: 4, fontWeight: 500 }}>文件格式</div>
            <Select value={fileFormat} onChange={setFileFormat} style={{ width: "100%" }}
              options={[{ value: "xlsx", label: "xlsx" }, { value: "xls", label: "xls" }, { value: "csv", label: "csv" }]} />
          </Col>
          <Col xs={12} sm={6} md={3}>
            <div style={{ marginBottom: 4, fontWeight: 500 }}>表头行号</div>
            <InputNumber value={headerRow} onChange={(v) => setHeaderRow(v || 1)} min={1} max={10} style={{ width: "100%" }} />
          </Col>
          <Col xs={12} sm={6} md={3}>
            <div style={{ marginBottom: 4, fontWeight: 500 }}>Sheet 索引</div>
            <InputNumber value={sheetIndex} onChange={(v) => setSheetIndex(v || 0)} min={0} max={10} style={{ width: "100%" }} />
          </Col>
          <Col xs={12} sm={6} md={3}>
            <div style={{ marginBottom: 4, fontWeight: 500 }}>状态</div>
            <Select value={status} onChange={setStatus} style={{ width: "100%" }}
              options={[{ value: "active", label: "启用" }, { value: "inactive", label: "禁用" }]} />
          </Col>
        </Row>
      </Card>

      {/* 规则编辑区 */}
      <Card
        title="映射规则编辑"
        extra={
          <Space>
            <Text type="secondary" style={{ fontSize: 12 }}>定义 Excel 列 → 系统字段的对应关系</Text>
            <Button type="primary" size="small" icon={<PlusOutlined />} onClick={addRule}>新增规则</Button>
          </Space>
        }
      >
        <Table
          columns={ruleColumns}
          dataSource={rules}
          size="small"
          rowKey="id"
          pagination={false}
          scroll={{ x: 760 }}
          footer={() => (
            <div style={{ fontSize: 12, color: "#999" }}>
              <Text type="secondary">
                提示：系统字段和转换器由后端预置（共 {SYSTEM_FIELDS.length} 个系统字段、{CONVERTERS.length} 个转换器），
                映射规则由用户自定义配置。点击「新增规则」添加一行，输入 Excel 列名并选择对应的系统字段和转换器。
              </Text>
            </div>
          )}
        />
      </Card>

      {/* 预览测试区 */}
      <Collapse style={{ marginTop: 16 }} items={[{
        key: "preview",
        label: "预览测试区 ▼",
        children: (
          <div>
            <Space style={{ marginBottom: 12 }}>
              <Button icon={<UploadOutlined />} onClick={() => message.info("上传示例 Excel 测试解析结果")}>
                上传示例 Excel
              </Button>
              <Text type="secondary" style={{ fontSize: 12 }}>上传示例文件后，系统按当前规则解析前 3 行并显示映射结果</Text>
            </Space>
            <Table
              size="small" pagination={false}
              dataSource={previewData}
              columns={[
                { title: "#", dataIndex: "seq", width: 40 },
                { title: "日期 → data_date", dataIndex: "date", width: 110 },
                { title: "类别 → category", dataIndex: "category", width: 100 },
                { title: "分项 → item_name", dataIndex: "item", width: 140 },
                { title: "工程量 → actual_qty", dataIndex: "qty", width: 80 },
                { title: "单价 → unit_price", dataIndex: "price", width: 80 },
                { title: "金额 → amount", dataIndex: "amount", width: 110 },
                { title: "单位 → unit", dataIndex: "unit", width: 60 },
              ]}
            />
            <div style={{ marginTop: 8 }}>
              {rules.some(r => !r.user_header || !r.system_field) ? (
                <Text style={{ color: "#fa8c16" }}>⚠ 部分映射规则不完整，请补全后测试</Text>
              ) : (
                <Text style={{ color: "#52c41a" }}>✅ 全部规则配置完整，可以进行测试</Text>
              )}
            </div>
          </div>
        ),
      }]} />

      {/* 底部操作 */}
      <div style={{ marginTop: 24, textAlign: "right", borderTop: "1px solid #f0f0f0", paddingTop: 16 }}>
        <Space>
          <Button onClick={() => window.history.back()}>取消</Button>
          <Button onClick={() => message.info("保存并测试")}>保存并测试</Button>
          <Button type="primary" onClick={handleSave}>保存</Button>
        </Space>
      </div>
    </div>
  );
}
