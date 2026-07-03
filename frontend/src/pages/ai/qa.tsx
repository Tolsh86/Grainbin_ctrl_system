import { useState } from "react";
import { Card, Input, Button, message, List, Tag } from "antd";
import { RobotOutlined, ThunderboltOutlined } from "@ant-design/icons";

const { TextArea } = Input;

const mockHistory = [
  { question: "本月投资为什么下降？", answer: "4月因雨季影响室外作业，产值下降10.5%。5-6月已回升至正常水平。", time: "2026-06-25" },
  { question: "第三方检测费用占比？", answer: "第三方检测费用约占合同总额1.5%，符合行业标准。", time: "2026-06-20" },
];

export default function AIQA() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");

  const handleAsk = () => {
    if (!question.trim()) return;
    message.loading("AI 正在分析...", 1.5, () => {
      setAnswer("分析结果：相关指标在正常范围内波动，短期趋势稳定。建议持续监控，按计划执行日常管理。\n\n（引用源：数据中心 t_data_rows / 知识库文档）");
      message.success("分析完成");
    });
  };

  return (
    <div>
      <Card size="small" style={{ marginBottom: 16 }}>
        <TextArea rows={2} value={question} onChange={e => setQuestion(e.target.value)} placeholder="如：本月投资为什么下降？第三方检测费用占比多少？" />
        <div style={{ marginTop: 8, textAlign: "right" }}><Button type="primary" icon={<ThunderboltOutlined />} onClick={handleAsk}>AI 分析</Button></div>
      </Card>
      {answer && (
        <Card title={<><RobotOutlined style={{ marginRight: 8 }} />AI 回答</>} style={{ marginBottom: 16 }} size="small">
          <div style={{ whiteSpace: "pre-wrap", fontSize: 13, lineHeight: 2, padding: 12, background: "#f6ffed", borderRadius: 6 }}>
            {answer}
            <div style={{ marginTop: 8, fontSize: 11, color: "#999" }}>📎 引用源：数据中心 · 知识库文档</div>
          </div>
        </Card>
      )}
      <Card title="历史提问" size="small">
        <List size="small" dataSource={mockHistory} renderItem={item => (
          <List.Item actions={[<a key="reuse" onClick={() => setQuestion(item.question)}>复用</a>]}>
            <List.Item.Meta title={<span style={{ fontSize: 13 }}>{item.question}</span>}
              description={<><Tag>{item.time}</Tag><span style={{ fontSize: 11, color: "#999" }}>{item.answer}</span></>} />
          </List.Item>
        )} />
      </Card>
    </div>
  );
}