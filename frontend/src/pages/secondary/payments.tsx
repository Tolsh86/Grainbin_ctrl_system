import { useState, useMemo } from "react";
import {
  Card, Table, Tag, Button, Space, Statistic, Row, Col,
  Modal, DatePicker, InputNumber, Input, message, Select, Typography
} from "antd";
import {
  ExportOutlined, CheckCircleOutlined, SearchOutlined
} from "@ant-design/icons";
import { mockSecondaryContracts, mockPaymentNodes, mockFeeTypes, formatYuan } from "../../utils/mock";

const { Text } = Typography;

const STATUS_MAP: Record<string, { color: string; text: string }> = {
  paid: { color: "green", text: "已支付" },
  overdue: { color: "red", text: "逾期未付" },
  pending: { color: "default", text: "未到期" },
};

export default function PaymentLedger() {
  const [reconOpen, setReconOpen] = useState(false);
  const [payModalOpen, setPayModalOpen] = useState(false);
  const [payingNode, setPayingNode] = useState<any>(null);
  const [filterContract, setFilterContract] = useState<string>("all");
  const [filterStatus, setFilterStatus] = useState<string>("all");
  const [filterFeeType, setFilterFeeType] = useState<string>("all");

  // 动态汇总全量支付台账
  const allPayments = useMemo(() => {
    const list: any[] = [];
    mockSecondaryContracts.forEach((contract) => {
      const nodes = mockPaymentNodes[contract.id];
      if (!nodes) return;
      nodes.forEach((node) => {
        list.push({
          id: node.id,
          nodeName: node.name,
          contractName: contract.contract_name,
          contractId: contract.id,
          project: contract.project_name,
          feeType: contract.fee_type,
          contractor: contract.contractor,
          dueAmount: node.amount,
          paidAmount: node.paid_amount || 0,
          remainingAmount: node.amount - (node.paid_amount || 0),
          paidDate: node.actual_date,
          plannedDate: node.planned_date,
          status: node.status,
          trigger: node.trigger,
          formula_expr: node.formula_expr,
        });
      });
    });
    return list;
  }, []);

  let filtered = allPayments;
  if (filterContract !== "all") filtered = filtered.filter((p) => p.contractId === filterContract);
  if (filterStatus !== "all") filtered = filtered.filter((p) => p.status === filterStatus);
  if (filterFeeType !== "all") filtered = filtered.filter((p) => p.feeType === filterFeeType);

  const totalDue = filtered.reduce((s, p) => s + p.dueAmount, 0);
  const totalPaid = filtered.filter((p) => p.status === "paid").reduce((s, p) => s + p.paidAmount, 0);
  const totalUnpaid = filtered.filter((p) => p.status !== "paid").reduce((s, p) => s + p.remainingAmount, 0);
  const overdueCount = filtered.filter((p) => p.status === "overdue").length;

  const markPaid = (node: any) => {
    setPayingNode(node);
    setPayModalOpen(true);
  };

  const confirmPay = () => {
    message.success(`已标记支付：${payingNode?.nodeName}（${payingNode?.contractName}）`);
    setPayModalOpen(false);
  };

  const columns = [
    { title: "节点", dataIndex: "nodeName", width: 100 },
    { title: "合同", dataIndex: "contractName", width: 140, ellipsis: true },
    { title: "承接单位", dataIndex: "contractor", width: 110, ellipsis: true },
    { title: "项目", dataIndex: "project", width: 120, ellipsis: true },
    { title: "费用类型", dataIndex: "feeType", width: 80, render: (v: string) => <Tag color="blue">{v}</Tag> },
    { title: "应付(元)", dataIndex: "dueAmount", width: 110, align: "right" as const,
      render: (v: number) => <Text strong>¥{formatYuan(v)}</Text> },
    { title: "已付(元)", dataIndex: "paidAmount", width: 110, align: "right" as const,
      render: (v: number) => v > 0 ? <Text style={{ color: "#52c41a" }}>¥{formatYuan(v)}</Text> : <Text type="secondary">—</Text> },
    { title: "未付(元)", dataIndex: "remainingAmount", width: 110, align: "right" as const,
      render: (v: number, r: any) => {
        if (r.status === "paid") return <Text type="secondary">—</Text>;
        return <Text style={{ color: r.status === "overdue" ? "#ff4d4f" : "#fa8c16" }}>¥{formatYuan(v)}</Text>;
      }},
    { title: "计划日期", dataIndex: "plannedDate", width: 100 },
    { title: "触发条件", dataIndex: "trigger", width: 130, ellipsis: true },
    { title: "公式", dataIndex: "formula_expr", width: 120, render: (v: string) => <Tag color="blue">{v}</Tag> },
    { title: "状态", dataIndex: "status", width: 85, render: (v: string) => <Tag color={STATUS_MAP[v]?.color}>{STATUS_MAP[v]?.text}</Tag> },
    {
      title: "操作", width: 80, render: (_: any, r: any) => (
        r.status !== "paid"
          ? <a onClick={() => markPaid(r)}><CheckCircleOutlined /> 支付</a>
          : <Text type="secondary">已付</Text>
      ),
    },
  ];

  return (
    <div>
      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        {[
          { title: "应付总额", val: `¥${formatYuan(totalDue)}`, color: "#1677ff" },
          { title: "已支付", val: `¥${formatYuan(totalPaid)}`, color: "#52c41a" },
          { title: "未支付", val: `¥${formatYuan(totalUnpaid)}`, color: "#fa8c16" },
          { title: "逾期未付", val: overdueCount, color: "#ff4d4f", suffix: "笔" },
        ].map((s, i) => (
          <Col xs={12} sm={6} key={i}>
            <Card size="small">
              <Statistic title={s.title} value={s.val} suffix={s.suffix} valueStyle={{ color: s.color, fontSize: 20 }} />
            </Card>
          </Col>
        ))}
      </Row>

      {/* 筛选 + 操作 */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={12} align="middle">
          <Col>
            <Select style={{ width: 200 }} value={filterContract} onChange={setFilterContract}
              placeholder="选择合同"
              options={[{ value: "all", label: "全部合同" }, ...mockSecondaryContracts.map(c => ({ value: c.id, label: c.contract_name }))]} />
          </Col>
          <Col>
            <Select style={{ width: 120 }} value={filterStatus} onChange={setFilterStatus}
              options={[{ value: "all", label: "全部状态" }, { value: "paid", label: "已支付" }, { value: "overdue", label: "逾期未付" }, { value: "pending", label: "未到期" }]} />
          </Col>
          <Col>
            <Select style={{ width: 120 }} value={filterFeeType} onChange={setFilterFeeType}
              options={[{ value: "all", label: "全部类型" }, ...mockFeeTypes.map(t => ({ value: t, label: t }))]} />
          </Col>
          <Col flex="auto" />
          <Col>
            <Button icon={<ExportOutlined />} onClick={() => setReconOpen(true)}>对账报告</Button>
          </Col>
        </Row>
      </Card>

      {/* 支付台账表格 */}
      <Card title={`支付台账（${filtered.length} 条）`}>
        <Table size="small" rowKey="id" dataSource={filtered} columns={columns}
          pagination={{ pageSize: 20, showTotal: (t) => `共 ${t} 条记录` }}
          scroll={{ x: 1300 }} />
      </Card>

      {/* 支付登记弹窗 */}
      <Modal
        title="登记支付"
        open={payModalOpen}
        onCancel={() => setPayModalOpen(false)}
        onOk={confirmPay}
        okText="确认支付"
        width={480}
      >
        {payingNode && (
          <div>
            <Row gutter={[0, 12]}>
              <Col span={12}><Text type="secondary">节点：</Text><Text strong>{payingNode.nodeName}</Text></Col>
              <Col span={12}><Text type="secondary">合同：</Text><Text strong>{payingNode.contractName}</Text></Col>
              <Col span={12}><Text type="secondary">承接单位：</Text><Text>{payingNode.contractor}</Text></Col>
              <Col span={12}><Text type="secondary">费用类型：</Text><Tag color="blue">{payingNode.feeType}</Tag></Col>
              <Col span={12}><Text type="secondary">应付金额：</Text><Text strong style={{ fontSize: 16 }}>¥{formatYuan(payingNode.dueAmount)}</Text></Col>
              <Col span={12}><Text type="secondary">未付金额：</Text><Text strong style={{ fontSize: 16, color: "#fa8c16" }}>¥{formatYuan(payingNode.remainingAmount)}</Text></Col>
            </Row>
            <div style={{ marginTop: 20, padding: 16, background: "#f6f8fa", borderRadius: 6 }}>
              <Row gutter={12}>
                <Col span={12}>
                  <div style={{ marginBottom: 4, fontWeight: 500 }}>本次支付金额（元）</div>
                  <InputNumber style={{ width: "100%" }} min={0} max={payingNode.remainingAmount / 100}
                    placeholder="输入本次支付金额"
                    formatter={(v) => `${v}`.replace(/\B(?=(\d{3})+(?!\d))/g, ",")}
                    parser={(v: any) => v.replace(/,/g, "")} />
                </Col>
                <Col span={12}>
                  <div style={{ marginBottom: 4, fontWeight: 500 }}>支付日期</div>
                  <DatePicker style={{ width: "100%" }} />
                </Col>
              </Row>
              <div style={{ marginTop: 12 }}>
                <div style={{ marginBottom: 4, fontWeight: 500 }}>支付凭证</div>
                <Input placeholder="凭证编号或说明" />
              </div>
            </div>
          </div>
        )}
      </Modal>

      {/* 对账报告弹窗 */}
      <Modal
        title="合同-节点-支付对账报告"
        width={900}
        open={reconOpen}
        onCancel={() => setReconOpen(false)}
        onOk={() => { message.success("对账报告导出成功"); setReconOpen(false); }}
        okText="导出 Excel"
      >
        {mockSecondaryContracts.map((contract) => {
          const nodes = mockPaymentNodes[contract.id] || [];
          const contractPaid = nodes.filter((n) => n.status === "paid").reduce((s, n) => s + n.paid_amount, 0);
          const contractUnpaid = nodes.filter((n) => n.status !== "paid").reduce((s, n) => s + n.amount, 0);
          const paidRatio = contract.contract_amount > 0 ? Math.round(contractPaid / contract.contract_amount * 100) : 0;
          return (
            <Card
              key={contract.id}
              size="small"
              title={
                <Space>
                  <Text strong>{contract.contract_name}</Text>
                  <Tag color="blue">{contract.fee_type}</Tag>
                  <Text type="secondary">— {contract.contractor}</Text>
                  <Tag color={contract.status === "active" ? "green" : "red"}>
                    {contract.status === "active" ? "生效中" : contract.status === "terminated" ? "已终止" : "已到期"}
                  </Tag>
                </Space>
              }
              style={{ marginBottom: 16 }}
            >
              <Row gutter={16} style={{ marginBottom: 12 }}>
                <Col><Text type="secondary">合同总额：</Text><Text strong>¥{formatYuan(contract.contract_amount)}</Text></Col>
                <Col><Text type="secondary">已支付：</Text><Text style={{ color: "#52c41a" }}>¥{formatYuan(contractPaid)}</Text></Col>
                <Col><Text type="secondary">未支付：</Text><Text style={{ color: "#fa8c16" }}>¥{formatYuan(contractUnpaid)}</Text></Col>
                <Col><Text type="secondary">支付比例：</Text><Text>{paidRatio}%</Text></Col>
              </Row>
              {nodes.length > 0 ? (
                <Table size="small" pagination={false} rowKey="id" dataSource={nodes}
                  columns={[
                    { title: "#", dataIndex: "seq", width: 40 },
                    { title: "节点", dataIndex: "name", width: 80 },
                    { title: "公式", dataIndex: "formula_expr", width: 130, render: (v: string) => <Tag color="blue">{v}</Tag> },
                    { title: "应付(元)", dataIndex: "amount", width: 100, align: "right" as const, render: (v: number) => `¥${formatYuan(v)}` },
                    { title: "实付(元)", dataIndex: "paid_amount", width: 100, align: "right" as const, render: (v: number) => v > 0 ? `¥${formatYuan(v)}` : "—" },
                    { title: "计划日期", dataIndex: "planned_date", width: 100 },
                    { title: "实际日期", dataIndex: "actual_date", width: 100, render: (v: string | null) => v || "—" },
                    { title: "状态", dataIndex: "status", width: 80, render: (v: string) => <Tag color={STATUS_MAP[v]?.color}>{STATUS_MAP[v]?.text}</Tag> },
                  ]}
                />
              ) : (
                <Text type="secondary">未配置支付节点</Text>
              )}
            </Card>
          );
        })}
      </Modal>
    </div>
  );
}
