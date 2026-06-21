from django.http import JsonResponse


def success(data=None, message="success"):
    return JsonResponse({"code": 200, "message": message, "data": data})


def error(message="error", code=200):
    return JsonResponse({"code": code, "message": message, "data": None})
