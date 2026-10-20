import { useState, useEffect, useCallback, useMemo } from "react";
import {
  Card, Select, Row, Col, Statistic, Tag, Button, Space, Table,
  InputNumber, Drawer, message, Divider, Modal, Typography, Badge, Empty,
  Form, Checkbox, Input, List, Tabs,
} from "antd";
import {
  PlusOutlined, CheckCircleOutlined,
  SendOutlined, EyeOutlined, DeleteOutlined, FundOutlined, WalletOutlined,
  ExclamationCircleOutlined, ThunderboltOutlined, FileExcelOutlined,
} from "@ant-design/icons";
import { getProjects } from "../../api/projects";
import { getContractGroups } from "../../api/contracts";
import {
  getPeriods, createPeriod, getPeriod, deletePeriod,
  getPeriodReviews, getPeriodExportUrl,
  type Period, type ReviewPhase2, type ReviewFeeItem,
} from "../../api/periods";
import { getReview, updateReview, updateReviewStatus, aggregateDaily } from "../../api/reviews";

const { Text } = Typography;

// ── 分→万元 ──
const fenToWan = (fen: number | null | undefined): number => {
  if (fen == null || fen === 0) return 0;
  return fen / 1000000;
};
const fenToWanStr = (fen: number | null | undefined): string =>
  fenToWan(fen).toLocaleString("zh-CN", { minimumFractionDigits: 4, maximumFractionDigits: 4 });

const statusTag: Record<string, { color: string; text: string }> = {
  draft: { color: "default", text: "草稿" },
  in_progress: { color: "processing", text: "进行中" },
  reviewed: { color: "success", text: "已审核" },
  closed: { color: "warning", text: "已关闭" },
};

const reviewStatusTag: Record<string, { color: string; text: string }> = {
  draft: { color: "default", text: "草稿" },
  submitted: { color: "blue", text: "已报送" },
  reviewed: { color: "green", text: "已审定" },
};

const reviewModeTag: Record<string, { color: string; text: string }> = {
  daily_aggregate: { color: "blue", text: "建安费用" },
  node_judge: { color: "green", text: "二类费用" },
  none: { color: "default", text: "无产值" },
};

export default function AuditWorkbench() {
  // ── State ──
  const [projects, setProjects] = useState<any[]>([]);
  const [projectId, setProjectId] = useState<string | null>(null);
  const [periods, setPeriods] = useState<Period[]>([]);
  const [periodLoading, setPeriodLoading] = useState(false);

  // selected period → reviews
  const [selectedPeriod, setSelectedPeriod] = useState<Period | null>(null);
  const [allReviews, setAllReviews] = useState<ReviewPhase2[]>([]);
  const [reviewsLoading, setReviewsLoading] = useState(false);

  // ── Review mode filter ──
  const [activeTab, setActiveTab] = useState<string>("node_judge");

  // contracts cache (for mapping review_mode)
  const [contractModeMap, setContractModeMap] = useState<Record<string, string>>({});

  // Filter reviews by review_mode based on contract_id → review_mode
  const reviewsByMode = useMemo(() => {
    return {
      daily_aggregate: allReviews.filter((r) => contractModeMap[r.contract_id] === "daily_aggregate"),
      node_judge: allReviews.filter((r) => {
        const mode = contractModeMap[r.contract_id];
        return mode === "node_judge" || mode === undefined;
      }),
    };
  }, [allReviews, contractModeMap]);

  // create period modal
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const [allContracts, setAllContracts] = useState<any[]>([]);
  const [selectedContractIds, setSelectedContractIds] = useState<string[]>([]);
  const [newPeriodMonth, setNewPeriodMonth] = useState("");
  const [newPeriodNo, setNewPeriodNo] = useState(1);

  // review detail drawer
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailReview, setDetailReview] = useState<ReviewPhase2 | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [editingFeeItems, setEditingFeeItems] = useState<Record<string, { reported: number; reviewed: number }>>({});
  const [saving, setSaving] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  // for daily_aggregate: aggregating state
  const [aggregating, setAggregating] = useState(false);

  // ── Load projects ──
  useEffect(() => {
    getProjects({ page: 1, page_size: 100 })
      .then((res) => {
        const list = res.items ?? [];
        setProjects(list);
        if (list.length > 0 && !projectId) setProjectId(list[0].id);
      })
      .catch(() => {});
  }, []);

  // ── Load periods ──
  const loadPeriods = useCallback(() => {
    if (!projectId) return;
    setPeriodLoading(true);
    getPeriods(projectId, { page: 1, page_size: 50 })
      .then((res) => setPeriods(res.items))
      .catch(() => message.error("加载期次失败"))
      .finally(() => setPeriodLoading(false));
  }, [projectId]);

  useEffect(() => { loadPeriods(); }, [loadPeriods]);

  // ── Load reviews for selected period ──
  const loadReviews = useCallback((periodId: string) => {
    setReviewsLoading(true);
    getPeriodReviews(periodId, { page: 1, page_size: 100 })
      .then((res) => {
        setAllReviews(res.items);
        // Build contract → review_mode map from items
        const modeMap: Record<string, string> = {};
        // We'll also try to get contract info from the period contracts
        Promise.all(
          res.items.map((r) =>
            fetch(`/api/v1/contracts/${r.contract_id}`)
              .then((resp) => resp.json())
              .then((c: any) => { modeMap[r.contract_id] = c.review_mode || "node_judge"; })
              .catch(() => { modeMap[r.contract_id] = "node_judge"; })
          )
        ).then(() => setContractModeMap({ ...modeMap }));
      })
      .catch(() => message.error("加载审核记录失败"))
      .finally(() => setReviewsLoading(false));
  }, []);

  const selectPeriod = (p: Period) => {
    setSelectedPeriod(p);
    loadReviews(p.id);
    setActiveTab("node_judge");
  };

  // ── Create period ──
  const openCreateModal = async () => {
    if (!projectId) { message.warning("请先选择项目"); return; }
    try {
      const groups = await getContractGroups(projectId);
      const contracts = (groups ?? []).flatMap((g: any) => g.contracts);
      setAllContracts(contracts);
      setSelectedContractIds(contracts.filter((c: any) => c.status === "active").map((c: any) => c.id));
      const maxNo = periods.length > 0 ? Math.max(...periods.map((p) => p.period_no)) : 0;
      setNewPeriodNo(maxNo + 1);
      const now = new Date();
      setNewPeriodMonth(`${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`);
      setCreateModalOpen(true);
    } catch { message.error("加载合同列表失败"); }
  };

  const doCreatePeriod = async () => {
    if (!projectId) return;
    if (!newPeriodMonth.match(/^\d{4}-\d{2}$/)) { message.warning("月份格式为 YYYY-MM"); return; }
    if (selectedContractIds.length === 0) { message.warning("请至少选择一个合同"); return; }
    setCreateLoading(true);
    try {
      const period = await createPeriod(projectId, {
        period_month: newPeriodMonth,
        period_no: newPeriodNo,
        contract_ids: selectedContractIds,
      });
      message.success(`期次第${newPeriodNo}期创建成功，已生成 ${period.review_count} 条审核草稿`);
      setCreateModalOpen(false);
      loadPeriods();
    } catch (e: any) { message.error(e?.response?.data?.detail || "创建失败"); }
    finally { setCreateLoading(false); }
  };

  // ── Delete period ──
  const doDeletePeriod = async (period: Period) => {
    Modal.confirm({
      title: "确认删除",
      content: `确认删除第${period.period_no}期（${period.period_month}）？将同步删除所有审核记录。`,
      okText: "确认删除", okButtonProps: { danger: true },
      onOk: async () => {
        try {
          await deletePeriod(period.id);
          message.success("期次已删除");
          setSelectedPeriod(null);
          setAllReviews([]);
          loadPeriods();
        } catch (e: any) { message.error(e?.response?.data?.detail || "删除失败"); }
      },
    });
  };

  // ── Aggregate daily data (建安费用专用) ──
  const doAggregateDaily = async (review: ReviewPhase2) => {
    Modal.confirm({
      title: "从日报自动汇总",
      content: `系统将从 ${selectedPeriod?.period_month} 的日报数据中自动汇总报送金额，覆盖当前报送值。确认继续？`,
      icon: <ThunderboltOutlined />,
      okText: "汇总",
      onOk: async () => {
        setAggregating(true);
        try {
          const updated = await aggregateDaily(review.id);
          if (updated) {
            const r = await getReview(review.id);
            setDetailReview(r);
            const init: Record<string, { reported: number; reviewed: number }> = {};
            (r.fee_items || []).forEach((fi) => {
              init[fi.id] = { reported: fi.reported_amount || 0, reviewed: fi.reviewed_amount || 0 };
            });
            setEditingFeeItems(init);
            message.success("日报数据已自动汇总");
          }
        } catch (e: any) {
          message.error(e?.response?.data?.detail || "汇总失败");
        } finally { setAggregating(false); }
      },
    });
  };

  // ── Open review detail ──
  const openDetail = async (review: ReviewPhase2) => {
    setDetailOpen(true);
    setDetailLoading(true);
    setDetailReview(null);
    try {
      const r = await getReview(review.id);
      setDetailReview(r);
      const init: Record<string, { reported: number; reviewed: number }> = {};
      (r.fee_items || []).forEach((fi) => {
        init[fi.id] = { reported: fi.reported_amount || 0, reviewed: fi.reviewed_amount || 0 };
      });
      setEditingFeeItems(init);
    } catch { message.error("加载审核详情失败"); }
    finally { setDetailLoading(false); }
  };

  // ── Save review ──
  const saveDetail = async () => {
    if (!detailReview) return;
    setSaving(true);
    try {
      const feeItems = (detailReview.fee_items || []).map((fi) => {
        const ed = editingFeeItems[fi.id];
        return {
          id: fi.id,
          reported_amount: ed?.reported ?? fi.reported_amount,
          reviewed_amount: ed?.reviewed ?? fi.reviewed_amount,
        };
      });
      await updateReview(detailReview.id, { fee_items: feeItems });
      message.success("审核数据已保存");
      setDetailOpen(false);
      if (selectedPeriod) loadReviews(selectedPeriod.id);
    } catch (e: any) { message.error(e?.response?.data?.detail || "保存失败"); }
    finally { setSaving(false); }
  };

  // ── Submit review (draft → submitted) ──
  const submitReview = async () => {
    if (!detailReview) return;
    setSubmitting(true);
    try {
      const feeItems = (detailReview.fee_items || []).map((fi) => {
        const ed = editingFeeItems[fi.id];
        return {
          id: fi.id,
          reported_amount: ed?.reported ?? fi.reported_amount,
          reviewed_amount: ed?.reviewed ?? fi.reviewed_amount,
        };
      });
      await updateReview(detailReview.id, { fee_items: feeItems });
      await updateReviewStatus(detailReview.id, { audit_status: "submitted" });
      message.success("审核已报送");
      setDetailOpen(false);
      if (selectedPeriod) loadReviews(selectedPeriod.id);
      loadPeriods();
    } catch (e: any) { message.error(e?.response?.data?.detail || "报送失败"); }
    finally { setSubmitting(false); }
  };

  // ── Export period summary ──
  const handleExport = () => {
    if (!selectedPeriod) return;
    const token = localStorage.getItem("access_token");
    const url = getPeriodExportUrl(selectedPeriod.id);
    const xhr = new XMLHttpRequest();
    xhr.open("GET", url, true);
    xhr.responseType = "blob";
    xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    xhr.onload = () => {
      if (xhr.status === 200) {
        const blob = xhr.response;
        const disposition = xhr.getResponseHeader("Content-Disposition") || "";
        const match = disposition.match(/filename\*?=(?:UTF-8'')?(.+)/);
        const filename = match ? decodeURIComponent(match[1]) : `审核汇总表_第${selectedPeriod.period_no}期.xlsx`;
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = downloadUrl;
        a.download = filename;
        a.click();
        window.URL.revokeObjectURL(downloadUrl);
        message.success("导出成功");
      } else { message.error("导出失败"); }
    };
    xhr.onerror = () => message.error("导出失败");
    xhr.send();
  };

  // ── Confirm review (submitted → reviewed) ──
  const confirmReview = (reviewId: string) => {
    Modal.confirm({
      title: "确认审定",
      content: "确认后将自动写入月度台账，且推进期次状态。确认继续？",
      icon: <ExclamationCircleOutlined />,
      okText: "确认审定",
      onOk: async () => {
        try {
          await updateReviewStatus(reviewId, { audit_status: "reviewed" });
          message.success("审定已确认，已写入月度台账");
          if (selectedPeriod) loadReviews(selectedPeriod.id);
          loadPeriods();
        } catch (e: any) { message.error(e?.response?.data?.detail || "操作失败"); }
      },
    });
  };

  // ── Reviews table columns ──
  const reviewColumns = [
    { title: "申请单位", dataIndex: "applicant_unit", width: 140, ellipsis: true },
    { title: "审核类型", dataIndex: "review_type", width: 90, render: (v: string) => <Tag>{v}</Tag> },
    {
      title: "合同金额(万元)", dataIndex: "contract_amount", width: 110, align: "right" as const,
      render: (v: number) => fenToWanStr(v),
    },
    {
      title: "本期审定产值(万元)", dataIndex: "current_audited_output", width: 130, align: "right" as const,
      render: (v: number) => <span style={{ fontWeight: 600, color: "#1677ff" }}>{fenToWanStr(v)}</span>,
    },
    {
      title: "累计应付款(万元)", dataIndex: "cumulative_audited_payable", width: 130, align: "right" as const,
      render: (v: number) => <span style={{ color: "#cf1322" }}>{fenToWanStr(v)}</span>,
    },
    {
      title: "状态", dataIndex: "audit_status", width: 80,
      render: (v: string) => {
        const t = reviewStatusTag[v] || { color: "default", text: v };
        return <Tag color={t.color}>{t.text}</Tag>;
      },
    },
    {
      title: "操作", key: "op", width: 200,
      render: (_: any, r: ReviewPhase2) => (
        <Space size="small">
          <a onClick={() => openDetail(r)}><EyeOutlined /> 审核</a>
          {contractModeMap[r.contract_id] === "daily_aggregate" && (
            <a onClick={() => doAggregateDaily(r)} style={{ color: "#722ed1" }}>
              <ThunderboltOutlined /> 日报汇总
            </a>
          )}
          {r.audit_status === "submitted" && (
            <a onClick={() => confirmReview(r.id)} style={{ color: "#52c41a" }}>
              <CheckCircleOutlined /> 确认
            </a>
          )}
        </Space>
      ),
    },
  ];

  // ── Stats ──
  const periodStats = useMemo(() => {
    const currentReviews = activeTab === "daily_aggregate" ? reviewsByMode.daily_aggregate : reviewsByMode.node_judge;
    return {
      total: currentReviews.length,
      draft: currentReviews.filter((r) => r.audit_status === "draft").length,
      submitted: currentReviews.filter((r) => r.audit_status === "submitted").length,
      reviewed: currentReviews.filter((r) => r.audit_status === "reviewed").length,
    };
  }, [allReviews, activeTab, reviewsByMode]);

  const currentReviews = activeTab === "daily_aggregate" ? reviewsByMode.daily_aggregate : reviewsByMode.node_judge;

  // ── Render ──
  return (
    <div>
      {/* ── Top bar ── */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={16} align="middle">
          <Col>
            <span style={{ marginRight: 8 }}>项目：</span>
            <Select
              style={{ width: 260 }}
              value={projectId}
              onChange={(v) => { setProjectId(v); setSelectedPeriod(null); setAllReviews([]); }}
              options={projects.map((p) => ({ value: p.id, label: p.project_name }))}
            />
          </Col>
          <Col flex="auto" />
          <Col>
            <Button type="primary" icon={<PlusOutlined />} onClick={openCreateModal} disabled={!projectId}>
              新建期次
            </Button>
          </Col>
        </Row>
      </Card>

      {/* ── Period cards ── */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        {periods.map((p) => {
          const isActive = selectedPeriod?.id === p.id;
          const s = statusTag[p.status] || { color: "default", text: p.status };
          return (
            <Col xs={24} sm={12} md={8} lg={6} key={p.id}>
              <Badge.Ribbon text={s.text} color={s.color}>
                <Card
                  size="small"
                  hoverable
                  onClick={() => selectPeriod(p)}
                  style={{ cursor: "pointer", border: isActive ? "2px solid #1677ff" : undefined }}
                  actions={[
                    <DeleteOutlined key="del" style={{ color: "#ff4d4f" }}
                      onClick={(e) => { e.stopPropagation(); doDeletePeriod(p); }} />,
                  ]}
                >
                  <Statistic
                    title={`第 ${p.period_no} 期`}
                    value={p.period_month}
                    valueStyle={{ fontSize: 18, fontWeight: 600, color: isActive ? "#1677ff" : "#333" }}
                  />
                  <div style={{ marginTop: 8, fontSize: 12, color: "#999" }}>
                    {p.contract_count ?? 0} 份合同 · {p.review_count ?? 0} 条审核
                  </div>
                </Card>
              </Badge.Ribbon>
            </Col>
          );
        })}
        {periods.length === 0 && !periodLoading && (
          <Col span={24}><Empty description="暂无期次，请先新建期次" /></Col>
        )}
      </Row>

      {/* ── Reviews section with Tabs ── */}
      {selectedPeriod && (
        <>
          <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
            {[
              { title: "审核总数", value: periodStats.total, color: "#1677ff" },
              { title: "草稿", value: periodStats.draft, color: "#999" },
              { title: "已报送", value: periodStats.submitted, color: "#faad14" },
              { title: "已审定", value: periodStats.reviewed, color: "#52c41a" },
            ].map((s) => (
              <Col xs={12} sm={6} key={s.title}>
                <Card size="small">
                  <Statistic title={s.title} value={s.value} suffix=" 条" valueStyle={{ color: s.color }} />
                </Card>
              </Col>
            ))}
          </Row>
          <Card
            title={`第 ${selectedPeriod.period_no} 期 · ${selectedPeriod.period_month}`}
            extra={
              <Space size="small">
                <Button size="small" icon={<FileExcelOutlined />} onClick={handleExport}>
                  导出汇总表
                </Button>
                <Tag color={statusTag[selectedPeriod.status]?.color}>{statusTag[selectedPeriod.status]?.text}</Tag>
              </Space>
            }
          >
            <Tabs
              activeKey={activeTab}
              onChange={setActiveTab}
              items={[
                {
                  key: "node_judge",
                  label: <span><WalletOutlined /> 二类费用审核</span>,
                  children: (
                    <div>
                      <div style={{ marginBottom: 12, color: "#666", fontSize: 12 }}>
                        review_mode=node_judge — 设备/设计/监理过控类合同，人工填写报送值和审定值
                      </div>
                      <Table
                        size="small"
                        rowKey="id"
                        columns={reviewColumns}
                        dataSource={reviewsByMode.node_judge}
                        loading={reviewsLoading}
                        pagination={false}
                      />
                    </div>
                  ),
                },
                {
                  key: "daily_aggregate",
                  label: <span><FundOutlined /> 建安费用审核</span>,
                  children: (
                    <div>
                      <div style={{ marginBottom: 12, color: "#666", fontSize: 12 }}>
                        review_mode=daily_aggregate — 施工类合同，点击「日报汇总」自动填入报送值，审定确认
                      </div>
                      <Table
                        size="small"
                        rowKey="id"
                        columns={reviewColumns}
                        dataSource={reviewsByMode.daily_aggregate}
                        loading={reviewsLoading}
                        pagination={false}
                      />
                    </div>
                  ),
                },
              ]}
            />
          </Card>
        </>
      )}

      {/* ── Create Period Modal ── */}
      <Modal
        title="新建报送期次"
        open={createModalOpen}
        onOk={doCreatePeriod}
        onCancel={() => setCreateModalOpen(false)}
        confirmLoading={createLoading}
        okText="确认创建"
        width={600}
      >
        <Form layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="期次编号" required>
                <InputNumber style={{ width: "100%" }} min={1} value={newPeriodNo} onChange={(v) => setNewPeriodNo(v ?? 1)} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="月份" required help="格式：YYYY-MM">
                <Input placeholder="如 2026-07" value={newPeriodMonth}
                  onChange={(e) => setNewPeriodMonth(e.target.value)} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item label="选择参与本期的合同" required>
            <Checkbox.Group
              style={{ width: "100%" }}
              value={selectedContractIds}
              onChange={(vals) => setSelectedContractIds(vals as string[])}
            >
              <List
                dataSource={allContracts}
                size="small"
                renderItem={(c: any) => (
                  <List.Item style={{ padding: "4px 0" }}>
                    <Checkbox value={c.id}>
                      <Tag color={c.review_mode === "daily_aggregate" ? "blue" : "green"}>
                        {reviewModeTag[c.review_mode]?.text || "无产值"}
                      </Tag>
                      <Tag color={c.status === "active" ? "green" : "default"}>{c.contract_no}</Tag>
                      {c.supplier_name}
                      <span style={{ color: "#999", marginLeft: 8, fontSize: 12 }}>({c.contract_desc})</span>
                    </Checkbox>
                  </List.Item>
                )}
              />
            </Checkbox.Group>
          </Form.Item>
        </Form>
      </Modal>

      {/* ── Review Detail Drawer ── */}
      <Drawer
        title={detailReview ? `${detailReview.applicant_unit} — ${detailReview.review_type}` : "审核详情"}
        width={750}
        open={detailOpen}
        onClose={() => setDetailOpen(false)}
        loading={detailLoading}
        extra={
          <Space>
            <Button onClick={saveDetail} loading={saving}>保存</Button>
            <Button type="primary" icon={<SendOutlined />} loading={submitting}
              onClick={submitReview}
              disabled={detailReview?.audit_status !== "draft"}
            >
              报送审核
            </Button>
          </Space>
        }
      >
        {detailReview && (
          <>
            <Card size="small" style={{ marginBottom: 16 }}>
              <Row gutter={16}>
                <Col span={8}>
                  <Statistic title="合同金额(万元)" value={fenToWanStr(detailReview.contract_amount)} />
                </Col>
                <Col span={8}>
                  <Statistic title="累计报送产值(万元)" value={fenToWanStr(detailReview.cumulative_reported_output)} />
                </Col>
                <Col span={8}>
                  <Statistic title="本期审定产值(万元)" value={fenToWanStr(detailReview.current_audited_output)}
                    valueStyle={{ color: "#1677ff" }} />
                </Col>
              </Row>
              <Divider style={{ margin: "12px 0" }} />
              <Row gutter={16}>
                <Col span={8}><Text type="secondary">审核类型：</Text><Tag>{detailReview.review_type}</Tag></Col>
                <Col span={8}><Text type="secondary">状态：</Text>
                  <Tag color={reviewStatusTag[detailReview.audit_status]?.color}>
                    {reviewStatusTag[detailReview.audit_status]?.text}
                  </Tag>
                </Col>
                <Col span={8}><Text type="secondary">申报日期：</Text>{detailReview.submit_date || "—"}</Col>
              </Row>
              {detailReview.remark && (
                <div style={{ marginTop: 8, color: "#666", fontSize: 12 }}>备注：{detailReview.remark}</div>
              )}
            </Card>

            <div style={{ fontWeight: 600, marginBottom: 12 }}>费用分项</div>
            <Table
              size="small"
              rowKey="id"
              pagination={false}
              dataSource={detailReview.fee_items || []}
              columns={[
                { title: "分项名称", dataIndex: "item_name", width: 140 },
                {
                  title: "付款比例", dataIndex: "payment_ratio", width: 100, align: "center" as const,
                  render: (v: number | null) => v != null ? `${(v * 100).toFixed(1)}%` : "—",
                },
                {
                  title: "报送金额(万元)", key: "reported", width: 150, align: "right" as const,
                  render: (_: any, fi: ReviewFeeItem) => (
                    <InputNumber
                      size="small" style={{ width: 130 }}
                      min={0} precision={4}
                      value={fenToWan(editingFeeItems[fi.id]?.reported ?? fi.reported_amount)}
                      disabled={detailReview.audit_status !== "draft"}
                      onChange={(v) => {
                        const cur = editingFeeItems[fi.id] || { reported: fi.reported_amount || 0, reviewed: fi.reviewed_amount || 0 };
                        setEditingFeeItems({ ...editingFeeItems, [fi.id]: { ...cur, reported: Math.round((v ?? 0) * 1000000) } });
                      }}
                    />
                  ),
                },
                {
                  title: "审定金额(万元)", key: "reviewed", width: 150, align: "right" as const,
                  render: (_: any, fi: ReviewFeeItem) => (
                    <InputNumber
                      size="small" style={{ width: 130 }}
                      min={0} precision={4}
                      value={fenToWan(editingFeeItems[fi.id]?.reviewed ?? fi.reviewed_amount)}
                      disabled={detailReview.audit_status === "reviewed"}
                      onChange={(v) => {
                        const cur = editingFeeItems[fi.id] || { reported: fi.reported_amount || 0, reviewed: fi.reviewed_amount || 0 };
                        setEditingFeeItems({ ...editingFeeItems, [fi.id]: { ...cur, reviewed: Math.round((v ?? 0) * 1000000) } });
                      }}
                    />
                  ),
                },
                {
                  title: "应付金额(万元)", key: "payable", width: 140, align: "right" as const,
                  render: (_: any, fi: ReviewFeeItem) => {
                    const ed = editingFeeItems[fi.id];
                    const reviewed = ed?.reviewed ?? fi.reviewed_amount ?? 0;
                    const payable = reviewed * (fi.payment_ratio || 0);
                    return (
                      <span style={{ fontWeight: 600, color: "#cf1322" }}>
                        {fenToWanStr(payable)}
                      </span>
                    );
                  },
                },
              ]}
              summary={() => {
                let totalReviewed = 0;
                let totalPayable = 0;
                (detailReview.fee_items || []).forEach((fi) => {
                  const ed = editingFeeItems[fi.id];
                  const reviewed = ed?.reviewed ?? fi.reviewed_amount ?? 0;
                  totalReviewed += reviewed;
                  totalPayable += reviewed * (fi.payment_ratio || 0);
                });
                return (
                  <Table.Summary fixed>
                    <Table.Summary.Row style={{ fontWeight: 700 }}>
                      <Table.Summary.Cell index={0} align="right" colSpan={3}>合计</Table.Summary.Cell>
                      <Table.Summary.Cell index={1} align="right">
                        {fenToWanStr(totalReviewed)}
                      </Table.Summary.Cell>
                      <Table.Summary.Cell index={2} align="right">
                        <span style={{ color: "#cf1322" }}>{fenToWanStr(totalPayable)}</span>
                      </Table.Summary.Cell>
                    </Table.Summary.Row>
                  </Table.Summary>
                );
              }}
            />
          </>
        )}
      </Drawer>
    </div>
  );
}
