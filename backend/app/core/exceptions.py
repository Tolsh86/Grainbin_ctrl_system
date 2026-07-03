"""全局异常定义与 FastAPI 异常处理器

提供：
- 业务异常基类 AppException 及常见子类
- 统一的 JSON 错误响应格式 {detail, code, errors?}
- FastAPI exception_handlers 注册函数
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from loguru import logger
from starlette.responses import JSONResponse


# ── 业务异常 ──────────────────────────────────────


class AppException(Exception):
    """业务异常基类"""

    def __init__(self, detail: str, code: str = "BAD_REQUEST", status_code: int = 400, errors: list | None = None):
        self.detail = detail
        self.code = code
        self.status_code = status_code
        self.errors = errors

    def __str__(self) -> str:
        return self.detail


class NotFound(AppException):
    def __init__(self, detail: str = "资源不存在", code: str = "NOT_FOUND"):
        super().__init__(detail=detail, code=code, status_code=404)


class BadRequest(AppException):
    def __init__(self, detail: str = "请求参数错误", code: str = "BAD_REQUEST"):
        super().__init__(detail=detail, code=code, status_code=400)


class Unauthorized(AppException):
    def __init__(self, detail: str = "未登录或令牌已过期", code: str = "UNAUTHORIZED"):
        super().__init__(detail=detail, code=code, status_code=401)


class Forbidden(AppException):
    def __init__(self, detail: str = "权限不足", code: str = "FORBIDDEN"):
        super().__init__(detail=detail, code=code, status_code=403)


class Conflict(AppException):
    def __init__(self, detail: str = "资源冲突", code: str = "CONFLICT"):
        super().__init__(detail=detail, code=code, status_code=409)


# ── 统一响应格式 ──────────────────────────────────


def _error_response(detail: str, code: str = "BAD_REQUEST", errors: list | None = None) -> dict:
    resp = {"detail": detail, "code": code}
    if errors:
        resp["errors"] = errors
    return resp


# ── 注册全局处理器 ──────────────────────────────


def register_exception_handlers(app: FastAPI) -> None:
    """将全局异常处理器挂载到 FastAPI 实例。"""

    @app.exception_handler(AppException)
    async def handle_app_exception(request: Request, exc: AppException):
        logger.warning(f"{exc.code} | {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_response(detail=exc.detail, code=exc.code, errors=exc.errors),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        errors = []
        for err in exc.errors():
            field = ".".join(str(loc) for loc in err.get("loc", []))
            msg = err.get("msg", "")
            field and errors.append(f"{field}: {msg}") or errors.append(msg)
        logger.warning(f"参数校验失败: {errors}")
        return JSONResponse(
            status_code=422,
            content=_error_response(detail="请求参数校验失败", code="VALIDATION_ERROR", errors=errors),
        )

    @app.exception_handler(Exception)
    async def handle_unhandled_exception(request: Request, exc: Exception):
        logger.opt(exception=True).error(f"未处理的异常: {exc}")
        return JSONResponse(
            status_code=500,
            content=_error_response(detail="服务器内部错误", code="INTERNAL_ERROR"),
        )
