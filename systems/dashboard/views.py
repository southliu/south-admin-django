"""仪表盘及下拉演示数据接口（数据写死，仅保证前端页面正常加载）"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
def dashboard_trends(request):
    return JsonResponse({
        "code": 200,
        "message": "获取成功",
        "data": {
            "payDate": "2022-10-19 ~ 2022-10-29",
            "user": 9424,
            "recharge": 2590,
            "order": 3478,
            "game": 350,
        },
    })


@require_http_methods(["GET"])
def partner_list(request):
    return JsonResponse({
        "code": 200,
        "message": "获取成功",
        "data": [
            {"id": "1", "name": "演示公司A"},
            {"id": "2", "name": "演示公司B"},
            {"id": "3", "name": "演示公司C"},
        ],
    })


@require_http_methods(["GET"])
def game_list(request):
    return JsonResponse({
        "code": 200,
        "message": "获取成功",
        "data": [
            {"id": "1", "name": "演示游戏A"},
            {"id": "2", "name": "演示游戏B"},
            {"id": "3", "name": "演示游戏C"},
        ],
    })
