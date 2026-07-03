import { useState } from "react";
import { Card, Table, Tag, Button, Space, Row, Col, Input, Drawer, Form, Select, message } from "antd";
import { PlusOutlined, SearchOutlined } from "@ant-design/icons";
import { mockUsers } from "../../utils/mock";

const roleMap: Record<string, string> = {
  admin: "管理员", project_manager: "项目负责人",
  auditor: "造价工程师", operator: "资料员", viewer: "只读用户",
};

export default function UserManagement() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [search, setSearch] = useState("");
  let filtered = mockUsers;
  if (search) filtered = filtered.filter((u) => u.full_name.includes(search) || u.username.includes(search));

  const cols = [
    { title: "用户名", dataIndex: "username", width: 100 },
    { title: "姓名", dataIndex: "full_name", width: 100 },
    { title: "邮箱", dataIndex: "email", width: 180 },
    { title: "角色", dataIndex: "role", width: 100, render: (v: string) => <Tag>{roleMap[v] || v}</Tag> },
    { title: "状态", dataIndex: "status", width: 80, render: (v: string) => <Tag color={v === "active" ? "green" : "default"}>{v === "active" ? "正常" : "禁用"}</Tag> },
    { title: "最后登录", dataIndex: "last_login", width: 150 },
    { title: "操作", key: "op", width: 140, render: () => (
      <Space size="small">
        <a onClick={() => setDrawerOpen(true)}>编辑</a>
        <a onClick={() => message.warning("禁用/启用")}>状态</a>
        <a onClick={() => message.info("重置密码")} style={{ color: "#ff4d4f" }}>重置</a>
      </Space>
    ) },
  ];

  return (
    <div>
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={[12, 8]} align="middle">
          <Col flex="auto"><Input.Search placeholder="搜索用户名/姓名" enterButton={<SearchOutlined />} value={search} onChange={(e) => setSearch(e.target.value)} /></Col>
          <Col><Button type="primary" icon={<PlusOutlined />} onClick={() => setDrawerOpen(true)}>新建用户</Button></Col>
        </Row>
      </Card>
      <Card title="用户管理"><Table columns={cols} dataSource={filtered} size="small" rowKey="id" /></Card>
      <Drawer title="新建/编辑用户" width={520} open={drawerOpen} onClose={() => setDrawerOpen(false)}
        extra={<Space><Button onClick={() => setDrawerOpen(false)}>取消</Button><Button type="primary" onClick={() => { message.success("用户已保存"); setDrawerOpen(false); }}>保存</Button></Space>}>
        <Form layout="vertical">
          <Form.Item label="用户名" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item label="姓名"><Input /></Form.Item>
          <Form.Item label="邮箱"><Input /></Form.Item>
          <Form.Item label="角色"><Select options={Object.entries(roleMap).map(([k, v]) => ({ value: k, label: v }))} /></Form.Item>
          <Form.Item label="初始密码"><Input.Password /></Form.Item>
        </Form>
      </Drawer>
    </div>
  );
}
