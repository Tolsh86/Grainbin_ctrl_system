import { useState, useEffect, useCallback } from "react";
import {
  Card, Table, Tag, Button, Space, Row, Col, Modal, Form, Input,
  InputNumber, message, Typography, Popconfirm, Tooltip, Divider,
} from "antd";
import {
  PlusOutlined, ArrowLeftOutlined, EditOutlined, DeleteOutlined,
} from "@ant-design/icons";
import { useParams, useNavigate } from "react-router-dom";
import {
  getContract,
  getContractFeeItems,
  createContractFeeItems,
  updateContractFeeItem,
  deleteContractFeeItem,
} from "../../api/contracts";
import type { ContractDetail, ContractFeeItem } from "../../api/contracts";

const { Text, Title } = Typography;

// ── 分→万元 ──
const fenToWanStr = (fen: number | null | undefined): string => {
  if (fen == null || fen === 0) return "0.0000";
  return (fen / 1000000).toLocaleString("zh-CN", {
    minimumFractionDigits: 4, maximumFractionDigits: 4,
  });
};

const ratioPercent = (ratio: number | null | undefined): string => {
  if (ratio == null) return "—";
  return `${(ratio * 100).toFixed(2)}%`;
};

export default function FeeItemsConfig() {
  const { id: contractId } = useParams<{ id: string }>();
  const navigate = useNavigate();

  // ── Contract info ──
  const [contract, setContract] = useState<ContractDetail | null>(null);
  const [contractLoading, setContractLoading] = useState(true);

  // ── Fee items ──
  const [feeItems, setFeeItems] = useState<ContractFeeItem[]>([]);
  const [loading, setLoading] = useState(false);

  // ── Edit modal ──
  const [modalOpen, setModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<ContractFeeItem | null>(null);
  const [saving, setSaving] = useState(false);
  const [form] = Form.useForm();

  // ── Load contract ──
  useEffect(() => {
    if (!contractId) return;
    setContractLoading(true);
    getContract(contractId)
      .then(setContract)
      .catch(() => message.error("加载合同信息失败"))
      .finally(() => setContractLoading(false));
  }, [contractId]);

  // ── Load fee items ──
  const loadItems = useCallback(() => {
    if (!contractId) return;
    setLoading(true);
    getContractFeeItems(contractId)
      .then(setFeeItems)
      .catch(() => message.error("加载费用分项失败"))
      .finally(() => setLoading(false));
  }, [contractId]);

  useEffect(() => { loadItems(); }, [loadItems]);

  // ── Open add modal ──
  const openAdd = () => {
    setEditingItem(null);
    form.resetFields();
    form.setFieldsValue({
      sort_order: feeItems.length + 1,
      current_ratio: undefined,
      contract_amount: undefined,
    });
    setModalOpen(true);
  };

  // ── Open edit modal ──
  const openEdit = (item: ContractFeeItem) => {
    setEditingItem(item);
    form.setFieldsValue({
      item_name: item.item_name,
      contract_amount: item.contract_amount ? item.contract_amount / 1000000 : undefined, // 分→万元
      current_ratio: item.current_ratio != null ? item.current_ratio * 100 : undefined,   // ratio→%
      sort_order: item.sort_order,
      remark: item.remark,
    });
    setModalOpen(true);
  };

  // ── Save ──
  const handleSave = async () => {
    if (!contractId) return;
    try {
      const values = await form.validateFields();
    } catch {
      return; // validation failed
    }

    setSaving(true);
    try {
      const values = form.getFieldsValue();
      const payload = {
        item_name: values.item_name,
        contract_amount: values.contract_amount != null
          ? Math.round(values.contract_amount * 1000000) // 万元→分
          : undefined,
        current_ratio: values.current_ratio != null
          ? values.current_ratio / 100 // %→ratio
          : undefined,
        sort_order: values.sort_order ?? 0,
        remark: values.remark || undefined,
      };

      if (editingItem) {
        await updateContractFeeItem(contractId!, editingItem.id, payload);
        message.success("费用分项已更新");
      } else {
        await createContractFeeItems(contractId!, [payload]);
        message.success("费用分项已添加");
      }

      setModalOpen(false);
      loadItems();
    } catch (e: any) {
      message.error(e?.response?.data?.detail || "保存失败");
    } finally {
      setSaving(false);
    }
  };

  // ── Delete ──
  const handleDelete = async (itemId: string) => {
    if (!contractId) return;
    try {
      await deleteContractFeeItem(contractId, itemId);
      message.success("费用分项已删除");
      loadItems();
    } catch {
      message.error("删除失败");
    }
  };

  // ── Table columns ──
  const columns = [
    {
      title: "#", dataIndex: "sort_order", width: 50,
      render: (v: number) => <span style={{ color: "#999" }}>{v}</span>,
    },
    {
      title: "费用分项名称", dataIndex: "item_name", width: 180,
      render: (v: string) => <Text strong>{v}</Text>,
    },
    {
      title: "分项合同金额(万元)", dataIndex: "contract_amount", width: 150, align: "right" as const,
      render: (v: number | null) => (
        <span style={{ color: v ? "#1677ff" : "#999" }}>{fenToWanStr(v)}</span>
      ),
    },
    {
      title: "付款比例", dataIndex: "current_ratio", width: 100, align: "center" as const,
      render: (v: number | null) => (
        <Tag color={v != null ? "blue" : "default"}>{ratioPercent(v)}</Tag>
      ),
    },
    {
      title: "应付金额(万元)", key: "payable", width: 150, align: "right" as const,
      render: (_: any, r: ContractFeeItem) => {
        if (!r.contract_amount || r.current_ratio == null) return <span style={{ color: "#ccc" }}>—</span>;
        const payable = r.contract_amount * r.current_ratio;
        return <span style={{ fontWeight: 600, color: "#cf1322" }}>{fenToWanStr(payable)}</span>;
      },
    },
    {
      title: "备注", dataIndex: "remark", width: 140, ellipsis: true,
      render: (v: string | null) => (
        <Tooltip title={v}>{v ? <Text type="secondary">{v}</Text> : <span style={{ color: "#ccc" }}>—</span>}</Tooltip>
      ),
    },
    {
      title: "操作", key: "op", width: 120, fixed: "right" as const,
      render: (_: any, r: ContractFeeItem) => (
        <Space size="small">
          <a onClick={() => openEdit(r)}><EditOutlined /> 编辑</a>
          <Popconfirm
            title="确定删除此费用分项？"
            description="删除后，使用该分项的审核记录可能受影响。"
            onConfirm={() => handleDelete(r.id)}
            okText="删除" cancelText="取消"
            okButtonProps={{ danger: true }}
          >
            <a style={{ color: "#ff4d4f" }}><DeleteOutlined /></a>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // ── Stat totals ──
  const totalContractAmount = feeItems.reduce((s, fi) => s + (fi.contract_amount || 0), 0);
  const avgRatio = feeItems.length > 0
    ? feeItems.reduce((s, fi) => s + (fi.current_ratio || 0), 0) / feeItems.length
    : 0;

  return (
    <div>
      {/* ── Header ── */}
      <Card size="small" style={{ marginBottom: 16 }} loading={contractLoading}>
        <Row align="middle" gutter={16}>
          <Col>
            <Button icon={<ArrowLeftOutlined />}
              onClick={() => navigate("/secondary/contracts")}>
              返回合同列表
            </Button>
          </Col>
          <Col flex="auto">
            {contract && (
              <Space size="middle" wrap>
                <Text strong style={{ fontSize: 16 }}>{contract.contract_no}</Text>
                <Tag color="blue">{contract.supplier_name}</Tag>
                <Text type="secondary">{contract.contract_desc}</Text>
                <Divider type="vertical" />
                <Text type="secondary">
                  合同金额：<span style={{ color: "#1677ff", fontWeight: 500 }}>
                    {fenToWanStr(contract.contract_amount)} 万元
                  </span>
                </Text>
              </Space>
            )}
          </Col>
          <Col>
            <Button type="primary" icon={<PlusOutlined />} onClick={openAdd}>
              添加费用分项
            </Button>
          </Col>
        </Row>
      </Card>

      {/* ── Stats ── */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        {[
          { title: "费用分项数", value: feeItems.length, suffix: " 项", color: "#722ed1" },
          { title: "分项金额合计(万元)", value: fenToWanStr(totalContractAmount), color: "#1677ff" },
          { title: "平均付款比例", value: ratioPercent(avgRatio), color: "#52c41a" },
        ].map((s, i) => (
          <Col xs={24} sm={8} key={i}>
            <Card size="small">
              <div style={{ textAlign: "center" }}>
                <div style={{ fontSize: 12, color: "#999", marginBottom: 4 }}>{s.title}</div>
                <div style={{ fontSize: 20, fontWeight: 700, color: s.color }}>
                  {(s as any).prefix}{s.value}{(s as any).suffix || ""}
                </div>
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      {/* ── Fee Items Table ── */}
      <Card
        title={
          <Space>
            <span>费用分项配置</span>
            <Text type="secondary" style={{ fontSize: 12 }}>
              用于审核时自动生成分项快照，付款比例决定应付金额计算
            </Text>
          </Space>
        }
      >
        <Table
          size="small"
          rowKey="id"
          columns={columns}
          dataSource={feeItems}
          loading={loading}
          pagination={false}
          scroll={{ x: 900 }}
          locale={{ emptyText: "暂无费用分项，请点击「添加费用分项」配置" }}
          summary={() => {
            if (feeItems.length === 0) return null;
            const totalPayable = feeItems.reduce(
              (s, fi) => s + (fi.contract_amount || 0) * (fi.current_ratio || 0), 0
            );
            return (
              <Table.Summary fixed>
                <Table.Summary.Row style={{ fontWeight: 700, background: "#fafafa" }}>
                  <Table.Summary.Cell index={0} colSpan={2} align="right">合计</Table.Summary.Cell>
                  <Table.Summary.Cell index={1} align="right">
                    {fenToWanStr(totalContractAmount)}
                  </Table.Summary.Cell>
                  <Table.Summary.Cell index={2} align="center">—</Table.Summary.Cell>
                  <Table.Summary.Cell index={3} align="right">
                    <span style={{ color: "#cf1322" }}>{fenToWanStr(totalPayable)}</span>
                  </Table.Summary.Cell>
                  <Table.Summary.Cell index={4} />
                  <Table.Summary.Cell index={5} />
                </Table.Summary.Row>
              </Table.Summary>
            );
          }}
        />
      </Card>

      {/* ── Add / Edit Modal ── */}
      <Modal
        title={editingItem ? "编辑费用分项" : "添加费用分项"}
        open={modalOpen}
        onOk={handleSave}
        onCancel={() => setModalOpen(false)}
        confirmLoading={saving}
        okText="保存"
        width={520}
        destroyOnClose
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item
            name="item_name"
            label="费用分项名称"
            rules={[{ required: true, message: "请输入费用分项名称" }]}
          >
            <Input placeholder="如：建筑安装工程费、安全文明施工费、监理服务费" maxLength={100} />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="contract_amount"
                label="分项合同金额（万元）"
                tooltip="该费用分项对应的合同约定金额"
              >
                <InputNumber
                  style={{ width: "100%" }}
                  min={0}
                  precision={4}
                  placeholder="如：13172.9850"
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="current_ratio"
                label="付款比例（%）"
                tooltip="本期该分项的付款比例，如 10% 表示按分项金额的 10% 付款"
              >
                <InputNumber
                  style={{ width: "100%" }}
                  min={0}
                  max={100}
                  precision={2}
                  placeholder="如：10"
                  addonAfter="%"
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="sort_order" label="排序">
                <InputNumber style={{ width: "100%" }} min={0} precision={0} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="remark" label="备注">
                <Input placeholder="可选" maxLength={200} />
              </Form.Item>
            </Col>
          </Row>

          {/* Preview */}
          <Form.Item noStyle shouldUpdate={(prev, cur) =>
            prev.contract_amount !== cur.contract_amount ||
            prev.current_ratio !== cur.current_ratio
          }>
            {({ getFieldValue }) => {
              const amt = getFieldValue("contract_amount");
              const ratio = getFieldValue("current_ratio");
              if (amt && ratio) {
                const payable = amt * (ratio / 100);
                return (
                  <div style={{
                    marginTop: 8, padding: "8px 12px", background: "#f6ffed",
                    borderRadius: 6, border: "1px solid #b7eb8f",
                  }}>
                    <Text type="secondary" style={{ fontSize: 12 }}>应付金额预览：</Text>
                    <Text strong style={{ color: "#cf1322", fontSize: 16, marginLeft: 8 }}>
                      {payable.toLocaleString("zh-CN", { minimumFractionDigits: 4, maximumFractionDigits: 4 })} 万元
                    </Text>
                  </div>
                );
              }
              return null;
            }}
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
