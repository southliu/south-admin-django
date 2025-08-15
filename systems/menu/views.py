from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken
from django.contrib.auth import get_user_model
from systems.menu.models import Menu
from systems.role.models import Role

User = get_user_model()

@csrf_exempt
def list(request):
    # 获取token中的用户信息
    try:
        # 从请求头中获取Authorization
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({
                'code': 401,
                'message': '未提供有效的认证令牌',
                'data': {}
            })
        
        # 提取token
        token_str = auth_header.split(' ')[1]
        
        # 验证token并获取用户信息
        token = AccessToken(token_str)
        user_id = token['user_id']
        user = User.objects.get(id=user_id)
        
        # 检查用户状态
        if user.status != 1:
            return JsonResponse({
                'code': 403,
                'message': '用户账户已被禁用',
                'data': {}
            })
        
        # 获取用户的角色
        user_roles = Role.objects.filter(users=user)
        
        # 通过角色获取关联的菜单
        menus = Menu.objects.filter(
            rolemenu__role__in=user_roles,
            is_visible=True
        ).distinct().order_by('order')
        
        # 构建菜单树
        menu_tree = build_menu_tree(menus)
        
        return JsonResponse({
            'code': 200,
            'message': 'success',
            'data': menu_tree
        })
        
    except InvalidToken:
        return JsonResponse({
            'code': 401,
            'message': '无效的认证令牌',
            'data': {}
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


def build_menu_tree(menus):
    """
    构建菜单树结构
    """
    # 创建菜单字典，便于查找
    menu_dict = {}
    for menu in menus:
        menu_dict[menu.id] = {
            'id': menu.id,
            'label': menu.label,
            'labelEn': menu.labelEn,
            'icon': menu.icon,
            'router': menu.router,
            'key': menu.router,  # 将router字段作为key字段返回
            'rule': menu.rule,
            'order': menu.order,
            'is_visible': menu.is_visible,
            'children': []
        }
    
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
    
    # 按order字段排序
    tree.sort(key=lambda x: x['order'])
    for item in tree:
        item['children'].sort(key=lambda x: x['order'])
    
    return tree
