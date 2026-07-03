import { useState, useCallback } from "react";
import {
  Card, Table, Tag, Button, Space, Row, Col, Drawer, Form, Input,
  Select, InputNumber, message, Popconfirm, Typography, Tooltip
} from "antd";
import {
  PlusOutlined, CopyOutlined, DeleteOutlined, EyeOutlined,
  PlusCircleOutlined, MinusCircleOutlined, InfoCircleOutlined,
  CloseOutlined,
} from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import { mockNodeTemplates, mockFeeTypes } from "../../utils/mock";
import type { NodeTemplate } from "../../utils/mock";

const { Text } = Typography;

// ── editable node row in the drawer ──
interface EditableNodeDef {
  key: string;
  seq: number;
  name: string;
  trigger: string;
  ratio: number;
  offset_days: number;
}

// ── status display map ──
const statusMap: Record<string, { color: string; text: string }> = {
  active: { color: "green", text: "启用" },
  inactive: { color: "default", text: "停用" },
};

// ── id generator ──
let idCounter = 200;
const genId = (prefix: string) => `${prefix}_${Date.now()}_${++idCounter}`;

export default function NodeTemplates() {
  // ── state ──
  const [templates, setTemplates] = useState<NodeTemplate[]>(mockNodeTemplates);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [feeTypes, setFeeTypes] = useState<string[]>([...mockFeeTypes]);

  // drawer form state
  const [formName, setFormName] = useState("");
  const [formFeeType, setFormFeeType] = useState<string>("");
  const [formNodes, setFormNodes] = useState<EditableNodeDef[]>([]);

  // ── derived ──
  const selectedTemplate = templates.find((t) => t.id === selectedTemplateId);

  // ════════════════════════════════════════════
  //  handlers – main table
  // ════════════════════════════════════════════

  /** copy a template (create a new custom entry from any template) */
  const copyTemplate = useCallback((tmpl: NodeTemplate) => {
    const clone: NodeTemplate = {
      ...tmpl,
      id: genId("nt"),
      name: tmpl.name + " (复制)",
      is_builtin: false,
      status: "active",
      nodes_def: tmpl.nodes_def.map((nd, i) => ({
        ...nd,
        seq: i + 1,
      })),
    };
    setTemplates((prev) => [...prev, clone]);
    message.success(`已复制模板：「${tmpl.name}」 → 「${clone.name}」`);
  }, []);

  /** delete a custom template */
  const deleteTemplate = useCallback((tmpl: NodeTemplate) => {
    if (tmpl.is_builtin) {
      message.warning("内置模板不可删除");
      return;
    }
    setTemplates((prev) => prev.filter((t) => t.id !== tmpl.id));
    if (selectedTemplateId === tmpl.id) setSelectedTemplateId(null);
    message.success(`模板「${tmpl.name}」已删除`);
  }, [selectedTemplateId]);

  // ════════════════════════════════════════════
  //  handlers – drawer
  // ════════════════════════════════════════════

  /** open drawer for a new template */
  const openNewTemplate = useCallback(() => {
    setFormName("");
    setFormFeeType("");
    setFormNodes([{
      key: genId("nd"),
      seq: 1,
      name: "",
      trigger: "",
      ratio: 0,
      offset_days: 0,
    }]);
    setDrawerOpen(true);
  }, []);

  /** update a single field on a node row in the drawer */
  const updateFormNode = useCallback((key: string, field: keyof EditableNodeDef, value: string | number) => {
    setFormNodes((prev) =>
      prev.map((nd) => (nd.key === key ? { ...nd, [field]: value } : nd))
    );
  }, []);

  /** add a blank node row */
  const addFormNode = useCallback(() => {
    const maxSeq = formNodes.reduce((m, nd) => Math.max(m, nd.seq), 0);
    setFormNodes((prev) => [
      ...prev,
      { key: genId("nd"), seq: maxSeq + 1, name: "", trigger: "", ratio: 0, offset_days: 0 },
    ]);
  }, [formNodes]);

  /** remove a node row */
  const removeFormNode = useCallback((key: string) => {
    setFormNodes((prev) => {
      if (prev.length <= 1) {
        message.warning("至少保留一个支付节点");
        return prev;
      }
      return prev.filter((nd) => nd.key !== key);
    });
  }, []);

  /** save template from drawer */
  const saveTemplate = useCallback(() => {
    // validation
    if (!formName.trim()) {
      message.warning("请输入模板名称");
      return;
    }
    if (!formFeeType) {
      message.warning("请选择费用类型");
      return;
    }
    const invalidNode = formNodes.find((nd) => !nd.name.trim());
    if (invalidNode) {
      message.warning("请为每个节点填写名称");
      return;
    }
    const totalRatio = formNodes.reduce((s, nd) => s + nd.ratio, 0);
    if (totalRatio !== 100) {
      message.warning(`所有节点比例之和应为 100%，当前为 ${totalRatio}%`);
      return;
    }

    const newTmpl: NodeTemplate = {
      id: genId("nt"),
      name: formName.trim(),
      fee_type: formFeeType,
      is_builtin: false,
      status: "active",
      nodes_def: formNodes.map(({ key, ...rest }, i) => ({
        ...rest,
        seq: i + 1,
      })),
    };

    setTemplates((prev) => [...prev, newTmpl]);
    message.success(`模板「${newTmpl.name}」创建成功`);
    setDrawerOpen(false);
  }, [formName, formFeeType, formNodes]);

  // ════════════════════════════════════════════
  //  columns – main template table
  // ════════════════════════════════════════════

  const mainColumns: ColumnsType<NodeTemplate> = [
    {
      title: "模板名称",
      dataIndex: "name",
      key: "name",
      width: 200,
      render: (v: string, r: NodeTemplate) => (
        <a
          onClick={() =>
            setSelectedTemplateId(selectedTemplateId === r.id ? null : r.id)
          }
          style={{ fontWeight: selectedTemplateId === r.id ? 600 : undefined }}
        >
          {selectedTemplateId === r.id ? "▾ " : "▸ "}{v}
        </a>
      ),
    },
    {
      title: "费用类型",
      dataIndex: "fee_type",
      key: "fee_type",
      width: 100,
      render: (v: string) => <Tag color="blue">{v}</Tag>,
    },
    {
      title: "节点数",
      key: "node_count",
      width: 80,
      align: "center",
      render: (_: unknown, r: NodeTemplate) => r.nodes_def.length,
    },
    {
      title: "内置",
      dataIndex: "is_builtin",
      key: "is_builtin",
      width: 70,
      align: "center",
      render: (v: boolean) =>
        v ? (
          <Tag color="blue">是</Tag>
        ) : (
          <Tag color="default">否</Tag>
        ),
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      width: 80,
      align: "center",
      render: (v: string) => (
        <Tag color={statusMap[v]?.color ?? "default"}>
          {statusMap[v]?.text ?? v}
        </Tag>
      ),
    },
    {
      title: "操作",
      key: "actions",
      width: 200,
      render: (_: unknown, r: NodeTemplate) => (
        <Space size="small">
          <a
            onClick={() =>
              setSelectedTemplateId(selectedTemplateId === r.id ? null : r.id)
            }
          >
            <EyeOutlined /> 查看
          </a>
          <a onClick={() => copyTemplate(r)}>
            <CopyOutlined /> 复制
          </a>
          {r.is_builtin ? (
            <Tooltip title="内置模板不可删除">
              <Text type="secondary" style={{ cursor: "not-allowed" }}>
                <DeleteOutlined /> 删除
              </Text>
            </Tooltip>
          ) : (
            <Popconfirm
              title="确认删除该模板？"
              description="删除后不可恢复"
              onConfirm={() => deleteTemplate(r)}
              okText="删除"
              cancelText="取消"
              okButtonProps={{ danger: true }}
            >
              <a style={{ color: "#ff4d4f" }}>
                <DeleteOutlined /> 删除
              </a>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  // ════════════════════════════════════════════
  //  columns – detail sub-table (nodes preview)
  // ════════════════════════════════════════════

  const detailColumns: ColumnsType<EditableNodeDef> = [
    {
      title: "#",
      dataIndex: "seq",
      key: "seq",
      width: 50,
      align: "center",
    },
    {
      title: "节点名称",
      dataIndex: "name",
      key: "name",
      width: 130,
    },
    {
      title: "触发条件",
      dataIndex: "trigger",
      key: "trigger",
      width: 180,
      ellipsis: true,
      render: (v: string) => v || <span style={{ color: "#ccc" }}>—</span>,
    },
    {
      title: "比例 (%)",
      dataIndex: "ratio",
      key: "ratio",
      width: 100,
      align: "center",
      render: (v: number) => (
        <span style={{ fontWeight: 500 }}>{v}%</span>
      ),
    },
    {
      title: "计划偏移 (天)",
      dataIndex: "offset_days",
      key: "offset_days",
      width: 140,
      align: "center",
      render: (v: number) =>
        v > 0 ? `${v} 天` : <span style={{ color: "#ccc" }}>—</span>,
    },
  ];

  // ════════════════════════════════════════════
  //  columns – drawer node-editing table
  // ════════════════════════════════════════════

  const drawerNodeColumns: ColumnsType<EditableNodeDef> = [
    {
      title: "#",
      width: 50,
      align: "center",
      render: (_: unknown, __: EditableNodeDef, idx: number) => idx + 1,
    },
    {
      title: "节点名称",
      width: 140,
      render: (_: unknown, nd: EditableNodeDef) => (
        <Input
          size="small"
          value={nd.name}
          placeholder="如：合同签订"
          onChange={(e) => updateFormNode(nd.key, "name", e.target.value)}
        />
      ),
    },
    {
      title: "触发条件",
      width: 180,
      render: (_: unknown, nd: EditableNodeDef) => (
        <Input
          size="small"
          value={nd.trigger}
          placeholder="如：双方盖章生效"
          onChange={(e) => updateFormNode(nd.key, "trigger", e.target.value)}
        />
      ),
    },
    {
      title: "比例 (%)",
      width: 100,
      align: "center",
      render: (_: unknown, nd: EditableNodeDef) => (
        <InputNumber
          size="small"
          min={0}
          max={100}
          value={nd.ratio}
          style={{ width: "100%" }}
          onChange={(v) => updateFormNode(nd.key, "ratio", v ?? 0)}
        />
      ),
    },
    {
      title: "偏移 (天)",
      width: 100,
      align: "center",
      render: (_: unknown, nd: EditableNodeDef) => (
        <InputNumber
          size="small"
          min={0}
          max={3650}
          value={nd.offset_days}
          style={{ width: "100%" }}
          onChange={(v) => updateFormNode(nd.key, "offset_days", v ?? 0)}
        />
      ),
    },
    {
      title: "",
      width: 40,
      align: "center",
      render: (_: unknown, nd: EditableNodeDef) => (
        <Button
          type="text"
          size="small"
          danger
          icon={<MinusCircleOutlined />}
          onClick={() => removeFormNode(nd.key)}
        />
      ),
    },
  ];

  // ════════════════════════════════════════════
  //  render
  // ════════════════════════════════════════════

  return (
    <div>
      {/* ── Header info card ── */}
      <Card
        size="small"
        style={{
          marginBottom: 16,
          background: "linear-gradient(135deg, #e6f0ff 0%, #d6e8ff 100%)",
          borderColor: "#91caff",
        }}
      >
        <Row justify="space-between" align="middle">
          <Col>
            <Space size={4}>
              <InfoCircleOutlined style={{ color: "#1677ff", fontSize: 16 }} />
              <Text style={{ color: "#1d39c4", fontSize: 14 }}>
                系统预置 <Text strong>3 套标准节点模板</Text>
                （监理 / 设计 / 检测），创建费用合同后可通过模板快速生成支付节点。
                您也可以根据业务需要 <Text strong>创建自定义模板</Text>。
              </Text>
            </Space>
          </Col>
          <Col>
            <Button type="primary" icon={<PlusOutlined />} onClick={openNewTemplate}>
              新建模板
            </Button>
          </Col>
        </Row>
      </Card>

      {/* ── Template table ── */}
      <Card title="节点模板管理">
        <Table
          size="small"
          rowKey="id"
          dataSource={templates}
          columns={mainColumns}
          pagination={false}
          locale={{ emptyText: "暂无模板" }}
        />
      </Card>

      {/* ── Detail section (below table) ── */}
      {selectedTemplate && (
        <Card
          title={
            <Space>
              <span>模板详情 — {selectedTemplate.name}</span>
              <Tag color={selectedTemplate.is_builtin ? "blue" : "default"}>
                {selectedTemplate.is_builtin ? "内置" : "自定义"}
              </Tag>
              <Tag color="blue">{selectedTemplate.fee_type}</Tag>
            </Space>
          }
          extra={
            <Space>
              <Button
                size="small"
                icon={<CopyOutlined />}
                onClick={() => copyTemplate(selectedTemplate)}
              >
                复制模板
              </Button>
              <Button
                size="small"
                icon={<CloseOutlined />}
                onClick={() => setSelectedTemplateId(null)}
              >
                收起
              </Button>
            </Space>
          }
          style={{ marginTop: 16 }}
        >
          <Table
            size="small"
            rowKey="seq"
            pagination={false}
            dataSource={selectedTemplate.nodes_def.map((nd) => ({
              key: `${selectedTemplate.id}_${nd.seq}`,
              ...nd,
            }))}
            columns={detailColumns}
            summary={() =>
              selectedTemplate.nodes_def.length > 0 ? (
                <Table.Summary.Row>
                  <Table.Summary.Cell index={0} colSpan={3}>
                    <Text strong>合计</Text>
                  </Table.Summary.Cell>
                  <Table.Summary.Cell index={3} align="center">
                    <Text strong type="success">
                      {selectedTemplate.nodes_def.reduce((s, nd) => s + nd.ratio, 0)}%
                    </Text>
                  </Table.Summary.Cell>
                  <Table.Summary.Cell index={4} align="center">
                    <Text type="secondary">
                      {selectedTemplate.nodes_def.length} 个节点
                    </Text>
                  </Table.Summary.Cell>
                </Table.Summary.Row>
              ) : null
            }
          />
        </Card>
      )}

      {/* ── New template drawer ── */}
      <Drawer
        title="新建节点模板"
        width={720}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        extra={
          <Space>
            <Button onClick={() => setDrawerOpen(false)}>取消</Button>
            <Button type="primary" onClick={saveTemplate}>
              保存模板
            </Button>
          </Space>
        }
      >
        <Form layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="模板名称"
                required
                help="例如：监理费用模板、设计费用模板"
              >
                <Input
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  placeholder="输入模板名称"
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="费用类型"
                required
                help="选择已有类型或直接输入新类型（回车添加）"
              >
                <Select
                  mode="tags"
                  maxCount={1}
                  value={formFeeType ? [formFeeType] : []}
                  placeholder="选择或输入费用类型"
                  style={{ width: "100%" }}
                  options={feeTypes.map((t) => ({ value: t, label: t }))}
                  onChange={(val: string[]) => {
                    const newVal = val.length > 0 ? val[val.length - 1] : "";
                    setFormFeeType(newVal);
                    if (newVal && !feeTypes.includes(newVal)) {
                      setFeeTypes((prev) => [...prev, newVal]);
                    }
                  }}
                />
              </Form.Item>
            </Col>
          </Row>

          {/* ── Node list editor ── */}
          <div style={{ marginTop: 8 }}>
            <Row justify="space-between" align="middle" style={{ marginBottom: 8 }}>
              <Col>
                <Text strong>支付节点配置</Text>
                <Text type="secondary" style={{ marginLeft: 8, fontSize: 12 }}>
                  （比例之和需为 100%）
                </Text>
              </Col>
              <Col>
                <Button
                  size="small"
                  type="dashed"
                  icon={<PlusCircleOutlined />}
                  onClick={addFormNode}
                >
                  添加节点
                </Button>
              </Col>
            </Row>

            <Table
              size="small"
              rowKey="key"
              dataSource={formNodes}
              columns={drawerNodeColumns}
              pagination={false}
              bordered
            />

            {/* ratio sum indicator */}
            <div style={{ marginTop: 8, textAlign: "right" }}>
              <Text
                type={formNodes.reduce((s, nd) => s + nd.ratio, 0) === 100 ? "success" : "danger"}
                strong
              >
                比例合计：{formNodes.reduce((s, nd) => s + nd.ratio, 0)}%
              </Text>
            </div>
          </div>
        </Form>
      </Drawer>
    </div>
  );
}
