import json
from datetime import datetime

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from common.responses import success, error
from systems.user.models import SysUser
from systems.menu.models import SysMenu
from utils import verify_password, hash_password, create_access_token


def _get_user_permissions(user):
    permission_set = set()
    for role in user.roles.all():
        for menu in role.menus.all():
            if menu.permission:
                permission_set.add(menu.permission.name)
    return list(permission_set)


def _get_user_role_ids(user):
    return [role.id for role in user.roles.all()]


def _parse_body(request):
    try:
        return json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return {}


@require_http_methods(["POST"])
def login(request):
    data = _parse_body(request)
    username = data.get("username", "")
    password = data.get("password", "")

    try:
        user = SysUser.objects.get(username=username, is_deleted=0)
    except SysUser.DoesNotExist:
        return error("用户名或密码错误")

    if not verify_password(password, user.password):
        return error("用户名或密码错误")

    if user.status != 1:
        return error("用户已被禁用")

    token = create_access_token(data={"sub": str(user.id)})
    permissions = _get_user_permissions(user)
    roles = _get_user_role_ids(user)

    return success({
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "name": user.name,
            "phone": user.phone,
            "email": user.email,
            "status": user.status,
            "roles": roles,
        },
        "roles": roles,
        "permissions": permissions,
    }, message="登录成功")


@require_http_methods(["POST"])
def logout(request):
    return success(message="退出登录成功")


@require_http_methods(["GET"])
def refresh_permissions(request):
    user = request.current_user
    permissions = _get_user_permissions(user)
    roles = _get_user_role_ids(user)

    return success({
        "user": {
            "id": user.id,
            "username": user.username,
            "name": user.name,
            "phone": user.phone,
            "email": user.email,
            "status": user.status,
            "roles": roles,
        },
        "permissions": permissions,
        "roles": roles,
    })


@require_http_methods(["GET"])
def get_user_page(request):
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("pageSize", 10))
    username = request.GET.get("username", None)

    queryset = SysUser.objects.filter(is_deleted=0)
    if username:
        queryset = queryset.filter(username__icontains=username)

    total = queryset.count()
    users = queryset.select_related().prefetch_related("roles").order_by("-create_at")[
        (page - 1) * page_size : page * page_size
    ]

    items = []
    for user in users:
        role_names = [role.name for role in user.roles.all()]
        items.append({
            "id": user.id,
            "username": user.username,
            "name": user.name,
            "phone": user.phone,
            "email": user.email,
            "status": user.status,
            "roles": [{"id": role.id, "name": role.name} for role in user.roles.all()],
            "rolesName": ",".join(role_names),
            "roleCount": user.roles.count(),
            "createdAt": user.create_at.strftime("%Y-%m-%d %H:%M:%S") if user.create_at else None,
            "updatedAt": user.update_at.strftime("%Y-%m-%d %H:%M:%S") if user.update_at else None,
        })

    total_pages = (total + page_size - 1) // page_size

    return success({
        "items": items,
        "page": page,
        "pageSize": page_size,
        "total": total,
        "totalPages": total_pages,
    })


@require_http_methods(["GET"])
def get_user_detail(request):
    user_id = request.GET.get("id")
    try:
        user = SysUser.objects.get(id=user_id, is_deleted=0)
    except SysUser.DoesNotExist:
        return error("用户不存在")

    return success({
        "id": user.id,
        "username": user.username,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "status": user.status,
        "roleIds": _get_user_role_ids(user),
        "roles": [{"id": role.id, "name": role.name} for role in user.roles.all()],
        "createdAt": user.create_at.strftime("%Y-%m-%d %H:%M:%S") if user.create_at else None,
        "updatedAt": user.update_at.strftime("%Y-%m-%d %H:%M:%S") if user.update_at else None,
    })


@require_http_methods(["POST"])
def create_user(request):
    data = _parse_body(request)
    username = data.get("username", "")
    password = data.get("password", "")

    if SysUser.objects.filter(username=username, is_deleted=0).exists():
        return error("用户名已存在")

    user = SysUser.objects.create(
        username=username,
        password=hash_password(password),
        name=data.get("name"),
        email=data.get("email"),
        phone=data.get("phone"),
        status=data.get("status", 1),
    )

    role_ids = data.get("roleIds", [])
    if role_ids:
        user.roles.set(role_ids)

    return success({
        "id": user.id,
        "username": user.username,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "status": user.status,
    })


@require_http_methods(["PUT"])
def update_user(request, user_id):
    data = _parse_body(request)

    try:
        user = SysUser.objects.get(id=user_id, is_deleted=0)
    except SysUser.DoesNotExist:
        return error("用户不存在")

    new_username = data.get("username")
    if new_username and new_username != user.username:
        if SysUser.objects.filter(username=new_username, is_deleted=0).exists():
            return error("用户名已存在")

    if new_username:
        user.username = new_username
    if data.get("password"):
        user.password = hash_password(data["password"])
    if "name" in data:
        user.name = data["name"]
    if "email" in data:
        user.email = data["email"]
    if "phone" in data:
        user.phone = data["phone"]
    if "status" in data:
        user.status = data["status"]
    user.save()

    if "roleIds" in data:
        user.roles.set(data["roleIds"] or [])

    return success({
        "id": user.id,
        "username": user.username,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "status": user.status,
    })


@require_http_methods(["DELETE"])
def delete_user(request, user_id):
    try:
        user = SysUser.objects.get(id=user_id, is_deleted=0)
    except SysUser.DoesNotExist:
        return error("用户不存在")

    user.is_deleted = 1
    user.deleted_at = datetime.now()
    user.save()

    return success()


@require_http_methods(["GET"])
def get_user_list(request):
    users = SysUser.objects.filter(is_deleted=0, status=1).prefetch_related("roles")
    return success([
        {
            "id": user.id,
            "username": user.username,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
        }
        for user in users
    ])


@require_http_methods(["POST"])
def update_password(request):
    data = _parse_body(request)
    old_password = data.get("oldPassword", "")
    new_password = data.get("newPassword", "")
    confirm_password = data.get("confirmPassword", "")

    if new_password != confirm_password:
        return error("新旧密码不一致")

    user = request.current_user

    if not verify_password(old_password, user.password):
        return error("旧密码错误")

    user.password = hash_password(new_password)
    user.save()

    return success()
