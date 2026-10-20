import { useState, useEffect } from "react";
import { Card, Select, Button, Table, Tag, Progress, Space, message, Row, Col, Input, Badge } from "antd";
import { PlusOutlined, SearchOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { getIngestBatches, commitBatch, rollbackBatch, type Batch } from "../../api/data";
import { getProjects, type ProjectResponse } from "../../api/projects";

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
  const [batches, setBatches] = useState<Batch[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const [search, setSearch] = useState("");

  useEffect(() => {
    setLoading(true);
    const params: any = { page, page_size: 20 };
    if (statusFilter) params.status = statusFilter;
    getIngestBatches(params)
      .then((res) => { setBatches(res.items); setTotal(res.total); })
      .catch(() => message.error("加载批次列表失败"))
      .finally(() => setLoading(false));
  }, [page, statusFilter]);

  const handleCommit = async (batch: Batch) => {
    try {
      await commitBatch(batch.id);
      message.success("批次已入库");
      // 重新加载
      setPage(1);
    } catch (e: any) {
      message.error(e?.response?.data?.detail || "入库失败");
    }
  };

  const handleRollback = async (batch: Batch) => {
    try {
      await rollbackBatch(batch.id);
      message.success("批次已撤回");
      setPage(1);
    } catch (e: any) {
      message.error(e?.response?.data?.detail || "撤回失败");
    }
  };

  const columns = [
    { title: "批次ID", dataIndex: "id", key: "id", width: 80, ellipsis: true,
      render: (v: string) => v.substring(0, 8) + "..." },
    { title: "来源文件", dataIndex: "source_doc", key: "file", width: 180, ellipsis: true },
    { title: "状态", dataIndex: "status", key: "status", width: 90,
      render: (v: string) => <Tag color={statusMap[v]?.color}>{statusMap[v]?.text || v}</Tag> },
    { title: "总行数", dataIndex: "total_rows", key: "total", width: 70, align: "right" as const },
    { title: "解析成功", dataIndex: "valid_rows", key: "valid", width: 80, align: "right" as const },
    { title: "错误数", dataIndex: "error_rows", key: "errors", width: 70,
      render: (v: number) => v > 0 ? <Badge count={v} overflowCount={99} style={{ backgroundColor: "#ff4d4f" }} /> : <span style={{ color: "#52c41a" }}>0</span> },
    { title: "质量分", dataIndex: "quality_score", key: "quality", width: 100,
      render: (v: number) => <Progress percent={Math.round(v || 0)} size="small"
        status={(v || 0) >= 90 ? "success" : (v || 0) >= 70 ? "normal" : "exception"} /> },
    { title: "创建时间", dataIndex: "created_at", key: "time", width: 150,
      render: (v: string) => new Date(v).toLocaleString("zh-CN") },
    { title: "操作", key: "action", width: 140, fixed: "right" as const,
      render: (_: unknown, r: Batch) => (
        <Space size="small">
          <a onClick={(e) => { e.stopPropagation(); navigate(`/data/batches/${r.id}`); }}>查看</a>
          {r.status === "validated" && <a onClick={(e) => { e.stopPropagation(); handleCommit(r); }}>入库</a>}
          {r.status === "committed" && <a onClick={(e) => { e.stopPropagation(); handleRollback(r); }} style={{ color: "#ff4d4f" }}>撤回</a>}
        </Space>
      ) },
  ];

  return (
    <div>
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={[12, 8]} align="middle">
          <Col>
            <Select placeholder="状态" style={{ width: 160 }} allowClear value={statusFilter} onChange={setStatusFilter}
              options={Object.entries(statusMap).map(([k, v]) => ({ value: k, label: v.text }))} />
          </Col>
          <Col flex="auto"><Input.Search placeholder="文件名搜索" enterButton={<SearchOutlined />} value={search} onChange={(e) => setSearch(e.target.value)} /></Col>
          <Col>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate("/data/upload")}>上传新数据</Button>
          </Col>
        </Row>
      </Card>
      <Card title="批次管理">
        <Table columns={columns} dataSource={batches} rowKey="id" size="small" scroll={{ x: 1200 }}
          loading={loading}
          pagination={{ current: page, total, pageSize: 20, onChange: setPage, showSizeChanger: false }}
          onRow={(r) => ({ onClick: () => navigate(`/data/batches/${r.id}`), style: { cursor: "pointer" } })} />
      </Card>
    </div>
  );
}
