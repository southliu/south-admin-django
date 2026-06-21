from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

from utils import decode_access_token


class AuthMiddleware(MiddlewareMixin):
    EXEMPT_PATHS = [
        "/system/user/login",
        "/system/user/logout",
    ]

    def process_view(self, request, view_func, view_args, view_kwargs):
        if any(request.path.startswith(p) for p in self.EXEMPT_PATHS):
            return None

        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Bearer "):
            return JsonResponse({"code": 401, "message": "未登录或登录已过期", "data": None}, status=401)

        token = auth_header.split(" ")[1]
        payload = decode_access_token(token)
        if payload is None:
            return JsonResponse({"code": 401, "message": "无效的认证凭据", "data": None}, status=401)

        user_id = payload.get("sub")
        if user_id is None:
            return JsonResponse({"code": 401, "message": "无效的认证凭据", "data": None}, status=401)

        from systems.user.models import SysUser
        try:
            user = SysUser.objects.get(id=int(user_id), is_deleted=0)
        except SysUser.DoesNotExist:
            return JsonResponse({"code": 401, "message": "用户不存在", "data": None}, status=401)

        request.current_user = user
        return None
