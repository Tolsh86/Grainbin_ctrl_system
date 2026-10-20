import { useState, useEffect, useCallback } from "react";
import {
  Card, Table, Tag, Button, Space, Row, Col, Input, Select, Drawer, AutoComplete,
  Form, InputNumber, message, Statistic, DatePicker, Tooltip, Divider, Popconfirm,
} from "antd";
import {
  PlusOutlined, SearchOutlined,
} from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import dayjs from "dayjs";
import { getProjects } from "../../api/projects";
import {
  getContractGroups,
  getReviewModes,
  getLedgerGroups,
  getContractNos,
  createContract as apiCreateContract,
  updateContract as apiUpdateContract,
  deleteContract as apiDeleteContract,
  getContractNodes,
} from "../../api/contracts";
import type { ContractGroup, ReviewMode, LedgerGroup } from "../../api/contracts";

// ── Helpers ──
const formatYuanNum = (fen: number) =>
  (fen / 100).toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

const statusMap: Record<string, { color: string; text: string }> = {
  active: { color: "green", text: "生效中" },
  terminated: { color: "red", text: "已终止" },
  expired: { color: "default", text: "已到期" },
};

const reviewModeLabels: Record<string, { color: string; text: string }> = {
  daily_aggregate: { color: "blue", text: "日报聚合" },
  node_judge: { color: "green", text: "节点判断" },
  none: { color: "default", text: "无产值" },
};

// ── Page component ──
export default function ContractsList() {
  const navigate = useNavigate();

  // project selector
  const [projects, setProjects] = useState<any[]>([]);
  const [projectId, setProjectId] = useState<string | null>(null);

  // grouped contracts
  const [groups, setGroups] = useState<ContractGroup[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");

  // payment stages cache
  const [stageCache, setStageCache] = useState<Record<string, any[]>>({});

  // drawer
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [editingContract, setEditingContract] = useState<any>(null);
  const [saving, setSaving] = useState(false);
  const [form] = Form.useForm();

	// contract group options from backend
  const [existingGroups, setExistingGroups] = useState<string[]>([]);

  // existing contract_no list for AutoComplete
  const [existingNos, setExistingNos] = useState<string[]>([]);

  // sub-type options from backend (with Chinese fallback)
  const [reviewModeOptions, setReviewModeOptions] = useState<ReviewMode[]>([
    { value: "daily_aggregate", label: "日报聚合模式", description: "建安工程/设备采购类，审核工作台读取日报数据" },
    { value: "node_judge", label: "节点判断模式", description: "咨询/服务类，过控手动判断节点是否达成" },
    { value: "none", label: "无产值模式", description: "土地/招标代理/农民工专户类，不参与审核" },
  ]);
  const [ledgerGroupOptions, setLedgerGroupOptions] = useState<LedgerGroup[]>([
    { value: "construction", label: "建安合计" },
    { value: "equipment", label: "设备合计" },
    { value: "service", label: "二类费用合计" },
    { value: "none", label: "不计入台账" },
  ]);

  // node modal
  const [nodeModalOpen, setNodeModalOpen] = useState(false);
  const [nodeContract, setNodeContract] = useState<any>(null);

  // ── Load projects ──
  useEffect(() => {
    getProjects({ page: 1, page_size: 100 }).then((res) => {
      const list = res.items ?? res ?? [];
      setProjects(list);
      if (list.length > 0 && !projectId) setProjectId(list[0].id);
    }).catch(() => {});
    getReviewModes().then((modes) => {
      setReviewModeOptions(modes);
    }).catch(() => {});
    getLedgerGroups().then((groups) => {
      setLedgerGroupOptions(groups);
    }).catch(() => {});
  }, []);

  // ── Load grouped contracts ──
  const loadGroups = useCallback(() => {
    if (!projectId) return;
    setLoading(true);
    getContractGroups(projectId)
      .then((data) => setGroups(data ?? []))
      .catch(() => message.error("加载合同失败"))
      .finally(() => setLoading(false));
  }, [projectId]);

  useEffect(() => {
    loadGroups();
  }, [loadGroups]);

  // Load existing contract groups + nos for dropdown
  useEffect(() => {
    if (!projectId) return;
    getContractGroups(projectId)
      .then((data) => {
        const names = (data ?? []).map((g) => g.contract_group).filter((n) => n && n !== "__ungrouped__") as string[];
        setExistingGroups([...new Set(names)]);
      })
      .catch(() => {});
    getContractNos(projectId)
      .then((data) => setExistingNos(data ?? []))
      .catch(() => {});
  }, [projectId, groups]);

  // ── Load payment stages ──
  const allContracts = groups.flatMap((g) => g.contracts);
  useEffect(() => {
    allContracts.forEach((c) => {
      if (!stageCache[c.id]) {
        getContractNodes(c.id)
          .then((nodes) => setStageCache((prev) => ({ ...prev, [c.id]: nodes ?? [] })))
          .catch(() => {});
      }
    });
  }, [groups]);

  // ── Stats ──
  const activeContracts = allContracts.filter((c) => c.status === "active");
  const totalAmount = activeContracts.reduce((s: number, c: any) => s + (c.contract_amount ?? 0), 0);
  const allStages = Object.values(stageCache).flat();
  const totalPaid = allStages.filter((n: any) => n.is_completed).reduce((s: number, n: any) => s + (n.cumulative_paid ?? 0), 0);

  // ── Drawer ──
  const openNew = () => {
    setEditingContract(null);
    form.resetFields();
    setDrawerOpen(true);
  };

  const openEdit = (c: any) => {
    setEditingContract(c);
    form.setFieldsValue({
      contract_no: c.contract_no,
      contract_desc: c.contract_desc,
      supplier_name: c.supplier_name,
      review_mode: c.review_mode || "node_judge",
      ledger_group: c.ledger_group || "service",
      contract_group: c.contract_group,
      contract_amount: c.contract_amount ? c.contract_amount / 100 : undefined,
      sign_date: c.sign_date ? dayjs(c.sign_date) : null,
      status: c.status,
    });
    setDrawerOpen(true);
  };

  const saveContract = useCallback(() => {
    form.validateFields().then(async (values: any) => {
      setSaving(true);

      const payload = {
        ...values,
        contract_type: "secondary",
        contract_amount: Math.round((values.contract_amount ?? 0) * 100),
        sign_date: values.sign_date ? values.sign_date.format("YYYY-MM-DD") : null,
      };
      try {
        if (editingContract) {
          await apiUpdateContract(editingContract.id, payload);
        } else {
          await apiCreateContract(projectId!, payload);
        }
        message.success("保存成功");
        setDrawerOpen(false);
        loadGroups();
      } catch {
        message.error("保存失败");
      } finally {
        setSaving(false);
      }
    }).catch(() => {});
  }, [editingContract, projectId, form, loadGroups]);

  // ── Node modal ──
  const openNodes = (c: any) => {
    setNodeContract(c);
    setNodeModalOpen(true);
  };

  // ── Delete ──
  const handleDelete = async (id: string) => {
    try {
      await apiDeleteContract(id);
      message.success("合同已删除");
      setStageCache((prev) => { const { [id]: _, ...rest } = prev; return rest; });
      loadGroups();
    } catch {
      message.error("删除失败");
    }
  };

  // ── Columns ──
  const cols = [
    {
      title: "合同编号", dataIndex: "contract_no", key: "no", width: 110,
      render: (v: string, r: any) => <a onClick={() => openEdit(r)}>{v}</a>,
    },
    {
      title: "合同描述", dataIndex: "contract_desc", key: "desc", width: 160,
      ellipsis: true,
      render: (v: string) => <Tooltip title={v}>{v || "—"}</Tooltip>,
    },
    {
      title: "审核模式", dataIndex: "review_mode", key: "reviewMode", width: 80,
      render: (v: string) => {
        const m = reviewModeLabels[v] ?? { color: "default", text: v ?? "—" };
        return <Tag color={m.color}>{m.text}</Tag>;
      },
    },
    {
      title: "台账分组", dataIndex: "ledger_group", key: "ledgerGroup", width: 80,
      render: (v: string) => {
        const labels: Record<string, string> = {
          construction: "建安", equipment: "设备", service: "二类", none: "不计入",
        };
        return <Tag>{labels[v] ?? v ?? "—"}</Tag>;
      },
    },
    {
      title: "供应商", dataIndex: "supplier_name", key: "supplier", width: 120,
      ellipsis: true,
      render: (v: string) => <Tooltip title={v}>{v || "—"}</Tooltip>,
    },
    {
      title: "合同金额", dataIndex: "contract_amount", key: "amount", width: 110,
      align: "right" as const,
      render: (v: number) => v ? `¥${formatYuanNum(v)}` : "—",
    },
    {
      title: "签订日期", dataIndex: "sign_date", key: "date", width: 100,
    },
    {
      title: "节点", key: "stages", width: 100,
      render: (_: any, r: any) => {
        const stages = stageCache[r.id];
        if (!stages) return <span style={{ color: "#999" }}>—</span>;
        const done = stages.filter((s: any) => s.is_completed).length;
        return <span><span style={{ color: "#52c41a", fontWeight: 500 }}>{done}</span>/{stages.length}</span>;
      },
    },
    {
      title: "状态", dataIndex: "status", key: "st", width: 80,
      render: (v: string) => (
        <Tag color={statusMap[v]?.color}>{statusMap[v]?.text ?? v}</Tag>
      ),
    },
    {
      title: "操作", key: "op", width: 220, fixed: "right" as const,
      render: (_: any, r: any) => (
        <Space size="small">
          <a onClick={() => openEdit(r)}>编辑</a>
          <a onClick={() => navigate(`/contracts/${r.id}/fee-items`)}>费用分项</a>
          <a onClick={() => openNodes(r)}>节点</a>
          <Popconfirm title="确定删除此合同？" description="删除后不可恢复" onConfirm={() => handleDelete(r.id)} okText="删除" cancelText="取消" okButtonProps={{ danger: true }}>
            <a style={{ color: "#ff4d4f" }}>删除</a>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      {/* ── Project selector ── */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={12} align="middle">
          <Col>
            <span style={{ marginRight: 8 }}>项目：</span>
            <Select
              style={{ width: 260 }}
              value={projectId}
              onChange={(v) => { setProjectId(v); setStageCache({}); }}
              options={projects.map((p) => ({ value: p.id, label: p.project_name }))}
            />
          </Col>
          <Col flex="auto">
            <Input
              placeholder="搜索合同编号 / 描述 / 供应商"
              prefix={<SearchOutlined />}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              allowClear
            />
          </Col>
          <Col>
            <Button type="primary" icon={<PlusOutlined />} onClick={openNew} disabled={!projectId}>
              新建合同
            </Button>
          </Col>
        </Row>
      </Card>

      {/* ── Stats ── */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        {[
          { title: "合同总额（生效中）", value: `¥${formatYuanNum(totalAmount)}`, color: "#1677ff" },
          { title: "已支付", value: `¥${formatYuanNum(totalPaid)}`, color: "#52c41a" },
          { title: "生效合同", value: activeContracts.length, color: "#722ed1", suffix: " 份" },
        ].map((s, i) => (
          <Col xs={24} sm={8} key={i}>
            <Card size="small">
              <Statistic title={s.title} value={s.value} suffix={(s as any).suffix} valueStyle={{ color: s.color }} />
            </Card>
          </Col>
        ))}
      </Row>

      {/* ── Grouped Table ── */}
      <Card title="二类费用合同">
        {groups.map((group) => {
          const groupContracts = group.contracts;
          const filteredGroup = search
            ? groupContracts.filter(
                (c) =>
                  (c.contract_desc ?? "").includes(search) ||
                  (c.supplier_name ?? "").includes(search) ||
                  (c.contract_no ?? "").includes(search)
              )
            : groupContracts;

          if (filteredGroup.length === 0) return null;

          return (
            <div key={group.contract_group} style={{ marginBottom: 16 }}>
              <Divider orientation="left" style={{ fontSize: 14, fontWeight: 600 }}>
                {group.contract_group === "__ungrouped__" ? "未分组" : group.contract_group}
              </Divider>
              <Table
                columns={cols}
                dataSource={filteredGroup}
                loading={loading}
                size="small"
                rowKey="id"
                pagination={false}
                scroll={{ x: 1300 }}
              />
            </div>
          );
        })}

        {groups.length === 0 && !loading && (
          <div style={{ textAlign: "center", padding: 40, color: "#999" }}>暂无合同数据</div>
        )}
      </Card>

      {/* ── Drawer ── */}
      <Drawer
        title={editingContract ? "编辑合同" : "新建合同"}
        width={640}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        extra={
          <Space>
            <Button onClick={() => setDrawerOpen(false)}>取消</Button>
            <Button type="primary" loading={saving} onClick={saveContract}>保存</Button>
          </Space>
        }
      >
        <Form form={form} layout="vertical" initialValues={{ review_mode: "node_judge", ledger_group: "service" }}>
          <Form.Item name="contract_no" label="合同编号" rules={[{ required: true }]}>
            <AutoComplete
              placeholder="输入编号或下拉选择已有"
              options={existingNos.map((no) => ({ value: no, label: no }))}
              filterOption={(inputValue, option) =>
                (option?.value ?? "").toUpperCase().includes(inputValue.toUpperCase())
              }
            />
          </Form.Item>
          <Form.Item name="contract_desc" label="合同描述" rules={[{ required: true }]}>
            <Input placeholder="如：监理服务合同" />
          </Form.Item>
          <Form.Item name="supplier_name" label="供应商/承包单位" rules={[{ required: true }]}>
            <Input placeholder="如：建科监理公司" />
          </Form.Item>
          <Form.Item name="review_mode" label="审核模式" rules={[{ required: true }]} tooltip="决定审核工作台如何取数：日报聚合→读日报数据；节点判断→手动判断节点；无产值→不参与审核">
            <Select
              options={reviewModeOptions.map((m) => ({
                value: m.value,
                label: `${m.label} — ${m.description}`,
              }))}
            />
          </Form.Item>
          <Form.Item name="ledger_group" label="台账分组" rules={[{ required: true }]} tooltip="决定导出报表时该合同计入哪个分项汇总">
            <Select options={ledgerGroupOptions} />
          </Form.Item>
          <Form.Item name="contract_group" label="合同组（同项目下多份合同归组）">
            <AutoComplete
              allowClear
              placeholder="输入新组名或下拉选择已有"
              options={existingGroups.map((g) => ({ value: g, label: g }))}
              filterOption={(inputValue, option) =>
                (option?.value ?? "").toUpperCase().includes(inputValue.toUpperCase())
              }
            />
          </Form.Item>
          <Form.Item name="contract_amount" label="合同金额（元）" rules={[{ required: true }]}>
            <InputNumber
              style={{ width: "100%" }}
              min={0}
              precision={2}
              formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ",")}
              parser={(value) => value?.replace(/,/g, "") as any}
            />
          </Form.Item>
          <Form.Item name="sign_date" label="签订日期">
            <DatePicker style={{ width: "100%" }} />
          </Form.Item>

          {editingContract && (
            <Form.Item name="status" label="状态">
              <Select
                options={[
                  { value: "active", label: "生效中" },
                  { value: "expired", label: "已到期" },
                  { value: "terminated", label: "已终止" },
                ]}
              />
            </Form.Item>
          )}
        </Form>
      </Drawer>

      {/* ── Node preview Modal ── */}
      <NodePreviewModal
        open={nodeModalOpen}
        contract={nodeContract}
        stages={nodeContract ? stageCache[nodeContract.id] ?? [] : []}
        onClose={() => setNodeModalOpen(false)}
        onGoToNodes={() => { setNodeModalOpen(false); navigate("/secondary/nodes"); }}
      />
    </div>
  );
}

// ── Node preview sub-component ──
function NodePreviewModal({
  open, contract, stages, onClose, onGoToNodes,
}: {
  open: boolean; contract: any; stages: any[]; onClose: () => void; onGoToNodes: () => void;
}) {
  return (
    <Drawer
      title={contract ? `支付节点 — ${contract.contract_no}` : "支付节点"}
      width={720}
      open={open}
      onClose={onClose}
      extra={
        <Button type="primary" onClick={onGoToNodes}>前往节点管理</Button>
      }
    >
      {stages.length > 0 ? (
        <Table
          size="small"
          rowKey="id"
          pagination={false}
          dataSource={stages}
          columns={[
            { title: "阶段", dataIndex: "stage_name", width: 80 },
            { title: "节点名称", dataIndex: "node_name", width: 100, ellipsis: true },
            { title: "支付比例", dataIndex: "agreed_ratio", width: 80, render: (v: number) => v ? `${(v * 100).toFixed(1)}%` : "—" },
            { title: "约定金额", dataIndex: "agreed_amount", width: 110, align: "right" as const, render: (v: number) => v ? `¥${(v / 100).toLocaleString("zh-CN", { minimumFractionDigits: 2 })}` : "—" },
            { title: "预计支付日", dataIndex: "planned_pay_date", width: 100 },
            { title: "累计已付", dataIndex: "cumulative_paid", width: 110, align: "right" as const, render: (v: number) => v ? `¥${(v / 100).toLocaleString("zh-CN", { minimumFractionDigits: 2 })}` : "—" },
            {
              title: "完成", dataIndex: "is_completed", width: 60,
              render: (v: boolean) => <Tag color={v ? "green" : "default"}>{v ? "是" : "否"}</Tag>,
            },
          ]}
        />
      ) : (
        <div style={{ textAlign: "center", padding: 40, color: "#999" }}>暂未配置支付节点</div>
      )}
    </Drawer>
  );
}
