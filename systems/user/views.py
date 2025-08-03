from django.contrib import auth
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json

@csrf_exempt
@require_POST
def login(request):
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            username = data.get('username', '')
            password = data.get('password', '')
        else:  # 表单格式
            username = request.POST.get('username', '')
            password = request.POST.get('password', '')
    except json.JSONDecodeError:
        return JsonResponse(
            {'code': 500, 'message': '无效的JSON格式'},
            status=500
        )

    # 参数验证
    if not username or not password:
        return JsonResponse(
            {'code': 500, 'message': '用户名和密码不能为空'},
            status=500
        )

    user = auth.authenticate(
        request, 
        username=username, 
        password=password
    )

    # 处理认证结果
    if user is not None and user.is_active:
        # 登录并创建会话
        auth.login(request, user)
        return JsonResponse({
            'code': 200,
            'message': '登录成功',
            'data': {
                'user_id': user.id,
                'username': user.username
            }
        })
    else:
        return JsonResponse(
            {'code': 500, 'message': '用户名或密码错误'},
            status=500
        )