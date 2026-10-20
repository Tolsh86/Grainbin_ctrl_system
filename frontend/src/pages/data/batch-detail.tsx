import { useState, useEffect } from "react";
import {
  Card, Row, Col, Statistic, Steps, Table, Tag, Tabs, Button, Space,
  Spin, Typography, Alert, message,
} from "antd";
import {
  CheckCircleOutlined, WarningOutlined,
  ArrowLeftOutlined, RollbackOutlined, InfoCircleOutlined,
} from "@ant-design/icons";
import { useNavigate, useParams } from "react-router-dom";
import { getBatch, getBatchRows, getBatchErrors, commitBatch, rollbackBatch, parseBatch, type Batch, type BatchError } from "../../api/data";

const { Text } = Typography;

const BATCH_STATUS_STEPS = [
  { title: "待解析", description: "pending" },
  { title: "解析中", description: "parsing" },
  { title: "已归一化", description: "normalized" },
  { title: "已校验", description: "validated" },
  { title: "待确认", description: "review" },
  { title: "入库中", description: "committing" },
  { title: "已入库", description: "committed" },
];

const STATUS_COLORS: Record<string, string> = {
  pending: "default", parsing: "processing", normalized: "blue",
  validated: "orange", review: "orange", committing: "purple",
  committed: "green", rolled_back: "red", failed: "red",
};

const formatYuan = (fen: number) => {
  if (!fen && fen !== 0) return "—";
  return (fen / 100).toLocaleString();
};

export default function BatchDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [batch, setBatch] = useState<Batch | null>(null);
  const [rows, setRows] = useState<any[]>([]);
  const [errors, setErrors] = useState<BatchError[]>([]);
  const [loading, setLoading] = useState(true);
  const [rowLoading, setRowLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("all");

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    getBatch(id)
      .then((b) => {
        setBatch(b);
        // 如果状态不是 committed/rolled_back/failed，自动触发解析
        if (["pending", "parsing"].includes(b.status)) {
          parseBatch(id).then((updated) => {
            setBatch(updated);
            loadRows();
          }).catch(() => {});
        }
      })
      .catch(() => setBatch(null))
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    if (batch && batch.status !== "pending" && batch.status !== "parsing") {
      loadRows();
    }
  }, [batch]);

  const loadRows = () => {
    if (!id) return;
    setRowLoading(true);
    getBatchRows(id, { page: 1, page_size: 500 })
      .then((res) => setRows(res.items))
      .catch(() => {})
      .finally(() => setRowLoading(false));
    getBatchErrors(id, { page: 1, page_size: 100 })
      .then((res) => setErrors(res.items))
      .catch(() => {});
  };

  if (loading) return <Spin style={{ display: "block", marginTop: 80 }} />;
  if (!batch) {
    return (
      <Card>
        <Alert type="error" message="批次不存在或已被删除" showIcon />
        <Button style={{ marginTop: 16 }} onClick={() => navigate("/data/batches")}>返回批次列表</Button>
      </Card>
    );
  }

  const currentStep = BATCH_STATUS_STEPS.findIndex((s) => s.description === batch.status);
  const errorCount = batch.error_rows;

  const handleCommit = async () => {
    try {
      await commitBatch(batch.id);
      message.success("批次已入库");
      getBatch(batch.id).then(setBatch);
    } catch (e: any) {
      message.error(e?.response?.data?.detail || "入库失败");
    }
  };

  const handleRollback = async () => {
    try {
      await rollbackBatch(batch.id);
      message.success("批次已撤回");
      getBatch(batch.id).then(setBatch);
    } catch (e: any) {
      message.error(e?.response?.data?.detail || "撤回失败");
    }
  };

  const getFlagColor = (row: any) => {
    if (row.is_valid === false) return "red";
    if (row.validation_flags && Object.keys(row.validation_flags).length > 0) return "orange";
    return "green";
  };

  const getFlagText = (row: any) => {
    if (row.is_valid === false) return "错误";
    if (row.validation_flags && Object.keys(row.validation_flags).length > 0) return "警告";
    return "正常";
  };

  const filterRows = (filter: string) => {
    if (filter === "all") return rows;
    if (filter === "error") return rows.filter((r) => !r.is_valid);
    if (filter === "warning") return rows.filter((r) => r.is_valid !== false && r.validation_flags && Object.keys(r.validation_flags).length > 0);
    return rows;
  };

  const rowColumns = [
    { title: "行号", dataIndex: "row_no", width: 60, fixed: "left" as const },
    { title: "数据日期", dataIndex: "data_date", width: 100 },
    { title: "类别", dataIndex: "category", width: 90, ellipsis: true as const },
    { title: "分项", dataIndex: "item_name", width: 130, ellipsis: true as const },
    { title: "计划量", dataIndex: "planned_quantity", width: 80, align: "right" as const },
    { title: "实际量", dataIndex: "actual_quantity", width: 80, align: "right" as const },
    { title: "单位", dataIndex: "unit", width: 50 },
    { title: "单价(元)", dataIndex: "unit_price", width: 100, align: "right" as const,
      render: (v: number) => v ? formatYuan(v) : "—" },
    { title: "金额(元)", dataIndex: "amount", width: 110, align: "right" as const,
      render: (v: number) => v ? formatYuan(v) : "—" },
    { title: "费用类型", dataIndex: "cost_type", width: 80 },
    { title: "校验", dataIndex: "is_valid", width: 60, align: "center" as const,
      render: (_: unknown, r: any) => {
        const c = getFlagColor(r);
        return c === "green" ? <CheckCircleOutlined style={{ color: "#52c41a" }} /> :
          <WarningOutlined style={{ color: c === "red" ? "#ff4d4f" : "#fa8c16" }} />;
      } },
    { title: "校验详情", dataIndex: "error_message", width: 120, ellipsis: true as const,
      render: (v: string, r: any) => v || (r.validation_flags && Object.keys(r.validation_flags).length > 0 ? "有警告" : "—") },
  ];

  const errorCount_ = errors.filter(e => e.severity === "error").length;
  const warningCount = errors.filter(e => e.severity === "warning").length;

  return (
    <div>
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row justify="space-between" align="middle" wrap>
          <Col>
            <Space size="middle" wrap>
              <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate("/data/batches")}>返回</Button>
              <span style={{ fontSize: 16, fontWeight: 600 }}>批次 {batch.id.substring(0, 8)}</span>
              <Tag color="blue">{batch.source_doc}</Tag>
              <Tag color={STATUS_COLORS[batch.status] || "default"}>{batch.status}</Tag>
            </Space>
          </Col>
          <Col>
            <Space>
              {(batch.status === "validated" || batch.status === "review") && (
                <Button type="primary" icon={<CheckCircleOutlined />} onClick={handleCommit}>整批确认入库</Button>
              )}
              {batch.status === "committed" && (
                <Button icon={<RollbackOutlined />} danger onClick={handleRollback}>整批撤回</Button>
              )}
            </Space>
          </Col>
        </Row>
      </Card>

      <Card size="small" style={{ marginBottom: 16 }}>
        <Steps
          current={currentStep >= 0 ? currentStep : 0}
          size="small"
          status={batch.status === "failed" ? "error" : "process"}
          items={BATCH_STATUS_STEPS.map((s) => ({ title: s.title }))}
        />
        {batch.status === "validated" && (
          <Alert style={{ marginTop: 12 }} message="数据已校验通过，请检查后点击「整批确认入库」将数据写入正式表" type="info" showIcon />
        )}
      </Card>

      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={12} sm={4}><Card size="small"><Statistic title="总行数" value={batch.total_rows} /></Card></Col>
        <Col xs={12} sm={4}><Card size="small"><Statistic title="有效行" value={batch.valid_rows} valueStyle={{ color: batch.valid_rows === batch.total_rows ? "#52c41a" : "#fa8c16" }} /></Card></Col>
        <Col xs={12} sm={4}><Card size="small"><Statistic title="错误行" value={batch.error_rows} valueStyle={{ color: batch.error_rows > 0 ? "#ff4d4f" : "#52c41a" }} /></Card></Col>
        <Col xs={12} sm={4}><Card size="small"><Statistic title="质量分" value={Math.round(batch.quality_score || 0)} suffix="/100" /></Card></Col>
        <Col xs={12} sm={4}><Card size="small"><Statistic title="创建时间" value={new Date(batch.created_at).toLocaleDateString("zh-CN")} /></Card></Col>
        <Col xs={12} sm={4}><Card size="small"><Statistic title="关联项目" value={batch.project_id.substring(0, 8) + "..."} /></Card></Col>
      </Row>

      <Card title="数据明细">
        <Tabs activeKey={activeTab} onChange={setActiveTab}
          items={[
            { key: "all", label: `全部行 (${rows.length})` },
            { key: "error", label: `错误行 (${rows.filter((r) => !r.is_valid).length})` },
            { key: "warning", label: `警告行 (${rows.filter((r) => r.is_valid !== false && r.validation_flags && Object.keys(r.validation_flags).length > 0).length})` },
          ].map((tab) => ({
            key: tab.key,
            label: tab.label,
            children: (
              <Table
                columns={rowColumns}
                dataSource={filterRows(tab.key)}
                rowKey="id"
                size="small"
                loading={rowLoading}
                scroll={{ x: 1100 }}
                pagination={{ pageSize: 30, showSizeChanger: true, showTotal: (t) => `共 ${t} 行` }}
              />
            ),
          }))}
        />
      </Card>

      {errors.length > 0 && (
        <Card title="错误详情" size="small" style={{ marginTop: 16 }}>
          <Table
            size="small" pagination={{ pageSize: 10 }}
            dataSource={errors}
            rowKey="id"
            columns={[
              { title: "错误码", dataIndex: "error_code", width: 120, render: (v: string) => <Tag color="red">{v}</Tag> },
              { title: "消息", dataIndex: "error_message", ellipsis: true },
              { title: "严重级别", dataIndex: "severity", width: 80, render: (v: string) => <Tag color={v === "error" ? "red" : "orange"}>{v}</Tag> },
              { title: "已解决", dataIndex: "resolved", width: 70, render: (v: boolean) => v ? <Tag color="green">是</Tag> : <Tag>否</Tag> },
            ]}
          />
        </Card>
      )}
    </div>
  );
}
