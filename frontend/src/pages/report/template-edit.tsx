import { useState } from "react";
import { Card, Row, Col, Form, Input, Select, Button, Table, Tag, Space, message, InputNumber, Collapse } from "antd";
import { PlusOutlined, DeleteOutlined, EyeOutlined } from "@ant-design/icons";

const mockFields = [
  { id: "f1", key: "progress_desc", label: "本周施工进度描述", type: "text", required: true, unit: "", default: "", formula: "" },
  { id: "f2", key: "completed_value", label: "本周完成产值(元)", type: "number", required: true, unit: "元", default: "", formula: "" },
  { id: "f3", key: "cumulative_value", label: "累计完成产值(元)", type: "formula", required: false, unit: "元", default: "", formula: "上期累计 + 本期完成" },
  { id: "f4", key: "quality_status", label: "质量检查情况", type: "text", required: false, unit: "", default: "", formula: "" },
];

const fieldTypes = [
  { value: "text", label: "text — 文本" },
  { value: "number", label: "number — 数字" },
  { value: "date", label: "date — 日期" },
  { value: "formula", label: "formula — 公式" },
  { value: "reference", label: "reference — 引用" },
];

export default function TemplateEdit() {
  const [fields, setFields] = useState(mockFields);

  const addField = () => {
    setFields((prev) => [...prev, { id: `f${Date.now()}`, key: "", label: "", type: "text", required: false, unit: "", default: "", formula: "" }]);
  };

  const updateField = (id: string, f: string, v: string | boolean) => {
    setFields((prev) => prev.map((r) => (r.id === id ? { ...r, [f]: v } : r)));
  };

  const removeField = (id: string) => setFields((prev) => prev.filter((r) => r.id !== id));

  const cols = [
    { title: "字段 Key", dataIndex: "key", width: 140, render: (v: string, r: typeof mockFields[0]) => <Input size="small" value={v} onChange={(e) => updateField(r.id, "key", e.target.value)} placeholder="progress_desc" /> },
    { title: "字段标签", dataIndex: "label", width: 160, render: (v: string, r: typeof mockFields[0]) => <Input size="small" value={v} onChange={(e) => updateField(r.id, "label", e.target.value)} placeholder="本周施工进度描述" /> },
    { title: "类型", dataIndex: "type", width: 130, render: (v: string, r: typeof mockFields[0]) => <Select size="small" value={v} style={{ width: "100%" }} options={fieldTypes} onChange={(val) => updateField(r.id, "type", val)} /> },
    { title: "必填", dataIndex: "required", width: 60, render: (v: boolean, r: typeof mockFields[0]) => <Select size="small" value={String(v)} style={{ width: "100%" }} options={[{ value: "true", label: "是" }, { value: "false", label: "否" }]} onChange={(val) => updateField(r.id, "required", val === "true")} /> },
    { title: "公式", dataIndex: "formula", width: 160, render: (v: string, r: typeof mockFields[0]) => <Input size="small" value={v} onChange={(e) => updateField(r.id, "formula", e.target.value)} placeholder="上期 + 本期" disabled={r.type !== "formula"} /> },
    { title: "操作", key: "op", width: 60, render: (_: unknown, r: typeof mockFields[0]) => <Button type="text" danger size="small" icon={<DeleteOutlined />} onClick={() => removeField(r.id)} /> },
  ];

  return (
    <div>
      <Card title="基本信息" size="small" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={6}><Form.Item label="模板名" style={{ marginBottom: 0 }}><Input defaultValue="周报标准模板" /></Form.Item></Col>
          <Col span={4}><Form.Item label="类型" style={{ marginBottom: 0 }}><Select defaultValue="weekly" options={[{ value: "weekly", label: "周报" }, { value: "monthly", label: "月报" }]} /></Form.Item></Col>
          <Col span={4}><Form.Item label="版本" style={{ marginBottom: 0 }}><InputNumber defaultValue={3} min={1} /></Form.Item></Col>
          <Col span={4}><Form.Item label="状态" style={{ marginBottom: 0 }}><Select defaultValue="active" options={[{ value: "active", label: "启用" }, { value: "inactive", label: "禁用" }]} /></Form.Item></Col>
        </Row>
      </Card>

      <Card title="字段定义区" extra={<Button icon={<PlusOutlined />} onClick={addField}>新增字段</Button>}>
        <Table columns={cols} dataSource={fields} size="small" rowKey="id" pagination={false} />
      </Card>

      <Collapse style={{ marginTop: 16 }} items={[{ key: "preview", label: "预览区 ▼", children: (
        <div>
          <p style={{ fontSize: 12, color: "#999" }}>以下为模拟的 DynamicForm 预览（实际将使用 Formily 渲染）</p>
          {fields.map((f) => (
            <div key={f.id} style={{ marginBottom: 8 }}>
              <div style={{ fontSize: 12, fontWeight: 500 }}>{f.label} {f.required && <span style={{ color: "#ff4d4f" }}>*</span>} <Tag color={f.type === "formula" ? "blue" : "green"}>{f.type}</Tag></div>
              <Input placeholder={f.label} size="small" disabled={f.type === "formula"} defaultValue={f.type === "formula" ? "[自动计算]" : ""} />
            </div>
          ))}
        </div>
      ) }]} />

      <div style={{ marginTop: 24, textAlign: "right" }}>
        <Space><Button onClick={() => window.history.back()}>取消</Button><Button type="primary" onClick={() => message.success("模板保存成功")}>保存</Button></Space>
      </div>
    </div>
  );
}