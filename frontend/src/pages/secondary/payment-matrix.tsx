import { useState, useEffect, useCallback, useMemo, createContext, useContext, memo } from "react";
import {
  Card, Select, Tag, Badge, Collapse, message, Spin, Empty,
  Typography, Row, Col, Statistic, Divider, Tooltip,
} from "antd";
import {
  CheckCircleFilled, CalendarOutlined, LeftOutlined, RightOutlined,
  BankOutlined, FileTextOutlined, DollarOutlined,
  NodeIndexOutlined, ProjectOutlined,
} from "@ant-design/icons";
import dayjs from "dayjs";
import { getProjects } from "../../api/projects";
import { getPaymentMatrix } from "../../api/payment-matrix";
import type { PaymentMatrixResponse, PaymentMatrixGroup, PaymentMatrixContract, PaymentMatrixNode } from "../../api/payment-matrix";

const { Text, Title } = Typography;

// ═══════════════════════════════════════════════════════════════════
// 金额/展示工具
// ═══════════════════════════════════════════════════════════════════

/** 分 → 万元字符串 */
const fenToWanStr = (fen: number | null | undefined): string => {
  if (fen == null || fen === 0) return "0.0000";
  return (fen / 1000000).toLocaleString("zh-CN", {
    minimumFractionDigits: 4,
    maximumFractionDigits: 4,
  });
};

/** 元 → 万元字符串 */
const yuanToWanStr = (yuan: number): string => {
  return (yuan / 10000).toLocaleString("zh-CN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
};

// review_mode 标签映射
const reviewModeLabels: Record<string, { color: string; text: string }> = {
  daily_aggregate: { color: "blue", text: "日报聚合" },
  node_judge: { color: "green", text: "节点判断" },
  none: { color: "default", text: "无产值" },
};

const reviewModeAccent: Record<string, string> = {
  daily_aggregate: "#1677ff",
  node_judge: "#52c41a",
  none: "#d9d9d9",
};

// ═══════════════════════════════════════════════════════════════════
// Context – 选中月份，跨层级驱动高亮
// ═══════════════════════════════════════════════════════════════════

const SelectedMonthContext = createContext<string | null>(null);

// ═══════════════════════════════════════════════════════════════════
// Style constants
// ═══════════════════════════════════════════════════════════════════

const MONTH_CELL_WIDTH = 100;
const MONTH_CELL_HEIGHT = 72;

// ═══════════════════════════════════════════════════════════════════
// MonthCell – 月度卡片
// ═══════════════════════════════════════════════════════════════════

interface MonthCellProps {
  month: string;
  total: number;
  isSelected: boolean;
  isCurrentMonth: boolean;
  hasData: boolean;
  onClick: (month: string) => void;
}

const MonthCell = memo(({ month, total, isSelected, isCurrentMonth, hasData, onClick }: MonthCellProps) => {
  const m = dayjs(month + "-01");
  const label = m.format("M月");
  const isFuture = m.isAfter(dayjs(), "month");

  return (
    <div
      onClick={() => !isFuture && onClick(month)}
      style={{
        flex: "0 0 auto",
        width: MONTH_CELL_WIDTH,
        height: MONTH_CELL_HEIGHT,
        padding: "10px 6px",
        borderRadius: 12,
        border: isSelected
          ? "1.5px solid #1677ff"
          : isCurrentMonth
            ? "1.5px solid #91caff"
            : "1.5px solid #e8e8e8",
        background: isSelected
          ? "linear-gradient(135deg, #1677ff 0%, #4096ff 100%)"
          : isCurrentMonth
            ? "#f0f5ff"
            : "#fafafa",
        cursor: isFuture ? "not-allowed" : "pointer",
        textAlign: "center",
        transition: "all 0.25s cubic-bezier(0.4, 0, 0.2, 1)",
        userSelect: "none",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        position: "relative",
        opacity: isFuture ? 0.45 : 1,
        boxShadow: isSelected
          ? "0 4px 12px rgba(22, 119, 255, 0.3)"
          : "0 1px 3px rgba(0,0,0,0.04)",
      }}
      className="month-cell"
    >
      {/* 有数据的小圆点 */}
      {hasData && !isSelected && (
        <div
          style={{
            position: "absolute",
            top: 6,
            right: 8,
            width: 6,
            height: 6,
            borderRadius: "50%",
            background: "#52c41a",
          }}
        />
      )}

      <div
        style={{
          fontSize: 14,
          fontWeight: 700,
          color: isSelected ? "#fff" : isCurrentMonth ? "#1677ff" : "#333",
          lineHeight: 1.3,
        }}
      >
        {label}
      </div>
      <div
        style={{
          fontSize: 11,
          fontWeight: 500,
          color: isSelected ? "rgba(255,255,255,0.85)" : "#999",
          marginTop: 2,
          fontVariantNumeric: "tabular-nums",
        }}
      >
        {total > 0 ? `${yuanToWanStr(total)}万` : "—"}
      </div>
    </div>
  );
});

// ═══════════════════════════════════════════════════════════════════
// MonthBar – 年份/月份导航条
// ═══════════════════════════════════════════════════════════════════

interface MonthBarProps {
  monthRange: string[];
  monthlyTotals: Record<string, number>;
  selectedMonth: string | null;
  onSelectMonth: (month: string) => void;
}

const MonthBar = memo(({
  monthRange, monthlyTotals, selectedMonth, onSelectMonth,
}: MonthBarProps) => {
  // 提取年份列表
  const years = useMemo(() => {
    const ySet = new Set(monthRange.map((m) => m.split("-")[0]));
    return Array.from(ySet).sort();
  }, [monthRange]);

  const [selectedYear, setSelectedYear] = useState<string>(years[0] || "");

  // 当 monthRange 变化时重置年份选择
  useEffect(() => {
    if (years.length > 0) {
      if (!selectedYear || !years.includes(selectedYear)) {
        setSelectedYear(years[0]);
      }
    }
  }, [years, selectedYear]);

  // 可见月份
  const visibleMonths = useMemo(() => {
    if (!selectedYear) return monthRange;
    return monthRange.filter((m) => m.startsWith(selectedYear));
  }, [monthRange, selectedYear]);

  const yearIndex = selectedYear ? years.indexOf(selectedYear) : -1;

  const goPrevYear = useCallback(() => {
    if (yearIndex > 0) setSelectedYear(years[yearIndex - 1]);
  }, [yearIndex, years]);

  const goNextYear = useCallback(() => {
    if (yearIndex < years.length - 1) setSelectedYear(years[yearIndex + 1]);
  }, [yearIndex, years]);

  const currentMonth = dayjs().format("YYYY-MM");

  // 当前年+选中年合计
  const yearTotalAmount = useMemo(() => {
    return visibleMonths.reduce((sum, m) => sum + (monthlyTotals[m] ?? 0), 0);
  }, [visibleMonths, monthlyTotals]);

  if (!monthRange.length) return null;

  return (
    <Card
      size="small"
      style={{
        marginBottom: 16,
        borderRadius: 12,
        overflow: "hidden",
      }}
      styles={{
        body: { padding: "16px 20px" },
      }}
    >
      {/* 年份切换 + 合计 */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: 16,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          {/* 年份切换器 */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 4,
              background: "#f5f7fa",
              borderRadius: 8,
              padding: "2px 4px",
            }}
          >
            <div
              onClick={goPrevYear}
              style={{
                width: 28,
                height: 28,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                borderRadius: 6,
                cursor: yearIndex <= 0 ? "not-allowed" : "pointer",
                color: yearIndex <= 0 ? "#d9d9d9" : "#666",
                transition: "all 0.2s",
              }}
              className="year-arrow-btn"
            >
              <LeftOutlined style={{ fontSize: 12 }} />
            </div>
            <span
              style={{
                fontSize: 16,
                fontWeight: 700,
                color: "#1a1a2e",
                padding: "0 12px",
                minWidth: 50,
                textAlign: "center",
                fontVariantNumeric: "tabular-nums",
              }}
            >
              {selectedYear}
            </span>
            <div
              onClick={goNextYear}
              style={{
                width: 28,
                height: 28,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                borderRadius: 6,
                cursor: yearIndex >= years.length - 1 ? "not-allowed" : "pointer",
                color: yearIndex >= years.length - 1 ? "#d9d9d9" : "#666",
                transition: "all 0.2s",
              }}
              className="year-arrow-btn"
            >
              <RightOutlined style={{ fontSize: 12 }} />
            </div>
          </div>

          {/* 年份标签 */}
          <div style={{ display: "flex", gap: 4 }}>
            {years.map((y) => (
              <Tag
                key={y}
                color={selectedYear === y ? "blue" : "default"}
                style={{
                  cursor: "pointer",
                  margin: 0,
                  borderRadius: 6,
                  padding: "2px 10px",
                  fontSize: 12,
                  fontWeight: selectedYear === y ? 600 : 400,
                }}
                onClick={() => setSelectedYear(y)}
              >
                {y}年
              </Tag>
            ))}
          </div>
        </div>

        {/* 年度合计 */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            background: "#f6ffed",
            borderRadius: 8,
            padding: "4px 14px",
            border: "1px solid #b7eb8f",
          }}
        >
          <DollarOutlined style={{ color: "#52c41a", fontSize: 14 }} />
          <Text style={{ fontSize: 12, color: "#666" }}>
            {selectedYear}年合计：
          </Text>
          <Text strong style={{ fontSize: 14, color: "#52c41a" }}>
            ¥ {yuanToWanStr(yearTotalAmount)} 万
          </Text>
        </div>
      </div>

      {/* 月份格滚动容器 */}
      <div
        style={{
          display: "flex",
          gap: 10,
          overflowX: "auto",
          paddingBottom: 6,
          margin: "0 -4px",
          padding: "0 4px",
        }}
        className="month-scroll-container"
      >
        {visibleMonths.map((m) => (
          <MonthCell
            key={m}
            month={m}
            total={monthlyTotals[m] ?? 0}
            isSelected={selectedMonth === m}
            isCurrentMonth={m === currentMonth}
            hasData={(monthlyTotals[m] ?? 0) > 0}
            onClick={onSelectMonth}
          />
        ))}
      </div>
    </Card>
  );
});

// ═══════════════════════════════════════════════════════════════════
// NodeTag – 单个节点精美标签
// ═══════════════════════════════════════════════════════════════════

interface NodeTagProps {
  node: PaymentMatrixNode;
  reviewMode: string | null;
}

const NodeTag = memo(({ node, reviewMode }: NodeTagProps) => {
  const selectedMonth = useContext(SelectedMonthContext);

  const isHighlighted =
    selectedMonth != null &&
    node.planned_pay_date != null &&
    node.planned_pay_date.startsWith(selectedMonth);

  const isCompleted = node.is_completed;

  const isNoneMode = reviewMode === "none";
  const amountText = isNoneMode
    ? "—"
    : node.agreed_amount != null && node.agreed_amount > 0
      ? fenToWanStr(node.agreed_amount) + "万"
      : "—";

  const dateText = node.planned_pay_date
    ? dayjs(node.planned_pay_date).format("MM-DD")
    : "—";

  const nameText =
    node.node_name && node.agreed_ratio != null
      ? `${node.node_name} ${(node.agreed_ratio * 100).toFixed(0)}%`
      : node.node_name || node.stage_name || "—";

  // 状态颜色
  const statusColor = isCompleted
    ? "#52c41a"
    : isHighlighted
      ? "#1677ff"
      : "#8c8c8c";

  const bgGradient = isCompleted
    ? "linear-gradient(135deg, #f6ffed 0%, #f0fff0 100%)"
    : isHighlighted
      ? "linear-gradient(135deg, #e6f4ff 0%, #f0f8ff 100%)"
      : "#fafafa";

  const borderColor = isCompleted
    ? "#95de64"
    : isHighlighted
      ? "#91caff"
      : "#f0f0f0";

  return (
    <div
      style={{
        padding: "8px 12px",
        borderRadius: 10,
        background: bgGradient,
        border: `1.5px solid ${borderColor}`,
        display: "inline-flex",
        alignItems: "center",
        gap: 8,
        transition: "all 0.25s ease",
        position: "relative",
        minWidth: 140,
        maxWidth: 200,
      }}
      className="node-tag"
    >
      {/* 左侧状态线 */}
      <div
        style={{
          width: 3,
          height: 32,
          borderRadius: 2,
          background: statusColor,
          flexShrink: 0,
          opacity: isCompleted ? 1 : isHighlighted ? 1 : 0.4,
        }}
      />

      {/* 节点信息 */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div
          style={{
            fontWeight: 600,
            fontSize: 12,
            color: "#1a1a2e",
            lineHeight: 1.4,
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
        >
          {nameText}
        </div>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            marginTop: 2,
          }}
        >
          <span
            style={{
              fontSize: 11,
              fontWeight: 500,
              color: isHighlighted ? "#1677ff" : "#666",
              fontVariantNumeric: "tabular-nums",
            }}
          >
            {amountText}
          </span>
          <span style={{ fontSize: 10, color: "#bbb" }}>|</span>
          <span style={{ fontSize: 11, color: "#999" }}>
            {dateText}
          </span>
        </div>
      </div>

      {/* 完成对勾 */}
      {isCompleted && (
        <CheckCircleFilled
          style={{
            color: "#52c41a",
            fontSize: 16,
            flexShrink: 0,
          }}
        />
      )}
    </div>
  );
});

// ═══════════════════════════════════════════════════════════════════
// ContractCard – 合同卡片
// ═══════════════════════════════════════════════════════════════════

interface ContractCardProps {
  contract: PaymentMatrixContract;
}

const ContractCard = memo(({ contract }: ContractCardProps) => {
  const hasNodes = contract.nodes.length > 0;
  const accentColor = reviewModeAccent[contract.review_mode ?? ""] || "#d9d9d9";
  const modeLabel = contract.review_mode
    ? reviewModeLabels[contract.review_mode] ?? { color: "default", text: contract.review_mode }
    : null;

  return (
    <div
      style={{
        display: "flex",
        gap: 0,
        marginBottom: 10,
        background: "#fff",
        border: "1px solid #f0f0f0",
        borderRadius: 12,
        overflow: "hidden",
        transition: "all 0.2s ease",
      }}
      className="contract-card"
    >
      {/* 左侧颜色条（审核模式） */}
      <div
        style={{
          width: 4,
          background: accentColor,
          flexShrink: 0,
          opacity: 0.7,
        }}
      />

      <div style={{ flex: 1, padding: "14px 16px" }}>
        {/* 合同头部 */}
        <div
          style={{
            display: "flex",
            alignItems: "flex-start",
            justifyContent: "space-between",
            marginBottom: 10,
          }}
        >
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
              <BankOutlined style={{ color: "#1677ff", fontSize: 14 }} />
              <Text strong style={{ fontSize: 13, color: "#1a1a2e" }}>
                {contract.supplier_name || "—"}
              </Text>
              {modeLabel && (
                <Tag color={modeLabel.color} style={{ margin: 0, fontSize: 10, lineHeight: "18px", borderRadius: 4 }}>
                  {modeLabel.text}
                </Tag>
              )}
            </div>
            <Tooltip title={contract.contract_desc}>
              <Text
                style={{
                  fontSize: 12,
                  color: "#666",
                  display: "block",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                  maxWidth: 400,
                }}
              >
                {contract.contract_desc || "—"}
              </Text>
            </Tooltip>
          </div>
          <div
            style={{
              textAlign: "right",
              flexShrink: 0,
              marginLeft: 16,
            }}
          >
            <div style={{ fontSize: 11, color: "#999" }}>合同金额</div>
            <div style={{ fontWeight: 700, fontSize: 14, color: "#cf1322", fontVariantNumeric: "tabular-nums" }}>
              ¥ {contract.contract_amount != null && contract.contract_amount > 0 ? fenToWanStr(contract.contract_amount) : "—"}
              <span style={{ fontSize: 11, fontWeight: 400, color: "#999" }}> 万</span>
            </div>
          </div>
        </div>

        {/* 节点标签区 */}
        {hasNodes ? (
          <div>
            <Divider style={{ margin: "6px 0 8px", borderColor: "#f0f0f0" }} />
            <div
              style={{
                display: "flex",
                flexWrap: "wrap",
                gap: 8,
              }}
            >
              {contract.nodes.map((n, idx) => (
                <NodeTag key={idx} node={n} reviewMode={contract.review_mode} />
              ))}
            </div>
          </div>
        ) : (
          <div style={{ color: "#ccc", fontSize: 12, padding: "4px 0", marginTop: 4 }}>
            {contract.review_mode === "none" ? "无产值（无节点数据）" : "暂无节点数据"}
          </div>
        )}
      </div>
    </div>
  );
});

// ═══════════════════════════════════════════════════════════════════
// ContractGroupList – 合同分组折叠面板
// ═══════════════════════════════════════════════════════════════════

interface ContractGroupListProps {
  groups: PaymentMatrixGroup[];
}

function getGroupDesc(contracts: PaymentMatrixContract[]): string {
  const descs = Array.from(new Set(contracts.map((c) => c.contract_desc).filter(Boolean)));
  if (descs.length === 0) return "—";
  if (descs.length === 1) return descs[0];
  return `${descs[0]} 等${descs.length}项`;
}

function getGroupReviewModes(contracts: PaymentMatrixContract[]): string[] {
  return Array.from(new Set(contracts.map((c) => c.review_mode).filter((m): m is string => m != null)));
}

function buildPanelHeader(group: PaymentMatrixGroup): React.ReactNode {
  const contracts = group.contracts;
  const descText = getGroupDesc(contracts);
  const reviewModes = getGroupReviewModes(contracts);
  const totalNodes = contracts.reduce((s, c) => s + c.nodes.length, 0);

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
        flexWrap: "wrap",
        paddingRight: 8,
        width: "100%",
      }}
    >
      {/* 合同编号徽标 */}
      <div
        style={{
          background: "linear-gradient(135deg, #1677ff 0%, #4096ff 100%)",
          color: "#fff",
          borderRadius: 6,
          padding: "2px 12px",
          fontWeight: 600,
          fontSize: 13,
          lineHeight: "28px",
          whiteSpace: "nowrap",
        }}
      >
        <FileTextOutlined style={{ marginRight: 4 }} />
        {group.contract_no}
      </div>

      {/* 描述 */}
      <Tooltip title={descText}>
        <span
          style={{
            fontSize: 13,
            color: "#666",
            maxWidth: 260,
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
        >
          {descText}
        </span>
      </Tooltip>

      {/* 审核模式标签 */}
      {reviewModes.map((mode) => {
        const m = reviewModeLabels[mode] ?? { color: "default", text: mode };
        return (
          <Tag key={mode} color={m.color} style={{ margin: 0, fontSize: 11, borderRadius: 4 }}>
            {m.text}
          </Tag>
        );
      })}

      {/* 合同/节点计数 */}
      <span style={{ fontSize: 12, color: "#999", whiteSpace: "nowrap" }}>
        {contracts.length} 份合同 · {totalNodes} 个节点
      </span>

      {/* 总额 */}
      <span
        style={{
          marginLeft: "auto",
          fontSize: 14,
          fontWeight: 700,
          color: "#cf1322",
          whiteSpace: "nowrap",
          fontVariantNumeric: "tabular-nums",
        }}
      >
        ¥ {fenToWanStr(group.total_amount)} 万
      </span>
    </div>
  );
}

const ContractGroupList = memo(({ groups }: ContractGroupListProps) => {
  const items = useMemo(() => groups.map((g) => ({
    key: g.contract_no,
    label: buildPanelHeader(g),
    children: g.contracts.map((c) => <ContractCard key={c.contract_id} contract={c} />),
  })), [groups]);

  if (groups.length === 0) {
    return (
      <Empty
        description="暂无合同数据"
        image={Empty.PRESENTED_IMAGE_SIMPLE}
        style={{ marginTop: 60 }}
      />
    );
  }

  return (
    <Collapse
      defaultActiveKey={[]}
      destroyOnHidden
      style={{
        background: "transparent",
        border: "none",
      }}
      expandIconPosition="end"
      items={items}
    />
  );
});

// ═══════════════════════════════════════════════════════════════════
// SelectProjectPrompt – 空状态提示
// ═══════════════════════════════════════════════════════════════════

const SelectProjectPrompt = () => (
  <Card
    style={{
      textAlign: "center",
      borderRadius: 16,
      minHeight: 360,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
    }}
    styles={{ body: { padding: "60px 20px" } }}
  >
    <CalendarOutlined
      style={{
        fontSize: 64,
        color: "#d9d9d9",
        display: "block",
        marginBottom: 24,
      }}
    />
    <Title level={4} type="secondary" style={{ margin: 0, fontWeight: 400 }}>
      请选择一个项目查看月度付款总览
    </Title>
    <Text type="secondary" style={{ fontSize: 13, marginTop: 8, display: "block" }}>
      选择项目后，您可以按年月查看合同付款节点分布
    </Text>
  </Card>
);

// ═══════════════════════════════════════════════════════════════════
// StatsBar – 统计指标栏
// ═══════════════════════════════════════════════════════════════════

interface StatsBarProps {
  groups: PaymentMatrixGroup[];
  selectedMonth: string | null;
  selectedMonthTotal: number;
}

const StatsBar = memo(({ groups, selectedMonth, selectedMonthTotal }: StatsBarProps) => {
  const totalContracts = groups.reduce((s, g) => s + g.contracts.length, 0);
  const totalNodes = groups.reduce((s, g) => s + g.contracts.reduce((s2, c) => s2 + c.nodes.length, 0), 0);
  const totalAmount = groups.reduce((s, g) => s + g.total_amount, 0);
  const completedNodes = groups.reduce(
    (s, g) => s + g.contracts.reduce((s2, c) => s2 + c.nodes.filter((n) => n.is_completed).length, 0),
    0,
  );

  const stats = [
    {
      title: "合同总数",
      value: totalContracts,
      suffix: "份",
      color: "#1677ff",
      icon: <FileTextOutlined />,
    },
    {
      title: "付款节点",
      value: totalNodes,
      suffix: "个",
      color: "#722ed1",
      icon: <NodeIndexOutlined />,
    },
    {
      title: "合同总额",
      value: `¥${fenToWanStr(totalAmount)}`,
      suffix: "万",
      color: "#cf1322",
      icon: <DollarOutlined />,
    },
    {
      title: "已完成节点",
      value: completedNodes,
      suffix: `/${totalNodes}`,
      color: "#52c41a",
      icon: <CheckCircleFilled />,
    },
  ];

  return (
    <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
      {stats.map((s, i) => (
        <Col xs={12} sm={6} key={i}>
          <Card
            size="small"
            style={{
              borderRadius: 10,
              overflow: "hidden",
            }}
            styles={{ body: { padding: "14px 16px" } }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <div
                style={{
                  width: 36,
                  height: 36,
                  borderRadius: 10,
                  background: `${s.color}12`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 18,
                  color: s.color,
                  flexShrink: 0,
                }}
              >
                {s.icon}
              </div>
              <div>
                <div style={{ fontSize: 11, color: "#999", marginBottom: 2 }}>{s.title}</div>
                <div style={{ fontSize: 18, fontWeight: 700, color: s.color, fontVariantNumeric: "tabular-nums", lineHeight: 1.2 }}>
                  {s.value}
                  <span style={{ fontSize: 11, fontWeight: 400, color: "#999", marginLeft: 2 }}>{s.suffix}</span>
                </div>
              </div>
            </div>
          </Card>
        </Col>
      ))}
    </Row>
  );
});

// ═══════════════════════════════════════════════════════════════════
// PaymentMatrixOverview – 主页面组件
// ═══════════════════════════════════════════════════════════════════

export default function PaymentMatrixOverview() {
  const [projects, setProjects] = useState<any[]>([]);
  const [projectId, setProjectId] = useState<string | null>(null);

  const [data, setData] = useState<PaymentMatrixResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [selectedMonth, setSelectedMonth] = useState<string | null>(null);

  // ── 加载项目列表 ──
  useEffect(() => {
    getProjects({ page: 1, page_size: 100 })
      .then((res) => {
        const list = res.items ?? res ?? [];
        setProjects(list);
      })
      .catch(() => message.error("加载项目列表失败"));
  }, []);

  // ── 加载付款矩阵数据 ──
  useEffect(() => {
    if (!projectId) {
      setData(null);
      setSelectedMonth(null);
      return;
    }

    setLoading(true);
    setError(null);
    getPaymentMatrix(projectId)
      .then(setData)
      .catch((e) => {
        const msg = e?.response?.data?.detail || "加载付款矩阵失败";
        setError(msg);
        message.error(msg);
      })
      .finally(() => setLoading(false));
  }, [projectId]);

  // ── 选择月份（点击切换选中/取消） ──
  const handleSelectMonth = useCallback((month: string) => {
    setSelectedMonth((prev) => (prev === month ? null : month));
  }, []);

  const selectedProject = projects.find((p) => p.id === projectId);

  // 选中月份的总金额
  const selectedMonthTotal = useMemo(() => {
    if (!selectedMonth || !data) return 0;
    return data.monthly_totals[selectedMonth] ?? 0;
  }, [selectedMonth, data]);

  return (
    <div style={{ maxWidth: 1400, margin: "0 auto" }}>
      {/* ── 顶部项目选择 + 标题 ── */}
      <Card
        size="small"
        style={{
          marginBottom: 16,
          borderRadius: 12,
          overflow: "hidden",
        }}
        styles={{
          body: { padding: "14px 20px" },
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: 12,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <div
              style={{
                width: 40,
                height: 40,
                borderRadius: 10,
                background: "linear-gradient(135deg, #1677ff 0%, #4096ff 100%)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#fff",
                fontSize: 20,
              }}
            >
              <ProjectOutlined />
            </div>
            <div>
              <Title level={5} style={{ margin: 0, fontWeight: 600 }}>
                月度付款总览
              </Title>
              <Text type="secondary" style={{ fontSize: 12 }}>
                按年月查看合同付款节点分布与状态
              </Text>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <Text style={{ fontSize: 13, color: "#666", whiteSpace: "nowrap" }}>选择项目：</Text>
            <Select
              style={{ width: 300 }}
              value={projectId}
              onChange={(val) => {
                setProjectId(val);
                setSelectedMonth(null);
              }}
              placeholder="请选择项目"
              allowClear
              options={projects.map((p) => ({ value: p.id, label: p.project_name }))}
            />
          </div>
        </div>

        {/* 选中项目名称条 */}
        {selectedProject && data && (
          <div
            style={{
              marginTop: 12,
              padding: "8px 14px",
              background: "#f0f5ff",
              borderRadius: 8,
              border: "1px solid #d6e4ff",
              display: "flex",
              alignItems: "center",
              gap: 8,
            }}
          >
            <ProjectOutlined style={{ color: "#1677ff", fontSize: 14 }} />
            <Text style={{ fontSize: 13, color: "#333" }}>
              当前项目：
            </Text>
            <Text strong style={{ fontSize: 13, color: "#1677ff" }}>
              {data.project_name}
            </Text>
            <Badge
              count={`${data.month_range.length} 个月`}
              style={{ backgroundColor: "#e6f4ff", color: "#1677ff", fontSize: 11, fontWeight: 400 }}
              overflowCount={999}
            />
          </div>
        )}
      </Card>

      {/* ── 主体内容 ── */}
      {!projectId ? (
        <SelectProjectPrompt />
      ) : loading ? (
        <Card
          style={{
            borderRadius: 12,
            minHeight: 360,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <div style={{ textAlign: "center", padding: 60 }}>
            <Spin size="large" />
            <div style={{ marginTop: 16, color: "#999", fontSize: 14 }}>正在加载付款矩阵数据…</div>
          </div>
        </Card>
      ) : error && !data ? (
        <Card
          style={{
            borderRadius: 12,
            minHeight: 360,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <div style={{ textAlign: "center", padding: 40 }}>
            <div style={{ fontSize: 48, marginBottom: 12 }}>⚠️</div>
            <div style={{ fontSize: 16, fontWeight: 600, color: "#ff4d4f", marginBottom: 8 }}>
              加载失败
            </div>
            <div style={{ fontSize: 13, color: "#999" }}>{error}</div>
          </div>
        </Card>
      ) : data ? (
        <SelectedMonthContext.Provider value={selectedMonth}>
          {/* 统计栏 */}
          <StatsBar
            groups={data.groups}
            selectedMonth={selectedMonth}
            selectedMonthTotal={selectedMonthTotal}
          />

          {/* 月份导航条 */}
          <MonthBar
            monthRange={data.month_range}
            monthlyTotals={data.monthly_totals}
            selectedMonth={selectedMonth}
            onSelectMonth={handleSelectMonth}
          />

          {/* 选中月份提示 */}
          {selectedMonth && (
            <Card
              size="small"
              style={{
                marginBottom: 16,
                borderRadius: 10,
                background: "linear-gradient(135deg, #e6f4ff 0%, #f0f8ff 100%)",
                border: "1px solid #91caff",
              }}
              styles={{ body: { padding: "10px 16px" } }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <CalendarOutlined style={{ color: "#1677ff" }} />
                <Text style={{ fontSize: 13 }}>
                  当前筛选：
                </Text>
                <Tag color="blue" style={{ fontWeight: 600 }}>
                  {dayjs(selectedMonth + "-01").format("YYYY年M月")}
                </Tag>
                <Text style={{ fontSize: 13, color: "#666" }}>
                  高亮显示该月相关付款节点
                </Text>
                <Tag
                  color="default"
                  style={{ marginLeft: "auto", cursor: "pointer" }}
                  onClick={() => setSelectedMonth(null)}
                >
                  清除筛选
                </Tag>
              </div>
            </Card>
          )}

          {/* 合同分组列表 */}
          <Card
            title={
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <FileTextOutlined style={{ color: "#1677ff" }} />
                <span style={{ fontSize: 15, fontWeight: 600 }}>付款矩阵</span>
                <span style={{ fontSize: 12, color: "#999", fontWeight: 400 }}>
                  {data.groups.length} 个合同编号 · 共 {data.groups.reduce((s, g) => s + g.contracts.length, 0)} 条合同
                </span>
              </div>
            }
            style={{
              borderRadius: 12,
              overflow: "hidden",
            }}
            styles={{ body: { padding: "12px 16px" } }}
          >
            <ContractGroupList groups={data.groups} />
          </Card>
        </SelectedMonthContext.Provider>
      ) : null}
    </div>
  );
}
