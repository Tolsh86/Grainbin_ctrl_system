import { useState } from "react";
import { Card, Form, InputNumber, Select, Button, Table, Tag, message, Tabs, Row, Col, Typography, Space, Switch, Popconfirm } from "antd";
import { mockReminderSettings, mockSecondaryContracts } from "../../utils/mock";

const { Text } = Typography;

export default function ReminderSettings() {
  const [defaultDays, setDefaultDays] = useState(mockReminderSettings.default_days);
  const [channels, setChannels] = useState<string[]>(mockReminderSettings.channels);
  const [remindTime, setRemindTime] = useState(mockReminderSettings.remind_time);
  const [overrides, setOverrides] = useState(mockReminderSettings.contract_overrides);

  const handleSaveGlobal = () => {
    message.success("全局提醒设置已保存");
  };

  const handleResend = (id: string) => {
    message.success(`提醒已重新发送`);
  };

  return (
    <div>
      {/* 全局设置 */}
      <Card title="全局提醒设置" size="small" style={{ marginBottom: 16 }}>
        <Row gutter={[16, 12]}>
          <Col xs={24} sm={8}>
            <div style={{ marginBottom: 4, fontWeight: 500 }}>提前提醒天数</div>
            <InputNumber value={defaultDays} onChange={(v) => setDefaultDays(v || 7)}
              min={1} max={90} style={{ width: "100%" }} addonAfter="天" />
            <Text type="secondary" style={{ fontSize: 11 }}>节点计划日期前N天开始提醒</Text>
          </Col>
          <Col xs={24} sm={8}>
            <div style={{ marginBottom: 4, fontWeight: 500 }}>提醒时间</div>
            <Select value={remindTime} onChange={setRemindTime} style={{ width: "100%" }}
              options={[
                { value: "08:00", label: "每天 08:00" },
                { value: "09:00", label: "每天 09:00" },
                { value: "10:00", label: "每天 10:00" },
                { value: "18:00", label: "每天 18:00" },
              ]} />
          </Col>
          <Col xs={24} sm={8}>
            <div style={{ marginBottom: 4, fontWeight: 500 }}>通知渠道</div>
            <Select mode="multiple" value={channels} onChange={setChannels} style={{ width: "100%" }}
              options={[
                { value: "站内信", label: "🔔 站内信（必选）" },
                { value: "邮件", label: "📧 邮件" },
                { value: "短信", label: "📱 短信" },
              ]} />
          </Col>
        </Row>
        <div style={{ marginTop: 16, textAlign: "right", borderTop: "1px solid #f0f0f0", paddingTop: 12 }}>
          <Space>
            <Text type="secondary" style={{ fontSize: 12 }}>
              {channels.includes("短信") ? "短信渠道需额外配置服务商" : ""}
            </Text>
            <Button type="primary" onClick={handleSaveGlobal}>保存全局设置</Button>
          </Space>
        </div>
      </Card>

      {/* Tabs */}
      <Tabs items={[
        {
          key: "override",
          label: "单合同覆盖规则",
          children: (
            <Card>
              <Text type="secondary" style={{ fontSize: 13, display: "block", marginBottom: 12 }}>
                可针对特定合同设置不同的提醒规则（提前天数、通知渠道）。未设置的合同使用全局规则（提前 {defaultDays} 天，渠道：{channels.join("、")}）。
              </Text>
              {overrides.length > 0 ? (
                <Table
                  size="small" rowKey="contract_id" pagination={false}
                  dataSource={overrides}
                  columns={[
                    { title: "合同", dataIndex: "contract_name", width: 160 },
                    { title: "提前天数", dataIndex: "days", width: 100, render: (v: number) => `${v} 天` },
                    { title: "渠道", dataIndex: "channels", width: 200, render: (v: string[]) => v.map(c => <Tag key={c}>{c}</Tag>) },
                    {
                      title: "操作", width: 100,
                      render: (_: unknown, r: typeof overrides[0]) => (
                        <Space size="small">
                          <a onClick={() => message.info("编辑覆盖规则")}>编辑</a>
                          <Popconfirm title="移除覆盖规则？" onConfirm={() => {
                            setOverrides(prev => prev.filter(o => o.contract_id !== r.contract_id));
                            message.success("已移除覆盖规则");
                          }}>
                            <a style={{ color: "#ff4d4f" }}>移除</a>
                          </Popconfirm>
                        </Space>
                      ),
                    },
                  ]}
                />
              ) : null}
              <Button size="small" style={{ marginTop: 12 }} onClick={() => message.info("选择合同并设置覆盖规则")}>
                新增覆盖规则
              </Button>
            </Card>
          ),
        },
        {
          key: "history",
          label: "提醒历史",
          children: (
            <Table
              size="small" rowKey="id"
              dataSource={mockReminderSettings.history}
              columns={[
                { title: "提醒时间", dataIndex: "time", width: 150 },
                { title: "节点", dataIndex: "node_name", width: 120 },
                { title: "合同", dataIndex: "contract_name", width: 140, ellipsis: true },
                { title: "渠道", dataIndex: "channel", width: 80, render: (v: string) => <Tag color="blue">{v}</Tag> },
                { title: "状态", dataIndex: "status", width: 80, render: (v: string) => <Tag color="green">{v}</Tag> },
                {
                  title: "操作", width: 60,
                  render: (_: unknown, r: typeof mockReminderSettings.history[0]) => (
                    <a onClick={() => handleResend(r.id)}>重发</a>
                  ),
                },
              ]}
            />
          ),
        },
      ]} />
    </div>
  );
}
