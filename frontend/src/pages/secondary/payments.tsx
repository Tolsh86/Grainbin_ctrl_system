import { useState, useEffect, useMemo } from "react";
import {
  Card, Table, Tag, Button, Space, Statistic, Row, Col,
  Modal, InputNumber, Input, message, Select, Typography,
  Collapse, Popconfirm, Tooltip, Divider,
} from "antd";
import {
  PlusOutlined, CheckCircleOutlined, CloseCircleOutlined,
} from "@ant-design/icons";
import dayjs from "dayjs";
import { getProjects } from "../../api/projects";
import { getContractGroups, getContractNodes } from "../../api/contracts";
import type { Contract } from "../../api/contracts";
import type { PaymentStage } from "../../api/contracts";
import {
  getContractPayments, createPayment, confirmPayment, rejectPayment,
} from "../../api/payments";
import type { PaymentResponse, PaymentLedgerGroup } from "../../api/payments";

const { Text } = Typography;

// ── 金额工具（分 → 元） ──

const fenToYuan = (fen: number): string => {
  return (fen / 100).toLocaleString("zh-CN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
};

// ── 状态标签 ──

const statusTag = (status: string) => {
  const map: Record<string, { color: string; text: string }> = {
    pending: { color: "processing", text: "待确认" },
    confirmed: { color: "success", text: "已确认" },
    rejected: { color: "error", text: "已驳回" },
  };
  const m = map[status] ?? { color: "default", text: status };
  return <Tag color={m.color}>{m.text}</Tag>;
};

// ═══════════════════════════════════════════════════════════════════

export default function PaymentLedger() {
  // ── 筛选 ──
  const [projects, setProjects] = useState<any[]>([]);
  const [projectId, setProjectId] = useState<string | null>(null);
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [contractId, setContractId] = useState<string | null>(null);
  const [year, setYear] = useState<number | undefined>(undefined);

  // ── 台账数据 ──
  const [ledger, setLedger] = useState<PaymentLedgerGroup[]>([]);
  const [loading, setLoading] = useState(false);

  // ── 报送弹窗 ──
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [stages, setStages] = useState<PaymentStage[]>([]);
  const [selectedStageId, setSelectedStageId] = useState<string | null>(null);
  const [reportedAmount, setReportedAmount] = useState<number>(0);
  const [creating, setCreating] = useState(false);

  // ── 驳回弹窗 ──
  const [rejectModalOpen, setRejectModalOpen] = useState(false);
  const [rejectPaymentId, setRejectPaymentId] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState("");

  // ── 加载项目列表 ──
  useEffect(() => {
    getProjects({ page: 1, page_size: 100 })
      .then((res) => {
        const list = res.items ?? res ?? [];
        setProjects(list);
        if (list.length > 0 && !projectId) setProjectId(list[0].id);
      })
      .catch(() => {});
  }, []);

  // ── 项目变更 → 加载合同列表 ──
  useEffect(() => {
    if (!projectId) { setContracts([]); setContractId(null); return; }
    getContractGroups(projectId)
      .then((groups) => {
        const all = groups.flatMap((g) => g.contracts);
        setContracts(all);
        if (all.length > 0 && !contractId) setContractId(all[0].id);
      })
      .catch(() => message.error("加载合同列表失败"));
  }, [projectId]);

  // ── 合同/年份变更 → 加载支付台账 ──
  useEffect(() => {
    if (!contractId) { setLedger([]); return; }
    setLoading(true);
    getContractPayments(contractId, year)
      .then(setLedger)
      .catch(() => message.error("加载支付台账失败"))
      .finally(() => setLoading(false));
  }, [contractId, year]);

  // ── 统计数据 ──
  const stats = useMemo(() => {
    let totalReported = 0;
    let totalApproved = 0;
    let pendingCount = 0;
    let confirmedCount = 0;
    for (const group of ledger) {
      totalReported += group.month_total_reported;
      totalApproved += group.month_total_approved;
      for (const item of group.items) {
        if (item.status === "pending") pendingCount++;
        else if (item.status === "confirmed") confirmedCount++;
      }
    }
    return { totalReported, totalApproved, pendingCount, confirmedCount };
  }, [ledger]);

  // ── 打开报送弹窗 ──
  const openCreateModal = async () => {
    if (!contractId) return;
    setCreateModalOpen(true);
    setSelectedStageId(null);
    setReportedAmount(0);
    try {
      const nodes = await getContractNodes(contractId);
      setStages(nodes);
    } catch {
      message.error("加载支付节点失败");
    }
  };

  // ── 提交报送 ──
  const submitCreate = async () => {
    if (!contractId || !selectedStageId || reportedAmount <= 0) {
      message.warning("请选择节点并填写报送金额");
      return;
    }
    setCreating(true);
    try {
      await createPayment(contractId, {
        stage_id: selectedStageId,
        reported_amount: Math.round(reportedAmount * 100), // 元 → 分
      });
      message.success("报送成功");
      setCreateModalOpen(false);
      const data = await getContractPayments(contractId, year);
      setLedger(data);
    } catch {
      message.error("报送失败");
    } finally {
      setCreating(false);
    }
  };

  // ── 确认批准 ──
  const handleConfirm = async (paymentId: string) => {
    if (!contractId) return;
    try {
      await confirmPayment(contractId, paymentId);
      message.success("已确认");
      const data = await getContractPayments(contractId, year);
      setLedger(data);
    } catch {
      message.error("确认失败");
    }
  };

  // ── 打开驳回弹窗 ──
  const openRejectModal = (paymentId: string) => {
    setRejectPaymentId(paymentId);
    setRejectReason("");
    setRejectModalOpen(true);
  };

  // ── 提交驳回 ──
  const submitReject = async () => {
    if (!contractId || !rejectPaymentId || !rejectReason.trim()) {
      message.warning("请填写驳回原因");
      return;
    }
    try {
      await rejectPayment(contractId, rejectPaymentId, { reject_reason: rejectReason });
      message.success("已驳回");
      setRejectModalOpen(false);
      const data = await getContractPayments(contractId, year);
      setLedger(data);
    } catch {
      message.error("驳回失败");
    }
  };

  // ── 台账表格列 ──
  const columns = [
    { title: "节点", dataIndex: "stage_name", width: 120, render: (v: string | null) => v || "—" },
    { title: "合同编号", dataIndex: "contract_no", width: 130 },
    { title: "供应商", dataIndex: "supplier_name", width: 130, ellipsis: true,
      render: (v: string | null) => v || "—" },
    { title: "报送金额(元)", dataIndex: "reported_amount", width: 130, align: "right" as const,
      render: (v: number) => <Text strong>¥{fenToYuan(v)}</Text> },
    { title: "批准金额(元)", dataIndex: "approved_amount", width: 130, align: "right" as const,
      render: (v: number) => v > 0
        ? <Text style={{ color: "#52c41a" }}>¥{fenToYuan(v)}</Text>
        : <Text type="secondary">—</Text> },
    { title: "状态", dataIndex: "status", width: 85, render: (v: string) => statusTag(v) },
    { title: "确认时间", dataIndex: "confirmed_at", width: 160,
      render: (v: string | null) => v ? dayjs(v).format("YYYY-MM-DD HH:mm") : "—" },
    { title: "驳回原因", dataIndex: "reject_reason", width: 140, ellipsis: true,
      render: (v: string | null) => v
        ? <Tooltip title={v}><Text type="danger" ellipsis>{v}</Text></Tooltip>
        : "—" },
    {
      title: "操作", width: 140, fixed: "right" as const,
      render: (_: unknown, r: PaymentResponse) => {
        if (r.status === "pending") {
          return (
            <Space size={0}>
              <Popconfirm
                title="确认批准该笔支付？"
                description="确认后金额将锁定，不可修改。"
                onConfirm={() => handleConfirm(r.id)}
                okText="确认批准"
                cancelText="取消"
              >
                <Button size="small" type="link" icon={<CheckCircleOutlined />}
                  style={{ color: "#52c41a" }}>
                  确认
                </Button>
              </Popconfirm>
              <Button size="small" type="link" danger icon={<CloseCircleOutlined />}
                onClick={() => openRejectModal(r.id)}>
                驳回
              </Button>
            </Space>
          );
        }
        return <Text type="secondary">—</Text>;
      },
    },
  ];

  // ── 选中的合同对象（用于展示） ──
  const selectedContract = contracts.find((c) => c.id === contractId);

  // ── Render ──
  return (
    <div>
      {/* ═══ 筛选栏 + 统计 ═══ */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
          {/* 项目 */}
          <div style={{ display: "flex", alignItems: "center", gap: 6, flex: "1 1 160px", minWidth: 0 }}>
            <span style={{ whiteSpace: "nowrap", color: "#666", fontSize: 13 }}>项目</span>
            <Select
              style={{ flex: 1, minWidth: 0 }}
              value={projectId}
              onChange={(v) => { setProjectId(v); setContractId(null); }}
              options={projects.map((p) => ({ value: p.id, label: p.project_name }))}
              placeholder="选择项目"
            />
          </div>
          {/* 合同 */}
          <div style={{ display: "flex", alignItems: "center", gap: 6, flex: "2 1 220px", minWidth: 0 }}>
            <span style={{ whiteSpace: "nowrap", color: "#666", fontSize: 13 }}>合同</span>
            <Select
              style={{ flex: 1, minWidth: 0 }}
              value={contractId}
              onChange={(v) => { setContractId(v); setLedger([]); }}
              options={contracts.map((c) => ({
                value: c.id,
                label: `${c.contract_no} — ${c.supplier_name}`,
              }))}
              placeholder="选择合同"
            />
          </div>
          {/* 年份 */}
          <div style={{ display: "flex", alignItems: "center", gap: 6, flex: "0 0 140px" }}>
            <span style={{ whiteSpace: "nowrap", color: "#666", fontSize: 13 }}>年份</span>
            <Select
              style={{ minWidth: 90 }}
              allowClear
              placeholder="全部"
              value={year}
              onChange={setYear}
              options={Array.from({ length: 5 }, (_, i) => {
                const y = dayjs().year() - 2 + i;
                return { value: y, label: `${y}年` };
              })}
            />
          </div>
          {/* 报送按钮 — 右对齐 */}
          <div style={{ marginLeft: "auto" }}>
            <Button type="primary" icon={<PlusOutlined />}
              disabled={!contractId} onClick={openCreateModal}>
              报送支付
            </Button>
          </div>
        </div>

        {/* ── 分割线 + 统计 ── */}
        <Divider style={{ margin: "12px 0 8px" }} />
        <Row gutter={[16, 8]}>
          {[
            { title: "报送总额", value: `¥${fenToYuan(stats.totalReported)}`, color: "#1677ff" },
            { title: "批准总额", value: `¥${fenToYuan(stats.totalApproved)}`, color: "#52c41a" },
            { title: "待确认", value: stats.pendingCount, color: "#faad14", suffix: "笔" },
            { title: "已确认", value: stats.confirmedCount, color: "#52c41a", suffix: "笔" },
          ].map((s, i) => (
            <Col xs={12} sm={6} md={3} key={i}>
              <Statistic
                title={s.title}
                value={s.value}
                suffix={s.suffix}
                valueStyle={{ color: s.color, fontSize: 18, fontWeight: 600 }}
              />
            </Col>
          ))}
        </Row>
      </Card>

      {/* ═══ 按月分组台账 ═══ */}
      <Card
        title={
          <Space size={4}>
            <span style={{ fontWeight: 600 }}>支付台账</span>
            {selectedContract && (
              <Text type="secondary" style={{ fontSize: 13 }}>
                {selectedContract.contract_no} — {selectedContract.supplier_name}
              </Text>
            )}
            {!loading && ledger.length > 0 && (
              <Tag style={{ marginLeft: 4 }}>
                {ledger.reduce((s, g) => s + g.items.length, 0)} 条
              </Tag>
            )}
          </Space>
        }
        loading={loading}
        bodyStyle={!contractId || ledger.length === 0 ? undefined : { padding: 0 }}
      >
        {!contractId ? (
          <div style={{ textAlign: "center", padding: "60px 20px", color: "#999" }}>
            请先选择项目和合同
          </div>
        ) : ledger.length === 0 ? (
          <div style={{ textAlign: "center", padding: "60px 20px", color: "#999" }}>
            暂无支付记录
            <br />
            <Button type="link" icon={<PlusOutlined />} onClick={openCreateModal}
              style={{ marginTop: 8 }}>
              报送第一笔支付
            </Button>
          </div>
        ) : (
          <Collapse
            size="small"
            bordered={false}
            defaultActiveKey={ledger.filter((g) => g.month === "未确认").map((g) => g.month)}
            items={ledger.map((group) => ({
              key: group.month,
              label: (
                <Space size={8}>
                  <span style={{ fontWeight: 600, fontSize: 14 }}>
                    {group.month === "未确认" ? "⏳ 未确认" : `${group.month}`}
                  </span>
                  <Tag color={group.month === "未确认" ? "warning" : "blue"}>
                    {group.items.length} 笔
                  </Tag>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    报送 ¥{fenToYuan(group.month_total_reported)}
                    &nbsp;|&nbsp;批准 ¥{fenToYuan(group.month_total_approved)}
                  </Text>
                </Space>
              ),
              children: (
                <div style={{ padding: 0 }}>
                  <Table
                    size="small"
                    rowKey="id"
                    dataSource={group.items}
                    columns={columns}
                    pagination={false}
                    scroll={{ x: 1000 }}
                  />
                </div>
              ),
            }))}
          />
        )}
      </Card>

      {/* ═══ 报送弹窗 ═══ */}
      <Modal
        title="报送支付"
        open={createModalOpen}
        width={500}
        onCancel={() => setCreateModalOpen(false)}
        onOk={submitCreate}
        confirmLoading={creating}
        okText="提交报送"
        destroyOnClose
      >
        <div style={{ marginBottom: 20 }}>
          <div style={{ marginBottom: 6, fontWeight: 500 }}>支付节点</div>
          <Select
            style={{ width: "100%" }}
            placeholder="请选择支付节点"
            value={selectedStageId}
            onChange={setSelectedStageId}
            options={stages.map((s) => ({
              value: s.id,
              label: `${s.stage_name}${s.node_name ? ` - ${s.node_name}` : ""}${s.agreed_amount ? ` (¥${fenToYuan(s.agreed_amount)})` : ""}`,
            }))}
          />
        </div>
        <div>
          <div style={{ marginBottom: 6, fontWeight: 500 }}>报送金额（元）</div>
          <InputNumber
            style={{ width: "100%" }}
            min={0}
            precision={2}
            placeholder="请输入报送金额"
            value={reportedAmount}
            onChange={(v) => setReportedAmount(v ?? 0)}
          />
          <div style={{ marginTop: 8, fontSize: 12, color: "#999" }}>
            系统将自动计算批准金额（不超过节点剩余额度）
          </div>
        </div>
      </Modal>

      {/* ═══ 驳回弹窗 ═══ */}
      <Modal
        title="驳回支付"
        open={rejectModalOpen}
        width={420}
        onCancel={() => { setRejectModalOpen(false); setRejectPaymentId(null); }}
        onOk={submitReject}
        okText="确认驳回"
        okButtonProps={{ danger: true }}
        destroyOnClose
      >
        <div style={{ marginBottom: 8 }}>
          <Text type="secondary">请输入驳回原因：</Text>
        </div>
        <Input.TextArea
          rows={3}
          value={rejectReason}
          onChange={(e) => setRejectReason(e.target.value)}
          placeholder="如：金额与合同约定不符"
          maxLength={200}
          showCount
        />
      </Modal>
    </div>
  );
}
