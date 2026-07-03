import fs from "fs";
import path from "path";

const BASE = "D:/company/Grainbin_system/frontend/src/pages";

const pages = {};

// ----- Roles -----
pages["system/roles.tsx"] = `import { useState } from "react";
import { Card, Table, Tag, Button, Space, Drawer, Form, Input, Tree, message } from "antd";
import { PlusOutlined } from "@ant-design/icons";

const roles = [
  { id: "admin", name: "管理员", desc: "系统管理员，拥有全部权限", permCount: 32, userCount: 1, builtin: true },
  { id: "project_manager", name: "项目负责人", desc: "查看驾驶舱、审批报告、管理项目", permCount: 18, userCount: 1, builtin: true },
  { id: "auditor", name: "造价工程师", desc: "审核进度款、管理二类费用", permCount: 14, userCount: 1, builtin: true },
  { id: "operator", name: "资料员", desc: "上传资料、AI识别数据、编制周月报", permCount: 10, userCount: 1, builtin: true },
  { id: "viewer", name: "只读用户", desc: "查看驾驶舱、报告、数据对比", permCount: 5, userCount: 1, builtin: true },
];

export default function RoleManagement() {
  const [open, setOpen] = useState(false);
  return (
    <div>
      <Card size="small" style={{ marginBottom: 16, textAlign: "right" }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setOpen(true)}>新建角色</Button>
      </Card>
      <Card title="角色管理">
        <Table size="small" rowKey="id" dataSource={roles} columns={[
          { title: "角色名", dataIndex: "name" },
          { title: "描述", dataIndex: "desc", ellipsis: true },
          { title: "权限数", dataIndex: "permCount", width: 80 },
          { title: "用户数", dataIndex: "userCount", width: 80 },
          { title: "内置", dataIndex: "builtin", width: 80, render: (v: boolean) => <Tag color={v ? "blue" : "default"}>{v ? "内置" : "自定义"}</Tag> },
          { title: "操作", key: "op", width: 80, render: () => <a onClick={() => setOpen(true)}>编辑</a> },
        ]} />
      </Card>
      <Drawer title="新建/编辑角色" width={520} open={open} onClose={() => setOpen(false)}
        extra={<Space><Button onClick={() => setOpen(false)}>取消</Button><Button type="primary" onClick={() => { message.success("角色已保存"); setOpen(false); }}>保存</Button></Space>}>
        <Form layout="vertical">
          <Form.Item label="角色名"><Input /></Form.Item>
          <Form.Item label="描述"><Input.TextArea rows={2} /></Form.Item>
          <Form.Item label="权限分配">
            <Tree checkable treeData={[
              { title: "工作台", key: "dashboard", children: [{ title: "查看", key: "dashboard:view" }] },
              { title: "项目中心", key: "project", children: [{ title: "查看", key: "project:view" }, { title: "编辑", key: "project:edit" }] },
              { title: "数据中心", key: "data", children: [{ title: "上传", key: "data:upload" }, { title: "确认入库", key: "data:commit" }] },
              { title: "报告中心", key: "report", children: [{ title: "发布", key: "report:publish" }, { title: "查看", key: "report:view" }] },
            ]} />
          </Form.Item>
        </Form>
      </Drawer>
    </div>
  );
}`;

// ----- Permissions -----
pages["system/permissions.tsx"] = `import { Card, Tree, Tag } from "antd";

const permTree = [
  { title: <><Tag color="blue">工作台</Tag> Dashboard</>, key: "d", children: [
    { title: <><Tag>dashboard:view</Tag> 查看工作台</>, key: "dashboard:view" },
  ]},
  { title: <><Tag color="blue">项目中心</Tag> Project</>, key: "p", children: [
    { title: <><Tag>project:view</Tag> 查看项目</>, key: "project:view" },
    { title: <><Tag>project:edit</Tag> 编辑项目</>, key: "project:edit" },
    { title: <><Tag>project:delete</Tag> 删除项目</>, key: "project:delete" },
  ]},
  { title: <><Tag color="blue">数据中心</Tag> Data</>, key: "da", children: [
    { title: <><Tag>data:upload</Tag> 上传数据</>, key: "data:upload" },
    { title: <><Tag>data:commit</Tag> 确认入库</>, key: "data:commit" },
    { title: <><Tag>data:rollback</Tag> 撤回批次</>, key: "data:rollback" },
  ]},
  { title: <><Tag color="blue">系统管理</Tag> System</>, key: "sy", children: [
    { title: <><Tag>system:user</Tag> 用户管理</>, key: "system:user" },
    { title: <><Tag>system:role</Tag> 角色管理</>, key: "system:role" },
    { title: <><Tag>system:menu</Tag> 菜单管理</>, key: "system:menu" },
  ]},
];

export default function PermissionManagement() {
  return (
    <div>
      <Card title="权限树（只读展示）" size="small" style={{ marginBottom: 16 }}>
        <Tree treeData={permTree} defaultExpandAll selectable={false} />
      </Card>
      <Card size="small">
        <p style={{ fontSize: 12, color: "#999" }}>权限按模块分组，每个模块下有查看/编辑/删除等操作权限。admin 拥有全部权限，其他角色按需分配。</p>
      </Card>
    </div>
  );
}`;

// ----- Menus -----
pages["system/menus.tsx"] = `import { Card, Tree, Button, message } from "antd";
import { PlusOutlined } from "@ant-design/icons";

const menuTree = [
  { title: <span style={{ fontWeight: 600 }}>工作台</span>, key: "/dashboard" },
  { title: <span style={{ fontWeight: 600 }}>项目中心</span>, key: "project", children: [
    { title: "项目列表 /projects", key: "/projects" },
    { title: "项目详情 /projects/:id", key: "/projects/:id" },
  ]},
  { title: <span style={{ fontWeight: 600 }}>数据中心</span>, key: "data", children: [
    { title: "数据上传 /data/upload", key: "/data/upload" },
    { title: "批次管理 /data/batches", key: "/data/batches" },
    { title: "数据列表 /data/list", key: "/data/list" },
    { title: "数据对比 /data/compare", key: "/data/compare" },
    { title: "字段映射 /data/mapping", key: "/data/mapping" },
    { title: "错误中心 /data/errors", key: "/data/errors" },
  ]},
  { title: <span style={{ fontWeight: 600 }}>报告中心</span>, key: "report", children: [
    { title: "报告列表 /reports", key: "/reports" },
    { title: "模板管理 /reports/templates", key: "/reports/templates" },
  ]},
  { title: <span style={{ fontWeight: 600 }}>审核中心</span>, key: "audit", children: [
    { title: "审核列表 /audits", key: "/audits" },
    { title: "上传审核 /audits/upload", key: "/audits/upload" },
  ]},
  { title: <span style={{ fontWeight: 600 }}>二类费用</span>, key: "secondary", children: [
    { title: "合同管理 /secondary/contracts", key: "/secondary/contracts" },
    { title: "节点管理 /secondary/nodes", key: "/secondary/nodes" },
    { title: "支付台账 /secondary/payments", key: "/secondary/payments" },
  ]},
];

export default function MenuManagement() {
  return (
    <div>
      <Card size="small" style={{ marginBottom: 16, textAlign: "right" }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => message.info("新增菜单")}>新增菜单</Button>
      </Card>
      <Card title="菜单树（拖拽排序，行可编辑）" size="small">
        <Tree treeData={menuTree} defaultExpandAll selectable={false} />
        <p style={{ fontSize: 12, color: "#999", marginTop: 12 }}>实际功能支持拖拽排序、编辑图标/标题/路径/是否隐藏/所需权限。此处为预置菜单树展示。</p>
      </Card>
    </div>
  );
}`;

// ----- Logs -----
pages["system/logs.tsx"] = `import { useState } from "react";
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
}`;

// Write all files
Object.entries(pages).forEach(([relPath, content]) => {
  const fullPath = path.join(BASE, relPath);
  fs.writeFileSync(fullPath, content, "utf-8");
  console.log("Written:", relPath);
});

console.log("All done!");