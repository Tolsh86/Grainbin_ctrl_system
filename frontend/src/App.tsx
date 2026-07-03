import { Routes, Route, Navigate } from "react-router-dom";
import AuthGuard from "./components/AuthGuard";
import MainLayout from "./components/MainLayout";
import Login from "./pages/login/index";
import Dashboard from "./pages/dashboard/index";
// 项目管理
import ProjectList from "./pages/project/index";
import ProjectDetail from "./pages/project/detail";
// 数据中心
import DataUpload from "./pages/data/upload";
import BatchesList from "./pages/data/batches";
import BatchDetail from "./pages/data/batch-detail";
import DataList from "./pages/data/list";
import DataCompare from "./pages/data/compare";
import MappingList from "./pages/data/mapping";
import MappingEdit from "./pages/data/mapping-edit";
import ErrorCenter from "./pages/data/errors";
// 报告中心
import ReportList from "./pages/report/index";
import ReportEdit from "./pages/report/edit";
import TemplateList from "./pages/report/templates";
import TemplateEdit from "./pages/report/template-edit";
// 审核中心
import AuditList from "./pages/audit/index";
import AuditUpload from "./pages/audit/upload";
import AuditDetail from "./pages/audit/detail";
// 二类费用
import ContractsList from "./pages/secondary/contracts";
import NodeTemplates from "./pages/secondary/node-templates";
import NodeManagement from "./pages/secondary/nodes";
import PaymentLedger from "./pages/secondary/payments";
import ReminderSettings from "./pages/secondary/reminder";
// 知识库
import KnowledgeDocs from "./pages/knowledge/docs";
import AIChat from "./pages/knowledge/chat";
// AI 分析
import TrendAnalysis from "./pages/ai/trend";
import RiskDetection from "./pages/ai/risk";
import SmartSummary from "./pages/ai/summary";
import AIQA from "./pages/ai/qa";
// 驾驶舱
import CockpitOverview from "./pages/cockpit/overview";
import SCurve from "./pages/cockpit/scurve";
import InvestmentAnalysis from "./pages/cockpit/investment";
// 系统管理
import UserManagement from "./pages/system/users";
import RoleManagement from "./pages/system/roles";
import PermissionManagement from "./pages/system/permissions";
import MenuManagement from "./pages/system/menus";
import LogManagement from "./pages/system/logs";

export default function App() {
  return (
    <Routes>
      {/* 公开路由 */}
      <Route path="/login" element={<Login />} />

      {/* 受保护的路由 - 使用 MainLayout 包裹 */}
      <Route
        element={
          <AuthGuard>
            <MainLayout />
          </AuthGuard>
        }
      >
        {/* 工作台 */}
        <Route path="/dashboard" element={<Dashboard />} />

        {/* 项目中心 */}
        <Route path="/projects" element={<ProjectList />} />
        <Route path="/projects/:id" element={<ProjectDetail />} />

        {/* 数据中心 */}
        <Route path="/data/upload" element={<DataUpload />} />
        <Route path="/data/batches" element={<BatchesList />} />
        <Route path="/data/batches/:id" element={<BatchDetail />} />
        <Route path="/data/list" element={<DataList />} />
        <Route path="/data/compare" element={<DataCompare />} />
        <Route path="/data/mapping" element={<MappingList />} />
        <Route path="/data/mapping/new" element={<MappingEdit />} />
        <Route path="/data/mapping/:id/edit" element={<MappingEdit />} />
        <Route path="/data/errors" element={<ErrorCenter />} />

        {/* 报告中心 */}
        <Route path="/reports" element={<ReportList />} />
        <Route path="/reports/:id/edit" element={<ReportEdit />} />
        <Route path="/reports/templates" element={<TemplateList />} />
        <Route path="/reports/templates/:id/edit" element={<TemplateEdit />} />

        {/* 审核中心 */}
        <Route path="/audits" element={<AuditList />} />
        <Route path="/audits/upload" element={<AuditUpload />} />
        <Route path="/audits/:id" element={<AuditDetail />} />

        {/* 二类费用 */}
        <Route path="/secondary/contracts" element={<ContractsList />} />
        <Route path="/secondary/node-templates" element={<NodeTemplates />} />
        <Route path="/secondary/nodes" element={<NodeManagement />} />
        <Route path="/secondary/payments" element={<PaymentLedger />} />
        <Route path="/secondary/reminder" element={<ReminderSettings />} />

        {/* 知识库 */}
        <Route path="/knowledge/docs" element={<KnowledgeDocs />} />
        <Route path="/knowledge/chat" element={<AIChat />} />

        {/* AI 分析中心 */}
        <Route path="/ai/trend" element={<TrendAnalysis />} />
        <Route path="/ai/risk" element={<RiskDetection />} />
        <Route path="/ai/summary" element={<SmartSummary />} />
        <Route path="/ai/qa" element={<AIQA />} />

        {/* 驾驶舱 */}
        <Route path="/cockpit/overview" element={<CockpitOverview />} />
        <Route path="/cockpit/scurve" element={<SCurve />} />
        <Route path="/cockpit/investment" element={<InvestmentAnalysis />} />

        {/* 系统管理 */}
        <Route path="/system/users" element={<UserManagement />} />
        <Route path="/system/roles" element={<RoleManagement />} />
        <Route path="/system/permissions" element={<PermissionManagement />} />
        <Route path="/system/menus" element={<MenuManagement />} />
        <Route path="/system/logs" element={<LogManagement />} />

        {/* 默认跳转到 Dashboard */}
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Route>
    </Routes>
  );
}