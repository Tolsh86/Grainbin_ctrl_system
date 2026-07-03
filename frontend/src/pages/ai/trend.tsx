import { useState } from "react";
import { Card, Select, Button, Space, message } from "antd";
import { RobotOutlined, ReloadOutlined } from "@ant-design/icons";
import ReactECharts from "echarts-for-react";
import { mockTrendData } from "../../utils/mock";

export default function TrendAnalysis() {
  const [conclusion, setConclusion] = useState(mockTrendData.conclusion);
  const option = {
    tooltip: { trigger: "axis" },
    legend: { data: mockTrendData.indicators.map((i) => i.name) },
    xAxis: { type: "category", data: mockTrendData.months },
    yAxis: { type: "value" },
    series: mockTrendData.indicators.map((ind) => ({
      name: ind.name, type: "line", data: ind.data, smooth: true,
    })),
  };
  return (
    <div>
      <Card size="small" style={{ marginBottom: 16 }}>
        <Space>
          <Select defaultValue="p1" style={{ width: 180 }} options={[{ value: "p1", label: "1-6号粮仓新建工程" }]} />
          <Select defaultValue="monthly" style={{ width: 100 }} options={[{ value: "monthly", label: "月" }, { value: "weekly", label: "周" }]} />
          <Button type="primary" icon={<RobotOutlined />} onClick={() => message.success("趋势分析完成")}>执行分析</Button>
        </Space>
      </Card>
      <Card title="趋势分析图"><ReactECharts option={option} style={{ height: 360 }} /></Card>
      <Card title="AI 分析结论" style={{ marginTop: 16 }} size="small"
        extra={<Button icon={<ReloadOutlined />} size="small" onClick={() => { setConclusion(mockTrendData.conclusion + " (已刷新)"); message.success("结论已重新生成"); }}>重新生成</Button>}>
        <p style={{ fontSize: 13, lineHeight: 1.8, whiteSpace: "pre-wrap" }}>{conclusion}</p>
      </Card>
    </div>
  );
}