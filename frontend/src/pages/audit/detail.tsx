import { useState, useEffect } from "react";
import { Card, Row, Col, Descriptions, Tag, Button, Space, message, Spin, Table, Statistic, Divider } from "antd";
import { ArrowLeftOutlined, CheckCircleOutlined } from "@ant-design/icons";
import { useNavigate, useParams } from "react-router-dom";
import { getReview, updateReviewStatus, type Review, type ReviewFeeItem } from "../../api/reviews";

const fenToWanStr = (fen: number | null | undefined): string => {
  if (fen == null || fen === 0) return "0.0000";
  return (fen / 1000000).toLocaleString("zh-CN", { minimumFractionDigits: 4, maximumFractionDigits: 4 });
};

const statusMap: Record<string, { color: string; text: string }> = {
  draft: { color: "default", text: "草稿" },
  submitted: { color: "blue", text: "已报送" },
  reviewed: { color: "green", text: "已审定" },
};

export default function AuditDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [review, setReview] = useState<Review | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    getReview(id)
      .then(setReview)
      .catch(() => message.error("加载审核详情失败"))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <Spin style={{ display: "block", marginTop: 80 }} />;
  if (!review) return <Card><p>审核不存在</p><Button onClick={() => navigate("/audits")}>返回</Button></Card>;

  const handleSubmit = async () => {
    try {
      const updated = await updateReviewStatus(review.id, { audit_status: "submitted" });
      setReview(updated);
      message.success("已报送");
    } catch (e: any) { message.error(e?.response?.data?.detail || "操作失败"); }
  };

  const handleConfirm = async () => {
    try {
      const updated = await updateReviewStatus(review.id, { audit_status: "reviewed" });
      setReview(updated);
      message.success("已确认审定，已写入月度台账");
    } catch (e: any) { message.error(e?.response?.data?.detail || "操作失败"); }
  };

  const s = statusMap[review.audit_status] || { color: "default", text: review.audit_status };

  // Calculate totals from fee_items
  let totalReported = 0, totalReviewed = 0, totalPayable = 0;
  (review.fee_items || []).forEach((fi) => {
    totalReported += fi.reported_amount || 0;
    totalReviewed += fi.reviewed_amount || 0;
    totalPayable += (fi.reviewed_amount || 0) * (fi.payment_ratio || 0);
  });

  return (
    <div>
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Space>
              <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate("/audits")}>返回</Button>
              <span style={{ fontSize: 16, fontWeight: 600 }}>{review.review_type}</span>
              <Tag color={s.color}>{s.text}</Tag>
            </Space>
          </Col>
          <Col>
            <Space>
              {review.audit_status === "draft" && (
                <Button type="primary" icon={<CheckCircleOutlined />} onClick={handleSubmit}>报送审核</Button>
              )}
              {review.audit_status === "submitted" && (
                <Button type="primary" icon={<CheckCircleOutlined />} onClick={handleConfirm}>确认审定</Button>
              )}
            </Space>
          </Col>
        </Row>
      </Card>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title="基本信息" size="small">
            <Descriptions bordered size="small" column={1}>
              <Descriptions.Item label="审核类型">{review.review_type}</Descriptions.Item>
              <Descriptions.Item label="申请单位">{review.applicant_unit}</Descriptions.Item>
              <Descriptions.Item label="申报日期">{review.submit_date || "—"}</Descriptions.Item>
              <Descriptions.Item label="税率">{review.tax_rate != null ? `${review.tax_rate}%` : "—"}</Descriptions.Item>
              <Descriptions.Item label="备注">{review.remark || "—"}</Descriptions.Item>
            </Descriptions>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title="金额汇总" size="small">
            <Row gutter={16}>
              <Col span={12}><Statistic title="合同金额(万元)" value={fenToWanStr(review.contract_amount)} /></Col>
              <Col span={12}><Statistic title="累计报送产值(万元)" value={fenToWanStr(review.cumulative_reported_output)} /></Col>
            </Row>
            <Divider style={{ margin: "12px 0" }} />
            <Row gutter={16}>
              <Col span={8}><Statistic title="报送合计" value={fenToWanStr(totalReported)} /></Col>
              <Col span={8}><Statistic title="审定合计" value={fenToWanStr(totalReviewed)} valueStyle={{ color: "#1677ff" }} /></Col>
              <Col span={8}><Statistic title="应付合计" value={fenToWanStr(totalPayable)} valueStyle={{ color: "#cf1322" }} /></Col>
            </Row>
          </Card>
        </Col>
      </Row>

      {/* Fee items detail */}
      <Card title="费用分项明细" size="small" style={{ marginTop: 16 }}>
        <Table
          size="small"
          rowKey="id"
          pagination={false}
          dataSource={review.fee_items || []}
          columns={[
            { title: "分项名称", dataIndex: "item_name", width: 150 },
            {
              title: "付款比例", dataIndex: "payment_ratio", width: 100, align: "center" as const,
              render: (v: number | null) => v != null ? `${(v * 100).toFixed(1)}%` : "—",
            },
            { title: "报送金额(万元)", dataIndex: "reported_amount", width: 130, align: "right" as const,
              render: (v: number | null) => fenToWanStr(v) },
            { title: "审定金额(万元)", dataIndex: "reviewed_amount", width: 130, align: "right" as const,
              render: (v: number | null) => <span style={{ fontWeight: 600, color: "#1677ff" }}>{fenToWanStr(v)}</span> },
            {
              title: "应付金额(万元)", key: "payable", width: 130, align: "right" as const,
              render: (_: any, fi: ReviewFeeItem) => {
                const p = (fi.reviewed_amount || 0) * (fi.payment_ratio || 0);
                return <span style={{ color: "#cf1322", fontWeight: 600 }}>{fenToWanStr(p)}</span>;
              },
            },
            { title: "备注", dataIndex: "remark", ellipsis: true,
              render: (v: string | null) => v || "—" },
          ]}
          summary={() => (
            <Table.Summary fixed>
              <Table.Summary.Row style={{ fontWeight: 700 }}>
                <Table.Summary.Cell index={0} align="right" colSpan={2}>合计</Table.Summary.Cell>
                <Table.Summary.Cell index={1} align="right">{fenToWanStr(totalReported)}</Table.Summary.Cell>
                <Table.Summary.Cell index={2} align="right">
                  <span style={{ color: "#1677ff" }}>{fenToWanStr(totalReviewed)}</span>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={3} align="right">
                  <span style={{ color: "#cf1322" }}>{fenToWanStr(totalPayable)}</span>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={4} />
              </Table.Summary.Row>
            </Table.Summary>
          )}
        />
      </Card>
    </div>
  );
}
