import { useState } from "react";
import { Card, Select, Space, Button, Row, Col, Tag, Statistic } from "antd";
import ReactECharts from "echarts-for-react";
import { mockSCurveData, mockProjects } from "../../utils/mock";

export default function SCurve() {
  const [selectedProjects, setSelectedProjects] = useState<string[]>(["p1"]);
  const d = mockSCurveData;

  const option = {
    tooltip: { trigger: "axis", formatter: (params: any) => {
      let r = `${params[0]?.axisValue}<br/>`;
      params.forEach((p: any) => { r += `${p.marker} ${p.seriesName}: ${p.value}%<br/>`; });
      return r;
    }},
    legend: { data: ["计划完成率", "实际完成率", "累计计划", "累计实际"], top: 10 },
    grid: { top: 60, right: 30, bottom: 30, left: 50 },
    xAxis: { type: "category", data: d.months, axisLabel: { rotate: 45, fontSize: 11 } },
    yAxis: { type: "value", name: "完成率(%)", max: 100 },
    series: [
      { name: "计划完成率", type: "line", data: d.planned, smooth: true,
        lineStyle: { type: "dashed", color: "#1677ff", width: 2 },
        itemStyle: { color: "#1677ff" } },
      { name: "实际完成率", type: "line", data: d.actual, smooth: true,
        lineStyle: { color: "#52c41a", width: 2 },
        itemStyle: { color: "#52c41a" },
        markLine: {
          silent: true,
          symbol: "none",
          label: { formatter: "主体封顶" },
          data: [{ xAxis: "2026-06", lineStyle: { color: "#fa8c16", type: "dashed" } }],
        }},
    ],
  };

  const p1 = mockProjects.find(p => p.id === "p1");
  const currentProgress = p1?.progress || 0;
  const plannedProgress = 75; // 计划此时应为75%

  return (
    <div>
      {/* 选择器 */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={[12, 8]} align="middle">
          <Col>
            <Select mode="multiple" value={selectedProjects} onChange={setSelectedProjects}
              style={{ minWidth: 280 }} placeholder="选择项目"
              options={mockProjects.map(p => ({ value: p.id, label: `${p.project_name} (${p.project_code})` }))} />
          </Col>
          <Col>
            <Button type="primary">生成 S 曲线</Button>
          </Col>
        </Row>
      </Card>

      {/* 进度偏差指标 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={12} sm={6}>
          <Card size="small"><Statistic title="当前实际进度" value={currentProgress} suffix="%" valueStyle={{ color: "#1677ff" }} /></Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small"><Statistic title="当前计划进度" value={plannedProgress} suffix="%" valueStyle={{ color: "#999" }} /></Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic title="进度偏差" value={Math.abs(currentProgress - plannedProgress)} suffix="%"
              valueStyle={{ color: currentProgress >= plannedProgress ? "#52c41a" : "#ff4d4f" }} />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic title="状态" value={currentProgress >= plannedProgress ? "正常/超前" : "滞后"}
              valueStyle={{ color: currentProgress >= plannedProgress ? "#52c41a" : "#ff4d4f", fontSize: 18 }} />
          </Card>
        </Col>
      </Row>

      {/* S 曲线图 */}
      <Card title="S 曲线（计划 vs 实际完成率）">
        <ReactECharts option={option} style={{ height: 420 }} />
      </Card>

      {/* 洞察卡片 */}
      <Card size="small" style={{ marginTop: 16, background: "#f6ffed" }}>
        <Row align="middle">
          <Col flex="auto">
            <span style={{ fontSize: 13 }}>
              💡 <strong>分析：</strong>1-6号粮仓工程实际进度 {currentProgress}%，较计划进度 {plannedProgress}% 偏差 -{plannedProgress - currentProgress}%。
              偏差在可控范围内（&lt;5%），主要受6月雨季影响。预计7月可追赶至计划线。
            </span>
          </Col>
          <Col>
            <Tag color="orange">偏差 -{plannedProgress - currentProgress}%</Tag>
          </Col>
        </Row>
      </Card>
    </div>
  );
}
