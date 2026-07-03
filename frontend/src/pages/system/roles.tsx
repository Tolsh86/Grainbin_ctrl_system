import { useState } from "react";
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
}