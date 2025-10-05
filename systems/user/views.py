from os import name
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken
from systems.user.models import User, UserSerializer, UserRole
from systems.menu.models import Menu
from systems.role.models import Role
from common.decorators import auth_required
from common.responses import success_response, error_response, model_to_dict, paginate_response

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
        return error_response('无效的JSON格式', 500)

    if not username or not password:
        return error_response('用户名和密码不能为空', 500)
    
    # 密码加密
    password = make_password(password, salt='salt_value', hasher='pbkdf2_sha256')

    try:
        user = User.objects.get(username=username, password=password)
    except User.DoesNotExist:
        return error_response('用户名或密码错误', 500)

    # 生成 JWT token
    refresh = RefreshToken.for_user(user)
    token = refresh.access_token

    # 序列化用户
    user_dict = UserSerializer(user).data

    # 获取用户关联的所有权限
    user_permissions = user.permissions.all()

    # 获取角色关联的所有权限
    permission_list = []
    for permission in user_permissions:
        permission_list.append(permission.name)

    return success_response({
        'user': user_dict,
        'token': str(token),
        'permissions': permission_list
    }, '登录成功')


@csrf_exempt
def refresh_permissions(request):
    """
    刷新用户权限信息
    """
    try:
        # 从请求头中获取Authorization
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Bearer '):
            return error_response('未提供有效的认证令牌', 401)
        
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
                return error_response('无效的认证令牌', 401)
        except Exception:
            return error_response('无效的认证令牌', 401)
        
        # 检查用户状态
        if user.status != 1:
            return error_response('用户账户已被禁用', 403)
        
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

        # 获取用户关联的所有权限（包括直接关联和通过角色关联的权限）
        # 直接关联的权限
        direct_permissions = user.permissions.all()
        
        permission_list = []
        for permission in direct_permissions:
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
        
        return success_response(response_data, message)
        
    except User.DoesNotExist:
        return error_response('用户不存在', 404)
    except Exception as e:
        return error_response(f'服务器内部错误: {str(e)}')


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
                roles_name.append(role.name)

            user_dict = model_to_dict(user)

            user_dict.pop('password', None)
            user_dict['roleCount'] = role_count
            user_dict['rolesName'] = roles_name
            
            user_items.append(user_dict)
        
        return paginate_response(user_items, page, page_size, total)
    except Exception as e:
        return error_response(f'服务器内部错误: {str(e)}')


# 用户详情接口
@csrf_exempt
@auth_required('GET')
def detail(request):
    try:
        # 获取用户ID参数
        user_id = request.GET.get('id')
        if not user_id:
            return error_response('缺少参数: id', 400)
        
        # 检查用户是否存在
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return error_response('用户不存在', 404)
        
        # 获取用户关联的未被软删除的角色ID列表
        role_ids = list(user.get_active_roles().values_list('id', flat=True))

        # 返回用户详情
        user_data = model_to_dict(user)
        user_data.pop('password', None)
        user_data['roleIds'] = role_ids

        return success_response(user_data)
        
    except Exception as e:
        return error_response(f'服务器内部错误: {str(e)}')


# 用户创建接口
@csrf_exempt
@auth_required('POST')
def create(request):
    try:
        # 解析请求体中的JSON数据
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return error_response('请求数据格式错误', 400)
        
        # 获取参数
        username = data.get('username')
        password = data.get('password')
        name = data.get('name')
        email = data.get('email')
        phone = data.get('phone')  # 获取电话字段
        status = data.get('status', 1)
        roles = data.get('roleIds', [])  # 角色ID列表
        
        # 参数校验
        if not username:
            return error_response('用户名不能为空', 400)
        
        if not password:
            return error_response('密码不能为空', 400)
        
        # 检查用户是否已存在
        if User.objects.filter(username=username).exists():
            return error_response('用户名已存在', 400)
        
        # 密码加密
        encrypted_password = make_password(password, salt='salt_value', hasher='pbkdf2_sha256')
        
        # 创建用户
        user = User.objects.create(
            username=username,
            password=encrypted_password,
            name=name,
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
        user_data = model_to_dict(user)
        user_data.pop('password', None)
        return success_response(user_data, '用户创建成功')
        
    except Exception as e:
        return error_response(f'服务器内部错误: {str(e)}')


# 用户更新接口
@csrf_exempt
@auth_required('PUT')
def update(request, user_id):
    try:
        # 检查用户是否存在
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return error_response('用户不存在', 404)
        
        # 解析请求体中的JSON数据
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return error_response('请求数据格式错误', 400)
        
        # 获取参数
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        phone = data.get('phone')
        name = data.get('name')
        status = data.get('status')
        roles = data.get('roleIds', [])  # 角色ID列表
        
        # 参数校验
        if not username:
            return error_response('用户名不能为空', 400)
        
        # 检查用户名是否已被其他用户使用
        if User.objects.filter(username=username).exclude(id=user_id).exists():
            return error_response('用户名已存在', 400)
        
        # 更新用户基本信息
        user.username = username
        if password:
            # 密码加密
            user.password = make_password(password, salt='salt_value', hasher='pbkdf2_sha256')
        if email is not None:
            user.email = email
        if phone is not None:
            user.phone = phone
        if name is not None:
            user.name = name
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
        user_data = model_to_dict(user)
        user_data.pop('password', None)
        return success_response(user_data, '用户更新成功')
        
    except Exception as e:
        return error_response(f'服务器内部错误: {str(e)}')


# 用户删除接口
@csrf_exempt
@auth_required('DELETE')
def delete(request, user_id):
    try:
        # 检查用户是否存在
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return error_response('用户不存在', 404)
        
        # 执行软删除
        user.delete()
        
        # 返回成功响应
        return success_response(None, '用户删除成功')
        
    except Exception as e:
        return error_response(f'服务器内部错误: {str(e)}')


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

            user_data = model_to_dict(user)
            user_data['roleCount'] = role_count;
            user_data.pop('password', None)
            user_items.append(user_data)
        
        return success_response(user_items)
        
    except Exception as e:
        return error_response(f'服务器内部错误: {str(e)}')

@csrf_exempt
@auth_required('POST')
def update_password(request):
    try:
        # 获取当前登录用户
        current_user = request.current_user
        
        # 解析请求体中的JSON数据
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return error_response('请求数据格式错误', 400)
        
        # 获取请求参数
        old_password = data.get('oldPassword')
        new_password = data.get('newPassword')
        confirm_password = data.get('confirmPassword')
        
        # 参数校验
        if not all([old_password, new_password, confirm_password]):
            return error_response('缺少必要参数', 400)
        
        # 密码加密
        password = make_password(old_password, salt='salt_value', hasher='pbkdf2_sha256')

        # 验证旧密码是否正确
        try:
            user = User.objects.get(username=current_user.username, password=password)
        except User.DoesNotExist:
            return error_response('旧密码不正确', 500)

        # 验证新密码与确认密码是否一致
        if new_password != confirm_password:
            return error_response('新密码与确认密码不一致', 400)
        
        # 更新密码
        new_password = make_password(new_password, salt='salt_value', hasher='pbkdf2_sha256')
        user.password = new_password
        user.save()
        
        return success_response(None, '密码修改成功')
        
    except Exception as e:
        return error_response(f'服务器内部错误: {str(e)}')

# 菜单树接口 - 返回用户已有权限和全部菜单列表
@csrf_exempt
@auth_required('GET')
def authorize(request):
    try:
        # 获取用户ID参数
        user_id = request.GET.get('userId')
        
        # 如果有userId则通过用户id获取，如果有roleId则从角色id获取
        if not user_id:
            return error_response('缺少参数: userId', 400)
            
        # 获取当前用户的角色
        user_roles = Role.objects.filter(users=request.current_user)
        
        # 获取当前角色可以获取到的全部菜单列表
        all_menus = Menu.objects.filter(
            rolemenu__role__in=user_roles,
            is_deleted=0
        ).distinct().order_by('order')

        
        # 构建完整的菜单树结构
        tree_data = build_menu_tree_for_user(all_menus)
        
        # 获取指定用户已有的权限菜单
        default_checked_keys = []
        try:
            from systems.user.models import User, UserPermission
            user = User.objects.get(id=user_id, is_deleted=0)
            # 从UserPermission获取用户直接关联的权限对应的菜单
            user_permissions = UserPermission.objects.filter(user=user).select_related('permission')
            permission_ids = [up.permission.id for up in user_permissions]
            # 获取这些权限关联的菜单
            checked_menus = Menu.objects.filter(permission_id__in=permission_ids, is_deleted=0)
            default_checked_keys = [str(menu.id) for menu in checked_menus]
        except User.DoesNotExist:
            # 用户不存在的情况下返回空列表
            default_checked_keys = []

        return success_response({
            'defaultCheckedKeys': default_checked_keys,
            'treeData': tree_data
        })
        
    except Exception as e:
        return error_response(f'服务器内部错误: {str(e)}')

def build_menu_tree_for_user(menus):
    """
    为角色构建菜单树结构，用于菜单分配
    """
    # 创建菜单字典，便于查找
    menu_dict = {}
    for menu in menus:
        menu_data = {
            'title': menu.label,
            'value': str(menu.id),
            'key': str(menu.id),
            'type': menu.type,
            'icon': menu.icon,
        }
        # 初始化所有节点都有children字段
        menu_data['children'] = []
        menu_dict[menu.id] = menu_data
    
    # 构建树形结构
    tree = []
    for menu in menus:
        menu_data = menu_dict[menu.id]
        # 如果有父菜单且父菜单在权限内，则添加到父菜单的children中
        if menu.parent_id and menu.parent_id in menu_dict:
            menu_dict[menu.parent_id]['children'].append(menu_data)
        else:
            # 否则作为根节点添加
            tree.append(menu_data)
    
    # 移除空的children字段
    def remove_empty_children(items):
        for item in items:
            if 'children' in item and item['children']:
                remove_empty_children(item['children'])
            elif 'children' in item and not item['children']:
                del item['children']
    
    remove_empty_children(tree)
    
    # 按照菜单顺序排序
    def sort_children(items):
        if not items:
            return
        items.sort(key=lambda x: int(x['value']))  # 按菜单ID排序
        for item in items:
            if 'children' in item and item['children']:
                sort_children(item['children'])
    
    sort_children(tree)
    
    return tree

# 保存用户菜单权限接口
@csrf_exempt
@auth_required('PUT')
def save_user_authorization(request):
    """
    保存用户授权信息
    参数:
    - userId: 用户ID
    - menuIds: 菜单ID数组
    """
    try:
        # 解析请求体中的JSON数据
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return error_response('请求数据格式错误', 400)
        
        # 获取参数
        user_id = data.get('userId')
        menu_ids = data.get('menuIds', [])
        
        # 参数校验
        if not user_id:
            return error_response('缺少用户ID参数', 400)
        
        # 检查用户是否存在
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return error_response('用户不存在', 404)
        
        # 删除对应的用户权限数据
        from systems.user.models import UserPermission
        UserPermission.objects.filter(user=user).delete()
        
        # 获取菜单对应的权限
        from systems.menu.models import Menu
        menus = Menu.objects.filter(id__in=menu_ids)
        
        # 收集所有菜单关联的权限
        permissions = []
        for menu in menus:
            if menu.permission:
                permissions.append(menu.permission)
        
        # 清除用户现有的直接权限关联
        from systems.user.models import UserPermission
        UserPermission.objects.filter(user=user).delete()
        
        # 创建新的用户权限关联
        user_permissions = []
        for permission in permissions:
            user_permissions.append(UserPermission(
                user=user,
                permission=permission
            ))
        
        if user_permissions:
            UserPermission.objects.bulk_create(user_permissions)
        
        return success_response(None, '用户授权保存成功')
        
    except Exception as e:
        return error_response(f'服务器内部错误: {str(e)}')
