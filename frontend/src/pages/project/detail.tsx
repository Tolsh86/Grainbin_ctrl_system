import { useState } from "react";
import {
  Card, Row, Col, Descriptions, Tag, Progress, Statistic, Timeline, Tabs,
  Button, Space, Tooltip, message, Steps, Typography,
} from "antd";
import {
  EditOutlined, DeleteOutlined, ArrowLeftOutlined,
  CheckCircleOutlined, ClockCircleOutlined, SyncOutlined,
  CalendarOutlined,
} from "@ant-design/icons";
import { useParams, useNavigate } from "react-router-dom";
import {
  mockProjects, mockMilestones, mockProgressReports, formatYuan,
} from "../../utils/mock";
import type { ProjectMilestone, ProgressReport } from "../../utils/mock";

const { Text } = Typography;

// ── Unit type display config ──
const unitTypeConfig: Record<ProgressReport["unit_type"], { label: string; color: string }> = {
  constructor: { label: "施工单位", color: "#1677ff" },
  supervisor: { label: "监理单位", color: "#52c41a" },
  designer:   { label: "设计单位", color: "#fa8c16" },
  owner:      { label: "建设单位", color: "#722ed1" },
};

const unitTypeOrder: ProgressReport["unit_type"][] = [
  "constructor", "supervisor", "designer", "owner",
];

// ── Milestone status display config ──
const milestoneStatusConfig: Record<
  ProjectMilestone["status"],
  { color: string; label: string; icon: React.ReactNode }
> = {
  completed:   { color: "green", label: "已完成", icon: <CheckCircleOutlined /> },
  in_progress: { color: "blue",  label: "进行中", icon: <SyncOutlined spin /> },
  pending:     { color: "gray",  label: "待开始", icon: <ClockCircleOutlined /> },
};

// ── Steps status mapping (milestone.status → Steps item status) ──
const stepsStatusMap: Record<ProjectMilestone["status"], "finish" | "process" | "wait"> = {
  completed:   "finish",
  in_progress: "process",
  pending:     "wait",
};

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const project = mockProjects.find((p) => p.id === id);

  // ── Not-found guard ──
  if (!project) {
    return (
      <Card>
        <p>项目不存在或您无权访问</p>
        <Button onClick={() => navigate("/projects")}>返回项目列表</Button>
      </Card>
    );
  }

  // ── Status label map ──
  const statusMap: Record<string, { color: string; text: string }> = {
    construction: { color: "blue",    text: "施工中" },
    preparation:  { color: "default", text: "筹备中" },
    completed:    { color: "green",   text: "已完工" },
    paused:       { color: "orange",  text: "暂停" },
  };
  const s = statusMap[project.status] || { color: "default", text: project.status };

  // ── Derived data ──
  const milestones = mockMilestones
    .filter((m) => m.project_id === project.id)
    .sort((a, b) => a.seq - b.seq);

  const progressReports = mockProgressReports.filter(
    (r) => r.project_id === project.id,
  );

  const contractAmount = project.total_investment;
  const paidAmount = Math.round((contractAmount * project.progress) / 100 * 0.75);
  const unpaidAmount = contractAmount - paidAmount;
  const pendingAmount = Math.round(contractAmount * 0.05);

  // ═══════════════════════════════════════════════════════════════
  //  Tab 1 — 概览 (Overview)
  // ═══════════════════════════════════════════════════════════════
  const overviewTab = (
    <div>
      <Row gutter={[16, 16]}>
        {/* ── 基本信息 ── */}
        <Col xs={24} lg={16}>
          <Card title="基本信息" size="small">
            <Descriptions bordered size="small" column={{ xs: 1, sm: 2 }}>
              <Descriptions.Item label="项目名称" span={2}>
                {project.project_name}
              </Descriptions.Item>
              <Descriptions.Item label="项目编号">{project.project_code}</Descriptions.Item>
              <Descriptions.Item label="建设规模">{project.construction_scale}</Descriptions.Item>
              <Descriptions.Item label="建设单位">{project.owner_unit}</Descriptions.Item>
              <Descriptions.Item label="施工单位">{project.constructor_unit}</Descriptions.Item>
              <Descriptions.Item label="监理单位">{project.supervisor_unit}</Descriptions.Item>
              <Descriptions.Item label="设计单位">{project.design_unit}</Descriptions.Item>
              <Descriptions.Item label="项目地点">{project.project_location}</Descriptions.Item>
              <Descriptions.Item label="项目经理">{project.project_manager}</Descriptions.Item>
              <Descriptions.Item label="计划开工">{project.planned_start_date}</Descriptions.Item>
              <Descriptions.Item label="计划竣工">{project.planned_end_date}</Descriptions.Item>
              <Descriptions.Item label="当前进度" span={2}>
                <Progress percent={project.progress} />
              </Descriptions.Item>
              <Descriptions.Item label="项目状态">
                <Tag color={s.color}>{s.text}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="备注">{project.description || "—"}</Descriptions.Item>
            </Descriptions>
          </Card>
        </Col>

        {/* ── 投资信息 + 进度信息 ── */}
        <Col xs={24} lg={8}>
          <Card title="投资信息" size="small" style={{ marginBottom: 16 }}>
            <Row gutter={[8, 8]}>
              <Col span={12}>
                <Statistic title="合同金额" value={`¥${formatYuan(contractAmount)}`} />
              </Col>
              <Col span={12}>
                <Statistic title="已支付" value={`¥${formatYuan(paidAmount)}`} />
              </Col>
              <Col span={12}>
                <Statistic
                  title="未支付"
                  value={`¥${formatYuan(unpaidAmount)}`}
                  valueStyle={{ color: "#fa8c16" }}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="待审核"
                  value={`¥${formatYuan(pendingAmount)}`}
                  valueStyle={{ color: "#ff4d4f" }}
                />
              </Col>
            </Row>
          </Card>

          <Card title="进度信息" size="small">
            <Statistic title="完成率" value={project.progress} suffix="%" />
            <div style={{ fontSize: 12, color: "#999", marginTop: 8 }}>
              本月新增产值: ¥{formatYuan(520000000)}
            </div>
          </Card>
        </Col>
      </Row>

      {/* ── 关键里程碑 (使用 mockMilestones) ── */}
      <Card title="关键里程碑" size="small" style={{ marginTop: 16 }}>
        {milestones.length > 0 ? (
          <Timeline
            items={milestones.map((m) => ({
              color: milestoneStatusConfig[m.status].color,
              dot: milestoneStatusConfig[m.status].icon,
              children: (
                <div>
                  <Text strong>{m.name}</Text>
                  <div style={{ fontSize: 12, color: "#666", marginTop: 2 }}>
                    <CalendarOutlined style={{ marginRight: 4 }} />
                    计划: {m.planned_date}
                    {m.actual_date && (
                      <span style={{ marginLeft: 16 }}>实际: {m.actual_date}</span>
                    )}
                  </div>
                  {m.description && (
                    <div style={{ fontSize: 12, color: "#999", marginTop: 2 }}>
                      {m.description}
                    </div>
                  )}
                  <Tag
                    color={milestoneStatusConfig[m.status].color}
                    style={{ marginTop: 4 }}
                  >
                    {milestoneStatusConfig[m.status].label}
                  </Tag>
                </div>
              ),
            }))}
          />
        ) : (
          <Text type="secondary">暂无里程碑数据</Text>
        )}
      </Card>
    </div>
  );

  // ═══════════════════════════════════════════════════════════════
  //  Tab 2 — 进度看板 (Progress Kanban)
  // ═══════════════════════════════════════════════════════════════
  const kanbanTab = (
    <div>
      {/* 四列参建单位进度卡片 */}
      <Row gutter={[16, 16]}>
        {unitTypeOrder.map((unitType) => {
          const report = progressReports.find((r) => r.unit_type === unitType);
          const cfg = unitTypeConfig[unitType];

          return (
            <Col xs={24} sm={12} lg={6} key={unitType}>
              <Card
                title={
                  <Space size={6}>
                    <span
                      style={{
                        display: "inline-block",
                        width: 8,
                        height: 8,
                        borderRadius: "50%",
                        background: cfg.color,
                      }}
                    />
                    <span>{cfg.label}</span>
                    {report && (
                      <Tooltip title="填报人">
                        <Tag style={{ marginLeft: 4 }}>{report.reporter_name}</Tag>
                      </Tooltip>
                    )}
                  </Space>
                }
                size="small"
                style={{ height: "100%" }}
              >
                {report ? (
                  <div>
                    {report.content.items.map((item, idx) => (
                      <div key={idx} style={{ marginBottom: 16 }}>
                        <div
                          style={{
                            display: "flex",
                            justifyContent: "space-between",
                            marginBottom: 4,
                          }}
                        >
                          <Text>{item.name}</Text>
                          <Text type="secondary">{item.progress}%</Text>
                        </div>
                        <Progress
                          percent={item.progress}
                          size="small"
                          strokeColor={cfg.color}
                        />
                        {item.note && (
                          <Text
                            type="secondary"
                            style={{ fontSize: 12, display: "block", marginTop: 2 }}
                          >
                            {item.note}
                          </Text>
                        )}
                      </div>
                    ))}
                    <div style={{ marginTop: 4 }}>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        填报日期: {report.report_date}
                      </Text>
                    </div>
                  </div>
                ) : (
                  <div
                    style={{
                      textAlign: "center",
                      padding: "24px 0",
                      color: "#bbb",
                    }}
                  >
                    暂无进度数据
                  </div>
                )}

                <div style={{ marginTop: 16 }}>
                  <Button
                    type="primary"
                    ghost
                    size="small"
                    block
                    onClick={() =>
                      message.info(`${cfg.label}进度填报功能开发中`)
                    }
                  >
                    填报进度
                  </Button>
                </div>
              </Card>
            </Col>
          );
        })}
      </Row>

      {/* 横向里程碑时间线 */}
      <Card title="项目里程碑" size="small" style={{ marginTop: 16 }}>
        {milestones.length > 0 ? (
          <div style={{ overflowX: "auto" }}>
            <Steps
              current={Math.max(
                milestones.findIndex((m) => m.status === "in_progress"),
                0,
              )}
              size="small"
              items={milestones.map((m) => ({
                title: m.name,
                description: (
                  <div style={{ fontSize: 12 }}>
                    <div>{m.planned_date}</div>
                    {m.actual_date && (
                      <div style={{ color: "#52c41a" }}>实际: {m.actual_date}</div>
                    )}
                    <Tag
                      color={milestoneStatusConfig[m.status].color}
                      style={{ fontSize: 10, marginTop: 2 }}
                    >
                      {milestoneStatusConfig[m.status].label}
                    </Tag>
                  </div>
                ),
                status: stepsStatusMap[m.status],
              }))}
            />
          </div>
        ) : (
          <Text type="secondary">暂无里程碑数据</Text>
        )}
      </Card>
    </div>
  );

  // ═══════════════════════════════════════════════════════════════
  //  Tab items
  // ═══════════════════════════════════════════════════════════════
  const tabItems = [
    { key: "overview", label: "概览", children: overviewTab },
    { key: "kanban",   label: "进度看板", children: kanbanTab },
    {
      key: "data",
      label: "数据",
      children: (
        <Card size="small">
          <p>
            跳转到{" "}
            <Button type="link" onClick={() => navigate("/data/list")}>
              数据中心
            </Button>{" "}
            查看本项目数据
          </p>
        </Card>
      ),
    },
    {
      key: "report",
      label: "报告",
      children: (
        <Card size="small">
          <p>
            跳转到{" "}
            <Button type="link" onClick={() => navigate("/reports")}>
              报告中心
            </Button>{" "}
            查看本项目报告
          </p>
        </Card>
      ),
    },
    {
      key: "audit",
      label: "审核",
      children: (
        <Card size="small">
          <p>
            跳转到{" "}
            <Button type="link" onClick={() => navigate("/audits")}>
              审核中心
            </Button>{" "}
            查看本项目审核
          </p>
        </Card>
      ),
    },
  ];

  // ═══════════════════════════════════════════════════════════════
  //  Render
  // ═══════════════════════════════════════════════════════════════
  return (
    <div>
      {/* ── 页头 ── */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Space size="middle" wrap>
              <Button
                type="text"
                icon={<ArrowLeftOutlined />}
                onClick={() => navigate("/projects")}
              >
                返回
              </Button>
              <span style={{ fontSize: 18, fontWeight: 600 }}>
                {project.project_name}
              </span>
              <Tag color="blue">{project.project_code}</Tag>
              <Tag color={s.color}>{s.text}</Tag>
              <Progress
                percent={project.progress}
                size="small"
                style={{ width: 120 }}
              />
            </Space>
          </Col>
          <Col>
            <Space>
              <Button icon={<EditOutlined />} onClick={() => message.info("编辑功能")}>
                编辑
              </Button>
              <Button
                icon={<DeleteOutlined />}
                danger
                onClick={() => message.warning("归档功能")}
              >
                归档
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      <Tabs defaultActiveKey="overview" items={tabItems} />
    </div>
  );
}
