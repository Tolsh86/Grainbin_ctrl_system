import { useState, useEffect } from "react";
import { Card, Button, Table, Tag, Space, Row, Col, Input, message, Select } from "antd";
import { PlusOutlined, EditOutlined, ExportOutlined, SearchOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { getFieldMappings, deleteFieldMapping, seedPresets, type FieldMapping } from "../../api/data";

export default function MappingList() {
  const navigate = useNavigate();
  const [mappings, setMappings] = useState<FieldMapping[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [formatFilter, setFormatFilter] = useState<string[]>([]);

  const fetchMappings = () => {
    setLoading(true);
    getFieldMappings({ page: 1, page_size: 100 })
      .then((res) => setMappings(res.items))
      .catch(() => message.error("加载映射列表失败"))
      .finally(() => setLoading(false));
  };
  useEffect(() => { fetchMappings(); }, []);

  const handleDelete = async (m: FieldMapping) => {
    try {
      await deleteFieldMapping(m.id);
      message.success("映射已删除");
      fetchMappings();
    } catch { message.error("删除失败"); }
  };

  const handleSeedPresets = async () => {
    try {
      await seedPresets();
      message.success("预置映射模板已初始化");
      fetchMappings();
    } catch { message.error("初始化预置模板失败"); }
  };

  let filtered = mappings;
  if (search) filtered = filtered.filter(m => m.mapping_name.includes(search));
  if (formatFilter.length) filtered = filtered.filter(m => formatFilter.includes(m.file_format));

  const columns = [
    { title: "映射名", dataIndex: "mapping_name", key: "name", width: 180,
      render: (v: string, r: FieldMapping) => <a onClick={() => navigate(`/data/mapping/${r.id}/edit`)}>{v}</a> },
    { title: "文件格式", dataIndex: "file_format", key: "fmt", width: 80, render: (v: string) => <Tag>{v}</Tag> },
    { title: "表头行号", dataIndex: "header_row", key: "hr", width: 80, align: "center" as const },
    { title: "Sheet", dataIndex: "sheet_index", key: "si", width: 70, align: "center" as const },
    { title: "状态", dataIndex: "is_active", key: "st", width: 80,
      render: (v: boolean) => <Tag color={v ? "green" : "default"}>{v ? "启用" : "停用"}</Tag> },
    { title: "创建时间", dataIndex: "created_at", key: "ct", width: 140,
      render: (v: string) => new Date(v).toLocaleString("zh-CN") },
    {
      title: "操作", key: "op", width: 120,
      render: (_: unknown, r: FieldMapping) => (
        <Space size="small">
          <a onClick={() => navigate(`/data/mapping/${r.id}/edit`)}><EditOutlined /> 编辑</a>
          <a onClick={() => handleDelete(r)} style={{ color: "#ff4d4f" }}>删除</a>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={[12, 8]} align="middle">
          <Col flex="auto">
            <Input.Search placeholder="搜索映射名" value={search}
              onChange={(e) => setSearch(e.target.value)} enterButton={<SearchOutlined />} />
          </Col>
          <Col>
            <Space>
              <Button onClick={handleSeedPresets}>初始化预置模板</Button>
              <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate("/data/mapping/new")}>新建映射</Button>
            </Space>
          </Col>
        </Row>
      </Card>

      <Card title={<Space><span>字段映射管理</span><Tag>{filtered.length} 个映射</Tag></Space>}>
        <Table
          columns={columns}
          dataSource={filtered}
          size="small"
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 20, showTotal: (t) => `共 ${t} 个映射` }}
          scroll={{ x: 800 }}
        />
      </Card>
    </div>
  );
}
