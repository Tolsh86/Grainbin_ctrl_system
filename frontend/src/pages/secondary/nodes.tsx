import { useState, useMemo } from "react";
import {
  Card, Table, Tag, Button, Space, Row, Col, Select, Modal, Input,
  InputNumber, message, Statistic, Tooltip, Empty, Typography, Popconfirm,
  Drawer, Divider, Dropdown,
} from "antd";
import {
  PlusOutlined, EditOutlined, DeleteOutlined, CopyOutlined,
  InfoCircleOutlined, ClockCircleOutlined, CheckCircleFilled,
  CloseCircleFilled, MinusCircleFilled, ImportOutlined,
  CalculatorOutlined, EnvironmentOutlined,
} from "@ant-design/icons";
import {
  mockSecondaryContracts,
  mockPaymentNodes,
  mockNodeTemplates,
  formatYuan,
  PaymentNode,
  NodeTemplate,
} from "../../utils/mock";

const { Text, Title } = Typography;

// ========== 常量 ==========
const statusMap: Record<string, { color: string; text: string }> = {
  paid: { color: "green", text: "已支付" },
  overdue: { color: "red", text: "逾期未付" },
  pending: { color: "default", text: "未到期" },
};

const STATUS_DOT: Record<string, { bg: string; icon: React.ReactNode }> = {
  paid: {
    bg: "#52c41a",
    icon: <CheckCircleFilled style={{ color: "#fff", fontSize: 10 }} />,
  },
  overdue: {
    bg: "#ff4d4f",
    icon: <CloseCircleFilled style={{ color: "#fff", fontSize: 10 }} />,
  },
  pending: {
    bg: "#d9d9d9",
    icon: <MinusCircleFilled style={{ color: "#fff", fontSize: 10 }} />,
  },
};

const FORMULA_PRESETS = [
  { label: "合同金额 x 比例", value: "=合同金额*0.30", desc: "按合同总金额固定比例计算" },
  { label: "固定金额", value: "=1200000", desc: "直接输入固定金额（单位：元，自动转分）" },
  { label: "自定义公式", value: "", desc: "自由输入公式表达式" },
];

// ========== 工具函数 ==========

/** 解析公式计算金额（fen） */
function calcAmount(formula: string, contractAmount: number): number {
  if (!formula) return 0;
  // =合同金额*比例
  const ratioMatch = formula.match(/^=合同金额\*(\d+(?:\.\d+)?)$/);
  if (ratioMatch) {
    return Math.round(contractAmount * parseFloat(ratioMatch[1]));
  }
  // =固定金额（元），需转为分
  const fixedMatch = formula.match(/^=(\d+(?:\.\d+)?)$/);
  if (fixedMatch) {
    return Math.round(parseFloat(fixedMatch[1]) * 100);
  }
  // 直接数字（分）
  const num = parseInt(formula.replace(/[=,]/g, ""), 10);
  if (!isNaN(num)) return num;
  return 0;
}

/** 从合同起始日 + 偏移天数 计算计划日期 */
function calcPlannedDate(startDate: string | null, offsetDays: number): string | null {
  if (!startDate) return null;
  const d = new Date(startDate);
  if (isNaN(d.getTime())) return null;
  d.setDate(d.getDate() + offsetDays);
  return d.toISOString().slice(0, 10);
}

/** 计算两个日期之间的天数差 */
function daysBetween(a: string, b: string): number {
  return (new Date(b).getTime() - new Date(a).getTime()) / 86400000;
}

/** 计算节点在时间轴上的位置比例（0~1） */
function timelineRatio(
  plannedDate: string,
  startDate: string,
  endDate: string,
): number {
  const total = daysBetween(startDate, endDate);
  if (total <= 0) return 0.5;
  const offset = daysBetween(startDate, plannedDate);
  return Math.max(0, Math.min(1, offset / total));
}

/** 构建 CSS calc 表达式：在时间轴上的水平位置 */
function timelineLeft(ratio: number): string {
  // 轴线 left:60px, right:60px → 可用宽度 = (100% - 120px)
  // 位置 = 60px + 可用宽度 * ratio
  return `calc(60px + (100% - 120px) * ${ratio})`;
}

/** 格式化日期为短格式 */
function shortDate(d: string | null): string {
  if (!d) return "—";
  const parts = d.split("-");
  if (parts.length === 3) return `${parts[1]}/${parts[2]}`;
  return d;
}

// ========== 时间轴组件 ==========
function PaymentTimeline({
  nodes,
  contractStart,
  contractEnd,
}: {
  nodes: PaymentNode[];
  contractStart: string;
  contractEnd: string;
}) {
  const today = new Date().toISOString().slice(0, 10);
  const todayRatio = Math.max(0, Math.min(1, timelineRatio(today, contractStart, contractEnd)));

  const positioned = useMemo(() => {
    return nodes.map((n) => ({
      ...n,
      ratio: timelineRatio(n.planned_date, contractStart, contractEnd),
    }));
  }, [nodes, contractStart, contractEnd]);

  if (nodes.length === 0) {
    return (
      <Empty
        description="暂无支付节点"
        image={Empty.PRESENTED_IMAGE_SIMPLE}
        style={{ padding: 24 }}
      />
    );
  }

  // 按日期排序所有节点
  const sorted = useMemo(() => {
    return [...positioned].sort((a, b) => a.planned_date.localeCompare(b.planned_date));
  }, [positioned]);

  // —— 固定布局参数：切换合同时轴线位置不变 ——
  const CONTAINER_H = 360;      // 固定容器总高度
  const AXIS_Y = 160;           // 轴线在容器中的固定 Y 坐标（距顶部 160px）
  const ABOVE_MAX = 6;          // 轴上方最多容纳的节点数
  const BELOW_MAX = 6;          // 轴下方最多容纳的节点数
  const CARD_W = 110;           // 卡片宽度
  const CARD_H = 52;            // 卡片高度
  const DOT_R = 8;              // 圆点半径
  const CONNECTOR = 10;         // 连接线长度

  const axisY = AXIS_Y;

  return (
    <div style={{ position: "relative", height: CONTAINER_H, overflow: "hidden" }}>
      {/* 轴线 */}
      <div
        style={{
          position: "absolute",
          top: axisY - 2, left: 60, right: 60,
          height: 4,
          background: "#e8e8e8",
          borderRadius: 2,
        }}
      />

      {/* 今日标记线 */}
      {todayRatio >= 0 && todayRatio <= 1 && (
        <>
          <div style={{ position: "absolute", top: 12, left: timelineLeft(todayRatio), transform: "translateX(-50%)", zIndex: 2 }}>
            <div style={{ fontSize: 10, color: "#1677ff", fontWeight: 600, background: "#fff", padding: "1px 4px", borderRadius: 2, whiteSpace: "nowrap" }}>今天</div>
          </div>
          <div style={{ position: "absolute", top: 28, left: timelineLeft(todayRatio), transform: "translateX(-50%)", width: 2, height: CONTAINER_H - 36, background: "#1677ff", opacity: 0.2, zIndex: 1 }} />
        </>
      )}

      {/* 起止日期 */}
      <div style={{ position: "absolute", top: 4, left: 60, fontSize: 11, color: "#999", transform: "translateX(-50%)", whiteSpace: "nowrap" }}>{contractStart}</div>
      <div style={{ position: "absolute", top: 4, right: 60, fontSize: 11, color: "#999", transform: "translateX(50%)", whiteSpace: "nowrap" }}>{contractEnd}</div>

      {/* 交替上下渲染节点 */}
      {sorted.map((node, i) => {
        const isAbove = i % 2 === 0;
        const dotColor = node.status === "paid" ? "#52c41a" : node.status === "overdue" ? "#ff4d4f" : "#d9d9d9";
        const cardBg = node.status === "overdue" ? "#fff2f0" : node.status === "paid" ? "#f6ffed" : "#fafafa";
        const cardBorder = node.status === "overdue" ? "#ffccc7" : node.status === "paid" ? "#b7eb8f" : "#f0f0f0";
        const amountStr = `¥${formatYuan(node.amount)}`;
        const dateStr = shortDate(node.planned_date);

        return (
          <div
            key={node.id}
            style={{
              position: "absolute",
              left: timelineLeft(node.ratio),
              transform: "translateX(-50%)",
              top: isAbove ? axisY - DOT_R - CONNECTOR - CARD_H : axisY + DOT_R + CONNECTOR,
              zIndex: 3,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
            }}
          >
            {isAbove ? (
              <>
                {/* 卡片在上 */}
                <div
                  style={{
                    width: CARD_W, padding: "3px 6px", borderRadius: 6,
                    background: cardBg, border: `1px solid ${cardBorder}`,
                    fontSize: 10, lineHeight: "15px", cursor: "pointer",
                    transition: "box-shadow 0.15s",
                  }}
                  onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.boxShadow = "0 2px 6px rgba(0,0,0,0.12)"; }}
                  onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.boxShadow = "none"; }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 3, marginBottom: 1 }}>
                    <span style={{ width: 5, height: 5, borderRadius: "50%", background: dotColor, flexShrink: 0 }} />
                    <span style={{ fontWeight: 600, color: "#262626", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {node.name || "未命名"}
                    </span>
                  </div>
                  <div style={{ color: "#1677ff", fontWeight: 500 }}>{amountStr}</div>
                  <div style={{ color: "#999", fontSize: 9 }}>{dateStr}</div>
                </div>
                {/* 连线向下 */}
                <div style={{ width: 2, height: CONNECTOR, background: dotColor, opacity: 0.5 }} />
                {/* 圆点 */}
                <div style={{ width: DOT_R * 2, height: DOT_R * 2, borderRadius: "50%", background: dotColor, border: "2px solid #fff", boxShadow: "0 1px 3px rgba(0,0,0,0.2)", flexShrink: 0 }} />
              </>
            ) : (
              <>
                {/* 圆点 */}
                <div style={{ width: DOT_R * 2, height: DOT_R * 2, borderRadius: "50%", background: dotColor, border: "2px solid #fff", boxShadow: "0 1px 3px rgba(0,0,0,0.2)", flexShrink: 0 }} />
                {/* 连线向下 */}
                <div style={{ width: 2, height: CONNECTOR, background: dotColor, opacity: 0.5 }} />
                {/* 卡片在下 */}
                <div
                  style={{
                    width: CARD_W, padding: "3px 6px", borderRadius: 6,
                    background: cardBg, border: `1px solid ${cardBorder}`,
                    fontSize: 10, lineHeight: "15px", cursor: "pointer",
                    transition: "box-shadow 0.15s",
                  }}
                  onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.boxShadow = "0 2px 6px rgba(0,0,0,0.12)"; }}
                  onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.boxShadow = "none"; }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 3, marginBottom: 1 }}>
                    <span style={{ width: 5, height: 5, borderRadius: "50%", background: dotColor, flexShrink: 0 }} />
                    <span style={{ fontWeight: 600, color: "#262626", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {node.name || "未命名"}
                    </span>
                  </div>
                  <div style={{ color: "#1677ff", fontWeight: 500 }}>{amountStr}</div>
                  <div style={{ color: "#999", fontSize: 9 }}>{dateStr}</div>
                </div>
              </>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ========== 主页面组件 ==========
export default function NodeManagement() {
  const [selectedContract, setSelectedContract] = useState<string>("sc1");
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [editingNode, setEditingNode] = useState<PaymentNode | null>(null);
  const [isEditing, setIsEditing] = useState(false);

  // 派生数据
  const contract = useMemo(
    () => mockSecondaryContracts.find((c) => c.id === selectedContract) || null,
    [selectedContract],
  );
  const nodes = useMemo<PaymentNode[]>(
    () => mockPaymentNodes[selectedContract] || [],
    [selectedContract],
  );

  // 统计数据
  const stats = useMemo(() => {
    const paidCount = nodes.filter((n) => n.status === "paid").length;
    const overdueCount = nodes.filter((n) => n.status === "overdue").length;
    const pendingCount = nodes.filter((n) => n.status === "pending").length;
    const totalAmount = nodes.reduce((s, n) => s + n.amount, 0);
    const paidAmount = nodes
      .filter((n) => n.status === "paid")
      .reduce((s, n) => s + n.paid_amount, 0);
    return { total: nodes.length, paidCount, overdueCount, pendingCount, totalAmount, paidAmount };
  }, [nodes]);

  // ========== 节点编辑 ==========

  const openNewNode = () => {
    const maxSeq = nodes.length > 0 ? Math.max(...nodes.map((n) => n.seq)) : 0;
    const initialFormula = "=合同金额*0.30";
    setEditingNode({
      id: "",
      contract_id: selectedContract,
      seq: maxSeq + 1,
      name: "",
      trigger: "",
      formula_expr: initialFormula,
      offset_days: 0,
      amount: contract ? calcAmount(initialFormula, contract.contract_amount) : 0,
      planned_date: contract ? (calcPlannedDate(contract.start_date, 0) ?? "") : "",
      actual_date: null,
      status: "pending",
      paid_amount: 0,
    });
    setIsEditing(false);
    setDrawerOpen(true);
  };

  const openEditNode = (node: PaymentNode) => {
    setEditingNode({ ...node });
    setIsEditing(true);
    setDrawerOpen(true);
  };

  const closeDrawer = () => {
    setDrawerOpen(false);
    setEditingNode(null);
  };

  const updateEditingNode = (patch: Partial<PaymentNode>) => {
    setEditingNode((prev) => (prev ? { ...prev, ...patch } : prev));
  };

  const onFormulaPreset = (value: string) => {
    if (!editingNode || !contract) return;
    const amount = calcAmount(value, contract.contract_amount);
    updateEditingNode({ formula_expr: value, amount });
  };

  const onFormulaChange = (value: string) => {
    if (!editingNode || !contract) return;
    const amount = calcAmount(value, contract.contract_amount);
    updateEditingNode({ formula_expr: value, amount });
  };

  const onOffsetChange = (value: number | null) => {
    if (!editingNode || !contract) return;
    const days = value || 0;
    updateEditingNode({
      offset_days: days,
      planned_date: calcPlannedDate(contract.start_date, days) || "",
    });
  };

  const saveNode = () => {
    if (!editingNode) return;
    if (!editingNode.name.trim()) {
      message.warning("请输入节点名称");
      return;
    }
    // 重新计算金额与日期
    if (contract) {
      editingNode.amount = calcAmount(editingNode.formula_expr, contract.contract_amount);
      editingNode.planned_date =
        calcPlannedDate(contract.start_date, editingNode.offset_days) || "";
    }
    if (isEditing) {
      // 更新已有节点
      const list = mockPaymentNodes[selectedContract];
      if (list) {
        const idx = list.findIndex((n) => n.id === editingNode.id);
        if (idx >= 0) list[idx] = { ...editingNode };
      }
      message.success(`节点"${editingNode.name}"已更新`);
    } else {
      // 新增节点
      const list = mockPaymentNodes[selectedContract] || [];
      const maxSeq = list.length > 0 ? Math.max(...list.map((n) => n.seq)) : 0;
      const newNode: PaymentNode = {
        ...editingNode,
        id: `n_${Date.now()}`,
        seq: editingNode.seq || maxSeq + 1,
      };
      if (!mockPaymentNodes[selectedContract]) {
        (mockPaymentNodes as any)[selectedContract] = [];
      }
      mockPaymentNodes[selectedContract].push(newNode);
      message.success(`节点"${newNode.name}"已添加`);
    }
    closeDrawer();
  };

  const copyNode = (node: PaymentNode) => {
    const list = mockPaymentNodes[selectedContract] || [];
    const maxSeq = list.length > 0 ? Math.max(...list.map((n) => n.seq)) : 0;
    const newNode: PaymentNode = {
      ...node,
      id: `n_${Date.now()}`,
      seq: maxSeq + 1,
      name: `${node.name}(复制)`,
      status: "pending",
      actual_date: null,
      paid_amount: 0,
    };
    if (!mockPaymentNodes[selectedContract]) {
      (mockPaymentNodes as any)[selectedContract] = [];
    }
    mockPaymentNodes[selectedContract].push(newNode);
    message.success("已复制节点");
  };

  const deleteNode = (nodeId: string) => {
    const list = mockPaymentNodes[selectedContract];
    if (!list) return;
    const idx = list.findIndex((n) => n.id === nodeId);
    if (idx >= 0) {
      list.splice(idx, 1);
      message.success("节点已删除");
    }
  };

  const importFromTemplate = (template: NodeTemplate) => {
    if (!contract) return;
    const list = mockPaymentNodes[selectedContract] || [];
    const maxSeq = list.length > 0 ? Math.max(...list.map((n) => n.seq)) : 0;
    const newNodes: PaymentNode[] = template.nodes_def.map((def, i) => ({
      id: `n_${Date.now()}_${i}`,
      contract_id: selectedContract,
      seq: maxSeq + 1 + i,
      name: def.name,
      trigger: def.trigger,
      formula_expr: `=合同金额*${(def.ratio / 100).toFixed(2)}`,
      offset_days: def.offset_days,
      amount: calcAmount(
        `=合同金额*${(def.ratio / 100).toFixed(2)}`,
        contract.contract_amount,
      ),
      planned_date: calcPlannedDate(contract.start_date, def.offset_days) || "",
      actual_date: null,
      status: "pending" as const,
      paid_amount: 0,
    }));
    if (!mockPaymentNodes[selectedContract]) {
      (mockPaymentNodes as any)[selectedContract] = [];
    }
    mockPaymentNodes[selectedContract].push(...newNodes);
    message.success(`已从模板"${template.name}"导入 ${newNodes.length} 个节点`);
  };

  // ========== 表格列定义 ==========
  const columns = [
    { title: "#", dataIndex: "seq", width: 48, align: "center" as const },
    {
      title: "节点名称",
      dataIndex: "name",
      width: 120,
      render: (v: string, r: PaymentNode) => (
        <span>
          {v || <span style={{ color: "#999" }}>未命名节点</span>}
          {r.offset_days > 0 && (
            <Tooltip title={`从合同生效起 ${r.offset_days} 天后`}>
              <ClockCircleOutlined style={{ marginLeft: 6, color: "#fa8c16", fontSize: 12 }} />
            </Tooltip>
          )}
        </span>
      ),
    },
    {
      title: "触发条件",
      dataIndex: "trigger",
      width: 150,
      ellipsis: true,
      render: (v: string) => v || <span style={{ color: "#ccc" }}>—</span>,
    },
    {
      title: "公式",
      dataIndex: "formula_expr",
      width: 144,
      render: (v: string) => (
        <Tag color="blue" style={{ fontFamily: "monospace", fontSize: 12 }}>{v}</Tag>
      ),
    },
    {
      title: "金额(元)",
      dataIndex: "amount",
      width: 112,
      align: "right" as const,
      render: (v: number) => <span style={{ fontVariantNumeric: "tabular-nums" }}>¥{formatYuan(v)}</span>,
    },
    {
      title: "偏移天数",
      key: "offset",
      width: 80,
      align: "center" as const,
      render: (_: any, r: PaymentNode) =>
        r.offset_days > 0 ? `${r.offset_days}天` : <span style={{ color: "#ccc" }}>—</span>,
    },
    {
      title: "计划日期",
      dataIndex: "planned_date",
      width: 104,
      render: (v: string) => v || <span style={{ color: "#ccc" }}>—</span>,
    },
    {
      title: "实际日期",
      dataIndex: "actual_date",
      width: 104,
      render: (v: string | null) => v || "—",
    },
    {
      title: "状态",
      dataIndex: "status",
      width: 80,
      align: "center" as const,
      render: (v: string) => <Tag color={statusMap[v]?.color}>{statusMap[v]?.text}</Tag>,
    },
    {
      title: "操作",
      key: "op",
      width: 136,
      render: (_: any, r: PaymentNode) => (
        <Space size="small">
          <a onClick={() => openEditNode(r)}>
            <EditOutlined /> 编辑
          </a>
          <a onClick={() => copyNode(r)}>复制</a>
          <Popconfirm
            title="确认删除该节点？"
            onConfirm={() => deleteNode(r.id)}
            okText="删除"
            cancelText="取消"
          >
            <a style={{ color: "#ff4d4f" }}>删除</a>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // ========== 渲染 ==========

  const templateMenuItems = mockNodeTemplates
    .filter((t) => t.status === "active")
    .map((t) => ({
      key: t.id,
      label: t.name,
      icon: <ImportOutlined />,
      onClick: () => importFromTemplate(t),
    }));

  return (
    <div>
      {/* ===== 1. 合同选择器 + 合同信息摘要 ===== */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={[16, 8]} align="middle">
          <Col>
            <span style={{ fontWeight: 600, marginRight: 8, fontSize: 14 }}>选择合同：</span>
            <Select
              style={{ width: 300 }}
              value={selectedContract}
              onChange={(v) => setSelectedContract(v)}
              showSearch
              optionFilterProp="label"
              options={mockSecondaryContracts.map((c) => ({
                value: c.id,
                label: `${c.contract_name}（${c.contractor}）`,
              }))}
            />
          </Col>
          <Col flex="auto" />
          <Col>
            <Space>
              <Button type="primary" icon={<PlusOutlined />} onClick={openNewNode}>
                新增节点
              </Button>
              <Dropdown menu={{ items: templateMenuItems }} placement="bottomRight" disabled={templateMenuItems.length === 0}>
                <Button icon={<ImportOutlined />}>
                  从模板导入
                </Button>
              </Dropdown>
            </Space>
          </Col>
        </Row>

        {/* 合同摘要信息 */}
        {contract && (
          <div
            style={{
              marginTop: 12,
              padding: "10px 16px",
              background: "linear-gradient(135deg, #f0f5ff 0%, #f6f8fa 100%)",
              borderRadius: 6,
              border: "1px solid #e6f0ff",
            }}
          >
            <Row gutter={[32, 4]}>
              <Col>
                <Text type="secondary" style={{ fontSize: 12 }}>合同名称：</Text>
                <Text strong style={{ fontSize: 13 }}>{contract.contract_name}</Text>
              </Col>
              <Col>
                <Text type="secondary" style={{ fontSize: 12 }}>承接单位：</Text>
                <Text style={{ fontSize: 13 }}>{contract.contractor}</Text>
              </Col>
              <Col>
                <Text type="secondary" style={{ fontSize: 12 }}>费用类型：</Text>
                <Tag color="purple" style={{ marginLeft: 0 }}>{contract.fee_type}</Tag>
              </Col>
              <Col>
                <Text type="secondary" style={{ fontSize: 12 }}>总金额：</Text>
                <Text strong style={{ fontSize: 13, color: "#1677ff" }}>
                  ¥{formatYuan(contract.contract_amount)}
                </Text>
              </Col>
              <Col>
                <Text type="secondary" style={{ fontSize: 12 }}>合同期限：</Text>
                <Text style={{ fontSize: 13 }}>
                  {contract.start_date || "—"} ~ {contract.end_date || "—"}
                </Text>
              </Col>
              <Col>
                <Tag color={contract.status === "active" ? "green" : "default"}>
                  {contract.status === "active" ? "履行中" : contract.status}
                </Tag>
              </Col>
            </Row>
          </div>
        )}
      </Card>

      {/* ===== 2. 统计卡片 ===== */}
      <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
        {[
          { title: "节点总数", val: stats.total, color: "#1677ff" },
          { title: "已支付", val: stats.paidCount, color: "#52c41a" },
          { title: "逾期未付", val: stats.overdueCount, color: "#ff4d4f" },
          { title: "待支付", val: stats.pendingCount, color: "#999" },
          { title: "总金额", val: `¥${formatYuan(stats.totalAmount)}`, color: "#1677ff" },
          { title: "已支付金额", val: `¥${formatYuan(stats.paidAmount)}`, color: "#52c41a" },
        ].map((s, i) => (
          <Col xs={12} sm={8} md={4} key={i}>
            <Card
              size="small"
              style={{
                borderLeft: `3px solid ${s.color}`,
                height: "100%",
              }}
              bodyStyle={{ padding: "12px 16px" }}
            >
              <Statistic
                title={<span style={{ fontSize: 12, color: "#666" }}>{s.title}</span>}
                value={s.val}
                valueStyle={{ color: s.color, fontSize: 20, fontWeight: 600 }}
              />
            </Card>
          </Col>
        ))}
      </Row>

      {/* ===== 3. 支付节点时间轴 ===== */}
      {contract && (
        <Card
          size="small"
          style={{ marginBottom: 16 }}
          title={
            <Space>
              <EnvironmentOutlined style={{ color: "#1677ff" }} />
              <span style={{ fontWeight: 600, fontSize: 14 }}>支付节点时间轴</span>
            </Space>
          }
          extra={
            <Space size={4} style={{ fontSize: 12, color: "#999" }}>
              <span style={{ display: "inline-block", width: 10, height: 10, borderRadius: "50%", background: "#52c41a" }} />
              <span>已支付</span>
              <span style={{ display: "inline-block", width: 10, height: 10, borderRadius: "50%", background: "#ff4d4f", marginLeft: 8 }} />
              <span>逾期</span>
              <span style={{ display: "inline-block", width: 10, height: 10, borderRadius: "50%", background: "#d9d9d9", marginLeft: 8 }} />
              <span>未到期</span>
            </Space>
          }
        >
          <PaymentTimeline
            nodes={nodes}
            contractStart={contract.start_date}
            contractEnd={contract.end_date}
          />
        </Card>
      )}

      {/* ===== 4. 节点列表表格 ===== */}
      <Card
        title={
          <Space>
            <span style={{ fontWeight: 600, fontSize: 14 }}>
              节点列表 — {contract?.contract_name || ""}
            </span>
          </Space>
        }
        extra={
          <Space size="small">
            <InfoCircleOutlined style={{ color: "#999" }} />
            <Text type="secondary" style={{ fontSize: 12 }}>
              支持公式：=合同金额*比例 或 =固定金额(元)
            </Text>
          </Space>
        }
      >
        {nodes.length === 0 ? (
          <Empty description="暂无支付节点，请新增节点或从模板导入" style={{ padding: 40 }} />
        ) : (
          <Table
            size="small"
            rowKey="id"
            dataSource={nodes}
            columns={columns}
            pagination={false}
            scroll={{ x: 1080 }}
          />
        )}
      </Card>

      {/* ===== 5. 节点编辑抽屉 ===== */}
      <Drawer
        title={
          <Space>
            <CalculatorOutlined style={{ color: "#1677ff" }} />
            <span>{isEditing ? "编辑支付节点" : "新增支付节点"}</span>
          </Space>
        }
        width={560}
        open={drawerOpen}
        onClose={closeDrawer}
        extra={
          <Space>
            <Button onClick={closeDrawer}>取消</Button>
            <Button type="primary" onClick={saveNode}>
              保存
            </Button>
          </Space>
        }
        destroyOnClose
      >
        {editingNode && contract && (
          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
            {/* 基本信息 */}
            <Row gutter={12}>
              <Col span={12}>
                <div style={{ marginBottom: 4, fontWeight: 600, fontSize: 13 }}>
                  节点名称 <span style={{ color: "#ff4d4f" }}>*</span>
                </div>
                <Input
                  value={editingNode.name}
                  onChange={(e) => updateEditingNode({ name: e.target.value })}
                  placeholder="如：中期监理费"
                />
              </Col>
              <Col span={6}>
                <div style={{ marginBottom: 4, fontWeight: 600, fontSize: 13 }}>序号</div>
                <InputNumber
                  value={editingNode.seq}
                  min={1}
                  style={{ width: "100%" }}
                  onChange={(v) => updateEditingNode({ seq: v || 0 })}
                />
              </Col>
              <Col span={6}>
                <div style={{ marginBottom: 4, fontWeight: 600, fontSize: 13 }}>状态</div>
                <Select
                  style={{ width: "100%" }}
                  value={editingNode.status}
                  onChange={(v) => updateEditingNode({ status: v as PaymentNode["status"] })}
                  options={[
                    { value: "pending", label: "未到期" },
                    { value: "overdue", label: "逾期未付" },
                    { value: "paid", label: "已支付" },
                  ]}
                />
              </Col>
            </Row>

            {/* 公式编辑器 */}
            <div
              style={{
                background: "linear-gradient(135deg, #fffbe6 0%, #fff7e6 100%)",
                padding: "16px 18px",
                borderRadius: 8,
                border: "1px solid #ffe58f",
              }}
            >
              <div style={{ marginBottom: 12, fontWeight: 600, fontSize: 14, color: "#ad6800" }}>
                <CalculatorOutlined style={{ marginRight: 6 }} />
                付款公式编辑器
              </div>

              {/* 预置公式 */}
              <div style={{ marginBottom: 10 }}>
                <div style={{ marginBottom: 4, fontSize: 12, color: "#666" }}>选择预置公式模板</div>
                <Select
                  style={{ width: "100%" }}
                  placeholder="选择预置公式模板..."
                  onChange={onFormulaPreset}
                  allowClear
                  options={FORMULA_PRESETS.map((p) => ({
                    value: p.value,
                    label: (
                      <span>
                        {p.label}
                        <span style={{ color: "#999", marginLeft: 8, fontSize: 11 }}>{p.desc}</span>
                      </span>
                    ),
                  }))}
                />
              </div>

              {/* 公式输入 */}
              <div style={{ marginBottom: 10 }}>
                <div style={{ marginBottom: 4, fontSize: 12, color: "#666" }}>公式表达式</div>
                <Input
                  value={editingNode.formula_expr}
                  onChange={(e) => onFormulaChange(e.target.value)}
                  addonBefore={<span style={{ fontWeight: 700, color: "#1677ff" }}>=</span>}
                  placeholder="合同金额*0.30 或 1200000（元）"
                  style={{ fontFamily: "monospace" }}
                />
              </div>

              {/* 可用变量提示 */}
              <div
                style={{
                  padding: "8px 12px",
                  background: "#fff",
                  borderRadius: 4,
                  border: "1px solid #f0f0f0",
                  marginBottom: 8,
                }}
              >
                <Text type="secondary" style={{ fontSize: 12 }}>
                  可用变量：<Tag color="blue" style={{ fontSize: 11, fontFamily: "monospace" }}>合同金额</Tag>
                  当前合同总金额：
                  <Text strong style={{ color: "#1677ff", fontFamily: "monospace" }}>
                    ¥{formatYuan(contract.contract_amount)}
                  </Text>
                </Text>
              </div>

              {/* 实时计算结果 */}
              <div
                style={{
                  padding: "10px 14px",
                  background: "#f6ffed",
                  borderRadius: 4,
                  border: "1px solid #b7eb8f",
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                }}
              >
                <Text style={{ fontSize: 13, color: "#52c41a" }}>计算结果：</Text>
                <Text strong style={{ fontSize: 18, color: "#389e0d", fontFamily: "monospace" }}>
                  ¥{formatYuan(editingNode.amount)}
                </Text>
              </div>
            </div>

            {/* 触发条件 */}
            <div>
              <div style={{ marginBottom: 4, fontWeight: 600, fontSize: 13 }}>触发条件</div>
              <Input
                value={editingNode.trigger}
                onChange={(e) => updateEditingNode({ trigger: e.target.value })}
                placeholder="如：竣工验收通过后"
              />
            </div>

            {/* 时间偏移 + 实际日期 */}
            <Row gutter={12}>
              <Col span={12}>
                <div style={{ marginBottom: 4, fontWeight: 600, fontSize: 13 }}>
                  时间偏移
                  <Tooltip title="从合同生效日起，多少天后触发该节点">
                    <InfoCircleOutlined style={{ marginLeft: 6, color: "#999", fontSize: 12 }} />
                  </Tooltip>
                </div>
                <InputNumber
                  value={editingNode.offset_days}
                  min={0}
                  max={3650}
                  style={{ width: "100%" }}
                  addonAfter="天"
                  onChange={onOffsetChange}
                  placeholder="0 = 合同生效日"
                />
                {editingNode.planned_date && (
                  <div style={{ marginTop: 4, fontSize: 12, color: "#1677ff" }}>
                    预计日期：{editingNode.planned_date}
                  </div>
                )}
              </Col>
              <Col span={12}>
                <div style={{ marginBottom: 4, fontWeight: 600, fontSize: 13 }}>实际支付日期</div>
                <Input
                  value={editingNode.actual_date || ""}
                  onChange={(e) => updateEditingNode({ actual_date: e.target.value || null })}
                  placeholder="支付时填写，如 2026-06-30"
                />
              </Col>
            </Row>

            <Divider style={{ margin: "4px 0" }} />

            {/* 已支付金额（已支付状态时显示） */}
            {editingNode.status === "paid" && (
              <div>
                <div style={{ marginBottom: 4, fontWeight: 600, fontSize: 13 }}>实际支付金额（分）</div>
                <InputNumber
                  value={editingNode.paid_amount}
                  min={0}
                  style={{ width: "100%" }}
                  onChange={(v) => updateEditingNode({ paid_amount: v || 0 })}
                  placeholder="实际到账金额"
                />
                <div style={{ marginTop: 4, fontSize: 12, color: "#52c41a" }}>
                  ¥{formatYuan(editingNode.paid_amount)}
                </div>
              </div>
            )}
          </div>
        )}
      </Drawer>
    </div>
  );
}
