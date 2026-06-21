import json
from datetime import datetime

from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from common.responses import success, error
from systems.menu.models import SysMenu
from systems.permission.models import SysPermission
from systems.user.models import SysUser

ACTION_LABELS = {
    "create": ("新增", "Create"),
    "update": ("修改", "Update"),
    "delete": ("删除", "Delete"),
    "detail": ("详情", "Detail"),
    "export": ("导出权限", "Export"),
    "status": ("状态权限", "Status"),
}


def _parse_body(request):
    try:
        return json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return {}


def _get_or_create_permission(name, description):
    permission, _ = SysPermission.objects.get_or_create(name=name, defaults={"description": description})
    return permission


def _build_menu_tree(menus, parent_id, include_button=False, allowed_ids=None):
    tree = []
    for menu in menus:
        if menu.parent_id == parent_id and (include_button or menu.type != 3):
            children = _build_menu_tree(menus, menu.id, include_button, allowed_ids)
            if allowed_ids is not None and menu.id not in allowed_ids and menu.type != 1 and not children:
                continue
            node = {
                "id": menu.id,
                "label": menu.label,
                "labelEn": menu.label_en,
                "title": menu.label,
                "titleEn": menu.label_en,
                "key": menu.router,
                "value": str(menu.id),
                "icon": menu.icon,
                "type": menu.type,
                "router": menu.router,
                "rule": menu.permission.name if menu.permission else None,
                "order": menu.order,
                "state": menu.state,
                "parentId": menu.parent_id,
                "permissionId": menu.permission_id,
                "createdAt": menu.create_at.strftime("%Y-%m-%d %H:%M:%S") if menu.create_at else None,
                "updatedAt": menu.update_at.strftime("%Y-%m-%d %H:%M:%S") if menu.update_at else None,
            }
            if children:
                node["children"] = children
            tree.append(node)
    return tree


@require_http_methods(["GET"])
def get_menu_list(request):
    user = request.current_user
    permission_ids = set()
    for role in user.roles.all():
        for menu in role.menus.all():
            if menu.permission_id:
                permission_ids.add(menu.permission_id)

    if not permission_ids:
        return success([])

    permitted_menu_ids = set(
        SysMenu.objects.filter(
            permission_id__in=permission_ids, is_deleted=0, type__in=[1, 2]
        ).values_list("id", flat=True)
    )

    if not permitted_menu_ids:
        return success([])

    all_menus = SysMenu.objects.filter(is_deleted=0, state=1).select_related("permission").order_by("order")
    tree = _build_menu_tree(list(all_menus), None, allowed_ids=permitted_menu_ids)

    return success(tree)


@require_http_methods(["GET"])
def get_menu_page(request):
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("pageSize", 10))
    label = request.GET.get("label", None)
    label_en = request.GET.get("labelEn", None)
    state = request.GET.get("state", None)
    rule = request.GET.get("rule", None)

    queryset = SysMenu.objects.filter(is_deleted=0)
    if label:
        queryset = queryset.filter(label__icontains=label)
    if label_en:
        queryset = queryset.filter(label_en__icontains=label_en)
    if state is not None and state != "":
        queryset = queryset.filter(state=int(state))
    if rule:
        queryset = queryset.filter(permission__name__icontains=rule)

    total = queryset.count()
    menus = queryset.select_related("permission").order_by("order")
    items = _build_menu_tree(list(menus), None, include_button=True)

    total_pages = (total + page_size - 1) // page_size

    return success({
        "items": items,
        "page": page,
        "pageSize": page_size,
        "total": total,
        "totalPages": total_pages,
    })


@require_http_methods(["GET"])
def get_menu_detail(request):
    menu_id = request.GET.get("id")
    try:
        menu = SysMenu.objects.select_related("permission").get(id=menu_id, is_deleted=0)
    except SysMenu.DoesNotExist:
        return error("菜单不存在")

    return success({
        "id": menu.id,
        "label": menu.label,
        "labelEn": menu.label_en,
        "icon": menu.icon,
        "type": menu.type,
        "router": menu.router,
        "rule": menu.permission.name if menu.permission else None,
        "order": menu.order,
        "state": menu.state,
        "parentId": menu.parent_id,
        "permissionId": menu.permission_id,
        "createdAt": menu.create_at.strftime("%Y-%m-%d %H:%M:%S") if menu.create_at else None,
        "updatedAt": menu.update_at.strftime("%Y-%m-%d %H:%M:%S") if menu.update_at else None,
    })


@require_http_methods(["POST"])
def create_menu(request):
    data = _parse_body(request)
    user = request.current_user

    permission_id = None
    rule = data.get("rule")
    if rule:
        permission = _get_or_create_permission(rule, data.get("label", ""))
        permission_id = permission.id

    menu = SysMenu.objects.create(
        label=data.get("label", ""),
        label_en=data.get("labelEn", ""),
        type=data.get("type", 2),
        icon=data.get("icon"),
        router=data.get("router"),
        order=data.get("order", 0),
        state=data.get("state", 1),
        parent_id=data.get("parentId"),
        permission_id=permission_id,
    )

    role_ids = list(user.roles.values_list("id", flat=True))
    if role_ids:
        for role_id in role_ids:
            role = user.roles.get(id=role_id)
            role.menus.add(menu)

    actions = data.get("actions")
    if actions and rule:
        for action in actions:
            labels = ACTION_LABELS.get(action)
            if not labels:
                continue
            button_rule = f"{rule}/{action}"
            button_permission = _get_or_create_permission(button_rule, labels[0])
            button_menu = SysMenu.objects.create(
                label=labels[0],
                label_en=labels[1],
                type=3,
                router="",
                order=0,
                state=1,
                parent=menu,
                permission=button_permission,
            )
            if role_ids:
                for role_id in role_ids:
                    role = user.roles.get(id=role_id)
                    role.menus.add(button_menu)

    return success({
        "id": menu.id,
        "label": menu.label,
        "labelEn": menu.label_en,
        "type": menu.type,
        "icon": menu.icon,
        "router": menu.router,
        "rule": menu.permission.name if menu.permission else None,
        "order": menu.order,
        "state": menu.state,
        "parentId": menu.parent_id,
    })


@require_http_methods(["PUT"])
def update_menu(request, menu_id):
    data = _parse_body(request)

    try:
        menu = SysMenu.objects.select_related("permission").get(id=menu_id, is_deleted=0)
    except SysMenu.DoesNotExist:
        return error("菜单不存在")

    menu.label = data.get("label", menu.label)
    menu.label_en = data.get("labelEn", menu.label_en)
    if "type" in data:
        menu.type = data["type"]
    if "icon" in data:
        menu.icon = data["icon"]
    if "router" in data:
        menu.router = data["router"]
    if "order" in data:
        menu.order = data["order"]
    if "state" in data:
        menu.state = data["state"]
    if "parentId" in data:
        menu.parent_id = data["parentId"]

    rule = data.get("rule")
    if rule is not None:
        if menu.permission:
            menu.permission.name = rule
            menu.permission.save()
        else:
            permission = SysPermission.objects.create(name=rule)
            menu.permission = permission

    menu.save()

    return success({
        "id": menu.id,
        "label": menu.label,
        "labelEn": menu.label_en,
        "type": menu.type,
        "icon": menu.icon,
        "router": menu.router,
        "rule": menu.permission.name if menu.permission else None,
        "order": menu.order,
        "state": menu.state,
        "parentId": menu.parent_id,
    })


@require_http_methods(["DELETE"])
def delete_menu(request, menu_id):
    try:
        menu = SysMenu.objects.get(id=menu_id, is_deleted=0)
    except SysMenu.DoesNotExist:
        return error("菜单不存在")

    menu.is_deleted = 1
    menu.deleted_at = datetime.now()
    menu.save()

    return success()


@require_http_methods(["POST"])
def batch_delete_menu(request):
    data = _parse_body(request)
    menu_ids = data.get("ids", [])

    if not menu_ids:
        return error("请选择要删除的菜单")

    menus = SysMenu.objects.filter(id__in=menu_ids, is_deleted=0)
    now = datetime.now()
    for menu in menus:
        menu.is_deleted = 1
        menu.deleted_at = now
        menu.save()

    return success()


@require_http_methods(["POST"])
def change_menu_state(request):
    data = _parse_body(request)
    menu_id = data.get("id")
    state = data.get("state")

    try:
        menu = SysMenu.objects.get(id=menu_id, is_deleted=0)
    except SysMenu.DoesNotExist:
        return error("菜单不存在")

    menu.state = state
    menu.save()

    return success()
