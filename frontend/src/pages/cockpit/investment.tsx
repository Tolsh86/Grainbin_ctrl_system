import { Card, Row, Col, Statistic } from "antd";
import ReactECharts from "echarts-for-react";
import { mockInvestmentData, formatYuan } from "../../utils/mock";

export default function InvestmentAnalysis() {
  const d = mockInvestmentData;

  const stats = [
    { title: "合同总额", value: `¥${formatYuan(d.contract_total)}`, color: "#1677ff" },
    { title: "累计完成", value: `¥${formatYuan(d.completed)}`, color: "#52c41a" },
    { title: "累计已付", value: `¥${formatYuan(d.paid)}`, color: "#722ed1" },
    { title: "待审核", value: `¥${formatYuan(d.pending_audit)}`, color: "#fa8c16" },
    { title: "待付金额", value: `¥${formatYuan(d.unpaid)}`, color: "#ff4d4f" },
  ];

  const investOption = {
    tooltip: { trigger: "axis" },
    legend: { data: ["月度投资(万元)", "累计投资(万元)"], top: 10 },
    grid: { top: 60, right: 30, bottom: 30, left: 60 },
    xAxis: { type: "category", data: d.months },
    yAxis: [
      { type: "value", name: "月度(万元)", axisLabel: { formatter: "{value}" } },
      { type: "value", name: "累计(万元)", axisLabel: { formatter: "{value}" } },
    ],
    series: [
      { name: "月度投资(万元)", type: "bar", data: d.monthly_investment, color: "#52c41a",
        barWidth: "50%", itemStyle: { borderRadius: [4, 4, 0, 0] } },
      { name: "累计投资(万元)", type: "line", yAxisIndex: 1, data: d.cumulative_investment,
        smooth: true, lineStyle: { color: "#1677ff", width: 2 },
        itemStyle: { color: "#1677ff" } },
    ],
  };

  const predictOption = {
    tooltip: { trigger: "axis" },
    legend: { data: ["预测月度投资(万元)"], top: 10 },
    grid: { top: 50, right: 20, bottom: 30, left: 60 },
    xAxis: { type: "category", data: ["7月", "8月", "9月"] },
    yAxis: { type: "value", name: "万元" },
    series: [{
      name: "预测月度投资(万元)", type: "bar", data: d.forecast, color: "#fa8c16",
      barWidth: "50%", itemStyle: { borderRadius: [4, 4, 0, 0] },
      label: { show: true, position: "top", formatter: "{c}万" },
    }],
  };

  return (
    <div>
      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        {stats.map((s, i) => (
          <Col xs={24} sm={12} md={Math.floor(24 / stats.length)} key={i}>
            <Card size="small" hoverable>
              <Statistic title={s.title} value={s.value} valueStyle={{ color: s.color, fontSize: 22, fontWeight: 600 }} />
            </Card>
          </Col>
        ))}
      </Row>

      {/* 图表区 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={14}>
          <Card title="投资趋势（月度 + 累计）">
            <ReactECharts option={investOption} style={{ height: 380 }} />
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card title="未来3个月投资预测" extra={<span style={{ fontSize: 12, color: "#999" }}>基于历史趋势，仅供参考</span>}>
            <ReactECharts option={predictOption} style={{ height: 380 }} />
          </Card>
        </Col>
      </Row>

      {/* 洞察卡片 */}
      <Card size="small" style={{ marginTop: 16, background: "#f0f5ff" }}>
        <Row align="middle">
          <Col flex="auto">
            <span style={{ fontSize: 13 }}>
              💡 <strong>分析：</strong>上半年累计完成投资 ¥{formatYuan(d.cumulative_investment[d.cumulative_investment.length - 1] * 10000)}，
              占合同总额的 {Math.round(d.cumulative_investment[d.cumulative_investment.length - 1] * 10000 / d.contract_total * 100)}%。
              投资节奏整体正常，月度波动在合理范围内。未来3个月预计投资强度维持在当前水平。
            </span>
          </Col>
        </Row>
      </Card>
    </div>
  );
}
