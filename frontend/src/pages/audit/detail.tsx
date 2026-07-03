import { useState, useMemo } from "react";
import { Card, Row, Col, Descriptions, Tag, Table, Button, Space, Input, InputNumber, message, Collapse, Alert, Statistic } from "antd";
import { RobotOutlined, CheckCircleOutlined, CloseCircleOutlined, ExportOutlined } from "@ant-design/icons";
import { useNavigate, useParams } from "react-router-dom";
import ReactECharts from "echarts-for-react";
import { mockAudits } from "../../utils/mock";

const formatYuan = (fen: number) => (fen / 100).toLocaleString();

export default function AuditDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const audit = mockAudits.find((a) => a.id === id);
  const [aiRan, setAiRan] = useState(false);
  const [adopted, setAdopted] = useState<Record<string, boolean>>({});
  const [opinion, setOpinion] = useState("");

  if (!audit) return <Card><p>审核不存在</p><Button onClick={() => navigate("/audits")}>返回</Button></Card>;

  const handleRunAI = () => {
    message.loading("AI 审核引擎运行中：重复计量/合同比对/付款比例/单价异常...", 2.5, () => { setAiRan(true); message.success("AI 审核完成，发现 2 项异常"); });
  };

  const handleAdopt = (findingId: string) => { setAdopted((p) => ({ ...p, [findingId]: true })); message.success("已采纳建议"); };
  const handleReject = (findingId: string) => { setAdopted((p) => ({ ...p, [findingId]: false })); message.info("已拒绝建议"); };

  const itemCols = [
    { title: "分项", dataIndex: "name", key: "n", width: 120, fixed: "left" as const },
    { title: "单位", dataIndex: "unit", key: "u", width: 60 },
    { title: "申报数量", dataIndex: "apply_qty", key: "aq", width: 90, align: "right" as const },
    { title: "申报单价", dataIndex: "apply_price", key: "ap", width: 90, align: "right" as const, render: (v: number) => v.toLocaleString() },
    { title: "申报金额", dataIndex: "apply_amount", key: "aa", width: 110, align: "right" as const, render: (v: number) => `¥${v.toLocaleString()}` },
    { title: "审核数量", dataIndex: "audit_qty", key: "dq", width: 90, align: "right" as const, render: (v: number, r: typeof audit.items[0]) => <InputNumber size="small" defaultValue={v} style={{ width: "100%" }} /> },
    { title: "审核金额", dataIndex: "audit_amount", key: "da", width: 110, align: "right" as const, render: (v: number) => <span style={{ color: "#1677ff" }}>¥{v.toLocaleString()}</span> },
    { title: "核减", dataIndex: "deduct", key: "dd", width: 90, align: "right" as const, render: (v: number) => v > 0 ? <span style={{ color: "#ff4d4f" }}>-¥{v.toLocaleString()}</span> : <span style={{ color: "#52c41a" }}>0</span> },
    { title: "异常", dataIndex: "anomaly", key: "an", width: 80, render: (v: string | null) => v ? <Tag color="red">{v}</Tag> : <Tag color="green">正常</Tag> },
  ];

  const historyCompareOption = {
    tooltip: { trigger: "axis" },
    xAxis: { type: "category", data: ["第8期","第9期","第10期","第11期","第12期"] },
    legend: { data: ["核减率(%)"] },
    yAxis: { type: "value", name: "%" },
    series: [{ name: "核减率(%)", type: "line", data: [3.8, 3.6, 4.7, 4.0, 4.8], smooth: true }],
  };

  return (
    <div>
      {/* 页头 */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Space size="middle">
              <Button type="text" onClick={() => navigate("/audits")}>← 返回</Button>
              <span style={{ fontSize: 16, fontWeight: 600 }}>{audit.period} 进度款审核</span>
              <Tag color="orange">待审核</Tag>
              <span style={{ fontSize: 13 }}>合同: {audit.contract_name} <Tag>{audit.contract_version}</Tag></span>
            </Space>
          </Col>
          <Col>
            <Space>
              {!aiRan && <Button icon={<RobotOutlined />} type="primary" ghost onClick={handleRunAI}>一键AI审核</Button>}
              <Button icon={<ExportOutlined />} onClick={() => message.info("导出审核报告")}>导出报告</Button>
              <Button type="primary" icon={<CheckCircleOutlined />} onClick={() => message.success("提交终审")}>提交终审</Button>
            </Space>
          </Col>
        </Row>
        <Row gutter={16} style={{ marginTop: 12 }}>
          <Col span={6}><Statistic title="申报金额" value={`¥${formatYuan(audit.apply_amount)}`} /></Col>
          <Col span={6}><Statistic title="AI 建议" value={aiRan ? `¥${formatYuan(audit.ai_suggest_amount || 0)}` : "—"} valueStyle={{ color: "#1677ff" }} /></Col>
          <Col span={6}><Statistic title="终审金额" value={audit.final_amount ? `¥${formatYuan(audit.final_amount)}` : "—"} /></Col>
          <Col span={6}><Statistic title="核减金额" value={audit.deduct_amount ? `¥${formatYuan(audit.deduct_amount)}` : "—"} valueStyle={{ color: "#ff4d4f" }} /></Col>
        </Row>
      </Card>

      <Row gutter={16}>
        {/* 左侧：工程量清单 */}
        <Col span={16}>
          <Card title="工程量清单明细" size="small">
            <Table columns={itemCols} dataSource={audit.items} size="small" rowKey="id" scroll={{ x: 1000 }} pagination={false} />
          </Card>
        </Col>
        {/* 右侧：AI 审核结果 */}
        <Col span={8}>
          <Card title={<><RobotOutlined /> AI 审核结果</>} size="small">
            {!aiRan ? (
              <div style={{ textAlign: "center", padding: 32, color: "#999" }}>
                <RobotOutlined style={{ fontSize: 32, marginBottom: 8 }} />
                <p>点击"一键AI审核"启动 AI 分析</p>
                <p style={{ fontSize: 11 }}>将自动检测：重复计量 / 合同单价比对 / 累计付款比例 / 单价异常</p>
              </div>
            ) : (
              <div>
                <Space style={{ marginBottom: 12 }}>
                  <Button size="small" onClick={() => { audit.ai_findings?.forEach((f) => handleAdopt(f.item)); message.success("全部采纳"); }}>全部采纳</Button>
                  <Button size="small" onClick={() => message.info("全部拒绝")}>全部拒绝</Button>
                </Space>
                {(audit.ai_findings || []).map((f, i) => (
                  <Alert
                    key={i}
                    type="error"
                    showIcon
                    message={<strong>{f.type}：{f.item}</strong>}
                    description={<div><p>建议核减：¥{formatYuan(f.suggest_deduct)}</p><p style={{ fontSize: 12 }}>{f.reason}</p></div>}
                    style={{ marginBottom: 8 }}
                    action={
                      adopted[`${i}`] === undefined ? (
                        <Space direction="vertical" size={4}>
                          <Button size="small" type="primary" onClick={() => handleAdopt(`${i}`)}>采纳</Button>
                          <Button size="small" onClick={() => handleReject(`${i}`)}>拒绝</Button>
                        </Space>
                      ) : adopted[`${i}`] ? <Tag color="green">已采纳</Tag> : <Tag color="default">已拒绝</Tag>
                    }
                  />
                ))}
                {audit.ai_findings?.length === 0 && <p style={{ color: "#52c41a" }}>✅ 未发现异常项</p>}
              </div>
            )}
          </Card>
        </Col>
      </Row>

      {/* 底部审核意见 */}
      <Card title="审核意见" size="small" style={{ marginTop: 16 }}>
        <Input.TextArea rows={3} placeholder="审核意见（提交终审时必填）" value={opinion} onChange={(e) => setOpinion(e.target.value)} />
        <div style={{ marginTop: 12, textAlign: "right" }}>
          <Space>
            <Button onClick={() => message.info("保存草稿")}>保存草稿</Button>
            <Button type="primary" onClick={() => message.success("提交终审成功")}>提交终审</Button>
            <Button danger onClick={() => message.warning("驳回")}>驳回</Button>
          </Space>
        </div>
      </Card>

      {/* 历期对比 */}
      <Collapse style={{ marginTop: 16 }} items={[{
        key: "history", label: "历期对比 ▼",
        children: <Row gutter={16}>
          <Col span={12}>
            <Table size="small" pagination={false} dataSource={[{ period: "第10期", apply: 520000000, final: 498000000, deduct: 22000000, rate: 4.2 }, { period: "第11期", apply: 620000000, final: 595000000, deduct: 25000000, rate: 4.0 }, { period: "第12期", apply: 580000000, final: null, deduct: null, rate: null }]} columns={[{ title: "期次", dataIndex: "period" }, { title: "申报(万)", dataIndex: "apply", render: (v: number) => formatYuan(v) }, { title: "终审(万)", dataIndex: "final", render: (v: number | null) => v ? formatYuan(v) : "—" }, { title: "核减(万)", dataIndex: "deduct", render: (v: number | null) => v ? formatYuan(v) : "—" }, { title: "核减率", dataIndex: "rate", render: (v: number | null) => v ? `${v}%` : "—" }]} />
          </Col>
          <Col span={12}>
            <Card size="small" title="核减率趋势"><ReactECharts option={historyCompareOption} style={{ height: 200 }} /></Card>
          </Col>
        </Row>
      }]} />
    </div>
  );
}