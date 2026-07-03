import { useState, useMemo } from "react";
import { Card, Select, Button, Table, Tag, Progress, Space, message, Row, Col, Input, Badge } from "antd";
import { PlusOutlined, RollbackOutlined, SearchOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { mockBatches } from "../../utils/mock";

const statusMap: Record<string, { color: string; text: string }> = {
  pending: { color: "default", text: "待解析" },
  parsing: { color: "processing", text: "解析中" },
  normalized: { color: "blue", text: "已归一化" },
  validated: { color: "cyan", text: "已校验" },
  review: { color: "orange", text: "待确认" },
  committing: { color: "processing", text: "入库中" },
  committed: { color: "green", text: "已入库" },
  rolled_back: { color: "red", text: "已撤回" },
  failed: { color: "red", text: "失败" },
};

export default function BatchesList() {
  const navigate = useNavigate();
  const [statusFilter, setStatusFilter] = useState<string[]>([]);
  const [search, setSearch] = useState("");

  const columns = useMemo(() => [
    { title: "批次号", dataIndex: "batch_no", key: "batch_no", width: 160, render: (v: string) => <a style={{ fontWeight: 500 }}>{v}</a> },
    { title: "原始文件名", dataIndex: "original_filename", key: "file", width: 180, ellipsis: true },
    { title: "项目", dataIndex: "project_name", key: "project", width: 150, ellipsis: true },
    { title: "状态", dataIndex: "status", key: "status", width: 90, render: (v: string) => <Tag color={statusMap[v]?.color}>{statusMap[v]?.text || v}</Tag> },
    { title: "总行数", dataIndex: "total_rows", key: "total", width: 70, align: "right" as const },
    { title: "解析成功", dataIndex: "parsed_rows", key: "parsed", width: 80, align: "right" as const },
    { title: "错误数", dataIndex: "error_count", key: "errors", width: 70,
      render: (v: number) => v > 0 ? <Badge count={v} overflowCount={99} style={{ backgroundColor: "#ff4d4f" }} /> : <span style={{ color: "#52c41a" }}>0</span> },
    { title: "质量分", dataIndex: "quality_score", key: "quality", width: 100,
      render: (v: number) => <Progress percent={v} size="small" status={v >= 90 ? "success" : v >= 70 ? "normal" : "exception"} /> },
    { title: "周期", dataIndex: "period_type", key: "period", width: 60 },
    { title: "上传者", dataIndex: "uploader_name", key: "uploader", width: 80 },
    { title: "上传时间", dataIndex: "upload_time", key: "time", width: 140 },
    { title: "操作", key: "action", width: 120, fixed: "right" as const,
      render: (_: unknown, r: typeof mockBatches[0]) => (
        <Space size="small">
          <a onClick={(e) => { e.stopPropagation(); navigate(`/data/batches/${r.id}`); }}>查看</a>
          {r.status === "committed" && <a onClick={(e) => { e.stopPropagation(); message.warning(`撤回批次 ${r.batch_no}`); }} style={{ color: "#ff4d4f" }}>撤回</a>}
        </Space>
      ) },
  ], [navigate]);

  let filtered = mockBatches;
  if (statusFilter.length) filtered = filtered.filter((b) => statusFilter.includes(b.status));
  if (search) filtered = filtered.filter((b) => b.batch_no.includes(search) || b.original_filename.includes(search));

  return (
    <div>
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={[12, 8]} align="middle">
          <Col><Select mode="multiple" placeholder="状态" style={{ width: 200 }} allowClear value={statusFilter} onChange={setStatusFilter} options={Object.entries(statusMap).map(([k, v]) => ({ value: k, label: v.text }))} /></Col>
          <Col flex="auto"><Input.Search placeholder="批次号/文件名" enterButton={<SearchOutlined />} value={search} onChange={(e) => setSearch(e.target.value)} /></Col>
          <Col>
            <Space>
              <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate("/data/upload")}>上传新数据</Button>
              <Button icon={<RollbackOutlined />} onClick={() => message.warning("批量撤回功能（二次确认）")}>批量撤回</Button>
            </Space>
          </Col>
        </Row>
      </Card>
      <Card title="批次管理">
        <Table columns={columns} dataSource={filtered} rowKey="id" size="small" scroll={{ x: 1200 }}
          pagination={{ pageSize: 20, showSizeChanger: true, pageSizeOptions: ["20", "50", "100"] }}
          onRow={(r) => ({ onClick: () => navigate(`/data/batches/${r.id}`), style: { cursor: "pointer" } })} />
      </Card>
    </div>
  );
}