#!/usr/bin/env sh
set -eu

cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

if [ ! -f .env ]; then
  echo "未找到 .env。请先复制 .env.example 为 .env 并填写域名、密码与 JWT 密钥。" >&2
  exit 1
fi

compose() {
  docker compose --env-file .env -f docker-compose.yml "$@"
}

# 数据服务先启动，再执行可重复运行的数据库迁移与演示数据初始化。
compose up -d postgres redis minio
compose run --rm api alembic upgrade head
compose run --rm api python -m app.seed_admin
compose run --rm api python -m app.seed_demo_secondary_costs
compose up -d --build api web caddy

echo "部署完成。域名 DNS 生效且 80/443 端口可达后，Caddy 会自动申请 HTTPS 证书。"
