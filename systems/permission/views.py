import json
from datetime import datetime

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from common.responses import success, error
from systems.permission.models import SysPermission


def _parse_body(request):
    try:
        return json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return {}


@require_http_methods(["GET"])
def get_permission_page(request):
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("pageSize", 10))
    name = request.GET.get("name", None)

    queryset = SysPermission.objects.filter(is_deleted=0)
    if name:
        queryset = queryset.filter(name__icontains=name)

    total = queryset.count()
    permissions = queryset.order_by("-create_at")[(page - 1) * page_size : page * page_size]

    items = []
    for p in permissions:
        items.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "createdAt": p.create_at.strftime("%Y-%m-%d %H:%M:%S") if p.create_at else None,
            "updatedAt": p.update_at.strftime("%Y-%m-%d %H:%M:%S") if p.update_at else None,
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
def get_permission_detail(request):
    permission_id = request.GET.get("id")
    try:
        p = SysPermission.objects.get(id=permission_id, is_deleted=0)
    except SysPermission.DoesNotExist:
        return error("权限不存在")

    return success({
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "createdAt": p.create_at.strftime("%Y-%m-%d %H:%M:%S") if p.create_at else None,
        "updatedAt": p.update_at.strftime("%Y-%m-%d %H:%M:%S") if p.update_at else None,
    })


@require_http_methods(["POST"])
def create_permission(request):
    data = _parse_body(request)
    name = data.get("name", "")

    if SysPermission.objects.filter(name=name, is_deleted=0).exists():
        return error("权限名已存在")

    p = SysPermission.objects.create(
        name=name,
        description=data.get("description"),
    )

    return success({
        "id": p.id,
        "name": p.name,
        "description": p.description,
    })


@require_http_methods(["PUT"])
def update_permission(request, permission_id):
    data = _parse_body(request)

    try:
        p = SysPermission.objects.get(id=permission_id, is_deleted=0)
    except SysPermission.DoesNotExist:
        return error("权限不存在")

    new_name = data.get("name")
    if new_name and new_name != p.name:
        if SysPermission.objects.filter(name=new_name, is_deleted=0).exists():
            return error("权限名已存在")

    if new_name:
        p.name = new_name
    if "description" in data:
        p.description = data["description"]
    p.save()

    return success({
        "id": p.id,
        "name": p.name,
        "description": p.description,
    })


@require_http_methods(["DELETE"])
def delete_permission(request, permission_id):
    try:
        p = SysPermission.objects.get(id=permission_id, is_deleted=0)
    except SysPermission.DoesNotExist:
        return error("权限不存在")

    p.is_deleted = 1
    p.deleted_at = datetime.now()
    p.save()

    return success()


@require_http_methods(["GET"])
def get_permission_list(request):
    permissions = SysPermission.objects.filter(is_deleted=0)
    return success([
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
        }
        for p in permissions
    ])
