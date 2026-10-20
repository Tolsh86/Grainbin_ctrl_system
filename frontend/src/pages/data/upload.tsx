import { useState, useEffect } from "react";
import { Card, Select, DatePicker, Upload, Button, Table, message, Collapse, Space, Alert, Row, Col, Steps, Typography } from "antd";
import { InboxOutlined, UploadOutlined, SettingOutlined, FileExcelOutlined, CheckCircleOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { getProjects, type ProjectResponse } from "../../api/projects";
import { getFieldMappings, uploadAndCreateBatch, parseBatch } from "../../api/data";

const { Dragger } = Upload;
const { RangePicker } = DatePicker;
const { Text } = Typography;

export default function DataUpload() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<ProjectResponse[]>([]);
  const [mappings, setMappings] = useState<any[]>([]);
  const [project, setProject] = useState<string>("");
  const [mappingId, setMappingId] = useState<string>("");
  const [dates, setDates] = useState<[any, any] | null>(null);
  const [fileList, setFileList] = useState<Array<{ name: string; size: number; uid: string; raw: File }>>([]);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    getProjects({ page: 1, page_size: 100 }).then((res) => setProjects(res.items)).catch(() => {});
    getFieldMappings({ page: 1, page_size: 100 }).then((res) => setMappings(res.items)).catch(() => {});
  }, []);

  const uploadProps = {
    name: "file",
    multiple: true,
    accept: ".xlsx,.xls,.csv",
    beforeUpload: (file: File & { uid: string }) => {
      if (fileList.length >= 20) { message.error("单批次最多20个文件"); return Upload.LIST_IGNORE; }
      if (file.size > 50 * 1024 * 1024) { message.error(`${file.name} 超过50MB限制`); return Upload.LIST_IGNORE; }
      setFileList((prev) => [...prev, { name: file.name, size: file.size, uid: file.uid, raw: file }]);
      return false;
    },
    onRemove: (file: { uid: string }) => { setFileList((prev) => prev.filter((f) => f.uid !== file.uid)); },
    fileList: fileList as never[],
  } as const;

  const handleUpload = async () => {
    if (!project) { message.warning("请选择项目"); return; }
    if (fileList.length === 0) { message.warning("请上传文件"); return; }
    setUploading(true);
    try {
      const params: any = {};
      if (mappingId) params.mapping_id = mappingId;
      const batch = await uploadAndCreateBatch(project, fileList[0].raw, params);
      message.success(`批次创建成功，正在解析中`);
      // 触发异步解析
      parseBatch(batch.id).catch(() => {});
      navigate(`/data/batches/${batch.id}`);
    } catch (e: any) {
      message.error(e?.response?.data?.detail || "上传失败");
    } finally {
      setUploading(false);
    }
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
        <div style={{ marginBottom: 20, padding: 16, background: "#f6f8fa", borderRadius: 8 }}>
          <Text strong style={{ fontSize: 14, marginBottom: 12, display: "block" }}>上传前配置</Text>
          <Row gutter={16}>
            <Col xs={24} sm={12} lg={8}>
              <div style={{ marginBottom: 4, fontWeight: 500 }}>关联项目 <span style={{ color: "#ff4d4f" }}>*</span></div>
              <Select value={project || undefined} onChange={setProject} style={{ width: "100%" }} placeholder="选择项目"
                options={projects.map((p) => ({ value: p.id, label: p.project_name }))} />
            </Col>
            <Col xs={24} sm={12} lg={8}>
              <div style={{ marginBottom: 4, fontWeight: 500 }}>起止日期</div>
              <RangePicker style={{ width: "100%" }} value={dates} onChange={setDates} />
            </Col>
            <Col xs={24} sm={12} lg={8}>
              <div style={{ marginBottom: 4, fontWeight: 500 }}>字段映射</div>
              <Select value={mappingId || undefined} onChange={setMappingId} style={{ width: "100%" }} placeholder="自动识别" allowClear
                options={mappings.map((m) => ({ value: m.id, label: m.mapping_name }))} />
            </Col>
          </Row>
        </div>

        <Dragger {...uploadProps} style={{ marginBottom: 16 }} disabled={uploading}>
          <p className="ant-upload-drag-icon"><InboxOutlined /></p>
          <p className="ant-upload-text" style={{ fontSize: 16 }}>拖拽文件到此处，或 <Text style={{ color: "#1677ff" }}>点击选择</Text></p>
          <p className="ant-upload-hint">支持 .xlsx / .xls / .csv 格式，单文件 ≤ 50MB</p>
        </Dragger>

        {fileList.length > 0 && (
          <Card title={`已选文件（${fileList.length} 个）`} size="small" style={{ marginBottom: 16 }}>
            {fileList.map((f, i) => (
              <Row key={f.uid} style={{ padding: "4px 0", borderBottom: i < fileList.length - 1 ? "1px solid #f0f0f0" : "none" }}
                justify="space-between" align="middle">
                <Col><FileExcelOutlined style={{ color: "#52c41a", marginRight: 8 }} />{f.name}</Col>
                <Col><Text type="secondary" style={{ fontSize: 12 }}>{formatSize(f.size)}</Text></Col>
              </Row>
            ))}
          </Card>
        )}

        <Button type="primary" size="large" icon={<UploadOutlined />} onClick={handleUpload}
          disabled={fileList.length === 0} loading={uploading} block>
          {fileList.length > 0 ? `开始上传（${fileList.length} 个文件）` : "请先选择文件"}
        </Button>
      </Card>

      <Collapse style={{ marginTop: 16 }} items={[{
        key: "tips", label: <Space><CheckCircleOutlined style={{ color: "#1677ff" }} />使用提示与数据处理流程</Space>,
        children: (
          <div style={{ fontSize: 13, lineHeight: 2.2 }}>
            <Steps size="small" direction="vertical" current={-1} style={{ marginTop: 8 }}
              items={[
                { title: "上传", description: "文件上传至 MinIO 对象存储，创建批次（status=pending）" },
                { title: "解析", description: "Celery 异步读取 Excel，识别表头和数据类型" },
                { title: "归一化+校验", description: "统一格式转换 + 5类校验规则（必填/范围/唯一/格式/逻辑）" },
                { title: "人工确认", description: "在批次详情页逐行检查或整批确认，确认后数据写入 t_data_rows" },
              ]} />
          </div>
        ),
      }]} />
    </div>
  );
}
