import { Card, Tree, Button, message } from "antd";
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
}