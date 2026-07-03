import { Card, Tree, Tag } from "antd";

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
}