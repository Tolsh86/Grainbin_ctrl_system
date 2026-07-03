import { useState } from "react";
import { Card, Select, Button, message, Space } from "antd";
import { RobotOutlined, ReloadOutlined } from "@ant-design/icons";
// mockSummary removed in V2.0 - using inline fallback
const mockSummary = { weekly: "本周（W26）完成产值约860万元，4个在建项目中3个进展正常。", monthly: "6月整体进展顺利，完成产值约3,860万元，较5月增长12.5%。累计完成率87%。" };

export default function SmartSummary() {
  const [typ, setTyp] = useState("weekly");
  const [result, setResult] = useState("");
  const handleGenerate = () => {
    message.loading("AI 正在生成摘要...", 1.5, () => {
      setResult(typ === "weekly" ? mockSummary.weekly : typ === "monthly" ? mockSummary.monthly : "项目阶段总结：整体进展正常，完成率72%，略低于计划进度75%。");
      message.success("摘要生成完成");
    });
  };
  return (
    <div>
      <Card size="small" style={{ marginBottom: 16 }}>
        <Space>
          <Select value={typ} onChange={setTyp} style={{ width: 140 }} options={[{ value: "weekly", label: "周总结" }, { value: "monthly", label: "月总结" }, { value: "phase", label: "阶段总结" }]} />
          <Select defaultValue="p1" style={{ width: 180 }} options={[{ value: "p1", label: "1-6号粮仓工程" }]} />
          <Button type="primary" icon={<RobotOutlined />} onClick={handleGenerate}>执行生成</Button>
        </Space>
      </Card>
      {result && (
        <Card title="AI 生成结果" extra={<Space><Button icon={<ReloadOutlined />} size="small" onClick={handleGenerate}>重新生成</Button><Button type="primary" size="small" onClick={() => message.success("采纳并导出")}>采纳并导出</Button></Space>}>
          <div style={{ padding: 16, background: "#f6ffed", borderRadius: 8, fontSize: 14, lineHeight: 2, whiteSpace: "pre-wrap" }}>{result}</div>
        </Card>
      )}
      {!result && <Card><p style={{ color: "#999", textAlign: "center", padding: 40 }}>选择摘要类型并点击执行生成，AI 将基于当前数据自动生成文字摘要</p></Card>}
    </div>
  );
}