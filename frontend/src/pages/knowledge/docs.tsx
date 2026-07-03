import { useState } from "react";
import { Card, Table, Tag, Button, Space, Row, Col, Input, Select, Upload, message, Progress, Drawer, Descriptions, List } from "antd";
import { PlusOutlined, SearchOutlined, InboxOutlined, RobotOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { mockKnowledgeDocs } from "../../utils/mock";

const { Dragger } = Upload;
const typeMap: Record<string, string> = { "合同": "blue", "图纸": "purple", "会议纪要": "cyan", "规范": "orange", "签证": "green", "历史报告": "default" };
const parseMap: Record<string, { color: string; text: string }> = { completed: { color: "green", text: "已完成" }, parsing: { color: "processing", text: "解析中" }, pending: { color: "default", text: "待解析" }, failed: { color: "red", text: "失败" } };

export default function KnowledgeDocs() {
  const navigate = useNavigate();
  const [detailOpen, setDetailOpen] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const sel = mockKnowledgeDocs.find((d) => d.id === detailOpen);
  let filtered = mockKnowledgeDocs;
  if (search) filtered = filtered.filter((d) => d.doc_name.includes(search));

  return (
    <div>
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={[12, 8]} align="middle">
          <Col flex="auto"><Input.Search placeholder="搜索文档名" enterButton={<SearchOutlined />} value={search} onChange={(e) => setSearch(e.target.value)} /></Col>
          <Col>
            <Upload customRequest={({ onSuccess }) => setTimeout(() => (onSuccess as (v: string) => void)?.("ok"), 500)} showUploadList={false}>
              <Button type="primary" icon={<PlusOutlined />}>上传文档</Button>
            </Upload>
          </Col>
        </Row>
      </Card>
      <Card title="知识库文档">
        <Table size="small" rowKey="id" dataSource={filtered}
          onRow={(r) => ({ onClick: () => setDetailOpen(r.id), style: { cursor: "pointer" } })}
          columns={[
            { title: "文档名", dataIndex: "doc_name", key: "n", width: 180, ellipsis: true },
            { title: "类型", dataIndex: "doc_type", key: "t", width: 80, render: (v: string) => <Tag color={typeMap[v] || "default"}>{v}</Tag> },
            { title: "大小", dataIndex: "file_size", key: "s", width: 80, render: (v: number) => `${(v / 1024 / 1024).toFixed(1)} MB` },
            { title: "分块数", dataIndex: "chunk_count", key: "c", width: 60 },
            { title: "解析状态", dataIndex: "parse_status", key: "ps", width: 90, render: (v: string) => <Tag color={parseMap[v]?.color}>{parseMap[v]?.text}</Tag> },
            { title: "摘要", dataIndex: "summary", key: "sm", width: 200, ellipsis: true, render: (v?: string) => v || "—" },
            { title: "上传者", dataIndex: "uploader_name", key: "u", width: 80 },
            { title: "上传时间", dataIndex: "upload_time", key: "ut", width: 110 },
            { title: "操作", key: "op", width: 100, render: (_: unknown, r: typeof mockKnowledgeDocs[0]) => (
              <Space size="small">
                <a onClick={(e) => { e.stopPropagation(); navigate(`/knowledge/chat`); }}><RobotOutlined />提问</a>
                <a onClick={(e) => { e.stopPropagation(); message.info("重新解析"); }}>重解析</a>
              </Space>
            ) },
          ]}
        />
      </Card>
      {sel && (
        <Drawer title={`文档详情 — ${sel.doc_name}`} width={720} open={!!sel} onClose={() => setDetailOpen(null)}>
          <Descriptions bordered size="small" column={2}>
            <Descriptions.Item label="文档名">{sel.doc_name}</Descriptions.Item>
            <Descriptions.Item label="类型"><Tag color={typeMap[sel.doc_type] || "default"}>{sel.doc_type}</Tag></Descriptions.Item>
            <Descriptions.Item label="大小">{(sel.file_size / 1024 / 1024).toFixed(1)} MB</Descriptions.Item>
            <Descriptions.Item label="分块数">{sel.chunk_count}</Descriptions.Item>
            <Descriptions.Item label="解析状态"><Tag color={parseMap[sel.parse_status]?.color}>{parseMap[sel.parse_status]?.text}</Tag></Descriptions.Item>
            <Descriptions.Item label="摘要" span={2}>{sel.summary || "—"}</Descriptions.Item>
          </Descriptions>
          <Card title="AI 推荐问题" size="small" style={{ marginTop: 16 }}>
            <p style={{ color: "#999" }}>暂无推荐问题（此功能在后续版本开放）</p>
          </Card>
        </Drawer>
      )}
    </div>
  );
}