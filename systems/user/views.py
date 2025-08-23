from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken
from systems.user.models import User, UserSerializer, UserRole
from systems.permission.models import Permission
from systems.role.models import Role
from common.decorators import auth_required

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


# 用户分页接口
@csrf_exempt
@auth_required('GET')
def page(request):
    try:
        # 获取查询参数
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('pageSize', 10))
        username = request.GET.get('username', '').strip()

        # 构建查询条件，只显示未被软删除的用户
        users = User.objects.filter(is_deleted=0)
        
        # 根据用户名进行过滤
        if username:
            users = users.filter(username__icontains=username)
        
        # 获取总数
        total = users.count()
        
        # 分页处理
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paginated_users = users[start_index:end_index]
        
        # 构建返回数据
        user_items = []
        for user in paginated_users:
            # 获取用户关联的角色数量（只统计未被软删除的角色）
            role_count = user.get_active_roles().count()
            
            # 获取用户关联的角色名称列表，优先使用description，不存在则使用name
            roles = user.get_active_roles()
            roles_name = []
            for role in roles:
                if role.description:
                    roles_name.append(role.description)
                else:
                    roles_name.append(role.name)
            
            user_items.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'phone': user.phone,  # 添加电话字段
                'status': user.status,
                'roleCount': role_count,
                'rolesName': roles_name,  # 添加角色名称列表，优先使用description
                'createdAt': user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else None,
                'updatedAt': user.updated_at.strftime('%Y-%m-%d %H:%M:%S') if user.updated_at else None,
            })
        
        return JsonResponse({
            'code': 200,
            'message': 'success',
            'data': {
                'items': user_items,
                'page': page,
                'pageSize': page_size,
                'total': total,
            }
        })
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': f'服务器内部错误: {str(e)}',
            'data': {}
        })


# 用户详情接口
@csrf_exempt
@auth_required('GET')
def detail(request):
    try:
        # 获取用户ID参数
        user_id = request.GET.get('id')
        if not user_id:
            return JsonResponse({
                'code': 400,
                'message': '缺少参数: id',
                'data': {}
            })
        
        # 检查用户是否存在
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                'code': 404,
                'message': '用户不存在',
                'data': {}
            })
        
        # 获取用户关联的未被软删除的角色ID列表
        role_ids = list(user.get_active_roles().values_list('id', flat=True))
        
        # 返回用户详情
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'phone': user.phone,  # 添加电话字段
            'status': user.status,
            'roleIds': role_ids,
            'createdAt': user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else None,
            'updatedAt': user.updated_at.strftime('%Y-%m-%d %H:%M:%S') if user.updated_at else None,
        }
        
        return JsonResponse({
            'code': 200,
            'message': 'success',
            'data': user_data
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': f'服务器内部错误: {str(e)}',
            'data': {}
        })


# 用户创建接口
@csrf_exempt
@auth_required('POST')
def create(request):
    try:
        # 解析请求体中的JSON数据
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'code': 400,
                'message': '请求数据格式错误',
                'data': {}
            })
        
        # 获取参数
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        phone = data.get('phone')  # 获取电话字段
        status = data.get('status', 1)
        roles = data.get('roles', [])  # 角色ID列表
        
        # 参数校验
        if not username:
            return JsonResponse({
                'code': 400,
                'message': '用户名不能为空',
                'data': {}
            })
        
        if not password:
            return JsonResponse({
                'code': 400,
                'message': '密码不能为空',
                'data': {}
            })
        
        # 检查用户是否已存在
        if User.objects.filter(username=username).exists():
            return JsonResponse({
                'code': 400,
                'message': '用户名已存在',
                'data': {}
            })
        
        # 密码加密
        encrypted_password = make_password(password, salt='salt_value', hasher='pbkdf2_sha256')
        
        # 创建用户
        user = User.objects.create(
            username=username,
            password=encrypted_password,
            email=email,
            phone=phone,  # 添加电话字段
            status=status
        )
        
        # 处理角色关联
        if roles:
            # 获取角色对象列表
            role_objects = Role.objects.filter(id__in=roles)
            
            # 创建用户角色关联
            user_roles = []
            for role in role_objects:
                user_roles.append(UserRole(
                    user=user,
                    role=role
                ))
            
            # 批量创建关联
            if user_roles:
                UserRole.objects.bulk_create(user_roles)
        
        # 返回成功响应
        return JsonResponse({
            'code': 200,
            'message': '用户创建成功',
            'data': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'phone': user.phone,  # 添加电话字段
                'status': user.status,
                'createdAt': user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else None,
                'updatedAt': user.updated_at.strftime('%Y-%m-%d %H:%M:%S') if user.updated_at else None,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': f'服务器内部错误: {str(e)}',
            'data': {}
        })


# 用户更新接口
@csrf_exempt
@auth_required('PUT')
def update(request, user_id):
    try:
        # 检查用户是否存在
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                'code': 404,
                'message': '用户不存在',
                'data': {}
            })
        
        # 解析请求体中的JSON数据
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'code': 400,
                'message': '请求数据格式错误',
                'data': {}
            })
        
        # 获取参数
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        phone = data.get('phone')  # 获取电话字段
        status = data.get('status')
        roles = data.get('roleIds', [])  # 角色ID列表
        
        # 参数校验
        if not username:
            return JsonResponse({
                'code': 400,
                'message': '用户名不能为空',
                'data': {}
            })
        
        # 检查用户名是否已被其他用户使用
        if User.objects.filter(username=username).exclude(id=user_id).exists():
            return JsonResponse({
                'code': 400,
                'message': '用户名已存在',
                'data': {}
            })
        
        # 更新用户基本信息
        user.username = username
        if password:
            # 密码加密
            user.password = make_password(password, salt='salt_value', hasher='pbkdf2_sha256')
        if email is not None:
            user.email = email
        if phone is not None:
            user.phone = phone
        if status is not None:
            user.status = status
        user.save()
        
        # 处理角色关联 - 先删除原有的关联，再创建新的关联
        if roles is not None:
            # 删除原有的用户角色关联
            UserRole.objects.filter(user=user).delete()
            
            # 创建新的角色关联
            if roles:
                # 获取角色对象列表
                role_objects = Role.objects.filter(id__in=roles)
                
                # 创建用户角色关联
                user_roles = []
                for role in role_objects:
                    user_roles.append(UserRole(
                        user=user,
                        role=role
                    ))
                
                # 批量创建关联
                if user_roles:
                    UserRole.objects.bulk_create(user_roles)
        
        # 返回成功响应
        return JsonResponse({
            'code': 200,
            'message': '用户更新成功',
            'data': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'phone': user.phone,  # 添加电话字段
                'status': user.status,
                'createdAt': user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else None,
                'updatedAt': user.updated_at.strftime('%Y-%m-%d %H:%M:%S') if user.updated_at else None,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': f'服务器内部错误: {str(e)}',
            'data': {}
        })


# 用户删除接口
@csrf_exempt
@auth_required('DELETE')
def delete(request, user_id):
    try:
        # 检查用户是否存在
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                'code': 404,
                'message': '用户不存在',
                'data': {}
            })
        
        # 执行软删除
        user.delete()
        
        # 返回成功响应
        return JsonResponse({
            'code': 200,
            'message': '用户删除成功',
            'data': {}
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': f'服务器内部错误: {str(e)}',
            'data': {}
        })


# 获取全部未被软删除用户列表接口
@csrf_exempt
@auth_required('GET')
def list_users(request):
    try:
        # 获取所有未被软删除的用户
        users = User.objects.filter(is_deleted=0)
        
        # 构建返回数据
        user_items = []
        for user in users:
            # 获取用户关联的角色数量（只统计未被软删除的角色）
            role_count = user.get_active_roles().count()
            
            user_items.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'phone': user.phone,
                'status': user.status,
                'roleCount': role_count,
                'createdAt': user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else None,
                'updatedAt': user.updated_at.strftime('%Y-%m-%d %H:%M:%S') if user.updated_at else None,
            })
        
        return JsonResponse({
            'code': 200,
            'message': 'success',
            'data': user_items
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': f'服务器内部错误: {str(e)}',
            'data': {}
        })
