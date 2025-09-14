from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from systems.menu.models import Menu
from systems.role.models import Role
from common.decorators import auth_required
from systems.permission.models import Permission

# 列表接口
@csrf_exempt
@auth_required('GET')
def list(request):
    try:
        # 获取用户的角色
        user_roles = Role.objects.filter(users=request.current_user)
        
        # 通过角色获取关联的菜单，只显示type<3的数据，state过滤将在构建树时处理
        menus = Menu.objects.filter(
            rolemenu__role__in=user_roles,
            is_deleted=0,
            type__lt=3
        ).distinct().order_by('order')
        
        # 构建菜单树
        menu_tree = build_menu_tree(menus)
        
        # 过滤掉state为0的节点
        def filter_menu_tree_by_state(items):
            filtered_items = []
            for item in items:
                if item['state'] == 1:  # 只保留state为1的节点
                    if 'children' in item:
                        item['children'] = filter_menu_tree_by_state(item['children'])
                    filtered_items.append(item)
            return filtered_items
        
        menu_tree = filter_menu_tree_by_state(menu_tree)
        
        return JsonResponse({
            'code': 200,
            'message': 'success',
            'data': menu_tree
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': f'服务器内部错误: {str(e)}',
            'data': {}
        })


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
        menus = Menu.objects.filter(
            rolemenu__role__in=user_roles,
            is_deleted=0,
        ).distinct().order_by('order')
        
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
        
        return JsonResponse({
            'code': 200,
            'message': 'success',
            'data': {
                'items': paginated_tree,
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
            return JsonResponse({
                'code': 400,
                'message': '请求数据格式错误',
                'data': {}
            })
        
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
            return JsonResponse({
                'code': 400,
                'message': '缺少必要参数: label 或 type',
                'data': {}
            })
        
        # 权限操作操作但rule不存在
        if not rule and actions:
            return JsonResponse({
                'code': 400,
                'message': '权限标识不存在则无法快捷创建权限',
                'data': {}
            })
        
        # 检查权限是否存在
        if rule:
            try:
                # 尝试获取已存在的权限
                permission = Permission.objects.get(name=rule)
                # 如果权限已存在，返回错误信息
                return JsonResponse({
                    'code': 400,
                    'message': '权限已存在',
                    'data': {
                        'permission_id': permission.id,
                        'permission_name': permission.name
                    }
                })
            except Permission.DoesNotExist:
                # 权限不存在，创建新权限
                permission = Permission.objects.create(
                    name=rule,
                    description=f"菜单 {label} 的权限"
                )
        else:
            permission = None
        
        # 检查父菜单是否存在
        parent_menu = None
        if parent_id:
            try:
                parent_menu = Menu.objects.get(id=parent_id)
            except Menu.DoesNotExist:
                return JsonResponse({
                    'code': 400,
                    'message': '指定的父菜单不存在',
                    'data': {}
                })
        
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
                        description=f"菜单 {label} 的 {action} 权限"
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
        
        # 返回成功响应
        return JsonResponse({
            'code': 200,
            'message': '菜单创建成功',
            'data': {
                'id': menu.id,
                'label': menu.label,
                'labelEn': menu.label_en,
                'type': menu.type,
                'icon': menu.icon,
                'router': menu.router,
                'permission': menu.permission.name if menu.permission else None,
                'order': menu.order,
                'state': menu.state,
                'parentId': menu.parent.id if menu.parent else None,
                'createdAt': menu.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updatedAt': menu.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': f'服务器内部错误: {str(e)}',
            'data': {}
        })

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
            return JsonResponse({
                'code': 404,
                'message': '菜单不存在',
                'data': {}
            })
        
        # 检查是否存在子菜单
        if menu.get_children().filter(is_deleted=False).exists():
            return JsonResponse({
                'code': 400,
                'message': '存在子菜单，请先删除子菜单',
                'data': {}
            })
        
        # 执行软删除操作
        menu.delete()  # 这里调用的是模型中重写的delete方法
        
        # 返回成功响应
        return JsonResponse({
            'code': 200,
            'message': '菜单删除成功',
            'data': {}
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': f'服务器内部错误: {str(e)}',
            'data': {}
        })

# 更新菜单接口
@csrf_exempt
@auth_required('PUT')
def update(request, menu_id):
    try:
        # 检查菜单是否存在
        try:
            menu = Menu.objects.get(id=menu_id)
        except Menu.DoesNotExist:
            return JsonResponse({
                'code': 404,
                'message': '菜单不存在',
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
            return JsonResponse({
                'code': 400,
                'message': '缺少必要参数: label 或 type',
                'data': {}
            })
        
        # 检查父菜单是否存在
        parent_menu = None
        if parent_id:
            try:
                parent_menu = Menu.objects.get(id=parent_id)
                # 检查不能将菜单设置为自己的子菜单
                if parent_menu.id == menu.id:
                    return JsonResponse({
                        'code': 400,
                        'message': '不能将菜单设置为自己的子菜单',
                        'data': {}
                    })
            except Menu.DoesNotExist:
                return JsonResponse({
                    'code': 400,
                    'message': '指定的父菜单不存在',
                    'data': {}
                })
        
        # 处理权限更新
        permission = menu.permission
        if rule and rule != (menu.permission.name if menu.permission else None):
            try:
                # 尝试获取已存在的权限
                permission = Permission.objects.get(name=rule)
                # 如果权限已存在，返回错误信息
                return JsonResponse({
                    'code': 400,
                    'message': '权限已存在',
                    'data': {
                        'permission_id': permission.id,
                        'permission_name': permission.name
                    }
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
        return JsonResponse({
            'code': 200,
            'message': '菜单更新成功',
            'data': {
                'id': menu.id,
                'label': menu.label,
                'labelEn': menu.label_en,
                'type': menu.type,
                'icon': menu.icon,
                'router': menu.router,
                'rule': menu.permission.name if menu.permission else None,
                'order': menu.order,
                'state': menu.state,
                'parentId': menu.parent.id if menu.parent else None,
                'createdAt': menu.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updatedAt': menu.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': f'服务器内部错误: {str(e)}',
            'data': {}
        })


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
            return JsonResponse({
                'code': 400,
                'message': '请求数据格式错误',
                'data': {}
            })
        
        # 获取参数
        menu_id = data.get('id')
        state = data.get('state')
        
        # 参数校验
        if menu_id is None:
            return JsonResponse({
                'code': 400,
                'message': '缺少必要参数: id',
                'data': {}
            })
        
        if state is None:
            return JsonResponse({
                'code': 400,
                'message': '缺少必要参数: state',
                'data': {}
            })
        
        # 验证state参数是否为有效值(0或1)
        if state not in [0, 1]:
            return JsonResponse({
                'code': 400,
                'message': 'state参数必须为0或1',
                'data': {}
            })
        
        # 检查菜单是否存在
        try:
            menu = Menu.objects.get(id=menu_id)
        except Menu.DoesNotExist:
            return JsonResponse({
                'code': 404,
                'message': '菜单不存在',
                'data': {}
            })
        
        # 更新菜单状态
        menu.state = state
        menu.save()
        
        # 返回成功响应
        return JsonResponse({
            'code': 200,
            'message': '菜单状态更新成功',
            'data': {
                'id': menu.id,
                'state': menu.state
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': f'服务器内部错误: {str(e)}',
            'data': {}
        })


# 获取菜单详情接口
@csrf_exempt
@auth_required('GET')
def detail(request):
    try:
        # 获取菜单ID参数
        menu_id = request.GET.get('id')
        if not menu_id:
            return JsonResponse({
                'code': 400,
                'message': '缺少参数: id',
                'data': {}
            })
        
        # 检查菜单是否存在
        try:
            menu = Menu.objects.get(id=menu_id)
        except Menu.DoesNotExist:
            return JsonResponse({
                'code': 404,
                'message': '菜单不存在',
                'data': {}
            })
        
        # 返回菜单详情
        menu_data = {
            'id': menu.id,
            'label': menu.label,
            'labelEn': menu.label_en,
            'type': menu.type,
            'icon': menu.icon,
            'router': menu.router,
            'rule': menu.permission.name if menu.permission else None,
            'order': menu.order,
            'state': menu.state,
            'parentId': menu.parent.id if menu.parent else None,
            'createdAt': menu.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updatedAt': menu.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        return JsonResponse({
            'code': 200,
            'message': 'success',
            'data': menu_data
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': f'服务器内部错误: {str(e)}',
            'data': {}
        })
