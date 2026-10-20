import { useState, useEffect, useCallback, useMemo } from "react";
import {
  Card, Table, Tag, Button, Space, Row, Col, Select, DatePicker,
  message, Statistic, Divider, Tooltip, Modal, Typography, Tabs,
} from "antd";
import {
  RollbackOutlined, FileExcelOutlined, FundOutlined, WalletOutlined,
} from "@ant-design/icons";
import dayjs, { Dayjs } from "dayjs";
import { getProjects } from "../../api/projects";
import {
  getMonthlyList, revokeMonthlyDetail, getMonthlyExportUrl,
} from "../../api/monthly";
import type {
  MonthlyListResponse, MonthlyContractItem, MonthlyListGroup,
} from "../../api/monthly";

const { Text } = Typography;

const fenToWanStr = (fen: number | null | undefined): string => {
  if (fen == null || fen === 0) return "0.0000";
  return (fen / 1000000).toLocaleString("zh-CN", {
    minimumFractionDigits: 4, maximumFractionDigits: 4,
  });
};

const pctStr = (ratio: number | null | undefined): string => {
  if (ratio == null) return "—";
  return `${(ratio * 100).toFixed(2)}%`;
};

const reviewModeLabels: Record<string, { color: string; text: string }> = {
  daily_aggregate: { color: "blue", text: "建安费用" },
  node_judge: { color: "green", text: "二类费用" },
  none: { color: "default", text: "无产值" },
};

const sourceLabels: Record<string, { color: string; text: string }> = {
  auto: { color: "default", text: "系统汇总" },
  manual: { color: "blue", text: "人工审定" },
};

const statusLabels: Record<string, { color: string; text: string }> = {
  pending: { color: "orange", text: "待确认" },
  confirmed: { color: "green", text: "已确认" },
};

export default function MonthlyLedger() {
  const [projects, setProjects] = useState<any[]>([]);
  const [projectId, setProjectId] = useState<string | null>(null);
  const [month, setMonth] = useState<Dayjs | null>(null);

  const [data, setData] = useState<MonthlyListResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [revoking, setRevoking] = useState<string | null>(null);

  useEffect(() => {
    getProjects({ page: 1, page_size: 100 })
      .then((res) => {
        const list = res.items ?? res ?? [];
        setProjects(list);
        if (list.length > 0 && !projectId) setProjectId(list[0].id);
      })
      .catch(() => {});
  }, []);

  const monthParam = month ? month.format("YYYY-MM") : undefined;
  useEffect(() => {
    if (!projectId) return;
    setLoading(true);
    getMonthlyList(projectId, monthParam)
      .then(setData)
      .catch(() => message.error("加载台账失败"))
      .finally(() => setLoading(false));
  }, [projectId, monthParam]);

  const handleExport = useCallback(() => {
    if (!projectId) return;
    const token = localStorage.getItem("access_token");
    const url = getMonthlyExportUrl(projectId);
    const xhr = new XMLHttpRequest();
    xhr.open("GET", import.meta.env.BASE_URL + url.slice(1), true);
    xhr.responseType = "blob";
    xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    xhr.onload = () => {
      if (xhr.status === 200) {
        const blob = xhr.response;
        const disposition = xhr.getResponseHeader("Content-Disposition") || "";
        const match = disposition.match(/filename=(.+)/);
        const filename = match ? match[1] : `台账_${monthParam || "全部"}.xlsx`;
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = downloadUrl;
        a.download = filename;
        a.click();
        window.URL.revokeObjectURL(downloadUrl);
        message.success("导出成功");
      } else { message.error("导出失败"); }
    };
    xhr.onerror = () => message.error("导出失败");
    xhr.send();
  }, [projectId, monthParam]);

  // ── Revoke function ──
  const handleRevoke = useCallback(async (detailId: string) => {
    Modal.confirm({
      title: "确认撤回",
      content: "撤回后该合同对应的审核数据将重新变为待审状态，审核工作台可重新编辑并确认。",
      okText: "确认撤回", cancelText: "取消", okButtonProps: { danger: true },
      onOk: async () => {
        setRevoking(detailId);
        try {
          await revokeMonthlyDetail(detailId);
          message.success("已撤回，审核工作台可重新审定");
          if (projectId) {
            const fresh = await getMonthlyList(projectId, monthParam);
            setData(fresh);
          }
        } catch { message.error("撤回失败"); }
        finally { setRevoking(null); }
      },
    });
  }, [projectId, monthParam]);

  const allContracts = useMemo<MonthlyContractItem[]>(() => {
    if (!data?.groups) return [];
    return data.groups.flatMap((g) => g.contracts);
  }, [data]);

  // ── Separate by ledger type ──
  const constructionContracts = useMemo(
    () => allContracts.filter((c) => c.ledger_group === "construction"),
    [allContracts],
  );
  const secondaryContracts = useMemo(
    () => allContracts.filter((c) => c.ledger_group === "equipment" || c.ledger_group === "service"),
    [allContracts],
  );

  // Stats
  const constructionOutput = constructionContracts.reduce((s, c) => s + (c.monthly_output || 0), 0);
  const constructionPayable = constructionContracts.reduce((s, c) => s + (c.monthly_payable || 0), 0);
  const secondaryOutput = secondaryContracts.reduce((s, c) => s + (c.monthly_output || 0), 0);
  const secondaryPayable = secondaryContracts.reduce((s, c) => s + (c.monthly_payable || 0), 0);
  const totalMonthlyOutput = allContracts.reduce((s, c) => s + (c.monthly_output || 0), 0);
  const totalMonthlyPayable = allContracts.reduce((s, c) => s + (c.monthly_payable || 0), 0);
  const confirmedCount = allContracts.filter((c) => c.status === "confirmed").length;

  // ── Group contracts by contract_group for table rendering ──
  const groupedContracts = useMemo(() => {
    if (!data?.groups) return [];
    const map: Record<string, MonthlyContractItem[]> = {};
    for (const g of data.groups) {
      for (const c of g.contracts) {
        const grp = c.contract_group || "__ungrouped__";
        if (!map[grp]) map[grp] = [];
        map[grp].push(c);
      }
    }
    return Object.entries(map)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([group, contracts]) => ({ group, contracts }));
  }, [data]);

  const columns = [
    { title: "#", width: 40, render: (_: any, __: any, i: number) => i + 1 },
    { title: "合同编号", dataIndex: "contract_no", key: "no", width: 90 },
    {
      title: "供应商", dataIndex: "supplier_name", key: "supplier", width: 140, ellipsis: true,
      render: (v: string) => <Tooltip title={v}><span>{v || "—"}</span></Tooltip>,
    },
    {
      title: "审核模式", dataIndex: "review_mode", key: "reviewMode", width: 70,
      render: (v: string) => {
        const m = reviewModeLabels[v] ?? { color: "default", text: v ?? "—" };
        return <Tag color={m.color}>{m.text}</Tag>;
      },
    },
    {
      title: "合同金额(万元)", dataIndex: "contract_amount", key: "amount", width: 130, align: "right" as const,
      render: (v: number | null) => fenToWanStr(v),
    },
    {
      title: "本月产值(万元)", dataIndex: "monthly_output", key: "mOutput", width: 130, align: "right" as const,
      render: (v: number) => <span style={{ color: v > 0 ? "#1677ff" : "#999" }}>{fenToWanStr(v)}</span>,
    },
    {
      title: "本月应付(万元)", dataIndex: "monthly_payable", key: "mPayable", width: 130, align: "right" as const,
      render: (v: number) => <span style={{ color: v > 0 ? "#cf1322" : "#999" }}>{fenToWanStr(v)}</span>,
    },
    {
      title: "累计产值(万元)", dataIndex: "cumulative_output", key: "cOutput", width: 130, align: "right" as const,
      render: (v: number) => <span>{fenToWanStr(v)}</span>,
    },
    {
      title: "累计应付(万元)", dataIndex: "cumulative_payable", key: "cPayable", width: 130, align: "right" as const,
      render: (v: number) => <span>{fenToWanStr(v)}</span>,
    },
    {
      title: "已完比例", dataIndex: "completed_ratio", key: "ratio", width: 90, align: "right" as const,
      render: (v: number | null) => pctStr(v),
    },
    {
      title: "来源", dataIndex: "source", key: "source", width: 80,
      render: (v: string) => {
        const s = sourceLabels[v] ?? { color: "default", text: v ?? "—" };
        return <Tag color={s.color}>{s.text}</Tag>;
      },
    },
    {
      title: "状态", dataIndex: "status", key: "status", width: 80,
      render: (v: string) => {
        const s = statusLabels[v] ?? { color: "default", text: v ?? "—" };
        return <Tag color={s.color}>{s.text}</Tag>;
      },
    },
    {
      title: "操作", key: "op", width: 100, fixed: "right" as const,
      render: (_: any, r: MonthlyContractItem) => {
        const canRevoke = r.source === "manual" && r.status === "confirmed" && r.detail_id;
        if (!canRevoke) return <span style={{ color: "#ccc" }}>—</span>;
        return (
          <Button size="small" danger icon={<RollbackOutlined />}
            loading={revoking === r.detail_id} onClick={() => handleRevoke(r.detail_id!)}>
            撤回
          </Button>
        );
      },
    },
  ];

  const renderTable = (contracts: MonthlyContractItem[]) => (
    <div>
      {groupedContracts.map(({ group, contracts: groupContracts }) => {
        const groupName = group === "__ungrouped__" ? "未分组" : group;
        const filtered = contracts.length === allContracts.length ? groupContracts : groupContracts.filter(
          (gc) => contracts.some((c) => c.contract_id === gc.contract_id)
        );
        if (filtered.length === 0) return null;
        const gMonthly = filtered.reduce((s, c) => s + (c.monthly_output || 0), 0);
        const gCumulative = filtered.reduce((s, c) => s + (c.cumulative_output || 0), 0);
        const gPayable = filtered.reduce((s, c) => s + (c.monthly_payable || 0), 0);
        const gCumPayable = filtered.reduce((s, c) => s + (c.cumulative_payable || 0), 0);

        return (
          <div key={group} style={{ marginBottom: 16 }}>
            <Divider orientation="left" style={{ fontSize: 14, fontWeight: 600, margin: "8px 0 12px" }}>
              {groupName}
              <span style={{ fontSize: 12, color: "#999", fontWeight: 400, marginLeft: 8 }}>
                {filtered.length} 份合同
              </span>
            </Divider>
            <Table size="small" rowKey="contract_id" columns={columns} dataSource={filtered}
              loading={loading} pagination={false} scroll={{ x: 1380 }}
              summary={() => (
                <Table.Summary fixed>
                  <Table.Summary.Row style={{ fontWeight: 700, background: "#fafafa" }}>
                    <Table.Summary.Cell index={0} colSpan={4} align="right">{groupName} 小计</Table.Summary.Cell>
                    <Table.Summary.Cell index={1} align="right">—</Table.Summary.Cell>
                    <Table.Summary.Cell index={2} align="right">{fenToWanStr(gMonthly)}</Table.Summary.Cell>
                    <Table.Summary.Cell index={3} align="right">{fenToWanStr(gPayable)}</Table.Summary.Cell>
                    <Table.Summary.Cell index={4} align="right">{fenToWanStr(gCumulative)}</Table.Summary.Cell>
                    <Table.Summary.Cell index={5} align="right">{fenToWanStr(gCumPayable)}</Table.Summary.Cell>
                    <Table.Summary.Cell index={6} align="right">—</Table.Summary.Cell>
                    <Table.Summary.Cell index={7} /><Table.Summary.Cell index={8} /><Table.Summary.Cell index={9} />
                  </Table.Summary.Row>
                </Table.Summary>
              )}
            />
          </div>
        );
      })}
      {(!data || data.groups.length === 0) && !loading && (
        <div style={{ textAlign: "center", padding: 40, color: "#999" }}>暂无台账数据</div>
      )}
    </div>
  );

  return (
    <div>
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={16} align="middle">
          <Col>
            <span style={{ marginRight: 8 }}>项目：</span>
            <Select style={{ width: 260 }} value={projectId} onChange={setProjectId}
              options={projects.map((p) => ({ value: p.id, label: p.project_name }))} />
          </Col>
          <Col>
            <span style={{ marginRight: 8 }}>月份：</span>
            <DatePicker picker="month" value={month} onChange={setMonth} allowClear
              placeholder="全部月份" style={{ width: 160 }} />
          </Col>
          <Col flex="auto" />
          <Col>
            <Button icon={<FileExcelOutlined />} onClick={handleExport}
              disabled={!projectId} type="primary" ghost>导出 Excel</Button>
          </Col>
        </Row>
      </Card>

      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={6}>
          <Card size="small">
            <Statistic title="建安费用" value={fenToWanStr(constructionOutput)} suffix=" 万元"
              valueStyle={{ color: "#1677ff" }} prefix={<FundOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card size="small">
            <Statistic title="二类费用" value={fenToWanStr(secondaryOutput)} suffix=" 万元"
              valueStyle={{ color: "#52c41a" }} prefix={<WalletOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card size="small">
            <Statistic title="本月应付合计" value={fenToWanStr(totalMonthlyPayable)} suffix=" 万元"
              valueStyle={{ color: "#cf1322" }} />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card size="small">
            <Statistic title="已确认" value={`${confirmedCount} / ${allContracts.length}`}
              valueStyle={{ color: "#722ed1" }} />
          </Card>
        </Col>
      </Row>

      <Card title="月度台账">
        <Tabs
          items={[
            {
              key: "all",
              label: `全部 (${allContracts.length})`,
              children: renderTable(allContracts),
            },
            {
              key: "construction",
              label: <span><FundOutlined /> 建安费用 ({constructionContracts.length})</span>,
              children: renderTable(constructionContracts),
            },
            {
              key: "secondary",
              label: <span><WalletOutlined /> 二类费用 ({secondaryContracts.length})</span>,
              children: renderTable(secondaryContracts),
            },
          ]}
        />
      </Card>
    </div>
  );
}
