from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from systems.menu.models import Menu
from systems.role.models import Role
from common.decorators import auth_required

User = get_user_model()

# 列表接口
@csrf_exempt
@auth_required('GET')
def list(request):
    try:
        # 获取用户的角色
        user_roles = Role.objects.filter(users=request.current_user)
        
        # 通过角色获取关联的菜单，只显示type<3的数据
        menus = Menu.objects.filter(
            rolemenu__role__in=user_roles,
            state=True,
            type__lt=3
        ).distinct().order_by('order')
        
        # 构建菜单树
        menu_tree = build_menu_tree(menus)
        
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
            'rule': menu.rule,
            'type': menu.type,
            'order': menu.order,
            'state': menu.state,
            'createdAt': menu.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updatedAt': menu.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        }
        # 只有当children不为空时才添加到menu_data中
        if menu.get_children().exists():
            menu_data['children'] = []
        menu_dict[menu.id] = menu_data
    
    # 构建树形结构
    tree = []
    for menu in menus:
        menu_data = menu_dict[menu.id]
        # 如果有父菜单且父菜单在权限内，则添加到父菜单的children中
        if menu.parent_id and menu.parent_id in menu_dict:
            # 确保父节点有children字段
            if 'children' not in menu_dict[menu.parent_id]:
                menu_dict[menu.parent_id]['children'] = []
            menu_dict[menu.parent_id]['children'].append(menu_data)
        else:
            # 否则作为根节点添加
            tree.append(menu_data)
    
    # 按order字段排序
    tree.sort(key=lambda x: x['order'])
    # 对所有节点的children进行排序
    def sort_children(items):
        for item in items:
            if 'children' in item:
                item['children'].sort(key=lambda x: x['order'])
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
        
        # 获取用户的角色
        user_roles = Role.objects.filter(users=request.current_user)
        
        # 通过角色获取关联的菜单
        menus = Menu.objects.filter(
            rolemenu__role__in=user_roles,
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

        # 获取总数
        total = menus.count()
        
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
        rule = data.get('rule')
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
            rule=rule,
            order=order,
            state=state,
            parent=parent_menu
        )
        
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
                'rule': menu.rule,
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
        rule = data.get('rule')
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
        
        # 更新菜单
        menu.label = label
        menu.label_en = label_en
        menu.type = type_val
        menu.icon = icon
        menu.router = router
        menu.rule = rule
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
                'rule': menu.rule,
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
            'rule': menu.rule,
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