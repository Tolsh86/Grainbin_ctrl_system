import { useState, useMemo } from "react";
import {
  Card, Row, Col, Select, Button, Table, Tag, Statistic, Typography, Space, Collapse, message
} from "antd";
import { ArrowUpOutlined, ArrowDownOutlined, MinusOutlined, SwapOutlined, RobotOutlined } from "@ant-design/icons";
import ReactECharts from "echarts-for-react";
import { formatYuan } from "../../utils/mock";

const { Text } = Typography;

interface CompareRow {
  id: string;
  indicator: string;
  category: string;
  left: number;
  right: number;
  change: number;
  changeRate: number;
}

const generateMockData = (): CompareRow[] => {
  const items = ["C30混凝土浇筑", "HRB400钢筋", "土方开挖", "模板工程", "脚手架搭设", "砌体工程", "防水工程", "钢结构安装", "电气安装", "给排水"];
  const cats = ["土建工程", "土建工程", "土建工程", "土建工程", "土建工程", "土建工程", "装修工程", "安装工程", "安装工程", "安装工程"];
  return items.map((item, i) => {
    const left = Math.round(50000 + Math.random() * 800000);
    const change = Math.round((Math.random() - 0.5) * 80000);
    const right = left + change;
    return {
      id: `c${i + 1}`,
      indicator: item,
      category: cats[i],
      left,
      right,
      change,
      changeRate: left > 0 ? Math.round(change / left * 10000) / 100 : 0,
    };
  });
};

export default function DataCompare() {
  const [data] = useState<CompareRow[]>(generateMockData());

  const totalLeft = data.reduce((s, r) => s + r.left, 0);
  const totalRight = data.reduce((s, r) => s + r.right, 0);
  const totalChange = totalRight - totalLeft;

  const addedItems = data.filter(r => r.left === 0 && r.right > 0).length;
  const removedItems = data.filter(r => r.left > 0 && r.right === 0).length;
  const sameItems = data.length - addedItems - removedItems;

  const columns = [
    { title: "指标名", dataIndex: "indicator", width: 140 },
    { title: "类别", dataIndex: "category", width: 90 },
    { title: "左期值(元)", dataIndex: "left", width: 120, align: "right" as const,
      render: (v: number) => `¥${formatYuan(v)}` },
    { title: "右期值(元)", dataIndex: "right", width: 120, align: "right" as const,
      render: (v: number) => `¥${formatYuan(v)}` },
    { title: "变化量", dataIndex: "change", width: 110, align: "right" as const,
      render: (v: number) => (
        <Text style={{ color: v > 0 ? "#52c41a" : v < 0 ? "#ff4d4f" : "#999", fontWeight: 500 }}>
          {v > 0 ? "+" : ""}¥{formatYuan(Math.abs(v))}
        </Text>
      )},
    { title: "变化幅度", dataIndex: "changeRate", width: 110, align: "right" as const,
      render: (v: number) => (
        <Space size={4}>
          {v > 0 ? <ArrowUpOutlined style={{ color: "#52c41a" }} /> :
           v < 0 ? <ArrowDownOutlined style={{ color: "#ff4d4f" }} /> :
           <MinusOutlined style={{ color: "#999" }} />}
          <Text style={{ color: v > 0 ? "#52c41a" : v < 0 ? "#ff4d4f" : "#999", fontWeight: 500 }}>
            {Math.abs(v).toFixed(2)}%
          </Text>
        </Space>
      )},
  ];

  const barOption = {
    tooltip: { trigger: "axis" },
    legend: { data: ["左期（本期）", "右期（对比期）"] },
    xAxis: { type: "category", data: data.map(d => d.indicator.slice(0, 8)), axisLabel: { rotate: 30, fontSize: 11 } },
    yAxis: { type: "value", name: "金额(元)", axisLabel: { formatter: (v: number) => `${(v / 10000).toFixed(0)}万` } },
    series: [
      { name: "左期（本期）", type: "bar", data: data.map(d => d.left / 100), color: "#1677ff" },
      { name: "右期（对比期）", type: "bar", data: data.map(d => d.right / 100), color: "#52c41a" },
    ],
  };

  const lineOption = {
    tooltip: { trigger: "axis" },
    legend: { data: ["变化幅度(%)"] },
    xAxis: { type: "category", data: data.map(d => d.indicator.slice(0, 8)), axisLabel: { rotate: 30, fontSize: 11 } },
    yAxis: { type: "value", name: "%" },
    series: [
      { name: "变化幅度(%)", type: "line", data: data.map(d => d.changeRate), smooth: true,
        markLine: { data: [{ type: "average", name: "均值" }], lineStyle: { color: "#fa8c16" } } },
    ],
  };

  return (
    <div>
      {/* 对比选择器 */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={[12, 8]} align="middle">
          <Col><Text strong>对比配置：</Text></Col>
          <Col xs={24} sm={6} md={4}>
            <Select style={{ width: "100%" }} defaultValue="p1"
              options={[{ value: "p1", label: "1-6号粮仓新建工程" }, { value: "p2", label: "7-12号粮仓改造" }]} />
          </Col>
          <Col xs={24} sm={6} md={3}>
            <Select style={{ width: "100%" }} defaultValue="weekly"
              options={[{ value: "weekly", label: "周报" }, { value: "monthly", label: "月报" }, { value: "payment", label: "进度款" }]} />
          </Col>
          <Col xs={12} sm={6} md={3}>
            <Select style={{ width: "100%" }} defaultValue="W25"
              options={[{ value: "W25", label: "第25周 (左期)" }, { value: "W24", label: "第24周" }]} />
          </Col>
          <Col xs={12} sm={6} md={3}>
            <Select style={{ width: "100%" }} defaultValue="W26"
              options={[{ value: "W26", label: "第26周 (右期)" }, { value: "W25", label: "第25周" }]} />
          </Col>
          <Col><Button type="primary" icon={<SwapOutlined />} onClick={() => message.success("对比完成")}>开始对比</Button></Col>
        </Row>
      </Card>

      {/* 统计概览 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={12} sm={6}>
          <Card size="small"><Statistic title="左期总金额" value={`¥${formatYuan(totalLeft)}`} valueStyle={{ fontSize: 16 }} /></Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small"><Statistic title="右期总金额" value={`¥${formatYuan(totalRight)}`} valueStyle={{ fontSize: 16 }} /></Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic title="变化量" value={`¥${formatYuan(Math.abs(totalChange))}`}
              valueStyle={{ color: totalChange > 0 ? "#52c41a" : totalChange < 0 ? "#ff4d4f" : "#999", fontSize: 16 }}
              prefix={totalChange > 0 ? <ArrowUpOutlined /> : totalChange < 0 ? <ArrowDownOutlined /> : <MinusOutlined />} />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic title="变化幅度" value={totalLeft > 0 ? Math.abs(Math.round(totalChange / totalLeft * 10000) / 100) : 0}
              suffix="%" valueStyle={{ color: totalChange > 0 ? "#52c41a" : totalChange < 0 ? "#ff4d4f" : "#999", fontSize: 16 }} />
          </Card>
        </Col>
      </Row>

      {/* 对比表格 */}
      <Card title="数值对比表">
        <Table columns={columns} dataSource={data} size="small" rowKey="id"
          pagination={{ pageSize: 20, showTotal: (t) => `共 ${t} 项` }}
          scroll={{ x: 700 }} />
      </Card>

      {/* 展开区 */}
      <Collapse style={{ marginTop: 16 }} items={[
        {
          key: "charts", label: "图表可视化 ▼",
          children: (
            <Row gutter={16}>
              <Col xs={24} lg={12}>
                <Card size="small" title="分项金额对比">
                  <ReactECharts option={barOption} style={{ height: 300 }} />
                </Card>
              </Col>
              <Col xs={24} lg={12}>
                <Card size="small" title="变化幅度趋势">
                  <ReactECharts option={lineOption} style={{ height: 300 }} />
                </Card>
              </Col>
            </Row>
          ),
        },
        {
          key: "diff", label: "字段变更追踪 ▼",
          children: (
            <Row gutter={16}>
              <Col xs={24} sm={8}>
                <Card size="small" title="新增项" style={{ background: "#f6ffed" }}>
                  <Statistic title="右期新增" value={addedItems} suffix="项" valueStyle={{ color: "#52c41a" }} />
                </Card>
              </Col>
              <Col xs={24} sm={8}>
                <Card size="small" title="消失项" style={{ background: "#fff2f0" }}>
                  <Statistic title="左期消失" value={removedItems} suffix="项" valueStyle={{ color: "#ff4d4f" }} />
                </Card>
              </Col>
              <Col xs={24} sm={8}>
                <Card size="small" title="共有项">
                  <Statistic title="两期共有" value={sameItems} suffix="项" valueStyle={{ color: "#1677ff" }} />
                </Card>
              </Col>
            </Row>
          ),
        },
        {
          key: "ai", label: "AI 差异洞察 ▼",
          children: (
            <Card size="small" style={{ background: "#f0f5ff" }}>
              <Space>
                <RobotOutlined style={{ color: "#1677ff", fontSize: 18 }} />
                <span style={{ fontSize: 13 }}>
                  {totalChange > 0
                    ? `右期总金额较左期增长 ¥${formatYuan(Math.abs(totalChange))}，增幅 ${(totalChange / totalLeft * 100).toFixed(2)}%。AI 自动分析功能将在后续版本开放。`
                    : totalChange < 0
                    ? `右期总金额较左期减少 ¥${formatYuan(Math.abs(totalChange))}，降幅 ${(Math.abs(totalChange) / totalLeft * 100).toFixed(2)}%。AI 自动分析功能将在后续版本开放。`
                    : "两期数据基本持平。AI 自动分析功能将在后续版本开放。"}
                </span>
              </Space>
            </Card>
          ),
        },
      ]} />
    </div>
  );
}
