import { useState, useMemo } from "react";
import { Card, Table, Tag, Space, Button, Row, Col, Statistic, Input, Select, message } from "antd";
import { PlusOutlined, ExportOutlined, SearchOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { mockReports } from "../../utils/mock";

const typeMap: Record<string, string> = { daily: "日报", weekly: "周报", monthly: "月报", special: "专项" };
const statusMap: Record<string, { color: string; text: string }> = {
  draft: { color: "default", text: "草稿" },
  pending_review: { color: "orange", text: "待审核" },
  confirmed: { color: "blue", text: "已审核" },
  published: { color: "green", text: "已发布" },
};

export default function ReportList() {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<string[]>([]);
  const [statusFilter, setStatusFilter] = useState<string[]>([]);

  let filtered = mockReports;
  if (typeFilter.length) filtered = filtered.filter((r) => typeFilter.includes(r.type));
  if (statusFilter.length) filtered = filtered.filter((r) => statusFilter.includes(r.status));
  if (search) filtered = filtered.filter((r) => r.title.includes(search));

  const cols = useMemo(() => [
    { title: "报告标题", dataIndex: "title", key: "t", render: (v: string, r: typeof mockReports[0]) => <a onClick={() => navigate(`/reports/${r.id}/edit`)}>{v}</a> },
    { title: "项目", dataIndex: "project_name", key: "p", ellipsis: true },
    { title: "类型", dataIndex: "type", key: "tp", width: 80, render: (v: string) => <Tag>{typeMap[v]}</Tag> },
    { title: "周期", dataIndex: "period", key: "pr", width: 100 },
    { title: "状态", dataIndex: "status", key: "st", width: 90, render: (v: string) => <Tag color={statusMap[v]?.color}>{statusMap[v]?.text || v}</Tag> },
    { title: "创建人", dataIndex: "creator_name", key: "cr", width: 100 },
    { title: "创建时间", dataIndex: "created_at", key: "ct", width: 150 },
    { title: "操作", key: "op", width: 140,
      render: (_: unknown, r: typeof mockReports[0]) => (
        <Space size="small">
          <a onClick={() => navigate(`/reports/${r.id}/edit`)}>编辑</a>
          <a onClick={() => message.info("复制")}>复制</a>
          <a onClick={() => message.info("导出")}>导出</a>
        </Space>
      ) },
  ], [navigate]);

  return (
    <div>
      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        {[{ title: "本月生成", val: 28, color: "#1677ff" }, { title: "累计报告", val: 486, color: "#52c41a" }, { title: "待审核", val: 2, color: "#fa8c16" }, { title: "已发布", val: 25, color: "#722ed1" }].map((s, i) => (
          <Col xs={24} sm={12} lg={6} key={i}><Card size="small"><Statistic title={s.title} value={s.val} suffix="份" valueStyle={{ color: s.color }} /></Card></Col>
        ))}
      </Row>

      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={[12, 8]} align="middle">
          <Col><Select mode="multiple" placeholder="类型" style={{ width: 140 }} allowClear value={typeFilter} onChange={setTypeFilter} options={[{ value: "weekly", label: "周报" }, { value: "monthly", label: "月报" }, { value: "daily", label: "日报" }]} /></Col>
          <Col><Select mode="multiple" placeholder="状态" style={{ width: 140 }} allowClear value={statusFilter} onChange={setStatusFilter} options={Object.entries(statusMap).map(([k, v]) => ({ value: k, label: v.text }))} /></Col>
          <Col flex="auto"><Input.Search placeholder="搜索报告标题" enterButton={<SearchOutlined />} value={search} onChange={(e) => setSearch(e.target.value)} /></Col>
          <Col>
            <Space>
              <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate("/reports/1/edit")}>新建报告</Button>
              <Button icon={<ExportOutlined />} onClick={() => message.info("批量导出")}>导出</Button>
            </Space>
          </Col>
        </Row>
      </Card>
      <Card title="报告列表"><Table columns={cols} dataSource={filtered} size="small" rowKey="id" /></Card>
    </div>
  );
}