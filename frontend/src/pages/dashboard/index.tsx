import { useState, useEffect } from "react";
import { Row, Col, Card, Statistic, List, Badge, Button, message, Tag, Timeline, Progress } from "antd";
import {
  ProjectOutlined,
  DollarOutlined,
  AuditOutlined,
  FileTextOutlined,
  RobotOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  ReloadOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  CloudOutlined,
  UploadOutlined,
  PlusOutlined,
  FundOutlined,
  BookOutlined,
  SettingOutlined,
} from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import ReactECharts from "echarts-for-react";
import {
  mockDashboardStats,
  mockWeeklyReportStatus,
  mockSCurveMini,
  mockInvestmentMini,
  mockAISummary,
  mockTodos,
  mockWeather,
} from "../../utils/mock";

const formatYuan = (fen: number) => (fen / 100).toLocaleString();

export default function Dashboard() {
  const [currentTime, setCurrentTime] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    const tick = () => setCurrentTime(new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" }));
    tick();
    const timer = setInterval(tick, 60000);
    return () => clearInterval(timer);
  }, []);

  const scurveOption = {
    tooltip: { trigger: "axis" },
    legend: { data: ["计划完成率(%)", "实际完成率(%)"] },
    xAxis: { type: "category", data: mockSCurveMini.months },
    yAxis: { type: "value", name: "%", max: 100 },
    series: [
      { name: "计划完成率(%)", type: "line", data: mockSCurveMini.planned, smooth: true, lineStyle: { type: "dashed", color: "#1677ff" } },
      { name: "实际完成率(%)", type: "line", data: mockSCurveMini.actual, smooth: true, lineStyle: { color: "#52c41a" } },
    ],
  };

  const investOption = {
    tooltip: { trigger: "axis" },
    legend: { data: ["月度投资(万元)", "累计投资(万元)"] },
    xAxis: { type: "category", data: mockInvestmentMini.months },
    yAxis: [{ type: "value", name: "月度(万元)" }, { type: "value", name: "累计(万元)" }],
    series: [
      { name: "月度投资(万元)", type: "bar", data: mockInvestmentMini.monthly, color: "#52c41a" },
      { name: "累计投资(万元)", type: "line", yAxisIndex: 1, data: mockInvestmentMini.cumulative, smooth: true },
    ],
  };

  const levelTag = (level: string) => {
    const map: Record<string, { color: string; text: string }> = { danger: { color: "red", text: "高风险" }, warning: { color: "orange", text: "中风险" }, info: { color: "blue", text: "提示" } };
    const m = map[level] || { color: "default", text: level };
    return <Tag color={m.color}>{m.text}</Tag>;
  };

  const urgencyBadge = (u: string) => {
    const map: Record<string, "error" | "processing" | "default"> = { high: "error", medium: "processing", low: "default" };
    return <Badge status={map[u] || "default"} />;
  };

  const quickEntries = [
    { label: "数据上传", icon: <UploadOutlined />, path: "/data/upload" },
    { label: "新建周报", icon: <PlusOutlined />, path: "/reports" },
    { label: "新建审核", icon: <AuditOutlined />, path: "/audits/upload" },
    { label: "驾驶舱", icon: <FundOutlined />, path: "/cockpit/overview" },
    { label: "知识库", icon: <BookOutlined />, path: "/knowledge/docs" },
    { label: "系统设置", icon: <SettingOutlined />, path: "/system/users" },
  ];

  return (
    <div>
      {/* 1. 欢迎区 */}
      <Card style={{ marginBottom: 16 }} size="small">
        <Row justify="space-between" align="middle">
          <Col>
            <span style={{ fontSize: 16, fontWeight: 600 }}>欢迎回来，管理员</span>
            <span style={{ color: "#999", marginLeft: 12 }}>当前时间：{currentTime}</span>
            <Tag style={{ marginLeft: 12 }}>角色: admin</Tag>
          </Col>
          <Col>
            <span style={{ color: "#999" }}>当前项目：</span>
            <Tag color="blue">1-6号粮仓新建工程</Tag>
          </Col>
        </Row>
      </Card>

      {/* 2. 统计卡片 */}
      <Row gutter={[16, 16]}>
        {[
          { title: "在建项目数", value: mockDashboardStats.active_projects, suffix: "个", icon: <ProjectOutlined />, color: "#1677ff", path: "/projects" },
          { title: "本月总产值", value: `¥${formatYuan(mockDashboardStats.monthly_output)}`, suffix: "", icon: <DollarOutlined />, color: "#52c41a", trend: 12.5, path: "/cockpit/investment" },
          { title: "本月待审核", value: mockDashboardStats.pending_audits, suffix: "笔", icon: <AuditOutlined />, color: "#fa8c16", path: "/audits" },
          { title: "已完成报告", value: mockDashboardStats.completed_reports, suffix: "份", icon: <FileTextOutlined />, color: "#722ed1", path: "/reports" },
        ].map((item, i) => (
          <Col xs={24} sm={12} lg={6} key={i}>
            <Card hoverable onClick={() => navigate(item.path)} style={{ cursor: "pointer" }}>
              <Statistic title={item.title} value={item.value} suffix={item.suffix} prefix={item.icon} valueStyle={{ color: item.color }} />
              {"trend" in item && item.trend !== undefined && (
                <div style={{ marginTop: 8, fontSize: 12 }}>
                  较上月 {item.trend > 0 ? <span style={{ color: "#52c41a" }}><ArrowUpOutlined /> {item.trend}%</span> : <span style={{ color: "#ff4d4f" }}><ArrowDownOutlined /> {Math.abs(item.trend)}%</span>}
                </div>
              )}
            </Card>
          </Col>
        ))}
      </Row>

      {/* 3. 本周周报状态 + 6. AI 摘要 */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={8}>
          <Card title="本周周报状态" size="small">
            <Row gutter={8}>
              <Col span={8}><Card size="small" style={{ textAlign: "center" }}><Statistic title="草稿" value={mockWeeklyReportStatus.draft} valueStyle={{ color: "#999" }} /></Card></Col>
              <Col span={8}><Card size="small" style={{ textAlign: "center" }}><Statistic title="待审核" value={mockWeeklyReportStatus.pending_review} valueStyle={{ color: "#fa8c16" }} /></Card></Col>
              <Col span={8}><Card size="small" style={{ textAlign: "center" }}><Statistic title="已发布" value={mockWeeklyReportStatus.published} valueStyle={{ color: "#52c41a" }} /></Card></Col>
            </Row>
            <Button type="link" onClick={() => navigate("/reports")} style={{ marginTop: 8 }}>前往报告中心 →</Button>
          </Card>
        </Col>
        <Col xs={24} lg={16}>
          <Card title={<><RobotOutlined style={{ marginRight: 8 }} />AI 分析摘要</>} size="small"
            extra={<Button size="small" icon={<ReloadOutlined />} onClick={() => message.success("AI 摘要已刷新")}>刷新</Button>}
          >
            {mockAISummary.map((item, i) => (
              <div key={i} style={{ marginBottom: 8, display: "flex", alignItems: "flex-start", gap: 8 }}>
                {levelTag(item.level)}
                <span style={{ fontSize: 13, lineHeight: "24px" }}>{item.content}</span>
              </div>
            ))}
          </Card>
        </Col>
      </Row>

      {/* 4. S曲线 + 5. 投资分析 */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <Card title="进度 S 曲线" size="small" extra={<Button type="link" size="small" onClick={() => navigate("/cockpit/scurve")}>全屏 →</Button>}>
            <ReactECharts option={scurveOption} style={{ height: 260 }} />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="投资分析" size="small" extra={<Button type="link" size="small" onClick={() => navigate("/cockpit/investment")}>全屏 →</Button>}>
            <ReactECharts option={investOption} style={{ height: 260 }} />
          </Card>
        </Col>
      </Row>

      {/* 7. 待办列表 + 8. 天气 */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <Card title="待办列表" size="small">
            <List
              size="small"
              dataSource={mockTodos}
              renderItem={(item) => (
                <List.Item style={{ cursor: "pointer" }} onClick={() => navigate(item.target)}>
                  <List.Item.Meta avatar={urgencyBadge(item.urgency)} title={<span style={{ fontSize: 13 }}>{item.title}</span>} />
                  <Tag>{item.type === "batch" ? "批次" : item.type === "report" ? "报告" : "审核"}</Tag>
                </List.Item>
              )}
            />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title={<><CloudOutlined /> {mockWeather.city} 天气</>} size="small">
            <Row gutter={8}>
              <Col span={12}>
                <Statistic title="当前温度" value={mockWeather.temp} suffix="℃" />
                <div style={{ fontSize: 12, color: "#999" }}>湿度 {mockWeather.humidity}% · {mockWeather.condition}</div>
              </Col>
              <Col span={12}>
                <Row gutter={4}>
                  {mockWeather.forecast.slice(0, 4).map((f, i) => (
                    <Col span={6} key={i} style={{ textAlign: "center", fontSize: 11 }}>
                      <div>{f.day}</div>
                      <div style={{ color: "#ff4d4f" }}>{f.temp_high}°</div>
                      <div style={{ color: "#1677ff" }}>{f.temp_low}°</div>
                    </Col>
                  ))}
                </Row>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>

      {/* 9. 快捷入口 */}
      <Card title="快捷入口" size="small" style={{ marginTop: 16 }}>
        <Row gutter={[16, 16]}>
          {quickEntries.map((item, i) => (
            <Col xs={12} sm={8} md={4} key={i}>
              <Card hoverable size="small" style={{ textAlign: "center" }} onClick={() => navigate(item.path)}>
                <div style={{ fontSize: 28, color: "#1677ff", marginBottom: 8 }}>{item.icon}</div>
                <div style={{ fontSize: 13 }}>{item.label}</div>
              </Card>
            </Col>
          ))}
        </Row>
      </Card>
    </div>
  );
}