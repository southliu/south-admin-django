from django.views.decorators.csrf import csrf_exempt
from systems.menu.models import Menu
from systems.role.models import Role
from common.decorators import auth_required
from common.responses import success_response, error_response, paginate_response, model_to_dict
from systems.permission.models import Permission

# 列表接口
@csrf_exempt
@auth_required('GET')
def list(request):
    try:
        # 获取用户的角色
        user_roles = Role.objects.filter(users=request.current_user)
        
        # 通过角色获取关联的菜单，只显示type<3的数据
        user_menus = Menu.objects.filter(
            rolemenu__role__in=user_roles,
            is_deleted=0,
            type__lt=3
        ).distinct()
        
        # 收集所有需要显示的菜单ID
        menu_ids_to_show = set()
        
        # 添加用户直接拥有的菜单
        for menu in user_menus:
            menu_ids_to_show.add(menu.id)
            
        # 添加子菜单的祖先菜单（即使用户没有直接权限）
        for menu in user_menus:
            ancestors = menu.get_ancestors()
            for ancestor in ancestors:
                # 只添加state为1的祖先菜单
                if ancestor.state == 1 and ancestor.type < 3 and ancestor.is_deleted == 0:
                    menu_ids_to_show.add(ancestor.id)
        
        # 获取所有需要显示的菜单对象
        menus = Menu.objects.filter(
            id__in=menu_ids_to_show,
            is_deleted=0,
            type__lt=3
        ).distinct().order_by('order')
        
        # 构建菜单树
        menu_tree = build_menu_tree(menus)
        
        # 过滤掉state为0的节点（以及它们的子节点）
        def filter_menu_tree_by_state(items):
            filtered_items = []
            for item in items:
                if item['state'] == 1:  # 只保留state为1的节点
                    if 'children' in item:
                        item['children'] = filter_menu_tree_by_state(item['children'])
                    filtered_items.append(item)
            return filtered_items
        
        menu_tree = filter_menu_tree_by_state(menu_tree)
        
        return success_response(menu_tree)
        
    except Exception as e:
        return error_response(f'服务器内部错误: {str(e)}')


def build_menu_tree(menus):
    """
    构建菜单树结构
    """
    # 创建菜单字典，便于查找
    menu_dict = {}
    for menu in menus:
        menu_data = {
            'id': menu.id,
            'label': menu.label,
            'labelEn': menu.label_en,
            'icon': menu.icon,
            'router': menu.router,
            'key': menu.router,  # 将router字段作为key字段返回
            'rule': menu.permission.name if menu.permission else None,
            'type': menu.type,
            'order': menu.order,
            'state': menu.state,
            'createdAt': menu.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updatedAt': menu.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
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
    
    # 按order字段排序
    def sort_children(items):
        if not items:
            return
        items.sort(key=lambda x: x['order'])
        for item in items:
            if 'children' in item and item['children']:
                sort_children(item['children'])
    
    sort_children(tree)
    
    return tree

# 分页接口
@csrf_exempt
@auth_required('GET')
def page(request):
    try:
        # 获取查询参数
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('pageSize', 10))
        label = request.GET.get('label', '').strip()
        labelEn = request.GET.get('labelEn', '').strip()
        state = request.GET.get('state', None)
        rule = request.GET.get('rule', '').strip()

        # 获取用户的角色
        user_roles = Role.objects.filter(users=request.current_user)
        
        # 通过角色获取关联的菜单
        user_menus = Menu.objects.filter(
            rolemenu__role__in=user_roles,
            is_deleted=0,
        ).distinct()
        
        # 收集所有需要显示的菜单ID
        menu_ids_to_show = set()
        
        # 添加用户直接拥有的菜单
        for menu in user_menus:
            menu_ids_to_show.add(menu.id)
            
        # 添加子菜单的祖先菜单（即使用户没有直接权限）
        for menu in user_menus:
            ancestors = menu.get_ancestors()
            for ancestor in ancestors:
                # 只添加state为1的祖先菜单
                if ancestor.state == 1 and ancestor.is_deleted == 0:
                    menu_ids_to_show.add(ancestor.id)
        
        # 获取所有需要显示的菜单对象
        menus = Menu.objects.filter(
            id__in=menu_ids_to_show,
            is_deleted=0,
        ).distinct()
        
        if label:
            menus = menus.filter(label__icontains=label)
        if labelEn:
            menus = menus.filter(label_en__icontains=labelEn)
        if state is not None:
            # 正确处理数字类型和字符串类型的参数
            if isinstance(state, str):
                if state.isdigit():  # 数字字符串
                    state_value = bool(int(state))
                else:  # true/false字符串
                    state_value = state.lower() == 'true'
            else:  # 数字类型
                state_value = bool(int(state))
            menus = menus.filter(state=state_value)
        
        # 构建菜单树
        menu_tree = build_menu_tree(menus)
        
        # 新增针对权限名称(rule)的过滤
        if rule:
            filtered_menu_tree = [item for item in menu_tree if 
                                 (item.get('permission') and rule.lower() in item['permission'].lower()) or
                                 rule.lower() in str(item.get('label', '')).lower() or
                                 rule.lower() in str(item.get('labelEn', '')).lower()]
            menu_tree = filtered_menu_tree
        
        # 获取总数
        total = len(menu_tree)
        
        # 分页处理 - 只对最终结果进行分页
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paginated_tree = menu_tree[start_index:end_index]

        return paginate_response(paginated_tree, page, page_size, total)
        
    except Exception as e:
        return error_response(f'服务器内部错误: {str(e)}')


# 添加菜单创建接口
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
        label = data.get('label')
        label_en = data.get('labelEn')
        type_val = data.get('type')
        icon = data.get('icon')
        router = data.get('router')
        rule = data.get('rule')  # 这里将rule作为权限名称使用
        order = data.get('order', 0)
        state = data.get('state', 1)
        parent_id = data.get('parentId')
        actions = data.get('actions') # 快捷新增权限
        
        # 参数校验
        if not label or not type_val:
            return error_response('缺少必要参数: 中文名称或类型', 400)
        
        # 权限操作操作但rule不存在
        if not rule and actions:
            return error_response('权限标识不存在则无法快捷创建权限', 400)
        
        # 检查权限是否存在
        if rule:
            try:
                # 尝试获取已存在的权限
                permission = Permission.objects.get(name=rule)
                # 如果权限已存在，返回错误信息
                return error_response('权限已存在', 400, {
                    'permission_id': permission.id,
                    'permission_name': permission.name
                })
            except Permission.DoesNotExist:
                # 权限不存在，创建新权限
                permission = Permission.objects.create(
                    name=rule,
                    description=f"查看{label}权限"
                )
        else:
            permission = None
        
        # 检查父菜单是否存在
        parent_menu = None
        if parent_id:
            try:
                parent_menu = Menu.objects.get(id=parent_id)
            except Menu.DoesNotExist:
                return error_response('指定的父菜单不存在', 400)
        
        # 创建菜单
        menu = Menu.objects.create(
            label=label,
            label_en=label_en,
            type=type_val,
            icon=icon,
            router=router,
            permission=permission,
            order=order,
            state=state,
            parent=parent_menu
        )
        
        # 处理actions参数，为每个action创建对应的权限
        if actions and rule:
            for action in actions:
                # 构造权限名称 /{rule}/{action}
                action_permission_name = f"{rule}/{action}"
                try:
                    # 尝试获取已存在的权限
                    action_permission = Permission.objects.get(name=action_permission_name)
                except Permission.DoesNotExist:
                    # 权限不存在，创建新权限
                    action_permission = Permission.objects.create(
                        name=action_permission_name,
                        description=f"{label}-{action}权限"
                    )
    
        # 为当前用户的角色添加菜单关联
        from systems.role.models import RoleMenu
        user_roles = Role.objects.filter(users=request.current_user)
        for role in user_roles:
            RoleMenu.objects.get_or_create(role=role, menu=menu)
            
            # 如果有actions，同时为角色添加这些action权限
            if actions and rule:
                for action in actions:
                    action_permission_name = f"{rule}/{action}"
                    try:
                        action_permission = Permission.objects.get(name=action_permission_name)
                        from systems.role.models import RolePermission
                        RolePermission.objects.get_or_create(role=role, permission=action_permission)
                    except Permission.DoesNotExist:
                        # 如果权限不存在，则跳过
                        pass

                # 添加对应的按钮菜单
                if actions and rule:
                    # 定义action到中文名称的映射
                    action_names = {
                        'create': '创建权限',
                        'update': '更新权限',
                        'delete': '删除权限',
                        'detail': '详情权限',
                        'export': '导出权限',
                        'status': '状态权限'
                    }
                    
                    for action in actions:
                        # 获取action对应的中文名称，默认使用action名首字母大写
                        name = action_names.get(action, action.capitalize())

                        # 为每个action创建对应的按钮类型菜单
                        action_menu_label = f"{label}-{name}"
                        action_permission_name = f"{rule}/{action}"
                        
                        # 查找对应的权限
                        try:
                            action_permission = Permission.objects.get(name=action_permission_name)
                            
                            # 创建按钮菜单
                            button_menu = Menu.objects.create(
                                label=action_menu_label,
                                label_en=f"{label_en or label} {action.capitalize()}" if label_en or label else "",
                                type=3,  # 按钮类型
                                permission=action_permission,
                                parent=menu,  # 父菜单为当前创建的菜单
                                order=order,  # 使用相同排序
                                state=state   # 使用相同状态
                            )
                            
                            # 将按钮菜单与角色关联
                            RoleMenu.objects.get_or_create(role=role, menu=button_menu)
                        except Permission.DoesNotExist:
                            # 如果权限不存在则跳过
                            pass
        
        # 返回成功响应
        menu_data = model_to_dict(menu)
        menu_data['permission'] = menu.permission.name if menu.permission else None
        menu_data['parentId'] = menu.parent.id if menu.parent else None
        return success_response(menu_data, '菜单创建成功')
        
    except Exception as e:
        return error_response(f'服务器内部错误: {str(e)}')

# 删除菜单接口
@csrf_exempt
@auth_required('DELETE')
def delete(request, menu_id):
    try:
        # 检查菜单是否存在
        try:
            # 使用默认管理器，不包含已软删除的记录
            menu = Menu.objects.get(id=menu_id)
        except Menu.DoesNotExist:
            return error_response('菜单不存在', 404)
        
        # 检查是否存在子菜单
        if menu.get_children().filter(is_deleted=False).exists():
            return error_response('存在子菜单，请先删除子菜单', 400)
        
        # 执行软删除操作
        menu.delete()  # 这里调用的是模型中重写的delete方法
        
        # 返回成功响应
        return success_response(None, '菜单删除成功')
        
    except Exception as e:
        return error_response(f'服务器内部错误: {str(e)}')

# 更新菜单接口
@csrf_exempt
@auth_required('PUT')
def update(request, menu_id):
    try:
        # 检查菜单是否存在
        try:
            menu = Menu.objects.get(id=menu_id)
        except Menu.DoesNotExist:
            return error_response('菜单不存在', 404)
        
        # 解析请求体中的JSON数据
        import json
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return error_response('请求数据格式错误', 400)
        
        # 获取参数
        label = data.get('label')
        label_en = data.get('labelEn')
        type_val = data.get('type')
        icon = data.get('icon')
        router = data.get('router')
        rule = data.get('rule')  # 这里将rule作为权限名称使用
        order = data.get('order', 0)
        state = data.get('state', 1)
        parent_id = data.get('parentId')
        
        # 参数校验
        if not label or not type_val:
            return error_response('缺少必要参数: label 或 type', 400)
        
        # 检查父菜单是否存在
        parent_menu = None
        if parent_id:
            try:
                parent_menu = Menu.objects.get(id=parent_id)
                # 检查不能将菜单设置为自己的子菜单
                if parent_menu.id == menu.id:
                    return error_response('不能将菜单设置为自己的子菜单', 400)
            except Menu.DoesNotExist:
                return error_response('指定的父菜单不存在', 400)
        
        # 处理权限更新
        permission = menu.permission
        if rule and rule != (menu.permission.name if menu.permission else None):
            try:
                # 尝试获取已存在的权限
                permission = Permission.objects.get(name=rule)
                # 如果权限已存在，返回错误信息
                return error_response('权限已存在', 400, {
                    'permission_id': permission.id,
                    'permission_name': permission.name
                })
            except Permission.DoesNotExist:
                # 权限不存在，创建新权限
                permission = Permission.objects.create(
                    name=rule,
                    description=f"菜单 {label} 的权限"
                )
        elif not rule:
            permission = None
        
        # 更新菜单
        menu.label = label
        menu.label_en = label_en
        menu.type = type_val
        menu.icon = icon
        menu.router = router
        menu.permission = permission
        menu.order = order
        menu.state = state
        menu.parent = parent_menu
        menu.save()
        
        # 返回成功响应
        menu_data = model_to_dict(menu)
        menu_data['permission'] = menu.permission.name if menu.permission else None
        menu_data['parentId'] = menu.parent.id if menu.parent else None

        return success_response(menu_data, '菜单更新成功')
        
    except Exception as e:
        return error_response(f'服务器内部错误: {str(e)}')


# 修改菜单状态接口
@csrf_exempt
@auth_required('PUT')
def change_state(request):
    try:
        # 解析请求体中的JSON数据
        import json
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return error_response('请求数据格式错误', 400)
        
        # 获取参数
        menu_id = data.get('id')
        state = data.get('state')
        
        # 参数校验
        if menu_id is None:
            return error_response('缺少必要参数: id', 400)
        
        if state is None:
            return error_response('缺少必要参数: state', 400)
        
        # 验证state参数是否为有效值(0或1)
        if state not in [0, 1]:
            return error_response('state参数必须为0或1', 400)
        
        # 检查菜单是否存在
        try:
            menu = Menu.objects.get(id=menu_id)
        except Menu.DoesNotExist:
            return error_response('菜单不存在', 404)
        
        # 更新菜单状态
        menu.state = state
        menu.save()
        
        # 返回成功响应
        return success_response({
            'id': menu.id,
            'state': menu.state
        }, '菜单状态更新成功')
        
    except Exception as e:
        return error_response(f'服务器内部错误: {str(e)}')


# 获取菜单详情接口
@csrf_exempt
@auth_required('GET')
def detail(request):
    try:
        # 获取菜单ID参数
        menu_id = request.GET.get('id')
        if not menu_id:
            return error_response('缺少参数: id', 400)
        
        # 检查菜单是否存在
        try:
            menu = Menu.objects.get(id=menu_id)
        except Menu.DoesNotExist:
            return error_response('菜单不存在', 404)
        
        # 返回菜单详情
        menu_data = model_to_dict(menu)
        menu_data['parentId'] = menu.parent.id if menu.parent else None
        menu_data['rule'] = menu.permission.name if menu.permission else None
        
        return success_response(menu_data)
        
    except Exception as e:
        return error_response(f'服务器内部错误: {str(e)}')
