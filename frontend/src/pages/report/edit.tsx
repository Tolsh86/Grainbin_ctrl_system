import { useState } from "react";
import { Card, Row, Col, Form, Input, Button, Space, Tag, Select, message, Descriptions, Collapse, Modal, Checkbox, Radio } from "antd";
import { RobotOutlined, EyeOutlined, ExportOutlined, SaveOutlined, SendOutlined } from "@ant-design/icons";
import { useNavigate, useParams } from "react-router-dom";
import { mockReports } from "../../utils/mock";

const { TextArea } = Input;

export default function ReportEdit() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const report = mockReports.find((r) => r.id === id);
  const [aiFilled, setAiFilled] = useState(false);
  const [exportModal, setExportModal] = useState(false);

  if (!report) return <Card><p>报告不存在</p><Button onClick={() => navigate("/reports")}>返回列表</Button></Card>;

  const statusMap: Record<string, { color: string; text: string }> = {
    draft: { color: "default", text: "草稿" }, pending_review: { color: "orange", text: "待审核" },
    confirmed: { color: "blue", text: "已审核" }, published: { color: "green", text: "已发布" },
  };

  const handleAIFill = () => {
    message.loading("AI 正在生成文字描述...", 2, () => { setAiFilled(true); message.success("AI 建议已生成，请审阅后确认"); });
  };

  // 模拟动态表单字段
  const mockFields = [
    { key: "progress_desc", label: "本周施工进度描述", type: "text", required: true, formula: null },
    { key: "completed_value", label: "本周完成产值(元)", type: "number", required: true, formula: "=SUM(本期工程量*单价)" },
    { key: "cumulative_value", label: "累计完成产值(元)", type: "formula", required: false, formula: "上期累计 + 本期完成" },
    { key: "quality_status", label: "质量检查情况", type: "text", required: false, formula: null },
    { key: "next_week_plan", label: "下周工作计划", type: "text", required: false, formula: null },
    { key: "issues", label: "存在问题及建议", type: "text", required: false, formula: null },
  ];

  return (
    <div>
      {/* 页头 */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Space size="middle">
              <Button type="text" onClick={() => navigate("/reports")}>← 返回</Button>
              <span style={{ fontSize: 16, fontWeight: 600 }}>{report.title}</span>
              <Tag>{report.project_name}</Tag>
              <Tag>周期: {report.period}</Tag>
              <Tag>{report.template_name}</Tag>
              <Tag color={statusMap[report.status]?.color}>{statusMap[report.status]?.text}</Tag>
            </Space>
          </Col>
          <Col>
            <Space>
              <Button icon={<SaveOutlined />} onClick={() => message.success("草稿已保存")}>保存草稿</Button>
              <Button icon={<SendOutlined />} onClick={() => message.success("已提交审核")}>提交审核</Button>
              <Button icon={<RobotOutlined />} type="primary" ghost onClick={handleAIFill}>AI 智能填写</Button>
              <Button icon={<EyeOutlined />} onClick={() => message.info("预览报告")}>预览</Button>
              <Button icon={<ExportOutlined />} onClick={() => setExportModal(true)}>导出</Button>
            </Space>
          </Col>
        </Row>
      </Card>

      <Row gutter={16}>
        <Col span={18}>
          <Card title="报告内容编辑">
            {aiFilled && (
              <div style={{ marginBottom: 16, padding: 12, background: "#f0f5ff", borderRadius: 6, border: "1px solid #adc6ff" }}>
                <span style={{ color: "#1677ff", fontWeight: 500 }}>💡 AI 建议已生成：</span> 进度描述、下周计划等文字字段已填入 AI 生成内容。请逐字段审核确认或编辑修改后保存。
              </div>
            )}
            <Form layout="vertical">
              {mockFields.map((f) => (
                <div key={f.key} style={{ marginBottom: 16 }}>
                  <div style={{ fontWeight: 500, marginBottom: 4 }}>
                    {f.label} {f.required && <span style={{ color: "#ff4d4f" }}>*</span>}
                    {f.type === "formula" && <Tag color="blue" style={{ marginLeft: 8 }}>公式</Tag>}
                  </div>
                  {f.type === "text" ? (
                    <TextArea rows={3} defaultValue={aiFilled ? `[AI生成] ${f.label} - 本周施工正常，完成计划产值的92%。主要工作：C30混凝土浇筑450m³，HRB400钢筋绑扎120t，模板安装2800m²...` : ""} placeholder={`请输入${f.label}`} />
                  ) : (
                    <Input defaultValue={f.type === "number" ? "580000" : f.type === "formula" ? "（自动计算：上期累计 + 本期完成）" : ""} disabled={f.type === "formula"} />
                  )}
                </div>
              ))}
            </Form>
          </Card>
        </Col>
        <Col span={6}>
          <Card title="本期数据预览" size="small" style={{ marginBottom: 16 }}>
            <Descriptions column={1} size="small">
              <Descriptions.Item label="本周产值">¥580,000</Descriptions.Item>
              <Descriptions.Item label="累计产值">¥5,500,000</Descriptions.Item>
              <Descriptions.Item label="主要分项">C30混凝土 / 钢筋</Descriptions.Item>
            </Descriptions>
            <Button type="link" size="small" onClick={() => message.success("已填入表单")}>填入表单</Button>
          </Card>
          <Card title="上期报告对比" size="small">
            <Descriptions column={1} size="small">
              <Descriptions.Item label="上期产值">¥620,000</Descriptions.Item>
              <Descriptions.Item label="上期进度">正常</Descriptions.Item>
            </Descriptions>
          </Card>
        </Col>
      </Row>

      {/* 导出弹窗 */}
      <Modal title="导出报告" open={exportModal} onCancel={() => setExportModal(false)} onOk={() => { message.success("导出任务已创建，请稍候下载"); setExportModal(false); }} okText="开始导出">
        <Form layout="vertical">
          <Form.Item label="导出格式"><Radio.Group defaultValue="word"><Radio value="word">Word</Radio><Radio value="ppt">PPT</Radio></Radio.Group></Form.Item>
          <Form.Item label="包含图表"><Checkbox defaultChecked>是</Checkbox></Form.Item>
          <Form.Item label="包含原始数据附件"><Checkbox>是</Checkbox></Form.Item>
        </Form>
      </Modal>
    </div>
  );
}