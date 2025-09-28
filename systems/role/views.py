from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from systems.menu.models import Menu
from systems.role.models import Role, RolePermission, RoleMenu
from common.decorators import auth_required
from common.responses import success_response, error_response, paginate_response, model_to_dict

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

            role_data = model_to_dict(role)
            role_data['menuCount'] = menu_count
            role_data['permissionCount'] = permission_count
            
            role_items.append(role_data)
        
        return paginate_response(role_items, page, page_size, total)

    except Exception as e:
        return error_response(f'服务器内部错误: {str(e)}')


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
            return error_response('请求数据格式错误', 400)
        
        # 获取参数
        name = data.get('name')
        description = data.get('description')
        authorize = data.get('authorize', [])  # 菜单ID列表
        
        # 参数校验
        if not name:
            return error_response('角色名称不能为空', 400)
        
        # 检查角色是否已存在
        if Role.objects.filter(name=name).exists():
            return error_response('角色已存在', 400)
        
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
        role_data = model_to_dict(role)
        return success_response(role_data, '角色创建成功')
        
    except Exception as e:
        return error_response(f'服务器内部错误: {str(e)}')


# 更新角色接口
@csrf_exempt
@auth_required('PUT')
def update(request, role_id):
    try:
        # 检查角色是否存在
        try:
            role = Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            return error_response('角色不存在', 404)
        
        # 解析请求体中的JSON数据
        import json
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return error_response('请求数据格式错误', 400)
        
        # 获取参数
        name = data.get('name')
        description = data.get('description')
        authorize = data.get('authorize', [])  # 菜单ID列表
        
        # 参数校验
        if not name:
            return error_response('角色名称不能为空', 400)
        
        # 检查角色名称是否已被其他角色使用
        if Role.objects.filter(name=name).exclude(id=role_id).exists():
            return error_response('角色名称已存在', 400)
        
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
                menus = Menu.objects.filter(id__in=authorize, is_deleted=0)
                
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
        role_data = model_to_dict(role)
        return success_response(role_data, '角色更新成功')
        
    except Exception as e:
        return error_response(f'服务器内部错误: {str(e)}')


# 获取角色详情接口
@csrf_exempt
@auth_required('GET')
def detail(request):
    try:
        # 获取角色ID参数
        role_id = request.GET.get('id')
        if not role_id:
            return error_response('缺少参数: id', 400)
        
        # 检查角色是否存在
        try:
            role = Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            return error_response('角色不存在', 404)
        
        # 获取角色关联的菜单ID列表
        menu_ids = list(role.rolemenu_set.values_list('menu_id', flat=True))
        
        # 返回角色详情
        role_data = model_to_dict(role)
        role_data['authorize'] = menu_ids
        return success_response(role_data)
        
    except Exception as e:
        return error_response(f'服务器内部错误: {str(e)}')


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
            role_data = model_to_dict(role)
            role_items.append(role_data)
        
        return success_response(role_items)
        
    except Exception as e:
        return error_response(f'服务器内部错误: {str(e)}')


# 删除角色接口
@csrf_exempt
@auth_required('DELETE')
def delete(request, role_id):
    try:
        # 检查角色是否存在
        try:
            role = Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            return error_response('角色不存在', 404)
        
        # 检查是否是管理员角色
        if role.name == 'admin':
            return error_response('不能删除管理员角色', 400)
        
        # 执行软删除
        role.delete()
        
        # 返回成功响应
        return success_response(None, '角色删除成功')
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': f'服务器内部错误: {str(e)}',
            'data': {}
        })

def build_menu_tree_for_role(menus):
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

# 获取角色权限接口
@csrf_exempt
@auth_required('GET')
def authorize(request):
    try:
        # 获取角色ID参数
        role_id = request.GET.get('roleId')
        
        # 如果有userId则通过用户id获取，如果有roleId则从角色id获取
        if not role_id:
            return error_response('缺少参数: roleId', 400)

        # 获取指定角色可以获取到的全部菜单列表
        all_menus = Menu.objects.filter(
            rolemenu__role__id=role_id,
            is_deleted=0
        ).distinct().order_by('order')

        
        # 构建完整的菜单树结构
        tree_data = build_menu_tree_for_role(all_menus)
        
        # 获取指定角色已有的权限菜单
        default_checked_keys = []
        role_menus = Menu.objects.filter(
            rolemenu__role__id=role_id,
            is_deleted=0
        ).distinct()
        
        # 提取菜单ID作为默认选中的键
        default_checked_keys = [str(menu.id) for menu in role_menus]
        
        return success_response({
            'defaultCheckedKeys': default_checked_keys,
            'treeData': tree_data
        })
        
    except Exception as e:
        return error_response(f'服务器内部错误: {str(e)}')


# 保存用户菜单权限接口
@csrf_exempt
@auth_required('PUT')
def save_authorize(request):
    try:
        # 解析请求体中的JSON数据
        import json
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return error_response('请求数据格式错误', 400)
        
        # 获取参数
        user_id = data.get('userId')
        menu_ids = data.get('menuIds', [])
        
        # 参数校验
        if not user_id:
            return error_response('缺少必要参数: userId', 400)
        
        # 检查用户是否存在
        try:
            from systems.user.models import User
            user = User.objects.get(id=user_id, is_deleted=0)
        except User.DoesNotExist:
            return error_response('用户不存在', 404)
        
        # 获取用户当前的角色
        user_roles = user.roles.filter(is_deleted=0)
        if not user_roles.exists():
            return error_response('用户未分配角色', 400)
        
        # 删除用户角色原有的菜单关联
        from systems.role.models import RoleMenu
        RoleMenu.objects.filter(role__in=user_roles).delete()
        
        # 为用户角色添加新的菜单关联
        role_menus = []
        for role in user_roles:
            for menu_id in menu_ids:
                try:
                    menu = Menu.objects.get(id=menu_id, is_deleted=0)
                    role_menus.append(RoleMenu(role=role, menu=menu))
                except Menu.DoesNotExist:
                    # 如果菜单不存在，则跳过
                    pass
        
        # 批量创建角色菜单关联
        if role_menus:
            RoleMenu.objects.bulk_create(role_menus)
        
        return success_response(None, '用户菜单权限保存成功')
        
    except Exception as e:
        return error_response(f'服务器内部错误: {str(e)}')

