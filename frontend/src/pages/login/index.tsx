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

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true);
    try {
      const result = await login(values);
      setAuth(result.access_token, result.user);
      message.success(`欢迎回来，${result.user.real_name}`);
      navigate("/dashboard", { replace: true });
    } catch (error) {
      const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      message.error(detail || "登录失败，请检查账号、密码或网络连接");
    } finally {
      setLoading(false);
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
              兴天华过控智能平台
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
              name="username"
              rules={[
                { required: true, message: "请输入管理员账号" },
              ]}
            >
              <Input prefix={<UserOutlined />} placeholder="管理员账号" autoComplete="username" />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[{ required: true, message: "请输入密码" }]}
            >
              <Input.Password prefix={<LockOutlined />} placeholder="密码" autoComplete="current-password" />
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
