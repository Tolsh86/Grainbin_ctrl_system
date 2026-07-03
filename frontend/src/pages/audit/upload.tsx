import { useState } from "react";
import { Card, Form, Select, Input, Button, Upload, Row, Col, InputNumber, message } from "antd";
import { InboxOutlined, UploadOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";

const { Dragger } = Upload;

export default function AuditUpload() {
  const navigate = useNavigate();
  const [form] = Form.useForm();

  const handleSubmit = () => {
    form.validateFields().then(() => {
      message.loading("正在创建审核并启动 AI 审核引擎...", 2, () => {
        message.success("审核创建成功，AI 正在分析中");
        navigate("/audits/3");
      });
    });
  };

  return (
    <div>
      <Card title="新进度款审核上传">
        <Row gutter={24}>
          <Col span={12}>
            <Form form={form} layout="vertical">
              <Form.Item name="project" label="项目" rules={[{ required: true }]}>
                <Select options={[{ value: "p1", label: "1-6号粮仓新建工程" }, { value: "p2", label: "7-12号粮仓改造工程" }]} />
              </Form.Item>
              <Form.Item name="contract" label="合同" rules={[{ required: true }]}>
                <Select options={[{ value: "c1", label: "施工总承包合同 (V3)" }]} />
              </Form.Item>
              <Form.Item name="period" label="期次" rules={[{ required: true }]}>
                <Select options={[{ value: "13", label: "第13期（自增）" }]} />
              </Form.Item>
              <Form.Item name="constructor" label="施工单位" rules={[{ required: true }]}>
                <Input defaultValue="中建三局" />
              </Form.Item>
              <Row gutter={12}>
                <Col span={12}><Form.Item name="apply_amount" label="申报金额(元)" rules={[{ required: true }]}><InputNumber style={{ width: "100%" }} min={0} /></Form.Item></Col>
                <Col span={12}><Form.Item name="submit_date" label="提交日期"><Input /></Form.Item></Col>
              </Row>
            </Form>
          </Col>
          <Col span={12}>
            <div style={{ marginBottom: 8, fontWeight: 500 }}>文件上传 <span style={{ color: "#ff4d4f" }}>*</span></div>
            <Dragger action="#" customRequest={({ onSuccess }) => setTimeout(() => (onSuccess as (v: string) => void)?.("ok"), 500)} style={{ marginBottom: 12 }}>
              <p className="ant-upload-drag-icon"><InboxOutlined /></p>
              <p className="ant-upload-text">上传工程量清单 Excel</p>
              <p className="ant-upload-hint">必传。支持 .xlsx / .xls</p>
            </Dragger>
            <Dragger action="#" customRequest={({ onSuccess }) => setTimeout(() => (onSuccess as (v: string) => void)?.("ok"), 500)}>
              <p className="ant-upload-drag-icon"><InboxOutlined /></p>
              <p className="ant-upload-text">合同扫描件 / 签证资料</p>
              <p className="ant-upload-hint">选传。支持 PDF / 图片</p>
            </Dragger>
          </Col>
        </Row>
        <div style={{ marginTop: 24, textAlign: "right" }}>
          <Button type="primary" size="large" icon={<UploadOutlined />} onClick={handleSubmit}>提交审核（AI 自动分析）</Button>
        </div>
      </Card>
    </div>
  );
}