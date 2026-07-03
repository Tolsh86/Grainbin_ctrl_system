import { useState } from "react";
import {
  Row, Col, Card, Select, Input, Button, Tag, Progress, Pagination,
  Space, Drawer, Form, InputNumber, Dropdown, message, Empty, MenuProps,
} from "antd";
import {
  PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined,
  SearchOutlined, MoreOutlined, ExportOutlined,
} from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { mockProjects } from "../../utils/mock";

const formatYuan = (fen: number) => (fen / 100).toLocaleString();

export default function ProjectList() {
  const navigate = useNavigate();
  const [statusFilter, setStatusFilter] = useState<string[]>([]);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [editProject, setEditProject] = useState<(typeof mockProjects)[0] | null>(null);
  const [form] = Form.useForm();
  const pageSize = 12;

  let filtered = mockProjects;
  if (statusFilter.length) filtered = filtered.filter((p) => statusFilter.includes(p.status));
  if (search) filtered = filtered.filter((p) => p.project_name.includes(search) || p.project_code.includes(search));
  const paginated = filtered.slice((page - 1) * pageSize, page * pageSize);

  const statusMap: Record<string, { color: string; text: string }> = {
    construction: { color: "blue", text: "施工中" },
    preparation: { color: "default", text: "筹备中" },
    completed: { color: "green", text: "已完工" },
    paused: { color: "orange", text: "暂停" },
  };

  const openCreate = () => { setEditProject(null); form.resetFields(); setDrawerOpen(true); };
  const openEdit = (p: (typeof mockProjects)[0]) => {
    setEditProject(p);
    form.setFieldsValue({
      project_name: p.project_name, project_code: p.project_code,
      total_investment: p.total_investment / 100,
      owner_unit: p.owner_unit, constructor_unit: p.constructor_unit,
      supervisor_unit: p.supervisor_unit, design_unit: p.design_unit,
      project_location: p.project_location, project_manager: p.project_manager,
      status: p.status, planned_start_date: p.planned_start_date,
      planned_end_date: p.planned_end_date,
    });
    setDrawerOpen(true);
  };
  const handleSave = () => {
    form.validateFields().then(() => {
      message.success(editProject ? "项目更新成功" : "项目创建成功");
      setDrawerOpen(false);
    });
  };

  return (
    <div>
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={[16, 8]} align="middle">
          <Col>
            <Select mode="multiple" placeholder="项目状态" style={{ width: 180 }} allowClear
              options={[{ value: "construction", label: "施工中" }, { value: "preparation", label: "筹备中" }]}
              value={statusFilter} onChange={setStatusFilter} />
          </Col>
          <Col>
            <Select placeholder="项目经理" style={{ width: 140 }} allowClear
              options={["张工", "李工", "王工", "孙工"].map((n) => ({ value: n, label: n }))} />
          </Col>
          <Col flex="auto">
            <Input.Search placeholder="搜索项目名称/编号" value={search}
              onChange={(e) => setSearch(e.target.value)} enterButton={<SearchOutlined />} />
          </Col>
          <Col>
            <Space>
              <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>新建项目</Button>
              <Button icon={<ExportOutlined />} onClick={() => message.info("导出功能开发中")}>导出</Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {paginated.length === 0 ? (
        <Empty description="暂无匹配的项目" style={{ marginTop: 64 }}>
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>新建项目</Button>
        </Empty>
      ) : (
        <Row gutter={[16, 16]}>
          {paginated.map((p) => (
            <Col xs={24} sm={12} md={8} lg={6} key={p.id}>
              <Card
                hoverable
                actions={[
                  <EyeOutlined key="view" onClick={() => navigate(`/projects/${p.id}`)} />,
                  <EditOutlined key="edit" onClick={() => openEdit(p)} />,
                  <DeleteOutlined key="del" onClick={() => message.warning(`软删功能：${p.project_name}`)} />,
                ]}
              >
                <Card.Meta
                  title={
                    <span style={{ fontSize: 14 }}>
                      {p.project_name}
                      <Tag style={{ marginLeft: 8 }} color={statusMap[p.status]?.color}>
                        {statusMap[p.status]?.text}
                      </Tag>
                    </span>
                  }
                  description={
                    <div style={{ fontSize: 12 }}>
                      <div>编号: {p.project_code}</div>
                      <div style={{ marginTop: 4 }}>经理: {p.project_manager}</div>
                      <div>合同: ¥{formatYuan(p.total_investment)}</div>
                      <div>开工: {p.planned_start_date}</div>
                      <div style={{ marginTop: 8 }}>
                        <Progress percent={p.progress} size="small" status={p.progress < 30 ? "exception" : "active"} />
                      </div>
                    </div>
                  }
                />
              </Card>
            </Col>
          ))}
        </Row>
      )}

      <div style={{ textAlign: "center", marginTop: 24 }}>
        <Pagination current={page} total={filtered.length} pageSize={pageSize} onChange={setPage} showSizeChanger={false} />
      </div>

      <Drawer
        title={editProject ? "编辑项目" : "新建项目"} width={640} open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        extra={<Space><Button onClick={() => setDrawerOpen(false)}>取消</Button><Button type="primary" onClick={handleSave}>{editProject ? "保存" : "创建"}</Button></Space>}
      >
        <Form form={form} layout="vertical">
          <Row gutter={16}>
            <Col span={12}><Form.Item name="project_name" label="项目名称" rules={[{ required: true }]}><Input /></Form.Item></Col>
            <Col span={12}><Form.Item name="project_code" label="项目编号" rules={[{ required: true }]}><Input /></Form.Item></Col>
            <Col span={12}><Form.Item name="owner_unit" label="建设单位"><Input /></Form.Item></Col>
            <Col span={12}><Form.Item name="constructor_unit" label="施工单位"><Input /></Form.Item></Col>
            <Col span={12}><Form.Item name="supervisor_unit" label="监理单位"><Input /></Form.Item></Col>
            <Col span={12}><Form.Item name="design_unit" label="设计单位"><Input /></Form.Item></Col>
            <Col span={12}><Form.Item name="project_manager" label="项目经理"><Input /></Form.Item></Col>
            <Col span={12}><Form.Item name="project_location" label="项目地点"><Input /></Form.Item></Col>
            <Col span={12}><Form.Item name="total_investment" label="总投资(元)" rules={[{ required: true }]}><InputNumber style={{ width: "100%" }} min={0} /></Form.Item></Col>
            <Col span={12}><Form.Item name="status" label="状态"><Select options={[{ value: "preparation", label: "筹备中" }, { value: "construction", label: "施工中" }]} /></Form.Item></Col>
            <Col span={12}><Form.Item name="planned_start_date" label="计划开工"><Input /></Form.Item></Col>
            <Col span={12}><Form.Item name="planned_end_date" label="计划完工"><Input /></Form.Item></Col>
          </Row>
        </Form>
      </Drawer>
    </div>
  );
}