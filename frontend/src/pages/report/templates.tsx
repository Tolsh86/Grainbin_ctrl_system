import { useMemo } from "react";
import { Card, Table, Tag, Button, Space, Row, Col, Input, message } from "antd";
import { PlusOutlined, ExportOutlined, ImportOutlined, SearchOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { mockReportTemplates } from "../../utils/mock";

const typeMap: Record<string, string> = { daily: "日报", weekly: "周报", monthly: "月报", special: "专项" };

export default function TemplateList() {
  const navigate = useNavigate();
  const cols = useMemo(() => [
    { title: "模板名", dataIndex: "name", key: "n", render: (v: string, r: typeof mockReportTemplates[0]) => <a onClick={() => navigate(`/reports/templates/${r.id}/edit`)}>{v}</a> },
    { title: "类型", dataIndex: "type", key: "t", width: 80, render: (v: string) => <Tag>{typeMap[v]}</Tag> },
    { title: "版本", dataIndex: "version", key: "v", width: 60, render: (v: number) => `V${v}` },
    { title: "字段数", dataIndex: "field_count", key: "fc", width: 80 },
    { title: "状态", dataIndex: "status", key: "st", width: 80, render: (v: string) => <Tag color={v === "active" ? "green" : "default"}>{v === "active" ? "启用" : "禁用"}</Tag> },
    { title: "创建人", dataIndex: "creator_name", key: "cr", width: 80 },
    { title: "创建时间", dataIndex: "created_at", key: "ct", width: 120 },
    { title: "操作", key: "op", width: 160, render: (_: unknown, r: typeof mockReportTemplates[0]) => (
      <Space size="small">
        <a onClick={() => navigate(`/reports/templates/${r.id}/edit`)}>编辑</a>
        <a onClick={() => message.info("复制模板")}>复制</a>
        <a onClick={() => message.success(`${r.name} 已${r.status === "active" ? "停用" : "启用"}`)}>{r.status === "active" ? "停用" : "启用"}</a>
      </Space>
    ) },
  ], [navigate]);

  return (
    <div>
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={[12, 8]} align="middle">
          <Col flex="auto"><Input.Search placeholder="搜索模板名" enterButton={<SearchOutlined />} /></Col>
          <Col>
            <Space>
              <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate("/reports/templates/1/edit")}>新建模板</Button>
              <Button icon={<ImportOutlined />} onClick={() => message.info("导入JSON Schema")}>导入</Button>
              <Button icon={<ExportOutlined />} onClick={() => message.info("导出")}>导出</Button>
            </Space>
          </Col>
        </Row>
      </Card>
      <Card title="模板管理">
        <Table columns={cols} dataSource={mockReportTemplates} size="small" rowKey="id" />
      </Card>
    </div>
  );
}