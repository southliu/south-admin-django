from django.http import JsonResponse
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken
from django.contrib.auth import get_user_model
from functools import wraps

User = get_user_model()

def auth_required(method='GET'):
    """
    认证装饰器，用于验证用户身份和请求方法
    :param method: 允许的请求方法，默认为GET
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # 检查请求方法
            if request.method != method:
                return JsonResponse({
                    'code': 405,
                    'message': '请求方法不允许',
                    'data': {}
                })
            
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
                
                # 将用户信息添加到request对象中供视图函数使用
                request.current_user = user
                
                # 调用原始视图函数
                return view_func(request, *args, **kwargs)
                
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
        return wrapper
    return decorator