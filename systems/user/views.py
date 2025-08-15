from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken
from systems.user.models import User, UserSerializer
from systems.permission.models import Permission

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
    
    # 密码加密
    password = make_password(password, salt='salt_value', hasher='pbkdf2_sha256')

    try:
        user = User.objects.get(username=username, password=password)
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
            'token': str(token),
            'permissions': permission_list
        }
    })


@csrf_exempt
def refresh_permissions(request):
    """
    刷新用户权限信息
    """
    try:
        # 从请求头中获取Authorization
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({
                'code': 401,
                'message': '未提供有效的认证令牌',
                'data': {}
            })
        
        # 获取refresh_cache参数，默认为True
        refresh_cache = request.GET.get('refresh_cache', 'true').lower() == 'true'
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body.decode('utf-8'))
                refresh_cache = data.get('refresh_cache', refresh_cache)
            except json.JSONDecodeError:
                pass
        
        # 提取token
        token_str = auth_header.split(' ')[1]
        
        # 验证token并获取用户信息
        try:
            token = AccessToken(token_str)
            user_id = token['user_id']
            user = User.objects.get(id=user_id)
        except InvalidToken:
            # 如果访问令牌无效或过期，尝试从刷新令牌获取用户信息
            try:
                refresh_token = RefreshToken(token_str)
                user_id = refresh_token['user_id']
                user = User.objects.get(id=user_id)
            except Exception:
                # 刷新令牌也无效
                return JsonResponse({
                    'code': 401,
                    'message': '无效的认证令牌',
                    'data': {}
                })
        except Exception:
            return JsonResponse({
                'code': 401,
                'message': '无效的认证令牌',
                'data': {}
            })
        
        # 检查用户状态
        if user.status != 1:
            return JsonResponse({
                'code': 403,
                'message': '用户账户已被禁用',
                'data': {}
            })
        
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
        
        # 根据refresh_cache参数决定是否生成新的JWT token
        response_data = {
            'user': user_dict,
            'permissions': permission_list,
            'roles': role_list
        }
        
        if refresh_cache:
            # 生成新的 JWT token
            refresh = RefreshToken.for_user(user)
            new_token = refresh.access_token
            response_data['token'] = str(new_token)
            message = '权限和令牌刷新成功'
        else:
            # 不刷新令牌时长，直接返回权限数据
            # 如果原始令牌有效，使用它；否则生成新令牌
            try:
                AccessToken(token_str)
                response_data['token'] = token_str
            except InvalidToken:
                # 原始令牌无效，生成新令牌
                refresh = RefreshToken.for_user(user)
                new_token = refresh.access_token
                response_data['token'] = str(new_token)
            message = '权限刷新成功'
        
        return JsonResponse({
            'code': 200,
            'message': message,
            'data': response_data
        })
        
    except User.DoesNotExist:
        return JsonResponse({
            'code': 404,
            'message': '用户不存在',
            'data': {}
        })
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': f'服务器内部错误: {str(e)}',
            'data': {}
        })
