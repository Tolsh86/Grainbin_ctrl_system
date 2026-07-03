import { useState, useCallback } from "react";
import {
  Card, Table, Tag, Button, Space, Row, Col, Input, Select, Drawer,
  Form, InputNumber, message, Statistic, Modal, DatePicker,
} from "antd";
import {
  PlusOutlined, SearchOutlined, SettingOutlined, RightOutlined,
  ExportOutlined,
} from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import dayjs, { Dayjs } from "dayjs";
import {
  mockSecondaryContracts,
  mockPaymentNodes,
  mockFeeTypes,
  formatYuan,
} from "../../utils/mock";

// ── Status maps ──────────────────────────────────────────────
const contractStatusMap: Record<string, { color: string; text: string }> = {
  active:     { color: "green",   text: "生效中" },
  terminated: { color: "red",     text: "已终止" },
  expired:    { color: "default", text: "已到期" },
};

const nodeStatusMap: Record<string, { color: string; text: string }> = {
  paid:    { color: "green",   text: "已付" },
  overdue: { color: "red",     text: "逾期" },
  pending: { color: "default", text: "待付" },
};

// ── Page component ───────────────────────────────────────────
export default function ContractsList() {
  const navigate = useNavigate();

  // ── Local state ────────────────────────────────────────────
  const [drawerOpen,      setDrawerOpen]      = useState(false);
  const [editingContract, setEditingContract] = useState<any>(null);
  const [search,          setSearch]           = useState("");
  const [feeTypes,        setFeeTypes]         = useState<string[]>([...mockFeeTypes]);
  const [nodeModalOpen,   setNodeModalOpen]    = useState(false);
  const [nodeContractId,  setNodeContractId]   = useState<string | null>(null);

  const [form] = Form.useForm();

  // ── Derived data ───────────────────────────────────────────
  let filtered = mockSecondaryContracts;
  if (search) {
    filtered = filtered.filter(
      (c) =>
        c.contract_name.includes(search) ||
        c.contractor.includes(search)
    );
  }

  const activeContracts    = mockSecondaryContracts.filter((c) => c.status === "active");
  const totalContractAmount = activeContracts.reduce((s, c) => s + c.contract_amount, 0);
  const allNodes           = Object.values(mockPaymentNodes).flat();
  const totalPaid          = allNodes.filter((n) => n.status === "paid").reduce((s, n) => s + n.paid_amount, 0);
  const totalUnpaid        = allNodes.filter((n) => n.status !== "paid").reduce((s, n) => s + n.amount, 0);
  const activeCount        = activeContracts.length;

  // ── Node preview helper ────────────────────────────────────
  const renderNodesPreview = (contractId: string) => {
    const nodes = mockPaymentNodes[contractId];
    if (!nodes || nodes.length === 0) {
      return <span style={{ color: "#999" }}>未配置</span>;
    }
    const paid  = nodes.filter((n) => n.status === "paid").length;
    const total = nodes.length;
    return (
      <span>
        <span style={{ color: "#52c41a", fontWeight: 500 }}>{paid}</span>
        /{total} 节点已支付
      </span>
    );
  };

  // ── Drawer open handlers ────────────────────────────────────
  const openNew = () => {
    setEditingContract(null);
    form.resetFields();
    setDrawerOpen(true);
  };

  const openEdit = (c: any) => {
    setEditingContract({ ...c });
    form.setFieldsValue({
      contract_name:   c.contract_name,
      fee_type:        c.fee_type ? [c.fee_type] : [],
      contractor:      c.contractor,
      contract_amount: c.contract_amount / 100,        // fen → yuan
      start_date:      c.start_date ? dayjs(c.start_date) : null,
      end_date:        c.end_date   ? dayjs(c.end_date)   : null,
      notes:           c.notes,
    });
    setDrawerOpen(true);
  };

  // ── Save ────────────────────────────────────────────────────
  const saveContract = useCallback(() => {
    form
      .validateFields()
      .then((values: any) => {
        const feeType =
          values.fee_type && values.fee_type.length > 0
            ? values.fee_type[0]
            : "";

        // Accumulate new fee types into the dropdown list
        if (feeType && !feeTypes.includes(feeType)) {
          setFeeTypes((prev) => [...prev, feeType]);
        }

        // Convert dates back to ISO strings and amount to fen
        const payload = {
          ...values,
          fee_type:        feeType,
          contract_amount: Math.round(values.contract_amount * 100), // yuan → fen
          start_date:
            values.start_date instanceof dayjs
              ? (values.start_date as Dayjs).format("YYYY-MM-DD")
              : values.start_date,
          end_date:
            values.end_date instanceof dayjs
              ? (values.end_date as Dayjs).format("YYYY-MM-DD")
              : values.end_date,
        };

        // TODO: replace with real API call
        console.log("Save payload:", payload);

        message.success(
          "合同已保存" +
            (editingContract ? "" : "，请前往节点管理配置支付节点")
        );
        setDrawerOpen(false);
      })
      .catch(() => {
        // validation failed – Ant Design shows inline errors automatically
      });
  }, [editingContract, feeTypes, form]);

  // ── Node modal ──────────────────────────────────────────────
  const openNodes = (contractId: string) => {
    setNodeContractId(contractId);
    setNodeModalOpen(true);
  };

  const currentNodeData = nodeContractId
    ? mockPaymentNodes[nodeContractId] || []
    : [];

  // ── Table columns ───────────────────────────────────────────
  const cols = [
    {
      title: "合同名", dataIndex: "contract_name", key: "n", width: 150,
      render: (v: string, r: any) => <a onClick={() => openEdit(r)}>{v}</a>,
    },
    {
      title: "项目", dataIndex: "project_name", key: "p", width: 160,
      ellipsis: true,
    },
    {
      title: "费用类型", dataIndex: "fee_type", key: "ft", width: 90,
      render: (v: string) => <Tag color="blue">{v}</Tag>,
    },
    {
      title: "承接单位", dataIndex: "contractor", key: "co", width: 140,
      ellipsis: true,
    },
    {
      title: "合同金额", dataIndex: "contract_amount", key: "ca", width: 120,
      align: "right" as const,
      render: (v: number) => `¥${formatYuan(v)}`,
    },
    {
      title: "节点状态", key: "nodes", width: 120,
      render: (_: any, r: any) => renderNodesPreview(r.id),
    },
    {
      title: "合同期限", key: "period", width: 180,
      render: (_: any, r: any) =>
        `${r.start_date || "—"} ~ ${r.end_date || "—"}`,
    },
    {
      title: "状态", dataIndex: "status", key: "st", width: 80,
      render: (v: string) => (
        <Tag color={contractStatusMap[v]?.color}>
          {contractStatusMap[v]?.text}
        </Tag>
      ),
    },
    {
      title: "操作", key: "op", width: 150,
      render: (_: any, r: any) => (
        <Space size="small">
          <a onClick={() => openEdit(r)}>编辑</a>
          <a onClick={() => openNodes(r.id)}>
            <RightOutlined /> 节点
          </a>
        </Space>
      ),
    },
  ];

  // ── Render ──────────────────────────────────────────────────
  return (
    <div>
      {/* ════ Statistics cards ════ */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        {[
          {
            title:  "合同总额（生效中）",
            value:  `¥${formatYuan(totalContractAmount)}`,
            color:  "#1677ff",
            suffix: undefined,
          },
          {
            title:  "已支付",
            value:  `¥${formatYuan(totalPaid)}`,
            color:  "#52c41a",
            suffix: undefined,
          },
          {
            title:  "待支付",
            value:  `¥${formatYuan(totalUnpaid)}`,
            color:  "#fa8c16",
            suffix: undefined,
          },
          {
            title:  "生效合同",
            value:  activeCount,
            color:  "#722ed1",
            suffix: " 份",
          },
        ].map((s, i) => (
          <Col xs={24} sm={12} lg={6} key={i}>
            <Card size="small">
              <Statistic
                title={s.title}
                value={s.value}
                suffix={s.suffix}
                valueStyle={{ color: s.color }}
              />
            </Card>
          </Col>
        ))}
      </Row>

      {/* ════ Search + New button ════ */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={12} align="middle">
          <Col flex="auto">
            <Input
              placeholder="搜索合同名称 / 承接单位"
              prefix={<SearchOutlined />}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              allowClear
            />
          </Col>
          <Col>
            <Button type="primary" icon={<PlusOutlined />} onClick={openNew}>
              新建合同
            </Button>
          </Col>
        </Row>
      </Card>

      {/* ════ Contract table ════ */}
      <Card
        title="二类费用合同"
        extra={
          <Button
            size="small"
            icon={<ExportOutlined />}
            onClick={() => message.info("导出功能开发中")}
          >
            导出
          </Button>
        }
      >
        <Table
          columns={cols}
          dataSource={filtered}
          size="small"
          rowKey="id"
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条`,
          }}
        />
      </Card>

      {/* ════ New / Edit Drawer ════ */}
      <Drawer
        title={editingContract ? "编辑合同" : "新建二类费用合同"}
        width={560}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        extra={
          <Space>
            <Button onClick={() => setDrawerOpen(false)}>取消</Button>
            <Button type="primary" onClick={saveContract}>
              保存
            </Button>
          </Space>
        }
      >
        <Form form={form} layout="vertical">
          {/* Contract name */}
          <Form.Item
            name="contract_name"
            label="合同名称"
            rules={[{ required: true, message: "请输入合同名称" }]}
          >
            <Input placeholder="如：监理服务合同" />
          </Form.Item>

          {/* Fee type — tags mode, max 1 selection */}
          <Form.Item
            name="fee_type"
            label="费用类型"
            help="选择已有类型或输入新类型（回车添加）"
          >
            <Select
              mode="tags"
              maxCount={1}
              placeholder="选择或输入费用类型"
              style={{ width: "100%" }}
              options={feeTypes.map((t) => ({ value: t, label: t }))}
              onChange={(val: string[]) => {
                if (val.length > 0) {
                  const newType = val[val.length - 1];
                  if (!feeTypes.includes(newType)) {
                    setFeeTypes((prev) => [...prev, newType]);
                  }
                }
              }}
            />
          </Form.Item>

          {/* Contractor */}
          <Form.Item
            name="contractor"
            label="承接单位"
            rules={[{ required: true, message: "请输入承接单位" }]}
          >
            <Input placeholder="如：XX监理公司" />
          </Form.Item>

          {/* Contract amount (yuan, stored as fen) */}
          <Form.Item
            name="contract_amount"
            label="合同金额（元）"
            rules={[{ required: true, message: "请输入合同金额" }]}
          >
            <InputNumber
              style={{ width: "100%" }}
              min={0}
              precision={2}
              formatter={(value) =>
                `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ",")
              }
              parser={(value) => value?.replace(/,/g, "") as any}
              placeholder="输入合同总金额"
            />
          </Form.Item>

          {/* Start / End dates */}
          <Row gutter={12}>
            <Col span={12}>
              <Form.Item name="start_date" label="起始日期">
                <DatePicker
                  style={{ width: "100%" }}
                  placeholder="选择起始日期"
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="end_date" label="终止日期">
                <DatePicker
                  style={{ width: "100%" }}
                  placeholder="选择终止日期"
                />
              </Form.Item>
            </Col>
          </Row>

          {/* Notes */}
          <Form.Item name="notes" label="备注">
            <Input.TextArea rows={3} placeholder="合同备注、说明等" />
          </Form.Item>
        </Form>

        {/* Payment nodes preview (edit mode only) */}
        {editingContract && (
          <div
            style={{
              borderTop: "1px solid #f0f0f0",
              marginTop: 16,
              paddingTop: 16,
            }}
          >
            <h4 style={{ marginBottom: 8 }}>支付节点管理</h4>
            {mockPaymentNodes[editingContract.id] ? (
              <div>
                <p style={{ fontSize: 13, color: "#666" }}>
                  当前配置了{" "}
                  <strong>{mockPaymentNodes[editingContract.id].length}</strong>{" "}
                  个支付节点
                </p>
                <Button
                  size="small"
                  icon={<SettingOutlined />}
                  onClick={() => {
                    setDrawerOpen(false);
                    openNodes(editingContract.id);
                  }}
                >
                  管理节点
                </Button>
              </div>
            ) : (
              <p style={{ fontSize: 13, color: "#999" }}>
                保存合同后可前往节点管理配置支付节点和公式
              </p>
            )}
          </div>
        )}
      </Drawer>

      {/* ════ Node preview Modal ════ */}
      <Modal
        title="支付节点列表"
        width={780}
        open={nodeModalOpen}
        onCancel={() => setNodeModalOpen(false)}
        footer={
          <Space>
            <Button onClick={() => setNodeModalOpen(false)}>关闭</Button>
            <Button
              type="primary"
              onClick={() => {
                setNodeModalOpen(false);
                navigate("/secondary/nodes");
              }}
            >
              前往节点管理
            </Button>
          </Space>
        }
      >
        {nodeContractId && currentNodeData.length > 0 ? (
          <Table
            size="small"
            rowKey="id"
            pagination={false}
            dataSource={currentNodeData}
            columns={[
              { title: "#",      dataIndex: "seq",          width: 40  },
              { title: "节点名称", dataIndex: "name",         width: 100 },
              { title: "触发条件", dataIndex: "trigger",      width: 150, ellipsis: true },
              { title: "公式",    dataIndex: "formula_expr",  width: 130, render: (v: string) => <Tag color="blue">{v}</Tag> },
              { title: "金额",    dataIndex: "amount",        width: 110, align: "right" as const, render: (v: number) => `¥${formatYuan(v)}` },
              { title: "计划日期", dataIndex: "planned_date",  width: 100 },
              {
                title: "状态", dataIndex: "status", width: 70,
                render: (v: string) => (
                  <Tag color={nodeStatusMap[v]?.color}>
                    {nodeStatusMap[v]?.text}
                  </Tag>
                ),
              },
            ]}
          />
        ) : (
          <div style={{ textAlign: "center", padding: 40, color: "#999" }}>
            暂未配置支付节点
          </div>
        )}
      </Modal>
    </div>
  );
}
