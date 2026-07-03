import { useMemo, useState } from "react";
import { Card, Button, Table, Tag, Space, Row, Col, Input, message, Select } from "antd";
import { PlusOutlined, EditOutlined, CopyOutlined, ExportOutlined, SearchOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { mockFieldMappings } from "../../utils/mock";

export default function MappingList() {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [formatFilter, setFormatFilter] = useState<string[]>([]);
  const [statusFilter, setStatusFilter] = useState<string[]>([]);

  let filtered = mockFieldMappings;
  if (search) filtered = filtered.filter(m => m.name.includes(search));
  if (formatFilter.length) filtered = filtered.filter(m => formatFilter.includes(m.file_format));
  if (statusFilter.length) filtered = filtered.filter(m => statusFilter.includes(m.status));

  const columns = useMemo(() => [
    { title: "映射名", dataIndex: "name", key: "name", width: 180,
      render: (v: string) => <a onClick={() => navigate(`/data/mapping/${mockFieldMappings.find(m => m.name === v)?.id}/edit`)}>{v}</a> },
    { title: "适用项目", dataIndex: "project_id", key: "proj", width: 140,
      render: (v: string | null) => v ? <span>{v}</span> : <Tag color="blue">通用</Tag> },
    { title: "文件格式", dataIndex: "file_format", key: "fmt", width: 80, render: (v: string) => <Tag>{v}</Tag> },
    { title: "表头行号", dataIndex: "header_row", key: "hr", width: 80, align: "center" as const },
    { title: "Sheet", dataIndex: "sheet_index", key: "si", width: 70, align: "center" as const },
    { title: "规则数", key: "rc", width: 70, align: "center" as const,
      render: (_: unknown, r: typeof mockFieldMappings[0]) => r.rules.length },
    { title: "状态", dataIndex: "status", key: "st", width: 80,
      render: (v: string) => <Tag color={v === "active" ? "green" : "default"}>{v === "active" ? "启用" : "停用"}</Tag> },
    { title: "创建人", dataIndex: "creator_name", key: "cr", width: 80 },
    { title: "创建时间", dataIndex: "created_at", key: "ct", width: 100 },
    {
      title: "操作", key: "op", width: 200, fixed: "right" as const,
      render: (_: unknown, r: typeof mockFieldMappings[0]) => (
        <Space size="small">
          <a onClick={() => navigate(`/data/mapping/${r.id}/edit`)}><EditOutlined /> 编辑</a>
          <a onClick={() => message.info(`已复制映射「${r.name}」的副本`)}><CopyOutlined /> 复制</a>
          <a onClick={() => message.success(`映射「${r.name}」${r.status === "active" ? "已停用" : "已启用"}`)}>
            {r.status === "active" ? "停用" : "启用"}
          </a>
          <a onClick={() => message.warning(`删除映射「${r.name}」`)} style={{ color: "#ff4d4f" }}>删除</a>
        </Space>
      ),
    },
  ], [navigate]);

  return (
    <div>
      {/* 筛选 + 操作 */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={[12, 8]} align="middle">
          <Col xs={24} sm={6}>
            <Input.Search placeholder="搜索映射名" value={search}
              onChange={(e) => setSearch(e.target.value)} enterButton={<SearchOutlined />} />
          </Col>
          <Col xs={12} sm={4}>
            <Select mode="multiple" placeholder="文件格式" style={{ width: "100%" }} allowClear
              value={formatFilter} onChange={setFormatFilter}
              options={[{ value: "xlsx", label: "xlsx" }, { value: "xls", label: "xls" }, { value: "csv", label: "csv" }]} />
          </Col>
          <Col xs={12} sm={4}>
            <Select mode="multiple" placeholder="状态" style={{ width: "100%" }} allowClear
              value={statusFilter} onChange={setStatusFilter}
              options={[{ value: "active", label: "启用" }, { value: "inactive", label: "停用" }]} />
          </Col>
          <Col flex="auto" />
          <Col>
            <Space>
              <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate("/data/mapping/new")}>新建映射</Button>
              <Button icon={<ExportOutlined />} onClick={() => message.info("导出映射配置 JSON")}>导出</Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 映射表格 */}
      <Card
        title={
          <Space>
            <span>字段映射管理</span>
            <Tag color="blue">预置 {mockFieldMappings.filter(m => m.project_id === null).length} 套</Tag>
            <Tag>{filtered.length} 个映射</Tag>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={filtered}
          size="small"
          rowKey="id"
          pagination={{ pageSize: 20, showTotal: (t) => `共 ${t} 个映射` }}
          scroll={{ x: 1000 }}
        />
      </Card>
    </div>
  );
}
