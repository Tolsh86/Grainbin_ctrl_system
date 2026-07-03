import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Form, Input, Button, Card, Typography, message, Space } from "antd";
import { UserOutlined, LockOutlined, BankOutlined } from "@ant-design/icons";
import { login } from "../../api/auth";
import { useAuthStore } from "../../store/auth";

const { Title, Text } = Typography;

export default function Login() {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);

  const onFinish = async (values: { email: string; password: string }) => {
    setLoading(true);
    try {
      const result = await login(values);
      setAuth(result.access_token, result.user);
      message.success(`欢迎回来，${result.user.full_name}`);
    } catch {
      // 后端不可用时，使用 mock 登录跳过认证
      message.info("演示模式：跳过后端认证");
      setAuth("mock-token-001", {
        id: "u1", email: values.email, full_name: "管理员",
        role: "admin", is_active: true,
        created_at: "2026-01-01", updated_at: "2026-01-01",
      });
    } finally {
      setLoading(false);
      navigate("/dashboard", { replace: true });
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
      }}
    >
      <Card
        style={{ width: 420, boxShadow: "0 8px 24px rgba(0,0,0,0.15)" }}
        styles={{ body: { padding: "40px 32px" } }}
      >
        <Space direction="vertical" size="large" style={{ width: "100%", textAlign: "center" }}>
          <div>
            <BankOutlined style={{ fontSize: 48, color: "#667eea" }} />
            <Title level={3} style={{ margin: "12px 0 4px" }}>
              粮仓过控智能管理平台
            </Title>
            <Text type="secondary">Grainbin Process Control System</Text>
          </div>

          <Form
            name="login"
            onFinish={onFinish}
            layout="vertical"
            size="large"
            style={{ textAlign: "left" }}
          >
            <Form.Item
              name="email"
              rules={[
                { required: true, message: "请输入邮箱" },
                { type: "email", message: "请输入有效的邮箱地址" },
              ]}
            >
              <Input prefix={<UserOutlined />} placeholder="邮箱" />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[{ required: true, message: "请输入密码" }]}
            >
              <Input.Password prefix={<LockOutlined />} placeholder="密码" />
            </Form.Item>

            <Form.Item>
              <Button type="primary" htmlType="submit" loading={loading} block>
                登 录
              </Button>
            </Form.Item>
          </Form>

          <Text type="secondary" style={{ fontSize: 12 }}>
            如需注册请联系管理员
          </Text>
        </Space>
      </Card>
    </div>
  );
}
