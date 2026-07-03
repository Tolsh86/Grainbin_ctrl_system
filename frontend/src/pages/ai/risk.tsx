import { useState } from "react";
import { Card, Table, Tag, Button, Space, message, Modal, Descriptions, Select } from "antd";
import { ThunderboltOutlined } from "@ant-design/icons";
import { mockRisks } from "../../utils/mock";

const levelMap: Record<string, { color: string; text: string }> = {
  high: { color: "red", text: "高风险" },
  medium: { color: "orange", text: "中风险" },
  low: { color: "blue", text: "低风险" },
};
const statusMap: Record<string, { color: string; text: string }> = {
  unprocessed: { color: "red", text: "未处理" },
  processing: { color: "orange", text: "处理中" },
  processed: { color: "green", text: "已处理" },
  ignored: { color: "default", text: "已忽略" },
};

export default function RiskDetection() {
  const [detailOpen, setDetailOpen] = useState<string | null>(null);
  const sel = mockRisks.find((r) => r.id === detailOpen);
  return (
    <div>
      <Card size="small" style={{ marginBottom: 16 }}>
        <Space>
          <Select defaultValue="p1" style={{ width: 180 }} options={[{ value: "p1", label: "1-6号粮仓新建工程" }]} />
          <Button type="primary" icon={<ThunderboltOutlined />} onClick={() => message.success("扫描完成，发现 2 项高风险")}>一键AI扫描</Button>
          <Button onClick={() => message.success("批量处理完成")}>批量处理</Button>
        </Space>
      </Card>
      <Card title="风险列表">
        <Table size="small" rowKey="id" dataSource={mockRisks}
          onRow={(r) => ({ onClick: () => setDetailOpen(r.id), style: { cursor: "pointer" } })}
          columns={[
            { title: "等级", dataIndex: "level", width: 80, render: (v: string) => <Tag color={levelMap[v]?.color}>{levelMap[v]?.text}</Tag> },
            { title: "类型", dataIndex: "type", width: 90 },
            { title: "描述", dataIndex: "description", ellipsis: true },
            { title: "关联对象", dataIndex: "target", width: 140, ellipsis: true },
            { title: "AI建议", dataIndex: "suggestion", width: 200, ellipsis: true },
            { title: "状态", dataIndex: "status", width: 80, render: (v: string) => <Tag color={statusMap[v]?.color}>{statusMap[v]?.text}</Tag> },
            { title: "操作", key: "op", width: 80, render: (_: unknown, r: typeof mockRisks[0]) => (
              <Space size="small">
                {r.status === "unprocessed" && <a onClick={(e) => { e.stopPropagation(); message.success("已标记处理中"); }}>处理</a>}
                <a onClick={(e) => { e.stopPropagation(); message.info("忽略"); }}>忽略</a>
              </Space>
            ) },
          ]}
        />
      </Card>
      {sel && (
        <Modal title="风险详情" open={true} onCancel={() => setDetailOpen(null)}
          footer={<Space><Button onClick={() => setDetailOpen(null)}>关闭</Button><Button type="primary" onClick={() => { setDetailOpen(null); message.success("风险已处理"); }}>确认处理</Button></Space>}>
          <Descriptions bordered size="small" column={1}>
            <Descriptions.Item label="等级"><Tag color={levelMap[sel.level]?.color}>{levelMap[sel.level]?.text}</Tag></Descriptions.Item>
            <Descriptions.Item label="类型">{sel.type}</Descriptions.Item>
            <Descriptions.Item label="描述">{sel.description}</Descriptions.Item>
            <Descriptions.Item label="关联对象">{sel.target}</Descriptions.Item>
            <Descriptions.Item label="AI建议">{sel.suggestion}</Descriptions.Item>
            <Descriptions.Item label="状态"><Tag color={statusMap[sel.status]?.color}>{statusMap[sel.status]?.text}</Tag></Descriptions.Item>
          </Descriptions>
        </Modal>
      )}
    </div>
  );
}
