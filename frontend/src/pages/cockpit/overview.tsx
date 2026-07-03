import { Card, Row, Col, Statistic, Select, Space } from "antd";
import ReactECharts from "echarts-for-react";
import { mockCockpitOverview } from "../../utils/mock";

export default function CockpitOverview() {
  const d = mockCockpitOverview;

  const stats = [
    { title: "在建项目", value: d.active_projects, color: "#1677ff", suffix: "个" },
    { title: "累计投资总额", value: `¥${(d.total_investment / 1000000).toFixed(0)}万`, color: "#52c41a" },
    { title: "累计已支付", value: `¥${(d.total_paid / 1000000).toFixed(0)}万`, color: "#722ed1" },
    { title: "平均完成率", value: d.avg_progress, color: "#1677ff", suffix: "%" },
    { title: "本月新增产值", value: `¥${(d.monthly_output / 1000000).toFixed(0)}万`, color: "#fa8c16" },
    { title: "待审核笔数", value: d.pending_audits, color: "#ff4d4f", suffix: "笔" },
    { title: "风险项目数", value: d.risk_count, color: "#ff4d4f", suffix: "个" },
    { title: "资料完整度", value: d.data_completeness, color: "#52c41a", suffix: "%" },
  ];

  const pieOption = {
    tooltip: { trigger: "item", formatter: "{b}: {c} 个 ({d}%)" },
    legend: { orient: "vertical", left: "left", top: "middle" },
    series: [{
      name: "项目状态", type: "pie", radius: ["50%", "75%"],
      data: d.status_pie.map(s => ({ value: s.value, name: s.name, itemStyle: { color: s.color } })),
      emphasis: { label: { fontSize: 16, fontWeight: "bold" } },
    }],
  };

  const gaugeOption = {
    series: [{
      type: "gauge", min: 0, max: 100, center: ["50%", "60%"], radius: "90%",
      startAngle: 210, endAngle: -30,
      data: [{ value: d.avg_progress, name: "完成率" }],
      axisLine: { lineStyle: { color: [[d.avg_progress / 100, "#52c41a"], [1, "#e0e0e0"]], width: 12 } },
      pointer: { length: "65%", width: 5 },
      detail: { fontSize: 16, offsetCenter: [0, "75%"], formatter: "{value}%" },
    }],
  };

  return (
    <div>
      {/* 顶部筛选 */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Space>
          <Select mode="multiple" defaultValue={["all"]} style={{ width: 200 }}
            placeholder="选择项目组"
            options={[{ value: "all", label: "全部项目" }, { value: "p1", label: "1-6号粮仓" }, { value: "p2", label: "7-12号改造" }, { value: "p3", label: "智能通风" }]} />
          <Select defaultValue="this_month" style={{ width: 140 }}
            options={[{ value: "this_month", label: "本月" }, { value: "this_quarter", label: "本季度" }, { value: "this_year", label: "本年度" }]} />
        </Space>
      </Card>

      {/* 关键指标卡片 */}
      <Row gutter={[16, 16]}>
        {stats.map((s, i) => (
          <Col xs={24} sm={12} md={6} key={i}>
            <Card size="small" hoverable>
              <Statistic title={s.title} value={s.value} suffix={s.suffix}
                valueStyle={{ color: s.color, fontSize: 24, fontWeight: 600 }} />
            </Card>
          </Col>
        ))}
      </Row>

      {/* 图表区 */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <Card title="平均完成率">
            <ReactECharts option={gaugeOption} style={{ height: 300 }} />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="项目状态分布">
            <ReactECharts option={pieOption} style={{ height: 300 }} />
          </Card>
        </Col>
      </Row>

      {/* 项目分布地图占位 */}
      <Card title="项目分布地图（全国）" style={{ marginTop: 16 }}>
        <div style={{ padding: 40, textAlign: "center" }}>
          <Row gutter={16} justify="center">
            {d.project_distribution.map((p, i) => (
              <Col key={i} style={{ marginBottom: 16 }}>
                <Card size="small" style={{ width: 200, textAlign: "center" }}>
                  <Statistic title={p.province} value={p.count} suffix="个项目" />
                </Card>
              </Col>
            ))}
          </Row>
          <p style={{ color: "#999", fontSize: 12, marginTop: 16 }}>
            💡 ECharts 中国地图组件需加载 GeoJSON 数据，当前展示项目分布卡片。点击省份可下钻到项目列表。
          </p>
        </div>
      </Card>
    </div>
  );
}
