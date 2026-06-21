import time

from django.utils.deprecation import MiddlewareMixin

from utils import decode_access_token


class LogMiddleware(MiddlewareMixin):
    SKIP_PATHS = ["/admin/", "/static/"]

    def process_request(self, request):
        request._start_time = time.time()

    def process_response(self, request, response):
        start_time = getattr(request, "_start_time", None)
        if start_time is None:
            return response

        url = request.path
        if any(url.startswith(p) for p in self.SKIP_PATHS):
            return response

        latency = int((time.time() - start_time) * 1000)
        method = request.method

        params = None
        try:
            if method == "GET":
                params = str(dict(request.GET)) if request.GET else None
            else:
                body = request.body
                if body:
                    params = body.decode("utf-8")
        except Exception:
            params = None

        ip = request.META.get("REMOTE_ADDR")
        user_agent = request.META.get("HTTP_USER_AGENT", "")

        username = None
        try:
            auth_header = request.META.get("HTTP_AUTHORIZATION", "")
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                payload = decode_access_token(token)
                if payload:
                    user_id = payload.get("sub")
                    if user_id:
                        from systems.user.models import SysUser
                        user = SysUser.objects.get(id=int(user_id))
                        username = user.username
        except Exception:
            pass

        status = "success" if response.status_code < 400 else "error"
        log_type = 1 if status == "success" else 0

        try:
            from systems.log.models import SysLog
            SysLog.objects.create(
                username=username,
                ip=ip,
                method=method,
                url=url,
                params=params,
                user_agent=user_agent,
                status=status,
                latency=latency,
                type=log_type,
            )
        except Exception:
            pass

        return response
