import { useState, useEffect } from "react";
import {
  Row, Col, Card, Select, Input, Button, Tag, Pagination,
  Space, Drawer, Form, InputNumber, DatePicker, message, Empty, Spin,
} from "antd";
import {
  PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined,
  SearchOutlined,
} from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { getProjects, createProject, updateProject, deleteProject, type ProjectResponse } from "../../api/projects";
import dayjs from "dayjs";

const fenToWan = (fen: number | null | undefined) => (fen ?? 0) / 1_000_000;
const wanToFen = (wan: number | null | undefined) => Math.round((wan ?? 0) * 1_000_000);
const formatWan = (fen: number | null | undefined) =>
  `${fenToWan(fen).toLocaleString("zh-CN", { maximumFractionDigits: 2 })} 万元`;

const formatPeriod = (start: string | null, end: string | null) => {
  if (!start && !end) return "—";
  return `${start ? dayjs(start).format("YYYY-MM") : "—"} 至 ${end ? dayjs(end).format("YYYY-MM") : "—"}`;
};

const statusMap: Record<string, { color: string; text: string }> = {
  constructing: { color: "blue", text: "施工中" },
  preparing: { color: "default", text: "筹备中" },
  completed: { color: "green", text: "已完工" },
  suspended: { color: "orange", text: "暂停" },
};

/** 从 start_date/end_date 解析出起始月和持续月数 */
function parseDateRange(start_date: string | null | undefined, end_date: string | null | undefined): { start_date: dayjs.Dayjs | null; duration_months: number } {
  if (!start_date || !end_date) return { start_date: null, duration_months: 24 };
  const sd = dayjs(start_date);
  const ed = dayjs(end_date);
  if (!sd.isValid() || !ed.isValid()) return { start_date: null, duration_months: 24 };
  const duration = ed.diff(sd, "month") + 1;
  return { start_date: sd, duration_months: Math.max(1, duration) };
}

export default function ProjectList() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<ProjectResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [editProject, setEditProject] = useState<ProjectResponse | null>(null);
  const [saving, setSaving] = useState(false);
  const [form] = Form.useForm();
  const pageSize = 12;

  const fetchProjects = async () => {
    setLoading(true);
    try {
      const res = await getProjects({ page, page_size: pageSize, status: statusFilter, keyword: search || undefined } as any);
      setProjects(res.items);
      setTotal(res.total);
    } catch {
      message.error("加载项目列表失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchProjects(); }, [page, statusFilter, search]);

  const openCreate = () => {
    setEditProject(null);
    form.resetFields();
    form.setFieldsValue({ duration_months: 24 });  // 默认 24 个月
    setDrawerOpen(true);
  };
  const openEdit = (p: ProjectResponse) => {
    setEditProject(p);
    const { start_date, duration_months } = parseDateRange(p.start_date, p.end_date);
    form.setFieldsValue({
      project_name: p.project_name,
      project_code: p.project_code,
      owner_unit: p.owner_unit,
      project_status: p.project_status,
      project_nature: p.project_nature,
      invest_timing: p.invest_timing,
      invest_nature: p.invest_nature,
      region: p.region,
      responsible_unit: p.responsible_unit,
      construction_content: p.construction_content,
      start_date,
      duration_months,
      planned_total_invest: fenToWan(p.planned_total_invest),
      planned_invest_2026: p.planned_invest_2026 == null ? null : fenToWan(p.planned_invest_2026),
    });
    setDrawerOpen(true);
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);
      const body: Record<string, unknown> = { ...values };
      // dayjs → "YYYY-MM-DD"（避免 Pydantic date 拒绝带 T 的 ISO 字符串）
      if (body.start_date && typeof body.start_date !== "string") {
        body.start_date = dayjs(body.start_date as any).format("YYYY-MM-DD");
      }
      body.planned_total_invest = wanToFen(body.planned_total_invest as number | null);
      if (body.planned_invest_2026 !== undefined && body.planned_invest_2026 !== null) {
        body.planned_invest_2026 = wanToFen(body.planned_invest_2026 as number);
      }
      delete body.project_code;  // 由后端自动生成
      if (editProject) {
        await updateProject(editProject.id, body);
        message.success("项目更新成功");
      } else {
        await createProject(body);
        message.success("项目创建成功");
      }
      setDrawerOpen(false);
      fetchProjects();
    } catch (e: any) {
      if (e?.errorFields) return;
      message.error(e?.response?.data?.detail || "操作失败");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (p: ProjectResponse) => {
    try {
      await deleteProject(p.id);
      message.success("项目已删除");
      fetchProjects();
    } catch {
      message.error("删除失败");
    }
  };

  return (
    <div>
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={[16, 8]} align="middle">
          <Col>
            <Select
              placeholder="项目状态" style={{ width: 160 }} allowClear
              value={statusFilter} onChange={setStatusFilter}
              options={[
                { value: "constructing", label: "施工中" },
                { value: "preparing", label: "筹备中" },
                { value: "completed", label: "已完工" },
                { value: "suspended", label: "暂停" },
              ]}
            />
          </Col>
          <Col flex="auto">
            <Input.Search placeholder="搜索项目名称/编号" value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              enterButton={<SearchOutlined />} />
          </Col>
          <Col>
            <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>新建项目</Button>
          </Col>
        </Row>
      </Card>

      <Spin spinning={loading}>
        {!loading && projects.length === 0 ? (
          <Empty description="暂无匹配的项目" style={{ marginTop: 64 }}>
            <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>新建项目</Button>
          </Empty>
        ) : (
          <Row gutter={[16, 16]}>
            {projects.map((p) => (
              <Col xs={24} sm={12} md={8} lg={6} key={p.id}>
                <Card
                  hoverable
                  actions={[
                    <EyeOutlined key="view" onClick={() => navigate(`/projects/${p.id}`)} />,
                    <EditOutlined key="edit" onClick={() => openEdit(p)} />,
                    <DeleteOutlined key="del"
                      onClick={() => {
                        if (confirm(`确定删除项目「${p.project_name}」吗？`)) handleDelete(p);
                      }}
                    />,
                  ]}
                >
                  <Card.Meta
                    title={
                      <span style={{ fontSize: 14 }}>
                        {p.project_name}
                        <Tag style={{ marginLeft: 8 }} color={statusMap[p.project_status]?.color}>
                          {statusMap[p.project_status]?.text || p.project_status}
                        </Tag>
                      </span>
                    }
                    description={
                      <div style={{ fontSize: 12 }}>
                        <div>编号: {p.project_code}</div>
                        <div>类型: {p.project_nature} · {p.invest_timing}</div>
                        <div>计划总投资: <strong>{formatWan(p.planned_total_invest)}</strong></div>
                        <div>年度计划: {p.planned_invest_2026 == null ? "—" : formatWan(p.planned_invest_2026)}</div>
                        <div>建设单位: {p.owner_unit || "—"}</div>
                        <div>实施周期: {formatPeriod(p.start_date, p.end_date)}</div>
                      </div>
                    }
                  />
                </Card>
              </Col>
            ))}
          </Row>
        )}
      </Spin>

      <div style={{ textAlign: "center", marginTop: 24 }}>
        <Pagination current={page} total={total} pageSize={pageSize} onChange={setPage} showSizeChanger={false} />
      </div>

      <Drawer
        title={editProject ? "编辑项目" : "新建项目"} width={640} open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        extra={<Space><Button onClick={() => setDrawerOpen(false)}>取消</Button><Button type="primary" onClick={handleSave} loading={saving}>{editProject ? "保存" : "创建"}</Button></Space>}
      >
        <Form form={form} layout="vertical">
          <Row gutter={16}>
            <Col span={12}><Form.Item name="project_name" label="项目名称" rules={[{ required: true }]}><Input /></Form.Item></Col>
            <Col span={12}>
              <Form.Item name="project_code" label="项目编号">
                <Input disabled placeholder="自动生成 PJ-20260707-001" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="project_nature" label="项目性质">
                <Select options={[
                  { value: "功能性项目", label: "功能性项目" },
                  { value: "商业性项目", label: "商业性项目" },
                ]} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="invest_timing" label="投资时序">
                <Select options={[
                  { value: "新投项目", label: "新投项目" },
                  { value: "续投项目", label: "续投项目" },
                ]} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="invest_nature" label="投资性质">
                <Select allowClear options={[
                  { value: "固定资产投资", label: "固定资产投资" },
                  { value: "股权投资", label: "股权投资" },
                  { value: "其他投资", label: "其他投资" },
                ]} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="region" label="项目区域" initialValue="市内">
                <Select options={[{ value: "市内", label: "市内" }, { value: "市外", label: "市外" }]} />
              </Form.Item>
            </Col>
            {/* 实施时间：起始月 + 持续月数 → 自动生成 end_date */}
            <Col span={12}>
              <Form.Item name="start_date" label="实施起始月" help="选起始月 + 持续月数，自动生成实施时间">
                <DatePicker picker="month" style={{ width: "100%" }} placeholder="选择起始月" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="duration_months" label="持续时间（月）" initialValue={24}>
                <InputNumber min={1} max={360} style={{ width: "100%" }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="planned_total_invest" label="计划总投资（万元）" initialValue={0}>
                <InputNumber min={0} precision={2} style={{ width: "100%" }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="planned_invest_2026" label="2026 年计划投资（万元）">
                <InputNumber min={0} precision={2} style={{ width: "100%" }} />
              </Form.Item>
            </Col>
            <Col span={12}><Form.Item name="owner_unit" label="建设单位"><Input /></Form.Item></Col>
            <Col span={12}><Form.Item name="responsible_unit" label="责任单位"><Input /></Form.Item></Col>
            <Col span={12}>
              <Form.Item name="project_status" label="状态">
                <Select options={[
                  { value: "preparing", label: "筹备中" },
                  { value: "constructing", label: "施工中" },
                  { value: "completed", label: "已完工" },
                  { value: "suspended", label: "暂停" },
                ]} />
              </Form.Item>
            </Col>
            <Col span={24}><Form.Item name="construction_content" label="建设内容"><Input.TextArea rows={3} /></Form.Item></Col>
          </Row>
        </Form>
      </Drawer>
    </div>
  );
}
