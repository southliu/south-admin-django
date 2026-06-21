import json
from functools import wraps
from django.http import JsonResponse


def api_response(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            if isinstance(result, JsonResponse):
                return result
            return JsonResponse({"code": 200, "message": "success", "data": result})
        except ValueError as e:
            return JsonResponse({"code": 200, "message": str(e), "data": None})
        except Exception as e:
            return JsonResponse({"code": 500, "message": str(e), "data": None}, status=500)
    return wrapper
