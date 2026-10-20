import { useState, useEffect } from "react";
import { Card, Table, Tag, Button, Space, Row, Col, Select, message } from "antd";
import { PlusOutlined, EyeOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { getProjects } from "../../api/projects";
import { getPeriods, type Period } from "../../api/periods";
import { getPeriodReviews, type ReviewPhase2 } from "../../api/periods";

const fenToWanStr = (fen: number | null | undefined): string => {
  if (fen == null || fen === 0) return "0.0000";
  return (fen / 1000000).toLocaleString("zh-CN", { minimumFractionDigits: 4, maximumFractionDigits: 4 });
};

const reviewStatusTag: Record<string, { color: string; text: string }> = {
  draft: { color: "default", text: "草稿" },
  submitted: { color: "blue", text: "已报送" },
  reviewed: { color: "green", text: "已审定" },
};

export default function AuditList() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<any[]>([]);
  const [projectId, setProjectId] = useState<string | null>(null);
  const [periods, setPeriods] = useState<Period[]>([]);
  const [selectedPeriodId, setSelectedPeriodId] = useState<string | null>(null);
  const [reviews, setReviews] = useState<ReviewPhase2[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getProjects({ page: 1, page_size: 100 })
      .then((res) => { setProjects(res.items); if (res.items.length > 0 && !projectId) setProjectId(res.items[0].id); })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!projectId) return;
    getPeriods(projectId, { page: 1, page_size: 50 })
      .then((res) => {
        setPeriods(res.items);
        if (res.items.length > 0 && !selectedPeriodId) {
          setSelectedPeriodId(res.items[0].id);
        }
      })
      .catch(() => {});
  }, [projectId]);

  useEffect(() => {
    if (!selectedPeriodId) return;
    setLoading(true);
    getPeriodReviews(selectedPeriodId, { page: 1, page_size: 100 })
      .then((res) => setReviews(res.items))
      .catch(() => message.error("加载审核记录失败"))
      .finally(() => setLoading(false));
  }, [selectedPeriodId]);

  const selectedPeriodName = periods.find((p) => p.id === selectedPeriodId);

  const columns = [
    { title: "审核类型", dataIndex: "review_type", width: 100, render: (v: string) => <Tag>{v}</Tag> },
    { title: "申请单位", dataIndex: "applicant_unit", width: 140, ellipsis: true },
    {
      title: "合同金额(万元)", dataIndex: "contract_amount", width: 120, align: "right" as const,
      render: (v: number) => fenToWanStr(v),
    },
    {
      title: "累计报送产值(万元)", dataIndex: "cumulative_reported_output", width: 140, align: "right" as const,
      render: (v: number) => fenToWanStr(v),
    },
    {
      title: "本期审定产值(万元)", dataIndex: "current_audited_output", width: 140, align: "right" as const,
      render: (v: number) => <span style={{ fontWeight: 600, color: "#1677ff" }}>{fenToWanStr(v)}</span>,
    },
    {
      title: "累计应付款(万元)", dataIndex: "cumulative_audited_payable", width: 140, align: "right" as const,
      render: (v: number) => <span style={{ color: "#cf1322" }}>{fenToWanStr(v)}</span>,
    },
    {
      title: "状态", dataIndex: "audit_status", width: 80,
      render: (v: string) => <Tag color={reviewStatusTag[v]?.color}>{reviewStatusTag[v]?.text || v}</Tag>,
    },
    {
      title: "操作", key: "op", width: 80,
      render: (_: any, r: ReviewPhase2) => <a onClick={() => navigate(`/audits/${r.id}`)}><EyeOutlined /> 查看</a>,
    },
  ];

  return (
    <div>
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={[12, 8]} align="middle">
          <Col>
            <Select
              style={{ width: 200 }} placeholder="选择项目" allowClear
              value={projectId}
              onChange={(v) => { setProjectId(v); setSelectedPeriodId(null); setReviews([]); }}
              options={projects.map((p) => ({ value: p.id, label: p.project_name }))}
            />
          </Col>
          <Col>
            <Select
              style={{ width: 200 }} placeholder="选择期次" allowClear
              value={selectedPeriodId}
              onChange={(v) => setSelectedPeriodId(v)}
              options={periods.map((p) => ({
                value: p.id,
                label: `第${p.period_no}期 · ${p.period_month} · ${statusText(p.status)}`,
              }))}
            />
          </Col>
          <Col flex="auto" />
          <Col>
            <Button type="primary" icon={<PlusOutlined />}
              onClick={() => navigate("/secondary/audit")}>审核工作台</Button>
          </Col>
        </Row>
      </Card>
      <Card title={selectedPeriodName ? `第${selectedPeriodName.period_no}期 · ${selectedPeriodName.period_month} · 审核记录` : "审核记录"}>
        <Table columns={columns} dataSource={reviews} size="small" rowKey="id" loading={loading}
          pagination={{ pageSize: 20, showTotal: (t) => `共 ${t} 条` }} scroll={{ x: 1000 }} />
      </Card>
    </div>
  );
}

function statusText(s: string): string {
  const map: Record<string, string> = { draft: "草稿", in_progress: "进行中", reviewed: "已审核", closed: "已关闭" };
  return map[s] || s;
}
