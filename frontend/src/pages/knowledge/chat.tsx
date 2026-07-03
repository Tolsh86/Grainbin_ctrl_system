import { useState } from "react";
import { Card, Row, Col, Input, Button, Select, Tag, message, Space } from "antd";
import { SendOutlined, RobotOutlined, UserOutlined, PlusOutlined, StopOutlined } from "@ant-design/icons";
import { mockAISessions } from "../../utils/mock";

interface ChatMessage { role: "user" | "assistant"; content: string; time: string; citations?: Array<{ title: string; page: string }>; }

const mockMessages: ChatMessage[] = [
  { role: "user", content: "3号粮仓最近温度正常吗？", time: "14:31" },
  { role: "assistant", content: "根据最新数据，3号粮仓当前温度26.5℃，已超过25℃警戒线，处于预警状态。建议立即启动加强通风模式并加密巡检。", time: "14:31", citations: [{ title: "粮仓温湿度监控系统", page: "第15页" }] },
  { role: "user", content: "需要采取什么措施？", time: "14:32" },
  { role: "assistant", content: "建议：1. 立即启动加强通风模式；2. 30分钟内派巡检人员现场确认；3. 如确认偏高考虑启动倒仓作业；4. 加密巡检至每2小时一次。", time: "14:32", citations: [{ title: "粮仓应急预案", page: "第8页" }] },
];

export default function AIChat() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>(mockMessages);
  const [streaming, setStreaming] = useState(false);
  const [activeSession, setActiveSession] = useState("cs1");

  const handleSend = () => {
    if (!input.trim() || streaming) return;
    const userMsg: ChatMessage = { role: "user", content: input, time: new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" }) };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setStreaming(true);
    setTimeout(() => {
      setMessages((prev) => [...prev, { role: "assistant", content: `针对您的问题已生成回答。此回答来自知识库中相关文档内容。`, time: new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" }), citations: [{ title: "知识库文档", page: "相关章节" }] }]);
      setStreaming(false);
    }, 2000);
  };

  return (
    <Row gutter={16} style={{ minHeight: 500 }}>
      <Col span={5}>
        <Card size="small" title="会话列表" extra={<Button type="text" icon={<PlusOutlined />} onClick={() => message.info("新建会话")} />}>
          {mockAISessions.map((s) => (
            <div key={s.id} onClick={() => setActiveSession(s.id)} style={{ padding: "8px 0", borderBottom: "1px solid #f0f0f0", cursor: "pointer", background: activeSession === s.id ? "#e6f4ff" : "transparent", borderRadius: 4 }}>
              <div style={{ fontSize: 13, fontWeight: activeSession === s.id ? 600 : 400 }}>{s.title}</div>
              <div style={{ fontSize: 11, color: "#999" }}>{s.created_at}</div>
            </div>
          ))}
        </Card>
      </Col>
      <Col span={19}>
        <Card size="small" title={<><RobotOutlined /> AI 问答</>}
          extra={<Space><Select defaultValue="deepseek" size="small" style={{ width: 120 }} options={[{ value: "deepseek", label: "DeepSeek" }, { value: "qwen", label: "Qwen2.5" }]} /><Select defaultValue="p1" size="small" style={{ width: 160 }} options={[{ value: "p1", label: "1-6号粮仓工程" }, { value: "all", label: "全部知识库" }]} /></Space>}
        >
          <div style={{ maxHeight: 380, overflow: "auto", padding: 8 }}>
            {messages.map((m, i) => (
              <div key={i} style={{ display: "flex", marginBottom: 16, justifyContent: m.role === "user" ? "flex-end" : "flex-start" }}>
                <div style={{ maxWidth: "75%", padding: "12px 16px", borderRadius: 12, background: m.role === "user" ? "#1677ff" : "#f5f5f5", color: m.role === "user" ? "#fff" : "#333" }}>
                  <div style={{ fontSize: 11, marginBottom: 4, opacity: 0.7 }}>{m.role === "user" ? <UserOutlined /> : <RobotOutlined />} {m.time}</div>
                  <div style={{ whiteSpace: "pre-wrap", fontSize: 13 }}>{m.content}</div>
                  {m.citations?.map((c, j) => (
                    <div key={j} style={{ marginTop: 6, fontSize: 11, color: "#1677ff", cursor: "pointer" }}>📎 {c.title} — {c.page}</div>
                  ))}
                </div>
              </div>
            ))}
            {streaming && <div style={{ color: "#999", fontSize: 12, padding: 8 }}>AI 正在生成中 ▍</div>}
          </div>
          <div style={{ display: "flex", gap: 8, marginTop: 12, borderTop: "1px solid #f0f0f0", paddingTop: 12 }}>
            <Input.TextArea value={input} onChange={(e) => setInput(e.target.value)} onPressEnter={(e) => { if (!e.shiftKey) { e.preventDefault(); handleSend(); } }} placeholder="输入问题... (Shift+Enter 换行)" autoSize={{ minRows: 1, maxRows: 4 }} style={{ flex: 1 }} />
            {streaming ? <Button icon={<StopOutlined />} danger onClick={() => setStreaming(false)}>停止</Button> : <Button type="primary" icon={<SendOutlined />} onClick={handleSend}>发送</Button>}
          </div>
        </Card>
      </Col>
    </Row>
  );
}