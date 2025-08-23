from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from systems.menu.models import Menu
from systems.role.models import Role, RolePermission, RoleMenu
from common.decorators import auth_required
from systems.permission.models import Permission

# 列表接口
@csrf_exempt
@auth_required('GET')
def page(request):
    try:
        # 获取查询参数
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('pageSize', 10))
        name = request.GET.get('name', '').strip()

        # 构建查询条件，只显示未被软删除的角色
        roles = Role.objects.filter(is_deleted=0)
        
        # 根据角色名称进行过滤
        if name:
            roles = roles.filter(name__icontains=name)
        
        # 获取总数
        total = roles.count()
        
        # 分页处理
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paginated_roles = roles[start_index:end_index]
        
        # 构建返回数据
        role_items = []
        for role in paginated_roles:
            # 获取角色关联的权限数量
            permission_count = role.rolepermission_set.count()
            
            # 获取角色关联的菜单数量
            menu_count = role.rolemenu_set.count()
            
            role_items.append({
                'id': role.id,
                'name': role.name,
                'description': role.description,
                'permissionCount': permission_count,
                'menuCount': menu_count,
                'createdAt': role.created_at.strftime('%Y-%m-%d %H:%M:%S') if role.created_at else None,
                'updatedAt': role.updated_at.strftime('%Y-%m-%d %H:%M:%S') if role.updated_at else None,
            })
        
        return JsonResponse({
            'code': 200,
            'message': 'success',
            'data': {
                'items': role_items,
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


# 创建角色接口
@csrf_exempt
@auth_required('POST')
def create(request):
    try:
        # 解析请求体中的JSON数据
        import json
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'code': 400,
                'message': '请求数据格式错误',
                'data': {}
            })
        
        # 获取参数
        name = data.get('name')
        description = data.get('description')
        authorize = data.get('authorize', [])  # 菜单ID列表
        
        # 参数校验
        if not name:
            return JsonResponse({
                'code': 400,
                'message': '角色名称不能为空',
                'data': {}
            })
        
        # 检查角色是否已存在
        if Role.objects.filter(name=name).exists():
            return JsonResponse({
                'code': 400,
                'message': '角色已存在',
                'data': {}
            })
        
        # 创建角色
        role = Role.objects.create(
            name=name,
            description=description
        )
        
        # 处理菜单关联
        if authorize:
            # 获取菜单对象列表
            menus = Menu.objects.filter(id__in=authorize)
            
            # 创建角色菜单关联
            role_menus = []
            role_permissions = []
            processed_permissions = set()  # 用于跟踪已处理的权限ID，避免重复
            
            for menu in menus:
                role_menus.append(RoleMenu(
                    role=role,
                    menu=menu
                ))
                
                # 如果菜单有关联权限，则也关联到角色
                if menu.permission and menu.permission.id not in processed_permissions:
                    role_permissions.append(RolePermission(
                        role=role,
                        permission=menu.permission
                    ))
                    processed_permissions.add(menu.permission.id)  # 记录已处理的权限ID
            
            # 批量创建菜单关联
            if role_menus:
                RoleMenu.objects.bulk_create(role_menus)
            
            # 批量创建权限关联
            if role_permissions:
                RolePermission.objects.bulk_create(role_permissions)
        
        # 返回成功响应
        return JsonResponse({
            'code': 200,
            'message': '角色创建成功',
            'data': {
                'id': role.id,
                'name': role.name,
                'description': role.description,
                'createdAt': role.created_at.strftime('%Y-%m-%d %H:%M:%S') if role.created_at else None,
                'updatedAt': role.updated_at.strftime('%Y-%m-%d %H:%M:%S') if role.updated_at else None,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': f'服务器内部错误: {str(e)}',
            'data': {}
        })


# 更新角色接口
@csrf_exempt
@auth_required('PUT')
def update(request, role_id):
    try:
        # 检查角色是否存在
        try:
            role = Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            return JsonResponse({
                'code': 404,
                'message': '角色不存在',
                'data': {}
            })
        
        # 解析请求体中的JSON数据
        import json
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'code': 400,
                'message': '请求数据格式错误',
                'data': {}
            })
        
        # 获取参数
        name = data.get('name')
        description = data.get('description')
        authorize = data.get('authorize', [])  # 菜单ID列表
        
        # 参数校验
        if not name:
            return JsonResponse({
                'code': 400,
                'message': '角色名称不能为空',
                'data': {}
            })
        
        # 检查角色名称是否已被其他角色使用
        if Role.objects.filter(name=name).exclude(id=role_id).exists():
            return JsonResponse({
                'code': 400,
                'message': '角色名称已存在',
                'data': {}
            })
        
        # 更新角色基本信息
        role.name = name
        role.description = description
        role.save()
        
        # 处理菜单关联 - 先删除原有的关联，再创建新的关联
        if authorize is not None:
            # 删除原有的角色菜单关联
            RoleMenu.objects.filter(role=role).delete()
            # 删除原有的角色权限关联
            RolePermission.objects.filter(role=role).delete()
            
            # 创建新的菜单关联
            if authorize:
                # 获取菜单对象列表
                menus = Menu.objects.filter(id__in=authorize)
                
                # 创建角色菜单关联
                role_menus = []
                role_permissions = []
                processed_permissions = set()  # 用于跟踪已处理的权限ID，避免重复
                
                for menu in menus:
                    role_menus.append(RoleMenu(
                        role=role,
                        menu=menu
                    ))
                    
                    # 如果菜单有关联权限，则也关联到角色
                    if menu.permission and menu.permission.id not in processed_permissions:
                        role_permissions.append(RolePermission(
                            role=role,
                            permission=menu.permission
                        ))
                        processed_permissions.add(menu.permission.id)  # 记录已处理的权限ID
                
                # 批量创建菜单关联
                if role_menus:
                    RoleMenu.objects.bulk_create(role_menus)
                
                # 批量创建权限关联
                if role_permissions:
                    RolePermission.objects.bulk_create(role_permissions)
        
        # 返回成功响应
        return JsonResponse({
            'code': 200,
            'message': '角色更新成功',
            'data': {
                'id': role.id,
                'name': role.name,
                'description': role.description,
                'createdAt': role.created_at.strftime('%Y-%m-%d %H:%M:%S') if role.created_at else None,
                'updatedAt': role.updated_at.strftime('%Y-%m-%d %H:%M:%S') if role.updated_at else None,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': f'服务器内部错误: {str(e)}',
            'data': {}
        })


# 获取角色详情接口
@csrf_exempt
@auth_required('GET')
def detail(request):
    try:
        # 获取角色ID参数
        role_id = request.GET.get('id')
        if not role_id:
            return JsonResponse({
                'code': 400,
                'message': '缺少参数: id',
                'data': {}
            })
        
        # 检查角色是否存在
        try:
            role = Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            return JsonResponse({
                'code': 404,
                'message': '角色不存在',
                'data': {}
            })
        
        # 获取角色关联的菜单ID列表
        menu_ids = list(role.rolemenu_set.values_list('menu_id', flat=True))
        
        # 返回角色详情
        role_data = {
            'id': role.id,
            'name': role.name,
            'description': role.description,
            'authorize': menu_ids,
            'createdAt': role.created_at.strftime('%Y-%m-%d %H:%M:%S') if role.created_at else None,
            'updatedAt': role.updated_at.strftime('%Y-%m-%d %H:%M:%S') if role.updated_at else None,
        }
        
        return JsonResponse({
            'code': 200,
            'message': 'success',
            'data': role_data
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': f'服务器内部错误: {str(e)}',
            'data': {}
        })


# 获取全部未被软删除角色列表接口
@csrf_exempt
@auth_required('GET')
def list_roles(request):
    try:
        # 获取所有未被软删除的角色
        roles = Role.objects.filter(is_deleted=0)
        
        # 构建返回数据
        role_items = []
        for role in roles:
            role_items.append({
                'id': role.id,
                'name': role.name,
                'description': role.description,
                'createdAt': role.created_at.strftime('%Y-%m-%d %H:%M:%S') if role.created_at else None,
                'updatedAt': role.updated_at.strftime('%Y-%m-%d %H:%M:%S') if role.updated_at else None,
            })
        
        return JsonResponse({
            'code': 200,
            'message': 'success',
            'data': role_items
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': f'服务器内部错误: {str(e)}',
            'data': {}
        })


# 删除角色接口
@csrf_exempt
@auth_required('DELETE')
def delete(request, role_id):
    try:
        # 检查角色是否存在
        try:
            role = Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            return JsonResponse({
                'code': 404,
                'message': '角色不存在',
                'data': {}
            })
        
        # 检查是否是管理员角色
        if role.name == 'admin':
            return JsonResponse({
                'code': 400,
                'message': '不能删除管理员角色',
                'data': {}
            })
        
        # 执行软删除
        role.delete()
        
        # 返回成功响应
        return JsonResponse({
            'code': 200,
            'message': '角色删除成功',
            'data': {}
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': f'服务器内部错误: {str(e)}',
            'data': {}
        })
