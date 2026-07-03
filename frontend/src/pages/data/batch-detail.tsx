import { useState, useCallback } from "react";
import {
  Card, Row, Col, Statistic, Steps, Table, Tag, Tabs, Button, Space,
  Drawer, Collapse, Input, InputNumber, message, Badge, Progress, Tooltip,
  Typography, Alert
} from "antd";
import {
  CheckCircleOutlined, WarningOutlined,
  ArrowLeftOutlined, DownloadOutlined, RollbackOutlined,
  InfoCircleOutlined
} from "@ant-design/icons";
import { useNavigate, useParams } from "react-router-dom";
import { mockBatches, mockDataRows, formatYuan } from "../../utils/mock";

const { Text } = Typography;

const BATCH_STATUS_STEPS = [
  { title: "待解析", description: "pending" },
  { title: "解析中", description: "parsing" },
  { title: "已归一化", description: "normalized" },
  { title: "已校验", description: "validated" },
  { title: "待确认", description: "review" },
  { title: "入库中", description: "committing" },
  { title: "已入库", description: "committed" },
];

const STATUS_COLORS: Record<string, string> = {
  pending: "default", parsing: "processing", normalized: "blue",
  validated: "orange", review: "orange", committing: "purple",
  committed: "green", rolled_back: "red", failed: "red",
};

const ERROR_CODE_DICT = [
  { code: "HEADER_NOT_FOUND", name: "表头未找到" },
  { code: "TYPE_MISMATCH", name: "类型不匹配" },
  { code: "AMOUNT_OUT_OF_RANGE", name: "金额超出合理范围" },
  { code: "REQUIRED_MISSING", name: "必填字段缺失" },
  { code: "CONVERTER_FAIL", name: "转换器执行失败" },
  { code: "DUPLICATE_ROW", name: "疑似重复行" },
  { code: "DATE_INVALID", name: "日期格式无效" },
];

export default function BatchDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const batch = mockBatches.find((b) => b.id === id);
  const [editDrawerOpen, setEditDrawerOpen] = useState(false);
  const [editingRow, setEditingRow] = useState<(typeof mockDataRows)[0] | null>(null);
  const [rows, setRows] = useState(mockDataRows);

  if (!batch) {
    return (
      <Card>
        <Alert type="error" message="批次不存在或已被删除" showIcon />
        <Button style={{ marginTop: 16 }} onClick={() => navigate("/data/batches")}>返回批次列表</Button>
      </Card>
    );
  }

  const totalRows = batch.total_rows;
  const parsedOk = batch.parsed_rows;
  const errorCount = batch.error_count;
  const validatedOk = parsedOk - errorCount;
  const unconfirmedCount = rows.filter((r) => !r.is_confirmed).length;
  const currentStep = BATCH_STATUS_STEPS.findIndex((s) => s.description === batch.status);

  // 内联编辑
  const handleCellEdit = useCallback((rowId: string, field: string, value: string | number) => {
    setRows((prev) => prev.map((r) => (r.id === rowId ? { ...r, [field]: value } : r)));
  }, []);

  const EditableCell = ({ value, rowId, field, editable }: { value: string | number; rowId: string; field: string; editable: boolean }) => {
    const [editing, setEditing] = useState(false);
    const [v, setV] = useState(value);
    if (!editable) return <span>{value}</span>;
    if (!editing) {
      return (
        <div
          onClick={() => setEditing(true)}
          style={{ cursor: "pointer", minHeight: 22, padding: "2px 4px", borderRadius: 4, transition: "background 0.2s" }}
          onMouseEnter={(e) => (e.currentTarget.style.background = "#e6f4ff")}
          onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
        >
          {value}
        </div>
      );
    }
    const isNumber = ["amount", "unit_price", "planned_quantity", "actual_quantity"].includes(field);
    const InputComp = isNumber ? (
      <InputNumber
        value={v as number} onChange={(n) => setV(n ?? 0)} autoFocus size="small"
        onBlur={() => { handleCellEdit(rowId, field, v); setEditing(false); }}
        onPressEnter={() => { handleCellEdit(rowId, field, v); setEditing(false); }}
        style={{ width: "100%" }}
      />
    ) : (
      <Input
        value={String(v)} onChange={(e) => setV(e.target.value)} autoFocus size="small"
        onBlur={() => { handleCellEdit(rowId, field, v); setEditing(false); }}
        onPressEnter={() => { handleCellEdit(rowId, field, v); setEditing(false); }}
      />
    );
    return InputComp;
  };

  // 校验标记
  const flagColor = (f: string) => f === "error" ? "red" : f === "warning" ? "orange" : "green";
  const flagText = (f: string) => f === "error" ? "错误" : f === "warning" ? "警告" : "正常";
  const flagIcon = (f: string) =>
    f === "error" ? <WarningOutlined style={{ color: "#ff4d4f" }} /> :
    f === "warning" ? <WarningOutlined style={{ color: "#fa8c16" }} /> :
    <CheckCircleOutlined style={{ color: "#52c41a" }} />;

  const rowColumns = [
    { title: "行号", dataIndex: "row_number", width: 60, fixed: "left" as const },
    { title: "数据日期", dataIndex: "data_date", width: 90 },
    { title: "类别", dataIndex: "category", width: 80 },
    { title: "分项", dataIndex: "item_name", width: 120, ellipsis: true,
      render: (v: string, r: typeof mockDataRows[0]) => <EditableCell value={v} rowId={r.id} field="item_name" editable={true} /> },
    { title: "计划量", dataIndex: "planned_quantity", width: 80, align: "right" as const,
      render: (v: number, r: typeof mockDataRows[0]) => <EditableCell value={v} rowId={r.id} field="planned_quantity" editable={true} /> },
    { title: "实际量", dataIndex: "actual_quantity", width: 80, align: "right" as const,
      render: (v: number, r: typeof mockDataRows[0]) => <EditableCell value={v} rowId={r.id} field="actual_quantity" editable={true} /> },
    { title: "单位", dataIndex: "unit", width: 50 },
    { title: "单价(元)", dataIndex: "unit_price", width: 90, align: "right" as const,
      render: (v: number, r: typeof mockDataRows[0]) => <EditableCell value={v} rowId={r.id} field="unit_price" editable={true} /> },
    { title: "金额(元)", dataIndex: "amount", width: 110, align: "right" as const,
      render: (v: number, r: typeof mockDataRows[0]) => <EditableCell value={v} rowId={r.id} field="amount" editable={true} /> },
    { title: "费用类型", dataIndex: "cost_type", width: 80,
      render: (v: string) => <Tag>{v}</Tag> },
    { title: "来源", dataIndex: "source_doc", width: 100, ellipsis: true },
    { title: "校验", dataIndex: "validation_flag", width: 60, align: "center" as const,
      render: (v: string) => <Tooltip title={flagText(v)}>{flagIcon(v)}</Tooltip> },
    { title: "确认", dataIndex: "is_confirmed", width: 60, align: "center" as const,
      render: (v: boolean) => v ? <Tag color="green">已确认</Tag> : <Tag color="orange">待确认</Tag> },
    {
      title: "操作", width: 100, fixed: "right" as const,
      render: (_: unknown, r: typeof mockDataRows[0]) => (
        <Space size="small">
          <a onClick={() => { setEditingRow(r); setEditDrawerOpen(true); }}>修正</a>
          <a onClick={() => message.warning(`排除行 ${r.row_number}`)} style={{ color: "#ff4d4f" }}>排除</a>
        </Space>
      ),
    },
  ];

  const filterRows = (filter: string) => {
    if (filter === "all") return rows;
    if (filter === "unconfirmed") return rows.filter((r) => !r.is_confirmed);
    if (filter === "error") return rows.filter((r) => r.validation_flag === "error");
    if (filter === "warning") return rows.filter((r) => r.validation_flag === "warning");
    return rows;
  };

  // 错误码 top 5
  const errorCodeStats = [
    { code: "AMOUNT_OUT_OF_RANGE", count: 3 },
    { code: "TYPE_MISMATCH", count: 1 },
    { code: "REQUIRED_MISSING", count: 1 },
    { code: "DUPLICATE_ROW", count: 1 },
  ];

  const handleCommit = () => {
    message.success(`整批确认入库成功：${batch.batch_no} → 状态变更为 committed`);
  };
  const handleRollback = () => {
    message.warning(`批次撤回操作已提交：${batch.batch_no}`);
  };

  const handleSaveEdit = () => {
    if (editingRow) {
      handleCellEdit(editingRow.id, "data_date", editingRow.data_date);
      message.success("保存成功，已自动重校验");
    }
    setEditDrawerOpen(false);
  };

  return (
    <div>
      {/* 页头 */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row justify="space-between" align="middle" wrap>
          <Col>
            <Space size="middle" wrap>
              <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate("/data/batches")}>返回</Button>
              <span style={{ fontSize: 16, fontWeight: 600 }}>{batch.batch_no}</span>
              <Tag color="blue">{batch.original_filename}</Tag>
              <Tag color={STATUS_COLORS[batch.status] || "default"}>{batch.status}</Tag>
              <Tooltip title={`质量分 ${batch.quality_score}/100`}>
                <Progress type="circle" percent={batch.quality_score} size={28} strokeColor={batch.quality_score >= 90 ? "#52c41a" : "#fa8c16"} />
              </Tooltip>
            </Space>
          </Col>
          <Col>
            <Space>
              <Button icon={<DownloadOutlined />} onClick={() => message.info("下载原始文件（MinIO预签名URL）")}>下载原始文件</Button>
              {(batch.status === "validated" || batch.status === "review") && (
                <Button type="primary" icon={<CheckCircleOutlined />} onClick={handleCommit}>整批确认入库</Button>
              )}
              {batch.status === "committed" && (
                <Button icon={<RollbackOutlined />} danger onClick={handleRollback}>整批撤回</Button>
              )}
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 状态时间线 */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Steps
          current={currentStep >= 0 ? currentStep : 0}
          size="small"
          status={batch.status === "failed" ? "error" : "process"}
          items={BATCH_STATUS_STEPS.map((s) => ({ title: s.title }))}
        />
        {batch.status === "validated" && (
          <Alert style={{ marginTop: 12 }} message="数据已校验通过，请逐行确认或点击「整批确认入库」将数据写入数据中心" type="info" showIcon />
        )}
      </Card>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={12} sm={6}><Card size="small"><Statistic title="总行数" value={totalRows} /></Card></Col>
        <Col xs={12} sm={6}><Card size="small"><Statistic title="解析成功" value={parsedOk} valueStyle={{ color: parsedOk === totalRows ? "#52c41a" : "#fa8c16" }} /></Card></Col>
        <Col xs={12} sm={6}><Card size="small"><Statistic title="校验通过" value={validatedOk} valueStyle={{ color: validatedOk === parsedOk ? "#52c41a" : "#fa8c16" }} /></Card></Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="错误/警告"
              value={errorCount}
              valueStyle={{ color: errorCount > 0 ? "#ff4d4f" : "#52c41a" }}
              suffix={<span style={{ fontSize: 14, color: "#fa8c16" }}>/ {rows.filter(r => r.validation_flag === "warning").length}</span>}
            />
          </Card>
        </Col>
      </Row>

      {/* 行数据表格（核心） */}
      <Card
        title="数据明细"
        extra={
          <Space>
            <Text type="secondary" style={{ fontSize: 12 }}>待确认: {unconfirmedCount}</Text>
            <Button size="small" onClick={() => message.success(`批量确认 ${unconfirmedCount} 行`)} disabled={unconfirmedCount === 0}>批量确认</Button>
            <Button size="small" onClick={() => message.warning("批量排除")}>批量排除</Button>
            <Button size="small" icon={<DownloadOutlined />} onClick={() => message.info("导出当前Tab")}>导出</Button>
          </Space>
        }
      >
        <Tabs
          defaultActiveKey="all"
          tabBarExtraContent={
            <Space size="small">
              <InfoCircleOutlined style={{ color: "#999" }} />
              <Text type="secondary" style={{ fontSize: 12 }}>点击单元格可直接编辑，回车保存后自动重校验</Text>
            </Space>
          }
          items={[
            { key: "all", label: `全部行 (${rows.length})` },
            { key: "unconfirmed", label: `待确认 (${unconfirmedCount})` },
            { key: "error", label: `错误行 (${errorCount})` },
            { key: "warning", label: `警告行 (${rows.filter(r => r.validation_flag === "warning").length})` },
          ].map((tab) => ({
            key: tab.key,
            label: tab.label,
            children: (
              <Table
                columns={rowColumns}
                dataSource={filterRows(tab.key)}
                rowKey="id"
                size="small"
                scroll={{ x: 1300 }}
                pagination={{ pageSize: 20, showSizeChanger: true, showTotal: (t) => `共 ${t} 行` }}
                rowClassName={(r) => r.validation_flag === "error" ? "row-error" : r.validation_flag === "warning" ? "row-warning" : ""}
              />
            ),
          }))}
        />
      </Card>

      {/* 错误侧栏 */}
      <Collapse
        style={{ marginTop: 16 }}
        items={[{
          key: "errors",
          label: <span>错误详情（共 {errorCount} 条）</span>,
          children: (
            <Row gutter={16}>
              <Col xs={24} md={12}>
                <Text strong style={{ fontSize: 13 }}>错误码 Top 5</Text>
                <Table
                  size="small" pagination={false} style={{ marginTop: 8 }}
                  dataSource={errorCodeStats}
                  columns={[
                    { title: "错误码", dataIndex: "code", render: (v: string) => <Tag color="red">{v}</Tag> },
                    { title: "说明", dataIndex: "code", render: (v: string) => ERROR_CODE_DICT.find(e => e.code === v)?.name || v },
                    { title: "数量", dataIndex: "count", align: "right" as const, render: (v: number) => <Badge count={v} overflowCount={99} style={{ backgroundColor: "#ff4d4f" }} /> },
                  ]}
                />
              </Col>
              <Col xs={24} md={12}>
                <Text strong style={{ fontSize: 13 }}>错误码字典</Text>
                <div style={{ marginTop: 8 }}>
                  {ERROR_CODE_DICT.map((e) => (
                    <div key={e.code} style={{ marginBottom: 4, fontSize: 12 }}>
                      <Tag color="red" style={{ fontSize: 11 }}>{e.code}</Tag> {e.name}
                    </div>
                  ))}
                </div>
              </Col>
            </Row>
          ),
        }]}
      />

      {/* 行级修正抽屉 */}
      <Drawer
        title={`行级修正 — 行号 #${editingRow?.row_number ?? ""}`}
        width={640}
        open={editDrawerOpen}
        onClose={() => setEditDrawerOpen(false)}
        extra={
          <Space>
            <Button onClick={() => setEditDrawerOpen(false)}>取消</Button>
            <Button type="primary" onClick={handleSaveEdit}>保存（自动重校验）</Button>
            <Button danger onClick={() => { message.warning("排除此行"); setEditDrawerOpen(false); }}>排除此行</Button>
          </Space>
        }
      >
        {editingRow && (
          <>
            {/* 原始数据区（只读） */}
            <Card title="原始数据（只读）" size="small" style={{ marginBottom: 16 }}>
              <pre style={{ fontSize: 12, background: "#f6f8fa", padding: 12, borderRadius: 6, margin: 0, overflow: "auto", maxHeight: 200 }}>
                {JSON.stringify(editingRow.raw_payload, null, 2)}
              </pre>
            </Card>

            {/* 归一化后（可编辑） */}
            <Card title="归一化后数据（可编辑）" size="small" style={{ marginBottom: 16 }}>
              <Row gutter={[12, 12]}>
                <Col span={12}>
                  <div style={{ marginBottom: 4, fontSize: 12, fontWeight: 500 }}>数据日期</div>
                  <Input defaultValue={editingRow.data_date}
                    onChange={(e) => setEditingRow(prev => prev ? { ...prev, data_date: e.target.value } : prev)} />
                </Col>
                <Col span={12}>
                  <div style={{ marginBottom: 4, fontSize: 12, fontWeight: 500 }}>类别</div>
                  <Input defaultValue={editingRow.category}
                    onChange={(e) => setEditingRow(prev => prev ? { ...prev, category: e.target.value } : prev)} />
                </Col>
                <Col span={12}>
                  <div style={{ marginBottom: 4, fontSize: 12, fontWeight: 500 }}>计划工程量</div>
                  <InputNumber style={{ width: "100%" }} defaultValue={editingRow.planned_quantity}
                    onChange={(v) => setEditingRow(prev => prev ? { ...prev, planned_quantity: v || 0 } : prev)} />
                </Col>
                <Col span={12}>
                  <div style={{ marginBottom: 4, fontSize: 12, fontWeight: 500 }}>实际工程量</div>
                  <InputNumber style={{ width: "100%" }} defaultValue={editingRow.actual_quantity}
                    onChange={(v) => setEditingRow(prev => prev ? { ...prev, actual_quantity: v || 0 } : prev)} />
                </Col>
              </Row>
            </Card>

            {/* 系统字段（可编辑） */}
            <Card title="映射后系统字段（可编辑）" size="small" style={{ marginBottom: 16 }}>
              <Row gutter={[12, 12]}>
                <Col span={12}>
                  <div style={{ marginBottom: 4, fontSize: 12, fontWeight: 500 }}>单价(元)</div>
                  <InputNumber style={{ width: "100%" }} defaultValue={editingRow.unit_price}
                    onChange={(v) => setEditingRow(prev => prev ? { ...prev, unit_price: v || 0 } : prev)} />
                </Col>
                <Col span={12}>
                  <div style={{ marginBottom: 4, fontSize: 12, fontWeight: 500 }}>金额(元)</div>
                  <InputNumber style={{ width: "100%" }} defaultValue={editingRow.amount}
                    onChange={(v) => setEditingRow(prev => prev ? { ...prev, amount: v || 0 } : prev)} />
                </Col>
                <Col span={12}>
                  <div style={{ marginBottom: 4, fontSize: 12, fontWeight: 500 }}>费用类型</div>
                  <Input defaultValue={editingRow.cost_type}
                    onChange={(e) => setEditingRow(prev => prev ? { ...prev, cost_type: e.target.value } : prev)} />
                </Col>
                <Col span={12}>
                  <div style={{ marginBottom: 4, fontSize: 12, fontWeight: 500 }}>分项名称</div>
                  <Input defaultValue={editingRow.item_name}
                    onChange={(e) => setEditingRow(prev => prev ? { ...prev, item_name: e.target.value } : prev)} />
                </Col>
              </Row>
            </Card>

            {/* 校验标记（只读） */}
            <Card size="small" style={{ background: editingRow.validation_flag === "ok" ? "#f6ffed" : "#fff7e6" }}>
              <Text strong>校验标记</Text>
              <div style={{ marginTop: 8 }}>
                {editingRow.validation_flag !== "ok" ? (
                  <Space>
                    <Tag color={flagColor(editingRow.validation_flag)}>{flagText(editingRow.validation_flag)}</Tag>
                    <Text type="secondary" style={{ fontSize: 12 }}>{editingRow.error_description}</Text>
                  </Space>
                ) : (
                  <Text style={{ color: "#52c41a" }}>✅ 无错误</Text>
                )}
              </div>
            </Card>
          </>
        )}
      </Drawer>
    </div>
  );
}
