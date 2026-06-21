import json
from datetime import datetime

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from common.responses import success, error
from systems.role.models import SysRole
from systems.menu.models import SysMenu
from systems.permission.models import SysPermission


def _parse_body(request):
    try:
        return json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return {}


@require_http_methods(["GET"])
def get_role_page(request):
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("pageSize", 10))
    name = request.GET.get("name", None)

    queryset = SysRole.objects.filter(is_deleted=0)
    if name:
        queryset = queryset.filter(name__icontains=name)

    total = queryset.count()
    roles = queryset.order_by("-create_at")[(page - 1) * page_size : page * page_size]

    items = []
    for role in roles:
        items.append({
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "createdAt": role.create_at.strftime("%Y-%m-%d %H:%M:%S") if role.create_at else None,
            "updatedAt": role.update_at.strftime("%Y-%m-%d %H:%M:%S") if role.update_at else None,
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
def get_role_detail(request):
    role_id = request.GET.get("id")
    try:
        role = SysRole.objects.get(id=role_id, is_deleted=0)
    except SysRole.DoesNotExist:
        return error("角色不存在")

    menu_ids = list(role.menus.values_list("id", flat=True))

    return success({
        "id": role.id,
        "name": role.name,
        "description": role.description,
        "createdAt": role.create_at.strftime("%Y-%m-%d %H:%M:%S") if role.create_at else None,
        "updatedAt": role.update_at.strftime("%Y-%m-%d %H:%M:%S") if role.update_at else None,
        "authorize": menu_ids,
    })


@require_http_methods(["POST"])
def create_role(request):
    data = _parse_body(request)
    name = data.get("name", "")

    if SysRole.objects.filter(name=name, is_deleted=0).exists():
        return error("角色名已存在")

    role = SysRole.objects.create(
        name=name,
        description=data.get("description"),
    )

    authorize = data.get("authorize")
    if authorize:
        role.menus.set(authorize)

    return success({
        "id": role.id,
        "name": role.name,
        "description": role.description,
    })


@require_http_methods(["PUT"])
def update_role(request, role_id):
    data = _parse_body(request)

    try:
        role = SysRole.objects.get(id=role_id, is_deleted=0)
    except SysRole.DoesNotExist:
        return error("角色不存在")

    new_name = data.get("name")
    if new_name and new_name != role.name:
        if SysRole.objects.filter(name=new_name, is_deleted=0).exists():
            return error("角色名已存在")

    if new_name:
        role.name = new_name
    if "description" in data:
        role.description = data["description"]
    role.save()

    if "authorize" in data:
        role.menus.set(data["authorize"] or [])

    return success({
        "id": role.id,
        "name": role.name,
        "description": role.description,
    })


@require_http_methods(["DELETE"])
def delete_role(request, role_id):
    try:
        role = SysRole.objects.get(id=role_id, is_deleted=0)
    except SysRole.DoesNotExist:
        return error("角色不存在")

    role.is_deleted = 1
    role.deleted_at = datetime.now()
    role.save()

    return success()


@require_http_methods(["GET"])
def get_role_list(request):
    roles = SysRole.objects.filter(is_deleted=0)
    return success([
        {
            "id": role.id,
            "name": role.name,
            "description": role.description,
        }
        for role in roles
    ])


def _build_authorize_tree(menus, parent_id, role_menu_ids):
    tree = []
    for menu in menus:
        if menu.parent_id == parent_id:
            children = _build_authorize_tree(menus, menu.id, role_menu_ids)
            if menu.id not in role_menu_ids and not children:
                continue
            node = {
                "title": menu.label,
                "value": str(menu.id),
                "key": str(menu.id),
                "type": menu.type,
                "icon": menu.icon,
            }
            if children:
                node["children"] = children
            tree.append(node)
    return tree


def role_authorize(request):
    if request.method == "GET":
        return _get_role_authorize(request)
    elif request.method == "POST":
        return _save_role_authorize(request)
    return error("不支持的请求方法")


def _get_role_authorize(request):
    role_id = request.GET.get("roleId")
    try:
        role = SysRole.objects.get(id=role_id, is_deleted=0)
    except SysRole.DoesNotExist:
        return error("角色不存在")

    role_menu_ids = set(role.menus.values_list("id", flat=True))
    default_checked_keys = [str(mid) for mid in role_menu_ids]

    all_menus = SysMenu.objects.filter(is_deleted=0).order_by("order")
    tree_data = _build_authorize_tree(list(all_menus), None, role_menu_ids)

    return success({
        "defaultCheckedKeys": default_checked_keys,
        "treeData": tree_data,
    })


def _save_role_authorize(request):
    data = _parse_body(request)
    role_id = data.get("roleId")
    menu_ids = data.get("menuIds", [])

    try:
        role = SysRole.objects.get(id=role_id, is_deleted=0)
    except SysRole.DoesNotExist:
        return error("角色不存在")

    role.menus.set(menu_ids)

    return success()
