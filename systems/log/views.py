import json

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from common.responses import success, error
from systems.log.models import SysLog


def _parse_body(request):
    try:
        return json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return {}


@require_http_methods(["POST"])
def create_log(request):
    data = _parse_body(request)

    SysLog.objects.create(
        username=data.get("username"),
        ip=data.get("ip"),
        method=data.get("method"),
        url=data.get("url"),
        params=data.get("params"),
        user_agent=data.get("userAgent"),
        status=data.get("status"),
        error=data.get("error"),
        latency=data.get("latency", 0),
        type=data.get("type", 0),
    )

    return success()


@require_http_methods(["GET"])
def get_log_page(request):
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("pageSize", 10))
    username = request.GET.get("username", None)
    log_type = int(request.GET.get("type", -1))

    queryset = SysLog.objects.all()
    if username:
        queryset = queryset.filter(username__icontains=username)
    if log_type >= 0:
        queryset = queryset.filter(type=log_type)

    total = queryset.count()
    logs = queryset.order_by("-create_at")[(page - 1) * page_size : page * page_size]

    items = []
    for log in logs:
        items.append({
            "id": log.id,
            "username": log.username,
            "ip": log.ip,
            "method": log.method,
            "url": log.url,
            "status": log.status,
            "error": log.error,
            "type": log.type,
            "createdAt": log.create_at.strftime("%Y-%m-%d %H:%M:%S") if log.create_at else None,
        })

    total_pages = (total + page_size - 1) // page_size

    return success({
        "items": items,
        "page": page,
        "pageSize": page_size,
        "total": total,
        "totalPages": total_pages,
    })


@require_http_methods(["DELETE"])
def delete_log(request, log_id):
    try:
        log = SysLog.objects.get(id=log_id)
    except SysLog.DoesNotExist:
        return error("日志不存在")

    log.delete()
    return success()


@require_http_methods(["POST"])
def batch_delete_log(request):
    data = _parse_body(request)
    log_ids = data.get("ids", [])

    SysLog.objects.filter(id__in=log_ids).delete()
    return success()
