import { useState } from "react";
import { Layout, Menu, Avatar, Dropdown, Space, Badge, Select } from "antd";
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import {
  DashboardOutlined,
  DatabaseOutlined,
  FileTextOutlined,
  AuditOutlined,
  ProjectOutlined,
  BellOutlined,
  UserOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  DollarOutlined,
} from "@ant-design/icons";
import { useAuthStore } from "../store/auth";

const { Header, Sider, Content } = Layout;

// 菜单顺序：工作台 → 项目中心 → 数据中心 → 报告中心 → 审核工作台 → 支付台账
const menuItems = [
  {
    key: "/dashboard",
    icon: <DashboardOutlined />,
    label: "工作台",
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
    key: "review-group",
    icon: <AuditOutlined />,
    label: "审核工作台",
    children: [
      { key: "/secondary/audit", label: "审核工作台" },
      { key: "/secondary/monthly", label: "月度台账" },
    ],
  },
  {
    key: "payment-group",
    icon: <DollarOutlined />,
    label: "支付台账",
    children: [
      { key: "/secondary/contracts", label: "合同管理" },
      { key: "/secondary/nodes", label: "节点管理" },
      { key: "/secondary/payments", label: "支付台账" },
      { key: "/secondary/payment-matrix", label: "月度总览" },
      { key: "/secondary/node-templates", label: "节点模板" },
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
    // 审核工作台子路由
    if (path.startsWith("/secondary/audit") || path.startsWith("/audits") || path.startsWith("/secondary/monthly")) {
      return ["review-group"];
    }
    // 支付台账子路由
    if (path.startsWith("/secondary/contracts") || path.startsWith("/secondary/nodes") ||
        path.startsWith("/secondary/payments") || path.startsWith("/secondary/payment-matrix") ||
        path.startsWith("/secondary/node-templates") ||
        path.startsWith("/contracts/")) {
      return ["payment-group"];
    }
    // 其他模块保持原逻辑
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
            {collapsed ? "XTH" : "兴天华过控智能平台"}
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
                <span>{user?.real_name ?? "管理员"}</span>
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
