import { useState } from "react";
import { Card, Tabs, Table, Tag, Button, Space, message, Modal } from "antd";
import { ExportOutlined } from "@ant-design/icons";

const logs = [
  { id: "l1", time: "2026-06-30 14:30", user: "王工", type: "数据入库", target: "批次 BT-20260630-001", action: "确认入库", ip: "192.168.1.100", browser: "Chrome 120", result: "成功", payload: JSON.stringify({ rows: 150 }) },
  { id: "l2", time: "2026-06-30 08:00", user: "系统", type: "自动生成", target: "6月30日粮情日报", action: "定时任务", ip: "—", browser: "—", result: "成功" },
  { id: "l3", time: "2026-06-29 16:30", user: "张工", type: "报告审批", target: "第26周质量检验周报", action: "审批通过", ip: "192.168.1.50", browser: "Edge 120", result: "成功" },
  { id: "l4", time: "2026-06-29 14:00", user: "张工", type: "登录", target: "系统", action: "用户登录", ip: "192.168.1.50", browser: "Chrome 120", result: "成功" },
  { id: "l5", time: "2026-06-28 09:00", user: "系统", type: "AI调用", target: "DeepSeek API", action: "AI分析", ip: "—", browser: "—", result: "成功", payload: JSON.stringify({ tokens: 2450 }) },
];

const cols = [
  { title: "时间", dataIndex: "time", width: 140 },
  { title: "用户", dataIndex: "user", width: 70 },
  { title: "类型", dataIndex: "type", width: 80, render: (v: string) => (
    <Tag color={v==="登录"?"blue":v==="数据入库"?"green":v==="AI调用"?"purple":"default"}>{v}</Tag>
  )},
  { title: "对象", dataIndex: "target", width: 160, ellipsis: true },
  { title: "操作", dataIndex: "action", width: 80 },
  { title: "IP", dataIndex: "ip", width: 120 },
  { title: "浏览器", dataIndex: "browser", width: 100 },
  { title: "结果", dataIndex: "result", width: 60, render: (v: string) => <Tag color={v==="成功"?"green":"red"}>{v}</Tag> },
  { title: "操作", key: "op", width: 60, render: () => <a onClick={() => message.info("查看详情")}>详情</a> },
];

export default function LogManagement() {
  const tabs = ["登录日志","操作日志","审计日志","AI调用日志"].map((t) => ({
    key: t, label: t,
    children: <Table size="small" rowKey="id"
      dataSource={t==="登录日志"?logs.filter(l=>l.type==="登录"):t==="AI调用日志"?logs.filter(l=>l.type==="AI调用"):logs}
      columns={cols} scroll={{ x: 1000 }} />,
  }));
  return (
    <div>
      <Card size="small" style={{ marginBottom: 16, textAlign: "right" }}>
        <Space><Button icon={<ExportOutlined />} onClick={() => message.info("导出日志")}>导出</Button></Space>
      </Card>
      <Card title="日志管理"><Tabs items={tabs} /></Card>
    </div>
  );
}