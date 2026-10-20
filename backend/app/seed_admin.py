"""初始化公网演示环境的固定管理员账号。

默认只创建账号；已有账号不会被改密。需要按环境变量重置密码时加
``--reset-password`` 参数。
"""

from __future__ import annotations

import argparse
import os

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models.user import User


def required_env(name: str, minimum_length: int = 1) -> str:
    value = os.getenv(name, "").strip()
    if len(value) < minimum_length or value.lower().startswith("change-"):
        raise SystemExit(f"请先在部署环境中设置安全的 {name}。")
    return value


def seed_admin(reset_password: bool = False) -> None:
    username = required_env("ADMIN_USERNAME", 2)
    password = required_env("ADMIN_PASSWORD", 12)
    real_name = required_env("ADMIN_REAL_NAME", 1)
    email = os.getenv("ADMIN_EMAIL", "").strip() or None

    engine = create_engine(settings.DATABASE_SYNC_URL)
    with Session(engine) as session:
        user = session.execute(select(User).where(User.username == username)).scalar_one_or_none()
        if user is None:
            session.add(User(
                username=username,
                password_hash=hash_password(password),
                real_name=real_name,
                email=email,
                role="admin",
                is_active=True,
            ))
            session.commit()
            print(f"已创建管理员账号：{username}")
            return

        user.real_name = real_name
        user.email = email
        user.role = "admin"
        user.is_active = True
        user.deleted_at = None
        if reset_password:
            user.password_hash = hash_password(password)
        session.commit()
        suffix = "，密码已重置" if reset_password else "，保留原密码"
        print(f"管理员账号已存在：{username}{suffix}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="创建或维护固定管理员账号")
    parser.add_argument("--reset-password", action="store_true", help="账号存在时按 ADMIN_PASSWORD 重置密码")
    seed_admin(reset_password=parser.parse_args().reset_password)
