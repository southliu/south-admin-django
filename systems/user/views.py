from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.hashers import make_password, check_password
from rest_framework_simplejwt.tokens import RefreshToken
from systems.user.models import User, UserSerializer
from systems.permission.models import Permission
from systems.role.models import Role

import json

@csrf_exempt
@require_POST
def login(request):
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body.decode('utf-8'))
            username = data.get('username', '')
            password = data.get('password', '')
        else:
            username = request.POST.get('username', '')
            password = request.POST.get('password', '')
    except json.JSONDecodeError:
        return JsonResponse({'code': 500, 'message': '无效的JSON格式'}, status=500)

    if not username or not password:
        return JsonResponse({'code': 500, 'message': '用户名和密码不能为空'}, status=500)
    
    try:
        user = User.objects.get(username=username)
        # 使用check_password验证密码
        if not check_password(password, user.password):
            return JsonResponse({'code': 500, 'message': '用户名或密码错误'}, status=500)
    except User.DoesNotExist:
        return JsonResponse({'code': 500, 'message': '用户名或密码错误'}, status=500)

    # 生成 JWT token
    refresh = RefreshToken.for_user(user)
    token = refresh.access_token

    # 序列化用户
    user_dict = UserSerializer(user).data

    # 获取用户关联的所有角色
    user_roles = user.roles.all()
    role_list = []
    for role in user_roles:
        role_list.append({
            'id': role.id,
            'name': role.name,
            'description': role.description
        })

    # 获取角色关联的所有权限
    permissions = Permission.objects.filter(rolepermission__role__in=user_roles).distinct()
    permission_list = []
    for permission in permissions:
        permission_list.append(permission.name)

    return JsonResponse({
        'code': 200,
        'message': '登录成功',
        'data': {
            'user': user_dict,
            'refresh': str(refresh),
            'token': str(token),
            'permissions': permission_list
        }
    })
