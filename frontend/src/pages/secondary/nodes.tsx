import { useState, useEffect, useMemo } from "react";
import {
  Card, Table, Tag, Button, Space, Row, Col, Select, Modal, Input,
  InputNumber, message, Statistic, Tooltip, Empty, Typography, Popconfirm,
  Drawer, Divider, DatePicker,
} from "antd";
import {
  PlusOutlined, EditOutlined, DeleteOutlined, CopyOutlined,
  ImportOutlined, CheckCircleFilled, CloseCircleFilled, MinusCircleFilled,
  EnvironmentOutlined, ClockCircleOutlined,
} from "@ant-design/icons";
import dayjs from "dayjs";
import { getProjects } from "../../api/projects";
import {
  getContracts,
  getContractNodes,
  getProjectNodes,
  createContractNode,
  updateContractNode,
  deleteContractNode,
  completeContractNode,
  generateNodesFromTemplate,
  getNodeTemplates,
} from "../../api/contracts";

const { Text } = Typography;

const fenToYuan = (fen: number) => (fen / 100).toFixed(2);
const formatYuanNum = (fen: number) =>
  (fen / 100).toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

// ── Page component ──
export default function NodeManagement() {
  // project + contract selector
  const [projects, setProjects] = useState<any[]>([]);
  const [projectId, setProjectId] = useState<string | null>(null);
  const [contracts, setContracts] = useState<any[]>([]);
  const [contractId, setContractId] = useState<string | null>(null);
  const [contract, setContract] = useState<any>(null);

  // stages
  const [stages, setStages] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  // contract select loading
  const [loadingContracts, setLoadingContracts] = useState(false);

  // drawer
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [editingStage, setEditingStage] = useState<any>(null);
  const [saving, setSaving] = useState(false);

  // template import
  const [importModalOpen, setImportModalOpen] = useState(false);
  const [templates, setTemplates] = useState<any[]>([]);

  // ── Load projects ──
  useEffect(() => {
    getProjects({ page: 1, page_size: 100 }).then((res) => {
      const list = res.items ?? res ?? [];
      setProjects(list);
      if (list.length > 0 && !projectId) setProjectId(list[0].id);
    }).catch(() => {});
  }, []);

  // ── Load contracts when project changes ──
  useEffect(() => {
    if (!projectId) return;
    setContractId(null);
    setContract(null);
    setContracts([]);

    // 未选择合同 → 加载项目下全部节点
    setLoading(true);
    getProjectNodes(projectId).then((nodes) => {
      setStages(nodes ?? []);
    }).catch(() => message.error("加载节点失败"))
      .finally(() => setLoading(false));

    // 加载合同下拉列表
    setLoadingContracts(true);
    getContracts(projectId, { page: 1, page_size: 100 }).then((res) => {
      const list = res.items ?? res ?? [];
      setContracts(list);
    }).catch(() => {}).finally(() => setLoadingContracts(false));
  }, [projectId]);

  // ── Load stages when contract changes ──
  useEffect(() => {
    if (!contractId) {
      // 清空合同选择 → 回到项目级全部节点
      if (projectId) {
        setLoading(true);
        getProjectNodes(projectId).then((nodes) => {
          setStages(nodes ?? []);
        }).catch(() => message.error("加载节点失败"))
          .finally(() => setLoading(false));
      }
      return;
    }
    setLoading(true);
    getContractNodes(contractId).then((nodes) => {
      setStages(nodes ?? []);
    }).catch(() => message.error("加载节点失败"))
      .finally(() => setLoading(false));

    const c = contracts.find((x) => x.id === contractId);
    setContract(c ?? null);
  }, [contractId, contracts]);

  // ── Reload helper ──
  const reloadStages = async () => {
    if (!projectId) return;
    if (contractId) {
      const nodes = await getContractNodes(contractId);
      setStages(nodes ?? []);
    } else {
      const nodes = await getProjectNodes(projectId);
      setStages(nodes ?? []);
    }
  };

  // ── Stats ──
  const stats = useMemo(() => {
    const completed = stages.filter((s) => s.is_completed).length;
    const pending = stages.length - completed;
    const totalAgreed = stages.reduce((sum: number, s: any) => sum + (s.agreed_amount ?? 0), 0);
    const totalPaid = stages.reduce((sum: number, s: any) => sum + (s.cumulative_paid ?? 0), 0);
    return { total: stages.length, completed, pending, totalAgreed, totalPaid };
  }, [stages]);

  // ── Drawer: open ──
  const openNew = () => {
    setEditingStage({
      stage_name: "",
      node_name: "",
      payment_terms: "",
      agreed_ratio: null,
      planned_pay_date: null,
    });
    setDrawerOpen(true);
  };

  const openEdit = (s: any) => {
    setEditingStage({
      id: s.id,
      stage_name: s.stage_name ?? "",
      node_name: s.node_name ?? "",
      payment_terms: s.payment_terms ?? "",
      agreed_ratio: s.agreed_ratio,
      planned_pay_date: s.planned_pay_date ? dayjs(s.planned_pay_date) : null,
    });
    setDrawerOpen(true);
  };

  const closeDrawer = () => {
    setDrawerOpen(false);
    setEditingStage(null);
  };

  // ── Drawer: save ──
  const saveStage = async () => {
    if (!editingStage || !contractId) return;
    if (!editingStage.stage_name.trim()) {
      message.warning("请输入阶段名称");
      return;
    }
    setSaving(true);
    const payload = {
      stage_name: editingStage.stage_name.trim(),
      node_name: editingStage.node_name?.trim() || null,
      payment_terms: editingStage.payment_terms?.trim() || null,
      agreed_ratio: editingStage.agreed_ratio ?? null,
      planned_pay_date: editingStage.planned_pay_date
        ? (editingStage.planned_pay_date.format ? editingStage.planned_pay_date.format("YYYY-MM-DD") : editingStage.planned_pay_date)
        : null,
    };
    // 如果 agreed_ratio 是百分比形式（>1），转为小数
    if (payload.agreed_ratio && payload.agreed_ratio > 1) {
      payload.agreed_ratio = payload.agreed_ratio / 100;
    }
    try {
      if (editingStage.id) {
        await updateContractNode(contractId, editingStage.id, payload);
      } else {
        await createContractNode(contractId, payload);
      }
      message.success("保存成功");
      closeDrawer();
      await reloadStages();
    } catch {
      message.error("保存失败");
    } finally {
      setSaving(false);
    }
  };

  // ── Delete ──
  const handleDelete = async (stageId: string) => {
    if (!contractId) return;
    try {
      await deleteContractNode(contractId, stageId);
      message.success("已删除");
      await reloadStages();
    } catch {
      message.error("删除失败");
    }
  };

  // ── Mark complete ──
  const handleToggleComplete = async (stage: any) => {
    if (!contractId) return;
    try {
      await completeContractNode(contractId, stage.id);
      message.success(stage.is_completed ? "已取消完成" : "已标记完成");
      await reloadStages();
    } catch {
      message.error("操作失败");
    }
  };

  // ── Import from template ──
  const openImportModal = async () => {
    setImportModalOpen(true);
    try {
      const res = await getNodeTemplates({ page: 1, page_size: 50 });
      setTemplates(res.items ?? res ?? []);
    } catch { setTemplates([]); }
  };

  const handleImportFromTemplate = async (template: any) => {
    if (!contractId || !contract) return;
    try {
      await generateNodesFromTemplate(contractId, {
        template_id: template.id,
        contract_amount: contract.contract_amount ?? 0,
        sign_date: contract.sign_date ?? null,
      });
      message.success(`从模板"${template.template_name}"导入成功`);
      setImportModalOpen(false);
      await reloadStages();
    } catch {
      message.error("导入失败");
    }
  };

  // ── Columns ──
  const columns = useMemo(() => {
    const cols: any[] = [
      // 未选择具体合同时显示所属合同列
      ...(!contractId ? [
        {
          title: "合同编号", dataIndex: "contract_no", width: 100, fixed: "left" as const,
          render: (v: string) => <Tag color="blue">{v}</Tag>,
        },
        {
          title: "供应商", dataIndex: "supplier_name", width: 110, ellipsis: true,
          render: (v: string | null) => v || "—",
        },
      ] : []),
      {
        title: "阶段", dataIndex: "stage_name", width: 90,
        render: (v: string) => v || <span style={{ color: "#999" }}>—</span>,
      },
      {
        title: "节点名称", dataIndex: "node_name", width: 110, ellipsis: true,
      render: (v: string) => v ? <Tooltip title={v}>{v}</Tooltip> : "—",
    },
    {
      title: "支付比例", dataIndex: "agreed_ratio", width: 80,
      render: (v: number | null) => v != null ? `${(v * 100).toFixed(1)}%` : "—",
    },
    {
      title: "约定金额(元)", dataIndex: "agreed_amount", width: 110, align: "right" as const,
      render: (v: number | null) => v ? `¥${formatYuanNum(v)}` : "—",
    },
    {
      title: "预计支付日", dataIndex: "planned_pay_date", width: 100,
    },
    {
      title: "报送产值(元)", dataIndex: "reported_amount", width: 100, align: "right" as const,
      render: (v: number | null) => v != null ? `¥${formatYuanNum(v)}` : "—",
    },
    {
      title: "审定产值(元)", dataIndex: "reviewed_amount", width: 100, align: "right" as const,
      render: (v: number | null) => v != null ? `¥${formatYuanNum(v)}` : "—",
    },
    {
      title: "累计已付(元)", dataIndex: "cumulative_paid", width: 110, align: "right" as const,
      render: (v: number | null) => v ? `¥${formatYuanNum(v)}` : "—",
    },
    {
      title: "完成", dataIndex: "is_completed", width: 56, align: "center" as const,
      render: (v: boolean) => (
        <Tag color={v ? "green" : "default"}>{v ? "是" : "否"}</Tag>
      ),
    },
    {
      title: "完成时间", dataIndex: "completed_at", width: 130,
      render: (v: string | null) => v ? dayjs(v).format("YYYY-MM-DD") : "—",
    },
    {
      title: "操作", key: "op", width: 160, fixed: "right" as const,
      render: (_: any, r: any) => (
        <Space size="small">
          <a onClick={() => openEdit(r)}><EditOutlined /></a>
          <a onClick={() => handleToggleComplete(r)}>
            {r.is_completed ? "取消" : "完成"}
          </a>
          <Popconfirm title="确认删除？" onConfirm={() => handleDelete(r.id)}>
            <a style={{ color: "#ff4d4f" }}>删除</a>
          </Popconfirm>
        </Space>
      ),
    },
    ];
    return cols;
  }, [contractId]);

  return (
    <div>
      {/* ── Selector bar ── */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={12} align="middle">
          <Col>
            <span style={{ marginRight: 8 }}>项目：</span>
            <Select
              style={{ width: 200 }}
              value={projectId}
              onChange={(v) => { setProjectId(v); setContractId(null); setContract(null); }}
              options={projects.map((p) => ({ value: p.id, label: p.project_name }))}
            />
          </Col>
          <Col>
            <span style={{ marginRight: 8 }}>合同：</span>
            <Select
              style={{ width: 280 }}
              value={contractId}
              onChange={(v) => { setContractId(v); if (!v) setContract(null); }}
              allowClear
              placeholder="全部合同（不筛选）"
              showSearch
              optionFilterProp="label"
              loading={loadingContracts}
              notFoundContent={loadingContracts ? "加载中…" : "暂无合同"}
              options={contracts.map((c) => ({
                value: c.id,
                label: `${c.contract_no} — ${c.contract_desc?.substring(0, 20)}`,
              }))}
            />
          </Col>
          <Col flex="auto" />
          <Col>
            <Space>
              <Button icon={<ImportOutlined />} onClick={openImportModal} disabled={!contractId}>
                从模板导入
              </Button>
              <Button type="primary" icon={<PlusOutlined />} onClick={openNew} disabled={!contractId}>
                新增节点
              </Button>
            </Space>
          </Col>
        </Row>
        {contract && (
          <div style={{ marginTop: 12, padding: "10px 16px", background: "#f0f5ff", borderRadius: 6, border: "1px solid #e6f0ff" }}>
            <Row gutter={[24, 4]}>
              <Col><Text type="secondary" style={{ fontSize: 12 }}>编号：</Text><Text strong style={{ fontSize: 13 }}>{contract.contract_no}</Text></Col>
              <Col><Text type="secondary" style={{ fontSize: 12 }}>供应商：</Text><Text style={{ fontSize: 13 }}>{contract.supplier_name}</Text></Col>
              <Col><Text type="secondary" style={{ fontSize: 12 }}>类型：</Text><Tag color="purple">{contract.contract_type ?? "二类费用"}</Tag></Col>
              <Col><Text type="secondary" style={{ fontSize: 12 }}>金额：</Text><Text strong style={{ fontSize: 13, color: "#1677ff" }}>¥{formatYuanNum(contract.contract_amount ?? 0)}</Text></Col>
              <Col><Text type="secondary" style={{ fontSize: 12 }}>签订日：</Text><Text style={{ fontSize: 13 }}>{contract.sign_date ?? "—"}</Text></Col>
              <Col><Text type="secondary" style={{ fontSize: 12 }}>审核模式：</Text><Text style={{ fontSize: 13 }}>{contract.review_mode === "daily_aggregate" ? "日报聚合" : contract.review_mode === "node_judge" ? "节点判断" : contract.review_mode === "none" ? "无产值" : contract.review_mode ?? "—"}</Text></Col>
              <Col><Tag color={contract.status === "active" ? "green" : "default"}>{contract.status === "active" ? "生效中" : contract.status}</Tag></Col>
            </Row>
          </div>
        )}
      </Card>

      {/* ── Stats ── */}
      <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
        {[
          { title: "节点总数", val: stats.total, color: "#1677ff" },
          { title: "已完成", val: stats.completed, color: "#52c41a" },
          { title: "待付", val: stats.pending, color: "#fa8c16" },
          { title: "约定总金额", val: `¥${formatYuanNum(stats.totalAgreed)}`, color: "#1677ff" },
          { title: "累计已付", val: `¥${formatYuanNum(stats.totalPaid)}`, color: "#52c41a" },
        ].map((s, i) => (
          <Col xs={12} sm={8} md={Math.floor(24 / 5)} key={i}>
            <Card size="small" style={{ borderLeft: `3px solid ${s.color}`, height: "100%" }}>
              <Statistic
                title={<span style={{ fontSize: 12, color: "#666" }}>{s.title}</span>}
                value={s.val}
                valueStyle={{ color: s.color, fontSize: 18, fontWeight: 600 }}
              />
            </Card>
          </Col>
        ))}
      </Row>

      {/* ── Payment timeline (simplified) ── */}
      {stages.length > 0 && (
        <Card size="small" style={{ marginBottom: 16 }} title="支付节点时间轴">
          <PaymentTimelineSimple stages={stages} signDate={contract?.sign_date ?? null} />
        </Card>
      )}

      {/* ── Table ── */}
      <Card title={`节点列表 — ${contract?.contract_no ?? (projectId ? "全部合同" : "请选择项目")}`}>
        {stages.length === 0 ? (
          <Empty description={contractId ? "暂无支付节点，请新增或从模板导入" : "暂无支付节点"} style={{ padding: 40 }} />
        ) : (
          <Table size="small" rowKey="id" dataSource={stages} columns={columns} loading={loading}
            pagination={false} scroll={{ x: 1500 }}
          />
        )}
      </Card>

      {/* ── Edit Drawer ── */}
      <Drawer
        title={editingStage?.id ? "编辑支付节点" : "新增支付节点"}
        width={480}
        open={drawerOpen}
        onClose={closeDrawer}
        extra={<Space><Button onClick={closeDrawer}>取消</Button><Button type="primary" loading={saving} onClick={saveStage}>保存</Button></Space>}
        destroyOnClose
      >
        {editingStage && (
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <div>
              <div style={{ marginBottom: 4, fontWeight: 600, fontSize: 13 }}>阶段名称 *</div>
              <Input value={editingStage.stage_name}
                onChange={(e) => setEditingStage({ ...editingStage, stage_name: e.target.value })}
                placeholder="如：施工前/预付款、竣工阶段" />
            </div>
            <div>
              <div style={{ marginBottom: 4, fontWeight: 600, fontSize: 13 }}>节点名称</div>
              <Input value={editingStage.node_name}
                onChange={(e) => setEditingStage({ ...editingStage, node_name: e.target.value })}
                placeholder="如：合同签订、竣工验收" />
            </div>
            <div>
              <div style={{ marginBottom: 4, fontWeight: 600, fontSize: 13 }}>支付条款</div>
              <Input.TextArea rows={2} value={editingStage.payment_terms ?? ""}
                onChange={(e) => setEditingStage({ ...editingStage, payment_terms: e.target.value })}
                placeholder="如：合同签订后7日内支付" />
            </div>
            <Row gutter={12}>
              <Col span={12}>
                <div style={{ marginBottom: 4, fontWeight: 600, fontSize: 13 }}>
                  支付比例
                  <Tooltip title="如 30 表示 30%"><span style={{ color: "#999", marginLeft: 4 }}>%</span></Tooltip>
                </div>
                <InputNumber value={editingStage.agreed_ratio != null ? editingStage.agreed_ratio * 100 : null}
                  min={0} max={100} precision={1} style={{ width: "100%" }}
                  onChange={(v) => setEditingStage({ ...editingStage, agreed_ratio: v != null ? v / 100 : null })}
                  placeholder="如 30" />
              </Col>
              <Col span={12}>
                <div style={{ marginBottom: 4, fontWeight: 600, fontSize: 13 }}>
                  {contract?.sign_date ? `预计支付日期（≥ ${contract.sign_date}）` : "预计支付日期"}
                </div>
                <DatePicker style={{ width: "100%" }}
                  value={editingStage.planned_pay_date ?? null}
                  disabledDate={(d) => contract?.sign_date ? d.isBefore(dayjs(contract.sign_date)) : false}
                  onChange={(v) => setEditingStage({ ...editingStage, planned_pay_date: v })} />
              </Col>
            </Row>
            {editingStage.agreed_ratio != null && contract?.contract_amount && (
              <div style={{
                padding: "10px 14px",
                background: "#f6ffed",
                border: "1px solid #b7eb8f",
                borderRadius: 6,
                display: "flex",
                alignItems: "center",
                gap: 8,
              }}>
                <span style={{ fontSize: 13, color: "#666" }}>预估金额：</span>
                <span style={{ fontSize: 18, fontWeight: 700, color: "#1677ff" }}>
                  ¥{formatYuanNum(Math.round(contract.contract_amount * editingStage.agreed_ratio))}
                </span>
                <span style={{ fontSize: 12, color: "#999" }}>
                  = 合同金额 ¥{formatYuanNum(contract.contract_amount)} × {(editingStage.agreed_ratio * 100).toFixed(1)}%
                </span>
              </div>
            )}
          </div>
        )}
      </Drawer>

      {/* ── Import from template Modal ── */}
      <Modal title="从模板导入节点" open={importModalOpen} onCancel={() => setImportModalOpen(false)} footer={null} width={640}>
        {templates.length === 0 ? (
          <Empty description="暂无可用模板" />
        ) : (
          <Table
            size="small"
            rowKey="id"
            dataSource={templates}
            pagination={false}
            columns={[
              { title: "模板名称", dataIndex: "template_name", width: 150 },
              { title: "业务类型", dataIndex: "biz_type", width: 100, render: (v: string) => <Tag color="blue">{v}</Tag> },
              { title: "描述", dataIndex: "description", ellipsis: true },
              { title: "预置", dataIndex: "is_preset", width: 60, render: (v: boolean) => v ? <Tag color="green">是</Tag> : "—" },
              {
                title: "操作", key: "op", width: 80,
                render: (_: any, r: any) => <a onClick={() => handleImportFromTemplate(r)}>导入</a>,
              },
            ]}
          />
        )}
      </Modal>
    </div>
  );
}

// ── Simplified timeline component ──
function PaymentTimelineSimple({ stages, signDate }: { stages: any[]; signDate: string | null }) {
  const sorted = [...stages].sort((a, b) => {
    const da = a.planned_pay_date ?? "9999";
    const db = b.planned_pay_date ?? "9999";
    return da.localeCompare(db);
  });

  // Find timeframe
  const allDates = sorted.map((s) => s.planned_pay_date).filter(Boolean) as string[];
  const startDate = signDate || allDates[0] || "";
  const endDate = allDates[allDates.length - 1] || startDate;

  const CONTAINER_H = 200;
  const AXIS_Y = 90;

  const today = dayjs().format("YYYY-MM-DD");
  const todayRatio = endDate !== startDate
    ? Math.max(0, Math.min(1, (new Date(today).getTime() - new Date(startDate).getTime()) / (new Date(endDate).getTime() - new Date(startDate).getTime())))
    : 0.5;

  const getRatio = (date: string | null) => {
    if (!date || endDate === startDate) return 0.5;
    return Math.max(0, Math.min(1, (new Date(date).getTime() - new Date(startDate).getTime()) / (new Date(endDate).getTime() - new Date(startDate).getTime())));
  };

  const getLeft = (ratio: number) => `calc(48px + (100% - 96px) * ${ratio})`;

  return (
    <div style={{ position: "relative", height: CONTAINER_H, overflow: "hidden" }}>
      {/* Axis */}
      <div style={{ position: "absolute", top: AXIS_Y - 2, left: 48, right: 48, height: 4, background: "#e8e8e8", borderRadius: 2 }} />

      {/* Today marker */}
      <div style={{ position: "absolute", top: 8, left: getLeft(todayRatio), transform: "translateX(-50%)", fontSize: 10, color: "#1677ff", fontWeight: 600, background: "#fff", padding: "1px 4px", borderRadius: 2, whiteSpace: "nowrap", zIndex: 2 }}>今天</div>
      <div style={{ position: "absolute", top: 24, left: getLeft(todayRatio), transform: "translateX(-50%)", width: 1, height: CONTAINER_H - 32, background: "#1677ff", opacity: 0.15, zIndex: 1 }} />

      {/* Date labels */}
      <div style={{ position: "absolute", top: 4, left: 48, fontSize: 10, color: "#999" }}>{startDate}</div>
      <div style={{ position: "absolute", top: 4, right: 48, fontSize: 10, color: "#999" }}>{endDate}</div>

      {/* Nodes */}
      {sorted.map((s, i) => {
        const ratio = getRatio(s.planned_pay_date);
        const isAbove = i % 2 === 0;
        const color = s.is_completed ? "#52c41a" : "#d9d9d9";
        const top = isAbove ? AXIS_Y - 60 : AXIS_Y + 18;
        return (
          <div key={s.id} style={{ position: "absolute", left: getLeft(ratio), transform: "translateX(-50%)", top, zIndex: 3, display: "flex", flexDirection: "column", alignItems: "center" }}>
            {isAbove ? (
              <>
                <div style={{ width: 90, padding: "2px 4px", borderRadius: 4, background: s.is_completed ? "#f6ffed" : "#fafafa", border: `1px solid ${s.is_completed ? "#b7eb8f" : "#f0f0f0"}`, fontSize: 9, lineHeight: "13px", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", textAlign: "center" }}>
                  <div style={{ fontWeight: 600 }}>{s.stage_name || s.node_name || "—"}</div>
                  <div style={{ color: "#1677ff" }}>{s.agreed_ratio != null ? `${(s.agreed_ratio * 100).toFixed(1)}%` : ""}</div>
                  <div style={{ color: "#999" }}>{s.planned_pay_date || "—"}</div>
                </div>
                <div style={{ width: 1, height: 8, background: color }} />
                <div style={{ width: 10, height: 10, borderRadius: "50%", background: color, border: "2px solid #fff", boxShadow: "0 1px 2px rgba(0,0,0,0.15)" }} />
              </>
            ) : (
              <>
                <div style={{ width: 10, height: 10, borderRadius: "50%", background: color, border: "2px solid #fff", boxShadow: "0 1px 2px rgba(0,0,0,0.15)" }} />
                <div style={{ width: 1, height: 8, background: color }} />
                <div style={{ width: 90, padding: "2px 4px", borderRadius: 4, background: s.is_completed ? "#f6ffed" : "#fafafa", border: `1px solid ${s.is_completed ? "#b7eb8f" : "#f0f0f0"}`, fontSize: 9, lineHeight: "13px", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", textAlign: "center" }}>
                  <div style={{ fontWeight: 600 }}>{s.stage_name || s.node_name || "—"}</div>
                  <div style={{ color: "#1677ff" }}>{s.agreed_ratio != null ? `${(s.agreed_ratio * 100).toFixed(1)}%` : ""}</div>
                  <div style={{ color: "#999" }}>{s.planned_pay_date || "—"}</div>
                </div>
              </>
            )}
          </div>
        );
      })}
    </div>
  );
}
