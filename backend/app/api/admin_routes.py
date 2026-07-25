"""
管理后台路由 - FastAPI + Jinja2 模板
登录 / 权限管理 / 仪表盘
"""
import json
from pathlib import Path
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

router = APIRouter(prefix="/admin")

# === 会话管理（基于 cookie 的签名 token）===
SECRET_KEY = "tianyi-admin-secret-key-change-in-production"
serializer = URLSafeTimedSerializer(SECRET_KEY, salt="admin-session")

# 模板目录
templates = Jinja2Templates(directory=Path(__file__).parent.parent.parent / "templates")


# === 用户权限数据 ===
ROLES = {
    "admin": {
        "name": "超级管理员",
        "permissions": ["dashboard", "users_view", "users_create", "users_edit", "users_delete", "roles_view"],
    },
    "editor": {
        "name": "编辑员",
        "permissions": ["dashboard", "users_view", "users_create", "users_edit"],
    },
    "viewer": {
        "name": "观察者",
        "permissions": ["dashboard", "users_view"],
    },
}

USERS = {
    "admin": {"password": "admin123", "display_name": "超级管理员", "role": "admin"},
    "editor": {"password": "editor123", "display_name": "编辑员", "role": "editor"},
    "viewer": {"password": "viewer123", "display_name": "观察者", "role": "viewer"},
}

MOCK_USERS_LIST = [
    {"id": 1, "username": "admin", "display_name": "超级管理员", "role": "admin", "email": "admin@tianyi.com", "status": "active"},
    {"id": 2, "username": "editor", "display_name": "编辑员", "role": "editor", "email": "editor@tianyi.com", "status": "active"},
    {"id": 3, "username": "viewer", "display_name": "观察者", "role": "viewer", "email": "viewer@tianyi.com", "status": "active"},
    {"id": 4, "username": "zhangsan", "display_name": "张三", "role": "editor", "email": "zhangsan@tianyi.com", "status": "active"},
    {"id": 5, "username": "lisi", "display_name": "李四", "role": "viewer", "email": "lisi@tianyi.com", "status": "disabled"},
]


# === 辅助函数 ===

def get_current_user(request: Request) -> dict | None:
    """从 cookie 中解析当前登录用户"""
    token = request.cookies.get("admin_token")
    if not token:
        return None
    try:
        data = serializer.loads(token, max_age=86400)  # 24h 过期
        return data
    except (BadSignature, SignatureExpired):
        return None


def has_permission(user: dict, perm: str) -> bool:
    role = user.get("role", "")
    return perm in ROLES.get(role, {}).get("permissions", [])


def require_auth(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")
    return user


# === JSON API（给前端 AJAX 调用）===

@router.post("/api/login")
async def api_login(request: Request):
    """登录 API"""
    body = await request.json()
    username = body.get("username", "")
    password = body.get("password", "")

    record = USERS.get(username)
    if not record or record["password"] != password:
        return JSONResponse({"ok": False, "message": "用户名或密码错误"}, status_code=401)

    user = {
        "id": username,
        "username": username,
        "display_name": record["display_name"],
        "role": record["role"],
        "permissions": ROLES[record["role"]]["permissions"],
    }
    token = serializer.dumps(user)
    resp = JSONResponse({"ok": True, "token": token, "user": user})
    resp.set_cookie(key="admin_token", value=token, max_age=86400, httponly=True)
    return resp


@router.delete("/api/login")
async def api_logout(request: Request):
    """退出登录"""
    resp = JSONResponse({"ok": True})
    resp.delete_cookie("admin_token")
    return resp


@router.get("/api/me")
async def api_me(request: Request):
    user = require_auth(request)
    return {
        "id": user["id"],
        "username": user["username"],
        "display_name": user["display_name"],
        "role": user["role"],
        "permissions": ROLES.get(user["role"], {}).get("permissions", []),
    }


@router.get("/api/users")
async def api_users(request: Request):
    user = require_auth(request)
    if not has_permission(user, "users_view"):
        raise HTTPException(status_code=403, detail="权限不足")
    return MOCK_USERS_LIST


@router.get("/api/roles")
async def api_roles(request: Request):
    user = require_auth(request)
    if not has_permission(user, "roles_view"):
        raise HTTPException(status_code=403, detail="权限不足")
    return [
        {"role": k, "name": v["name"], "permissions": v["permissions"]}
        for k, v in ROLES.items()
    ]


# === 页面路由（返回 HTML）===

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    user = get_current_user(request)
    if user:
        return RedirectResponse("/admin/dashboard", status_code=302)
    return templates.TemplateResponse(request, "admin/login.html", {})


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    user = require_auth(request)
    return templates.TemplateResponse(request, "admin/dashboard.html", {
        "user": user,
        "roles": ROLES,
    })


@router.get("/users", response_class=HTMLResponse)
async def users_page(request: Request):
    user = require_auth(request)
    if not has_permission(user, "users_view"):
        return HTMLResponse("权限不足", status_code=403)
    return templates.TemplateResponse(request, "admin/users.html", {
        "user": user,
        "users": MOCK_USERS_LIST,
    })


@router.get("/roles", response_class=HTMLResponse)
async def roles_page(request: Request):
    user = require_auth(request)
    if not has_permission(user, "roles_view"):
        return HTMLResponse("权限不足", status_code=403)
    return templates.TemplateResponse(request, "admin/roles.html", {
        "user": user,
        "roles": ROLES,
    })
