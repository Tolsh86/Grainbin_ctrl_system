import { useState } from "react";
import { Layout, Menu, Avatar, Dropdown, Space, Badge, Select } from "antd";
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import {
  DashboardOutlined,
  DatabaseOutlined,
  FileTextOutlined,
  AuditOutlined,
  RobotOutlined,
  ProjectOutlined,
  BellOutlined,
  UserOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  SettingOutlined,
  DollarOutlined,
  BookOutlined,
  FundOutlined,
} from "@ant-design/icons";
import { useAuthStore } from "../store/auth";

const { Header, Sider, Content } = Layout;

// 菜单顺序：工作台 → 驾驶舱 → 项目中心 → 数据中心 → 报告中心 → 审核中心 → 二类费用 → 知识库 → AI分析 → 系统管理
const menuItems = [
  {
    key: "/dashboard",
    icon: <DashboardOutlined />,
    label: "工作台",
  },
  {
    key: "cockpit-group",
    icon: <FundOutlined />,
    label: "驾驶舱",
    children: [
      { key: "/cockpit/overview", label: "项目总览" },
      { key: "/cockpit/scurve", label: "S 曲线" },
      { key: "/cockpit/investment", label: "投资分析" },
    ],
  },
  {
    key: "project-group",
    icon: <ProjectOutlined />,
    label: "项目中心",
    children: [
      { key: "/projects", label: "项目列表" },
    ],
  },
  {
    key: "data-group",
    icon: <DatabaseOutlined />,
    label: "数据中心",
    children: [
      { key: "/data/upload", label: "数据上传" },
      { key: "/data/batches", label: "批次管理" },
      { key: "/data/list", label: "数据列表" },
      { key: "/data/compare", label: "数据对比" },
      { key: "/data/mapping", label: "字段映射" },
      { key: "/data/errors", label: "错误中心" },
    ],
  },
  {
    key: "report-group",
    icon: <FileTextOutlined />,
    label: "报告中心",
    children: [
      { key: "/reports", label: "报告列表" },
      { key: "/reports/templates", label: "模板管理" },
    ],
  },
  {
    key: "audit-group",
    icon: <AuditOutlined />,
    label: "审核中心",
    children: [
      { key: "/audits", label: "审核列表" },
      { key: "/audits/upload", label: "上传审核" },
    ],
  },
  {
    key: "secondary-group",
    icon: <DollarOutlined />,
    label: "二类费用",
    children: [
      { key: "/secondary/contracts", label: "合同管理" },
      { key: "/secondary/nodes", label: "节点管理" },
      { key: "/secondary/payments", label: "支付台账" },
    ],
  },
  {
    key: "knowledge-group",
    icon: <BookOutlined />,
    label: "知识库",
    children: [
      { key: "/knowledge/docs", label: "文档管理" },
      { key: "/knowledge/chat", label: "AI 问答" },
    ],
  },
  {
    key: "ai-group",
    icon: <RobotOutlined />,
    label: "AI 分析中心",
    children: [
      { key: "/ai/trend", label: "趋势分析" },
      { key: "/ai/risk", label: "风险检测" },
      { key: "/ai/summary", label: "智能摘要" },
      { key: "/ai/qa", label: "智能提问" },
    ],
  },
  {
    key: "system-group",
    icon: <SettingOutlined />,
    label: "系统管理",
    children: [
      { key: "/system/users", label: "用户管理" },
      { key: "/system/roles", label: "角色管理" },
      { key: "/system/permissions", label: "权限管理" },
      { key: "/system/menus", label: "菜单管理" },
      { key: "/system/logs", label: "日志管理" },
    ],
  },
];

export default function MainLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  const userMenuItems = [
    { key: "profile", label: `角色: ${user?.role ?? "管理员"}` },
    { key: "logout", label: "退出登录", onClick: handleLogout },
  ];

  const getSelectedKeys = () => {
    const path = location.pathname;
    return [path];
  };

  const getOpenKeys = () => {
    const path = location.pathname;
    const parts = path.split("/");
    if (parts.length >= 2) {
      const groupKey = `${parts[1]}-group`;
      if (menuItems.some((item) => item.key === groupKey)) return [groupKey];
    }
    return [];
  };

  return (
    <Layout hasSider style={{ height: "100vh", overflow: "hidden" }}>
      {/* 固定侧边栏 */}
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        theme="light"
        width={220}
        style={{
          borderRight: "1px solid #f0f0f0",
          height: "100vh",
          position: "fixed",
          left: 0,
          top: 0,
          bottom: 0,
          zIndex: 100,
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div
          style={{
            height: 64,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            borderBottom: "1px solid #f0f0f0",
            flexShrink: 0,
          }}
        >
          <h2
            style={{
              margin: 0,
              fontSize: collapsed ? 14 : 16,
              color: "#1677ff",
              whiteSpace: "nowrap",
            }}
          >
            {collapsed ? "GCS" : "粮仓过控智能平台"}
          </h2>
        </div>
        <div
          style={{
            height: "calc(100vh - 64px)",
            overflowY: "auto",
            overflowX: "hidden",
            scrollbarWidth: "none",
          }}
          className="sider-menu-no-scrollbar"
        >
          <Menu
            mode="inline"
            selectedKeys={getSelectedKeys()}
            defaultOpenKeys={getOpenKeys()}
            items={menuItems}
            onClick={({ key }) => {
              if (key.includes("-group")) return;
              navigate(key);
            }}
            style={{ borderRight: 0 }}
          />
        </div>
      </Sider>

      {/* 主内容区 */}
      <Layout style={{ marginLeft: collapsed ? 80 : 220, transition: "margin-left 0.2s", height: "100vh" }}>
        {/* 固定顶栏 */}
        <Header
          style={{
            padding: "0 24px",
            background: "#fff",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            borderBottom: "1px solid #f0f0f0",
            height: 64,
            flexShrink: 0,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <div
              style={{ cursor: "pointer", fontSize: 18 }}
              onClick={() => setCollapsed(!collapsed)}
            >
              {collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            </div>
            <Select
              style={{ width: 220 }}
              defaultValue="p1"
              options={[
                { value: "p1", label: "1-6号粮仓新建工程" },
                { value: "p2", label: "7-12号粮仓改造工程" },
                { value: "p3", label: "智能通风系统安装" },
                { value: "p4", label: "中心粮库扩建" },
                { value: "p5", label: "粮库信息化平台建设" },
                { value: "all", label: "全部项目" },
              ]}
            />
          </div>
          <Space size={24}>
            <Badge count={3} size="small">
              <BellOutlined style={{ fontSize: 18, cursor: "pointer" }} />
            </Badge>
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <Space style={{ cursor: "pointer" }}>
                <Avatar icon={<UserOutlined />} />
                <span>{user?.full_name ?? "管理员"}</span>
              </Space>
            </Dropdown>
          </Space>
        </Header>

        {/* 可滚动内容区 */}
        <Content
          style={{
            margin: 24,
            flex: 1,
            overflowY: "auto",
            overflowX: "hidden",
            background: "#f5f5f5",
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}