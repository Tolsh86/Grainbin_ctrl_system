import { useState, useEffect } from "react";
import {
  Card, Row, Col, Descriptions, Tag, Statistic, Tabs,
  Button, Space, message, Spin, Alert,
} from "antd";
import {
  EditOutlined, ArrowLeftOutlined,
} from "@ant-design/icons";
import { useParams, useNavigate } from "react-router-dom";
import { getProject, type ProjectResponse } from "../../api/projects";

const formatWan = (fen: number | null | undefined) =>
  `${((fen ?? 0) / 1_000_000).toLocaleString("zh-CN", { maximumFractionDigits: 2 })} 万元`;

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<ProjectResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    getProject(id)
      .then(setProject)
      .catch(() => message.error("加载项目详情失败"))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <Spin style={{ display: "block", marginTop: 80 }} />;
  if (!project) {
    return (
      <Card>
        <p>项目不存在或您无权访问</p>
        <Button onClick={() => navigate("/projects")}>返回项目列表</Button>
      </Card>
    );
  }

  const statusMap: Record<string, { color: string; text: string }> = {
    constructing: { color: "blue",    text: "施工中" },
    preparing:    { color: "default", text: "筹备中" },
    completed:    { color: "green",   text: "已完工" },
    suspended:    { color: "orange",  text: "暂停" },
  };
  const s = statusMap[project.project_status] || { color: "default", text: project.project_status };

  const overviewTab = (
    <div>
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <Card title="基本信息" size="small">
            <Descriptions bordered size="small" column={{ xs: 1, sm: 2 }}>
              <Descriptions.Item label="项目名称" span={2}>{project.project_name}</Descriptions.Item>
              <Descriptions.Item label="项目编号">{project.project_code}</Descriptions.Item>
              <Descriptions.Item label="项目状态">
                <Tag color={s.color}>{s.text}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="项目性质">{project.project_nature || "—"}</Descriptions.Item>
              <Descriptions.Item label="投资时序">{project.invest_timing || "—"}</Descriptions.Item>
              <Descriptions.Item label="投资性质">{project.invest_nature || "—"}</Descriptions.Item>
              <Descriptions.Item label="投资领域">{project.invest_field || "—"}</Descriptions.Item>
              <Descriptions.Item label="区域">{project.region || "—"}</Descriptions.Item>
              <Descriptions.Item label="建设单位">{project.owner_unit || "—"}</Descriptions.Item>
              <Descriptions.Item label="责任单位">{project.responsible_unit || "—"}</Descriptions.Item>
              <Descriptions.Item label="实施周期">{project.start_date || "—"} 至 {project.end_date || "—"}</Descriptions.Item>
              <Descriptions.Item label="建设周期">{project.construction_period || "—"}</Descriptions.Item>
              <Descriptions.Item label="建设内容" span={2}>{project.construction_content || "—"}</Descriptions.Item>
              <Descriptions.Item label="创建时间">{new Date(project.created_at).toLocaleString("zh-CN")}</Descriptions.Item>
              <Descriptions.Item label="更新时间">{new Date(project.updated_at).toLocaleString("zh-CN")}</Descriptions.Item>
            </Descriptions>
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="投资信息" size="small" style={{ marginBottom: 16 }}>
            <Statistic title="计划总投资" value={formatWan(project.planned_total_invest)} />
            {project.planned_invest_2026 != null && (
              <Statistic title="2026年计划投资" value={formatWan(project.planned_invest_2026)} />
            )}
          </Card>
          <Card title="快捷操作" size="small">
            <Space direction="vertical" style={{ width: "100%" }}>
              <Button block onClick={() => navigate(`/projects/${project.id}/contracts`)}>管理合同</Button>
              <Button block onClick={() => navigate(`/audits?project_id=${project.id}`)}>审核记录</Button>
              <Button block onClick={() => navigate(`/data/upload`)}>上传数据</Button>
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  );

  const tabItems = [
    { key: "overview", label: "概览", children: overviewTab },
    {
      key: "data",
      label: "数据",
      children: (
        <Card size="small">
          <p>跳转到 <Button type="link" onClick={() => navigate("/data/list")}>数据中心</Button> 查看本项目数据</p>
        </Card>
      ),
    },
    {
      key: "report",
      label: "报告",
      children: (
        <Card size="small">
          <p>跳转到 <Button type="link" onClick={() => navigate("/reports")}>报告中心</Button> 查看本项目报告</p>
        </Card>
      ),
    },
    {
      key: "audit",
      label: "审核",
      children: (
        <Card size="small">
          <p>跳转到 <Button type="link" onClick={() => navigate("/audits")}>审核中心</Button> 查看本项目审核</p>
        </Card>
      ),
    },
  ];

  return (
    <div>
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Space size="middle" wrap>
              <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate("/projects")}>返回</Button>
              <span style={{ fontSize: 18, fontWeight: 600 }}>{project.project_name}</span>
              <Tag color="blue">{project.project_code}</Tag>
              <Tag color={s.color}>{s.text}</Tag>
            </Space>
          </Col>
          <Col>
            <Button icon={<EditOutlined />} onClick={() => message.info("编辑功能开发中")}>编辑</Button>
          </Col>
        </Row>
      </Card>

      {/* ── start_date/end_date 缺失提示 ── */}
      {!project.start_date && (
        <Alert
          type="warning"
          showIcon
          message="实施时间未设置"
          description="请编辑项目并设置实施起始月和持续时间，否则月度付款总览将按默认 24 个月范围展示。"
          style={{ marginBottom: 16 }}
          action={
            <Button size="small" onClick={() => message.info("请在项目列表页编辑项目信息")}>
              去设置
            </Button>
          }
        />
      )}

      <Tabs defaultActiveKey="overview" items={tabItems} />
    </div>
  );
}
