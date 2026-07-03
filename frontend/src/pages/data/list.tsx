import { useState } from "react";
import { Card, Select, Button, Table, Tag, Space, Row, Col, Input, Drawer, Descriptions, message, Collapse } from "antd";
import { PlusOutlined, ExportOutlined, SettingOutlined, SearchOutlined } from "@ant-design/icons";
import { mockDataRows } from "../../utils/mock";

const columns = [
  { title: "数据日期", dataIndex: "data_date", key: "date", width: 90 },
  { title: "项目", dataIndex: "category", key: "proj", width: 90 },
  { title: "类别", dataIndex: "category", key: "cat", width: 90 },
  { title: "分项", dataIndex: "item_name", key: "item", width: 120, ellipsis: true },
  { title: "计划工程量", dataIndex: "planned_quantity", key: "pq", width: 90, align: "right" as const },
  { title: "实际工程量", dataIndex: "actual_quantity", key: "aq", width: 90, align: "right" as const },
  { title: "单价(元)", dataIndex: "unit_price", key: "price", width: 90, align: "right" as const, render: (v: number) => v.toLocaleString() },
  { title: "金额(元)", dataIndex: "amount", key: "amount", width: 110, align: "right" as const, render: (v: number) => v.toLocaleString() },
  { title: "费用类型", dataIndex: "cost_type", key: "ct", width: 80 },
  { title: "来源", dataIndex: "source_doc", key: "src", width: 120, ellipsis: true },
  { title: "状态", dataIndex: "is_confirmed", key: "cf", width: 80, render: (v: boolean) => <Tag color={v ? "green" : "orange"}>{v ? "已确认" : "待确认"}</Tag> },
  { title: "操作", key: "action", width: 80, render: () => <Space size="small"><a>查看</a><a>编辑</a></Space> },
];

export default function DataList() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [confirmFilter, setConfirmFilter] = useState<string>("");

  let filtered = mockDataRows;
  if (confirmFilter === "confirmed") filtered = filtered.filter((r) => r.is_confirmed);
  if (confirmFilter === "unconfirmed") filtered = filtered.filter((r) => !r.is_confirmed);
  if (search) filtered = filtered.filter((r) => r.item_name.includes(search) || r.category.includes(search));

  return (
    <div>
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={[12, 8]} align="middle">
          <Col><Select placeholder="确认状态" allowClear style={{ width: 140 }} value={confirmFilter || undefined} onChange={(v) => setConfirmFilter(v ?? "")} options={[{ value: "confirmed", label: "已确认" }, { value: "unconfirmed", label: "待确认" }]} /></Col>
          <Col flex="auto"><Input.Search placeholder="搜索分项/类别" enterButton={<SearchOutlined />} value={search} onChange={(e) => setSearch(e.target.value)} /></Col>
          <Col>
            <Space>
              <Button icon={<ExportOutlined />} onClick={() => message.info("导出Excel（≤10万行）")}>导出</Button>
              <Button icon={<SettingOutlined />} onClick={() => message.info("列设置（显示/隐藏/排序）")}>列设置</Button>
            </Space>
          </Col>
        </Row>
      </Card>

      <Card title="数据列表">
        <Table
          columns={columns}
          dataSource={filtered}
          rowKey="id"
          size="small"
          scroll={{ x: 1100 }}
          pagination={{ pageSize: 20, showSizeChanger: true }}
          onRow={() => ({ onClick: () => setDrawerOpen(true), style: { cursor: "pointer" } })}
        />
      </Card>

      <Drawer title="数据详情" width={640} open={drawerOpen} onClose={() => setDrawerOpen(false)}
        extra={<Space><Button onClick={() => setDrawerOpen(false)}>取消</Button><Button type="primary" onClick={() => { message.success("保存修改"); setDrawerOpen(false); }}>保存修改</Button></Space>}
      >
        <Descriptions bordered column={2} size="small" title="基础信息（只读）">
          <Descriptions.Item label="数据ID">data-row-001</Descriptions.Item>
          <Descriptions.Item label="所属项目">1-6号粮仓新建工程</Descriptions.Item>
          <Descriptions.Item label="来源文档" span={2}><a>6月第4周工程量清单.xlsx</a></Descriptions.Item>
          <Descriptions.Item label="确认人">王工</Descriptions.Item>
          <Descriptions.Item label="确认时间">2026-06-30 16:30</Descriptions.Item>
        </Descriptions>

        <div style={{ marginTop: 16 }}><strong>核心数据（可编辑）</strong></div>
        <Row gutter={[12, 8]} style={{ marginTop: 8 }}>
          {["data_date","category","item_name","planned_quantity","actual_quantity","unit_price","amount","cost_type"].map((f) => (
            <Col span={12} key={f}><div style={{ fontSize: 12, marginBottom: 4 }}>{f}</div><Input defaultValue="—" /></Col>
          ))}
        </Row>

        <Collapse style={{ marginTop: 16 }} items={[
          { key: "raw", label: "原始数据预览（折叠）", children: <pre style={{ fontSize: 11, background: "#f5f5f5", padding: 12, borderRadius: 4 }}>{JSON.stringify({ 原始列A: "值A", 原始列B: 123, 原始列C: "2026/6/25" }, null, 2)}</pre> },
          { key: "history", label: "修改历史（折叠）", children: <Table size="small" pagination={false} dataSource={[{ time: "2026-06-30 16:30", field: "amount", oldVal: "50,000", newVal: "48,000", user: "王工", source: "批次确认" }]} columns={[{ title: "时间", dataIndex: "time" },{ title: "字段", dataIndex: "field" },{ title: "变更前", dataIndex: "oldVal" },{ title: "变更后", dataIndex: "newVal" },{ title: "操作人", dataIndex: "user" }]} /> },
        ]} />
      </Drawer>
    </div>
  );
}