import { useState } from "react";
import { Card, Select, DatePicker, Upload, Button, Table, message, Collapse, Space, Alert, Row, Col, Tag, Steps, Typography } from "antd";
import { InboxOutlined, UploadOutlined, SettingOutlined, FileExcelOutlined, CheckCircleOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";

const { Dragger } = Upload;
const { RangePicker } = DatePicker;
const { Text } = Typography;

export default function DataUpload() {
  const navigate = useNavigate();
  const [project, setProject] = useState("p1");
  const [periodType, setPeriodType] = useState("weekly");
  const [mapping, setMapping] = useState("m1");
  const [dates, setDates] = useState<[any, any] | null>(null);
  const [fileList, setFileList] = useState<Array<{ name: string; size: number; uid: string }>>([]);
  const [uploading, setUploading] = useState(false);

  const uploadProps = {
    name: "file",
    multiple: true,
    accept: ".xlsx,.xls,.csv",
    beforeUpload: (file: File & { uid: string }) => {
      if (fileList.length >= 20) { message.error("单批次最多20个文件"); return Upload.LIST_IGNORE; }
      if (file.size > 50 * 1024 * 1024) { message.error(`${file.name} 超过50MB限制`); return Upload.LIST_IGNORE; }
      setFileList((prev) => [...prev, { name: file.name, size: file.size, uid: file.uid }]);
      return false;
    },
    onRemove: (file: { uid: string }) => { setFileList((prev) => prev.filter((f) => f.uid !== file.uid)); },
    fileList: fileList as never[],
  } as const;

  const previewCols = [
    { title: "#", dataIndex: "seq", width: 50 },
    { title: "日期", dataIndex: "date", width: 100 },
    { title: "类别", dataIndex: "category", width: 90 },
    { title: "分项", dataIndex: "item", width: 130 },
    { title: "工程量", dataIndex: "qty", width: 80 },
    { title: "单价(元)", dataIndex: "price", width: 90 },
    { title: "金额(元)", dataIndex: "amount", width: 110 },
    { title: "单位", dataIndex: "unit", width: 60 },
  ];
  const previewData = [
    { seq: 1, date: "2026-06-24", category: "土建工程", item: "C30混凝土浇筑", qty: 450, price: 680, amount: "306,000", unit: "m³" },
    { seq: 2, date: "2026-06-25", category: "土建工程", item: "HRB400钢筋", qty: 120, price: 5200, amount: "624,000", unit: "t" },
    { seq: 3, date: "2026-06-25", category: "安装工程", item: "钢结构安装", qty: 85, price: 12000, amount: "1,020,000", unit: "t" },
  ];

  const handleUpload = () => {
    if (!project) { message.warning("请选择项目"); return; }
    if (!mapping) { message.warning("请选择字段映射"); return; }
    if (fileList.length === 0) { message.warning("请上传文件"); return; }
    setUploading(true);
    setTimeout(() => {
      setUploading(false);
      message.success("批次 BT-20260702-001 创建成功，正在解析中");
      navigate("/data/batches/1");
    }, 2000);
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  };

  return (
    <div>
      <Card title="数据上传" extra={
        <Button icon={<SettingOutlined />} onClick={() => navigate("/data/mapping")}>管理字段映射</Button>
      }>
        {/* 上传前配置 */}
        <div style={{ marginBottom: 20, padding: 16, background: "#f6f8fa", borderRadius: 8 }}>
          <Text strong style={{ fontSize: 14, marginBottom: 12, display: "block" }}>上传前配置</Text>
          <Row gutter={16}>
            <Col xs={24} sm={12} lg={6}>
              <div style={{ marginBottom: 4, fontWeight: 500 }}>关联项目 <span style={{ color: "#ff4d4f" }}>*</span></div>
              <Select value={project} onChange={setProject} style={{ width: "100%" }}
                options={[
                  { value: "p1", label: "1-6号粮仓新建工程" },
                  { value: "p2", label: "7-12号粮仓改造工程" },
                  { value: "p3", label: "智能通风系统安装" },
                  { value: "p4", label: "中心粮库扩建" },
                  { value: "p5", label: "粮库信息化平台建设" },
                ]} />
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <div style={{ marginBottom: 4, fontWeight: 500 }}>业务周期 <span style={{ color: "#ff4d4f" }}>*</span></div>
              <Select value={periodType} onChange={setPeriodType} style={{ width: "100%" }}
                options={[
                  { value: "weekly", label: "周报数据" },
                  { value: "monthly", label: "月报数据" },
                  { value: "payment", label: "进度款申报" },
                  { value: "audit", label: "审核资料" },
                  { value: "other", label: "其他" },
                ]} />
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <div style={{ marginBottom: 4, fontWeight: 500 }}>起止日期</div>
              <RangePicker style={{ width: "100%" }} value={dates} onChange={setDates} />
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <div style={{ marginBottom: 4, fontWeight: 500 }}>字段映射 <span style={{ color: "#ff4d4f" }}>*</span></div>
              <Select value={mapping} onChange={setMapping} style={{ width: "100%" }}
                options={[
                  { value: "m1", label: "Excel 工程量清单（xlsx）" },
                  { value: "m2", label: "监理月报（xlsx）" },
                  { value: "m3", label: "进度款申报（xlsx）" },
                ]} />
            </Col>
          </Row>
        </div>

        {/* 上传区 */}
        <Dragger {...uploadProps} style={{ marginBottom: 16 }} disabled={uploading}>
          <p className="ant-upload-drag-icon"><InboxOutlined /></p>
          <p className="ant-upload-text" style={{ fontSize: 16 }}>拖拽文件到此处，或 <Text style={{ color: "#1677ff" }}>点击选择</Text></p>
          <p className="ant-upload-hint">支持 .xlsx / .xls / .csv 格式，单文件 ≤ 50MB，单批次 ≤ 20 个文件</p>
        </Dragger>

        {/* 已选文件 */}
        {fileList.length > 0 && (
          <>
            <Card title={`已选文件（${fileList.length} 个）`} size="small" style={{ marginBottom: 16 }}>
              {fileList.map((f, i) => (
                <Row key={f.uid} style={{ padding: "4px 0", borderBottom: i < fileList.length - 1 ? "1px solid #f0f0f0" : "none" }}
                  justify="space-between" align="middle">
                  <Col><FileExcelOutlined style={{ color: "#52c41a", marginRight: 8 }} />{f.name}</Col>
                  <Col><Text type="secondary" style={{ fontSize: 12 }}>{formatSize(f.size)}</Text></Col>
                </Row>
              ))}
            </Card>

            {/* 预览表头 */}
            <Card title="数据预览（第1个文件前3行）" size="small" style={{ marginBottom: 16 }}>
              <Table columns={previewCols} dataSource={previewData} pagination={false} size="small" />
              <Alert style={{ marginTop: 12 }}
                message="请确认表头和数据格式正确。如有问题，请检查字段映射配置或修改 Excel 文件后重新上传。"
                type="info" showIcon />
            </Card>
          </>
        )}

        <Button
          type="primary" size="large" icon={<UploadOutlined />}
          onClick={handleUpload}
          disabled={fileList.length === 0}
          loading={uploading}
          block
        >
          {fileList.length > 0 ? `开始上传（${fileList.length} 个文件）` : "请先选择文件"}
        </Button>
      </Card>

      {/* 使用提示 */}
      <Collapse style={{ marginTop: 16 }} items={[{
        key: "tips",
        label: <Space><CheckCircleOutlined style={{ color: "#1677ff" }} />使用提示与数据处理流程</Space>,
        children: (
          <div style={{ fontSize: 13, lineHeight: 2.2 }}>
            <Text strong>数据处理流程：</Text>
            <Steps
              size="small"
              direction="vertical"
              current={-1}
              style={{ marginTop: 8 }}
              items={[
                { title: "上传", description: "文件上传至 MinIO 对象存储，创建批次记录（status=pending）" },
                { title: "解析（parse）", description: "读取 Excel 原始数据，识别表头和数据类型" },
                { title: "归一化（normalize）", description: "将原始值转换为统一格式（日期→ISO、中文→标准分类）" },
                { title: "映射（map）", description: "根据字段映射配置，将 Excel 列映射到系统字段（data_date / category / amount 等）" },
                { title: "校验（validate）", description: "校验数据类型、范围、必填项，标记错误行和警告行" },
                { title: "人工确认（commit）", description: "用户在批次详情页逐行确认或整批确认，确认后数据写入 t_data_rows" },
              ]}
            />
            <Text strong style={{ display: "block", marginTop: 16 }}>字段映射是什么？</Text>
            <p>字段映射定义了 Excel 表头列 → 系统字段（category, amount, unit_price 等）的对应关系，同时指定数据转换器（如"元→分"、"中文日期→ISO日期"）。选择正确的映射后系统自动解析数据。</p>
            <Text strong>如何创建映射？</Text>
            <p>在「字段映射管理」页面新建，或从预置的 3 套模板中选择使用。预置映射可复制修改。</p>
          </div>
        ),
      }]} />
    </div>
  );
}
