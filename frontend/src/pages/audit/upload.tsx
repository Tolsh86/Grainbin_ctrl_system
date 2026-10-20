import { useState, useEffect } from "react";
import { Card, Form, Select, Button, Row, Col, InputNumber, Input, message } from "antd";
import { PlusOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { getProjects } from "../../api/projects";
import { getPeriods, createReviewInPeriod } from "../../api/periods";
import type { Period } from "../../api/periods";

export default function AuditUpload() {
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [projects, setProjects] = useState<any[]>([]);
  const [periods, setPeriods] = useState<Period[]>([]);
  const [projectId, setProjectId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getProjects({ page: 1, page_size: 100 }).then((res) => setProjects(res.items)).catch(() => {});
  }, []);

  useEffect(() => {
    if (!projectId) return;
    getPeriods(projectId, { page: 1, page_size: 50 })
      .then((res) => setPeriods(res.items.filter((p) => p.status !== "closed")))
      .catch(() => setPeriods([]));
  }, [projectId]);

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);

      // Build fee_items from form
      const feeItemNames = values.fee_items_str
        ? values.fee_items_str.split("\n").filter((s: string) => s.trim())
        : [];
      const fee_items = feeItemNames.map((name: string) => ({
        item_name: name.trim(),
        payment_ratio: values.payment_ratio || null,
        reported_amount: 0,
        reviewed_amount: 0,
      }));

      const review = await createReviewInPeriod(values.period_id, {
        contract_id: values.contract_id,
        period_id: values.period_id,
        review_type: values.review_type || "施工单位",
        applicant_unit: values.applicant_unit,
        contract_amount: values.contract_amount ? Math.round(values.contract_amount * 100) : 0,
        cumulative_reported_output: values.cumulative_reported_output ? Math.round(values.cumulative_reported_output * 100) : 0,
        fee_items,
        remark: values.remark || null,
      });
      message.success("审核记录创建成功");
      navigate(`/audits/${review.id}`);
    } catch (e: any) {
      if (e?.errorFields) return;
      message.error(e?.response?.data?.detail || "创建失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Card title="手动录入审核记录">
        <Form form={form} layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="project_id" label="项目" rules={[{ required: true }]}>
                <Select placeholder="选择项目"
                  onChange={(v) => setProjectId(v)}
                  options={projects.map((p) => ({ value: p.id, label: p.project_name }))} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="period_id" label="所属期次" rules={[{ required: true }]}>
                <Select placeholder="选择期次"
                  options={periods.map((p) => ({
                    value: p.id,
                    label: `第${p.period_no}期 · ${p.period_month} · ${statusText(p.status)}`,
                  }))} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="review_type" label="审核类型" rules={[{ required: true }]}>
                <Select options={[
                  { value: "施工", label: "施工单位" },
                  { value: "设备", label: "设备单位" },
                  { value: "设计", label: "设计单位" },
                  { value: "监理过控", label: "监理过控" },
                ]} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="applicant_unit" label="申请单位" rules={[{ required: true }]}>
                <Select placeholder="输入供应商名称"
                  mode="tags" maxCount={1}
                  options={[]} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="contract_id" label="关联合同" rules={[{ required: true }]}>
                <Select placeholder="选择合同" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="contract_amount" label="合同金额(元)">
                <InputNumber style={{ width: "100%" }} min={0} placeholder="0" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="cumulative_reported_output" label="累计报送产值(元)">
                <InputNumber style={{ width: "100%" }} min={0} placeholder="0" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="payment_ratio" label="付款比例">
                <InputNumber style={{ width: "100%" }} min={0} max={1} step={0.01} placeholder="0.2 = 20%" />
              </Form.Item>
            </Col>
            <Col span={24}>
              <Form.Item name="fee_items_str" label="费用分项（每行一个分项名称）"
                tooltip="每行输入一个费用分项名称，如：建筑安装工程费">
                <Input.TextArea rows={4} placeholder={"建筑安装工程费\n安全文明施工费"} />
              </Form.Item>
            </Col>
            <Col span={24}>
              <Form.Item name="remark" label="备注">
                <Input.TextArea rows={2} />
              </Form.Item>
            </Col>
          </Row>
        </Form>
        <div style={{ marginTop: 24, textAlign: "right" }}>
          <Button type="primary" size="large" icon={<PlusOutlined />} onClick={handleSubmit} loading={loading}>提交审核</Button>
        </div>
      </Card>
    </div>
  );
}

function statusText(s: string): string {
  const map: Record<string, string> = { draft: "草稿", in_progress: "进行中", reviewed: "已审核", closed: "已关闭" };
  return map[s] || s;
}
