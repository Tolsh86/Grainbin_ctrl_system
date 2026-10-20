import { useState, useEffect } from "react";
import {
  Card, Table, Tag, Button, Space, Row, Col, Drawer, Form, Input,
  Select, InputNumber, message, Typography, Empty, Popconfirm,
} from "antd";
import {
  PlusOutlined, EyeOutlined, DeleteOutlined,
} from "@ant-design/icons";
import {
  getNodeTemplates,
  createNodeTemplate,
} from "../../api/contracts";

const { Text } = Typography;

/** 统一提取 stages 数组（兼容纯数组和 {stages: [...]} 两种格式） */
const getStageList = (stages: any): any[] => {
  if (!stages) return [];
  if (Array.isArray(stages)) return stages;
  if (typeof stages === "object") {
    // 兼容 seed_data 曾写出的 {"stages": [...]} 格式
    if (Array.isArray(stages.stages)) return stages.stages;
    const vals = Object.values(stages);
    if (vals.length > 0 && Array.isArray(vals[0])) return vals[0];
    return vals;
  }
  return [];
};

// ── Page component ──
export default function NodeTemplates() {
  const [templates, setTemplates] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  // drawer: create
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form] = Form.useForm();

  // drawer: view detail
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailTemplate, setDetailTemplate] = useState<any>(null);

  // ── Load ──
  const loadTemplates = async () => {
    setLoading(true);
    try {
      const res = await getNodeTemplates({ page: 1, page_size: 50 });
      setTemplates(res.items ?? res ?? []);
    } catch { message.error("加载模板失败"); }
    finally { setLoading(false); }
  };

  useEffect(() => { loadTemplates(); }, []);

  // ── Create ──
  const openCreate = () => {
    form.resetFields();
    form.setFieldsValue({ biz_type: "custom", stages: [{ order: 1, node_name: "", agreed_ratio: null, trigger_condition: "", offset_days: null }] });
    setDrawerOpen(true);
  };

  const handleCreate = async () => {
    const values = await form.validateFields().catch(() => null);
    if (!values) return;
    setSaving(true);
    try {
      // 处理 agreed_ratio: 表单存的是百分比数字（如 10 → 0.10）
      const stages = (values.stages || []).map((s: any, i: number) => ({
        order: i + 1,
        node_name: s.node_name,
        agreed_ratio: s.agreed_ratio != null ? Number((s.agreed_ratio / 100).toFixed(4)) : null,
        trigger_condition: s.trigger_condition || null,
        offset_days: s.offset_days != null ? Number(s.offset_days) : null,
      }));
      await createNodeTemplate({ ...values, stages });
      message.success("创建成功");
      setDrawerOpen(false);
      loadTemplates();
    } catch { message.error("创建失败"); }
    finally { setSaving(false); }
  };

  // ── View detail ──
  const viewDetail = (t: any) => {
    setDetailTemplate(t);
    setDetailOpen(true);
  };

  // ── Columns ──
  const columns = [
    {
      title: "模板名称", dataIndex: "template_name", key: "name", width: 180,
      render: (v: string, r: any) => <a onClick={() => viewDetail(r)}>{v}</a>,
    },
    {
      title: "业务类型", dataIndex: "biz_type", key: "type", width: 100,
      render: (v: string) => (
        <Tag color={v === "supervision" ? "purple" : v === "design" ? "blue" : v === "testing" ? "orange" : "cyan"}>
          {v === "supervision" ? "监理" : v === "design" ? "设计" : v === "testing" ? "检测" : v}
        </Tag>
      ),
    },
    {
      title: "描述", dataIndex: "description", key: "desc", ellipsis: true,
    },
    {
      title: "节点数", key: "count", width: 80, align: "center" as const,
      render: (_: any, r: any) => {
        const list = getStageList(r.stages);
        return list.length > 0 ? list.length : "—";
      },
    },
    {
      title: "预置", dataIndex: "is_preset", key: "preset", width: 70, align: "center" as const,
      render: (v: boolean) => <Tag color={v ? "green" : "default"}>{v ? "是" : "否"}</Tag>,
    },
    {
      title: "创建时间", dataIndex: "created_at", key: "time", width: 160,
      render: (v: string) => v ? new Date(v).toLocaleString("zh-CN") : "—",
    },
    {
      title: "操作", key: "op", width: 80,
      render: (_: any, r: any) => (
        <a onClick={() => viewDetail(r)}><EyeOutlined /> 查看</a>
      ),
    },
  ];

  return (
    <div>
      <Card
        title="节点模板"
        extra={<Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>创建模板</Button>}
      >
        <Table
          size="small"
          rowKey="id"
          dataSource={templates}
          columns={columns}
          loading={loading}
          pagination={{ pageSize: 20, showTotal: (total: number) => `共 ${total} 条` }}
        />
      </Card>

      {/* ── Create Drawer ── */}
      <Drawer
        title="创建节点模板"
        width={600}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        extra={<Space><Button onClick={() => setDrawerOpen(false)}>取消</Button><Button type="primary" loading={saving} onClick={handleCreate}>创建</Button></Space>}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="template_name" label="模板名称" rules={[{ required: true, message: "请输入模板名称" }]}>
            <Input placeholder="如：监理五节点标准模板" />
          </Form.Item>
          <Form.Item name="biz_type" label="业务类型" rules={[{ required: true, message: "请选择业务类型" }]}>
            <Select options={[
              { value: "supervision", label: "监理" },
              { value: "design", label: "设计" },
              { value: "testing", label: "检测" },
              { value: "construction", label: "施工" },
              { value: "custom", label: "自定义" },
            ]} />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={2} placeholder="模板用途说明" />
          </Form.Item>

          <div style={{ marginBottom: 8, fontWeight: 600, fontSize: 13 }}>节点配置</div>
          <Form.List name="stages">
            {(fields, { add, remove }) => (
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {fields.map(({ key, name, ...restField }, index) => (
                  <Card
                    key={key}
                    size="small"
                    title={`节点 ${index + 1}`}
                    style={{ background: "#fafafa" }}
                    extra={fields.length > 1 ? (
                      <a onClick={() => remove(name)} style={{ color: "#ff4d4f" }}>删除</a>
                    ) : null}
                  >
                    <Row gutter={12}>
                      <Col span={12}>
                        <Form.Item {...restField} name={[name, "node_name"]} label="节点名称"
                          rules={[{ required: true, message: "请输入节点名称" }]}
                        >
                          <Input placeholder="如：合同签订" />
                        </Form.Item>
                      </Col>
                      <Col span={12}>
                        <Form.Item {...restField} name={[name, "agreed_ratio"]} label={
                          <span>支付比例 <span style={{ color: "#999", fontWeight: 400 }}>%</span></span>
                        }>
                          <InputNumber min={0} max={100} precision={1} style={{ width: "100%" }}
                            placeholder="如 10 = 10%" />
                        </Form.Item>
                      </Col>
                    </Row>
                    <Row gutter={12}>
                      <Col span={12}>
                        <Form.Item {...restField} name={[name, "trigger_condition"]} label="触发条件">
                          <Input placeholder="如：签订后7日内" />
                        </Form.Item>
                      </Col>
                      <Col span={12}>
                        <Form.Item {...restField} name={[name, "offset_days"]} label="偏移天数（从签订日起）">
                          <InputNumber min={0} style={{ width: "100%" }} placeholder="如 7" />
                        </Form.Item>
                      </Col>
                    </Row>
                  </Card>
                ))}
                <Button type="dashed" onClick={() => add({ order: fields.length + 1, node_name: "", agreed_ratio: null, trigger_condition: "", offset_days: null })} block icon={<PlusOutlined />}>
                  添加节点
                </Button>
              </div>
            )}
          </Form.List>
        </Form>
      </Drawer>

      {/* ── Detail Drawer ── */}
      <Drawer
        title={detailTemplate?.template_name ?? "模板详情"}
        width={640}
        open={detailOpen}
        onClose={() => setDetailOpen(false)}
      >
        {detailTemplate && (
          <div>
            <Row gutter={[16, 12]}>
              <Col span={12}>
                <Text type="secondary">模板名称：</Text>
                <Text strong>{detailTemplate.template_name}</Text>
              </Col>
              <Col span={12}>
                <Text type="secondary">业务类型：</Text>
                <Tag color="blue">{detailTemplate.biz_type}</Tag>
              </Col>
              <Col span={12}>
                <Text type="secondary">预置：</Text>
                <Tag color={detailTemplate.is_preset ? "green" : "default"}>{detailTemplate.is_preset ? "是" : "否"}</Tag>
              </Col>
              <Col span={12}>
                <Text type="secondary">创建时间：</Text>
                <Text>{detailTemplate.created_at ? new Date(detailTemplate.created_at).toLocaleString("zh-CN") : "—"}</Text>
              </Col>
              {detailTemplate.description && (
                <Col span={24}>
                  <Text type="secondary">描述：</Text>
                  <Text>{detailTemplate.description}</Text>
                </Col>
              )}
            </Row>

            <div style={{ margin: "16px 0 8px" }}>
              <Text strong style={{ fontSize: 14 }}>
                节点配置
                <Text type="secondary" style={{ fontSize: 12, marginLeft: 8, fontWeight: 400 }}>
                  （共 {getStageList(detailTemplate.stages).length} 个节点）
                </Text>
              </Text>
            </div>

            {getStageList(detailTemplate.stages).length > 0 ? (
              <Table
                size="small"
                rowKey="order"
                dataSource={getStageList(detailTemplate.stages)}
                pagination={false}
                columns={[
                  { title: "#", dataIndex: "order", width: 40, align: "center" as const },
                  { title: "节点名称", dataIndex: "node_name", width: 110 },
                  {
                    title: "支付比例", dataIndex: "agreed_ratio", width: 80,
                    render: (v: number | null) => v != null ? `${(v * 100).toFixed(1)}%` : "—",
                  },
                  { title: "触发条件", dataIndex: "trigger_condition", ellipsis: true, render: (v: string | null) => v || "—" },
                  {
                    title: "偏移天数", dataIndex: "offset_days", width: 80,
                    render: (v: number | null) => v != null ? `${v} 天` : "—",
                  },
                ]}
              />
            ) : (
              <Empty description="无节点配置" />
            )}
          </div>
        )}
      </Drawer>
    </div>
  );
}
