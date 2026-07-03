import { useState, useMemo } from "react";
import { Card, Table, Tag, Button, Space, Row, Col, Statistic, Input, Select, Badge, message } from "antd";
import { PlusOutlined, ExportOutlined, SearchOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { mockAudits } from "../../utils/mock";

const formatYuan = (fen: number) => (fen / 100).toLocaleString();
const statusMap: Record<string, { color: string; text: string }> = {
  pending_audit: { color: "orange", text: "待审核" },
  audited: { color: "blue", text: "已审核" },
  paid: { color: "green", text: "已支付" },
  rejected: { color: "red", text: "已驳回" },
};

export default function AuditList() {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");

  let filtered = mockAudits;
  if (search) filtered = filtered.filter((a) => a.project_name.includes(search) || a.period.includes(search));

  const totalAudited = 595000000 + 552000000; // 累计审核通过
  const totalDeduct = 25000000 + 12000000 + 8000000; // 累计核减
  const avgDeductRate = 4.3;

  const cols = useMemo(() => [
    { title: "期次", dataIndex: "period", key: "p", width: 80 },
    { title: "项目", dataIndex: "project_name", key: "proj", width: 140, ellipsis: true },
    { title: "合同", dataIndex: "contract_name", key: "ct", width: 120, ellipsis: true, render: (v: string, r: typeof mockAudits[0]) => <>{v} <Tag>{r.contract_version}</Tag></> },
    { title: "施工单位", dataIndex: "constructor_unit", key: "cu", width: 100 },
    { title: "申报金额", dataIndex: "apply_amount", key: "aa", width: 120, align: "right" as const, render: (v: number) => `¥${formatYuan(v)}` },
    { title: "AI 建议", dataIndex: "ai_suggest_amount", key: "ai", width: 120, align: "right" as const, render: (v: number | null) => v ? `¥${formatYuan(v)}` : "—" },
    { title: "终审金额", dataIndex: "final_amount", key: "fa", width: 120, align: "right" as const, render: (v: number | null) => v ? <span style={{ fontWeight: 600 }}>¥{formatYuan(v)}</span> : "—" },
    { title: "核减", key: "dd", width: 100, render: (_: unknown, r: typeof mockAudits[0]) => r.deduct_amount ? <span style={{ color: "#ff4d4f" }}>¥{formatYuan(r.deduct_amount)} ({r.deduct_rate}%)</span> : "—" },
    { title: "异常", key: "an", width: 60, render: (_: unknown, r: typeof mockAudits[0]) => r.anomaly_count > 0 ? <Badge count={r.anomaly_count} size="small" /> : <span style={{ color: "#52c41a" }}>0</span> },
    { title: "状态", dataIndex: "status", key: "st", width: 80, render: (v: string) => <Tag color={statusMap[v]?.color}>{statusMap[v]?.text}</Tag> },
    { title: "操作", key: "op", width: 100, render: (_: unknown, r: typeof mockAudits[0]) => <Space size="small"><a onClick={() => navigate(`/audits/${r.id}`)}>{r.status === "pending_audit" ? "审核" : "查看"}</a></Space> },
  ], [navigate]);

  return (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        {[{ title: "累计审核通过", val: `¥${formatYuan(totalAudited)}`, color: "#52c41a" }, { title: "累计核减", val: `¥${formatYuan(totalDeduct)}`, color: "#ff4d4f" }, { title: "平均核减率", val: `${avgDeductRate}%`, color: "#fa8c16" }, { title: "待审核笔数", val: 2, color: "#1677ff" }].map((s, i) => (
          <Col xs={24} sm={12} lg={6} key={i}><Card size="small"><Statistic title={s.title} value={s.val} valueStyle={{ color: s.color }} /></Card></Col>
        ))}
      </Row>

      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={[12, 8]} align="middle">
          <Col flex="auto"><Input.Search placeholder="搜索项目/期次" enterButton={<SearchOutlined />} value={search} onChange={(e) => setSearch(e.target.value)} /></Col>
          <Col><Space><Button type="primary" icon={<PlusOutlined />} onClick={() => navigate("/audits/upload")}>上传新审核</Button><Button icon={<ExportOutlined />} onClick={() => message.info("批量导出")}>导出</Button></Space></Col>
        </Row>
      </Card>
      <Card title="审核记录"><Table columns={cols} dataSource={filtered} size="small" rowKey="id" /></Card>
    </div>
  );
}