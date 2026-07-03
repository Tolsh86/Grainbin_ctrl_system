import { useState, useMemo } from "react";
import { Card, Select, Row, Col, Input, Table, Tag, Space, Button, message, Collapse } from "antd";
import { SearchOutlined, CheckCircleOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";

const mockErrors = [
  { id: "e1", code: "AMOUNT_OUT_OF_RANGE", stage: "validate", field: "amount", value: "9999999", desc: "金额超出合理范围", severity: "error", batch_no: "BT-20260630-001", row_number: 21, status: "unresolved" },
  { id: "e2", code: "TYPE_MISMATCH", stage: "parse", field: "unit_price", value: "abc", desc: "类型不匹配", severity: "error", batch_no: "BT-20260630-001", row_number: 41, status: "unresolved" },
  { id: "e3", code: "REQUIRED_MISSING", stage: "map", field: "category", value: "", desc: "必填字段缺失", severity: "error", batch_no: "BT-20260630-001", row_number: 52, status: "unresolved" },
  { id: "e4", code: "DUPLICATE_ROW", stage: "validate", field: "item_name", value: "C30混凝土", desc: "可能有重复行", severity: "warning", batch_no: "BT-20260630-001", row_number: 61, status: "unresolved" },
  { id: "e5", code: "HEADER_NOT_FOUND", stage: "parse", field: "amount", value: "合价(元)", desc: "表头未匹配", severity: "info", batch_no: "BT-20260620-001", row_number: null, status: "resolved" },
];

const errorDict = [
  { code: "HEADER_NOT_FOUND", desc: "Excel 表头在字段映射中未找到对应字段" },
  { code: "TYPE_MISMATCH", desc: "单元格数据类型与系统字段类型不匹配" },
  { code: "AMOUNT_OUT_OF_RANGE", desc: "金额值超出合理范围（如单价>10万/单位）" },
  { code: "REQUIRED_MISSING", desc: "必填字段在映射后的值为空" },
  { code: "CONVERTER_FAIL", desc: "转换器执行失败（如日期格式不识别）" },
  { code: "DUPLICATE_ROW", desc: "可能存在重复的数据行" },
  { code: "REFERENCE_NOT_FOUND", desc: "引用的外部数据不存在" },
  { code: "DATE_INVALID", desc: "日期格式非法或超出合理范围" },
];

export default function ErrorCenter() {
  const navigate = useNavigate();
  const cols = useMemo(() => [
    { title: "错误码", dataIndex: "code", key: "code", width: 160, render: (v: string) => <Tag color="red">{v}</Tag> },
    { title: "阶段", dataIndex: "stage", key: "st", width: 80 },
    { title: "错误字段", dataIndex: "field", key: "f", width: 90 },
    { title: "错误值", dataIndex: "value", key: "val", width: 100, ellipsis: true },
    { title: "描述", dataIndex: "desc", key: "desc", width: 150, ellipsis: true },
    { title: "严重性", dataIndex: "severity", key: "sv", width: 70, render: (v: string) => <Tag color={v === "error" ? "red" : v === "warning" ? "orange" : "blue"}>{v}</Tag> },
    { title: "关联批次", dataIndex: "batch_no", key: "bn", width: 140 },
    { title: "行号", dataIndex: "row_number", key: "rn", width: 60, render: (v: number | null) => v ?? "-" },
    { title: "状态", dataIndex: "status", key: "st2", width: 80, render: (v: string) => <Tag color={v === "resolved" ? "green" : "red"}>{v === "resolved" ? "已解决" : "未解决"}</Tag> },
    { title: "操作", key: "op", width: 120, render: (_: unknown, r: typeof mockErrors[0]) => (
      <Space size="small">
        <a onClick={() => navigate("/data/batches/1")}>查看批次</a>
        {r.status !== "resolved" && <a onClick={() => message.success("已标记为已解决")}>标记解决</a>}
      </Space>
    ) },
  ], [navigate]);

  return (
    <div>
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={[12, 8]} align="middle">
          <Col><Input.Search placeholder="搜索错误码/描述" enterButton={<SearchOutlined />} style={{ width: 280 }} /></Col>
          <Col><Button icon={<CheckCircleOutlined />} onClick={() => message.success("批量标记已解决")}>批量标记已解决</Button></Col>
        </Row>
      </Card>
      <Card title="错误中心"><Table columns={cols} dataSource={mockErrors} size="small" rowKey="id" scroll={{ x: 1200 }} pagination={{ pageSize: 10 }} /></Card>
      <Collapse style={{ marginTop: 16 }} items={[{ key: "dict", label: "错误码字典 ▼",
        children: <Row gutter={16}>
          {errorDict.map((item, i) => (
            <Col span={12} key={i} style={{ marginBottom: 8 }}><Tag color="red">{item.code}</Tag><span style={{ fontSize: 12, marginLeft: 8 }}>{item.desc}</span></Col>
          ))}
        </Row>
      }]} />
    </div>
  );
}