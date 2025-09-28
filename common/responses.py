from django.http import JsonResponse
from datetime import datetime
import re

def to_camel_case(snake_str):
    """
    将下划线命名转换为驼峰命名
    
    :param snake_str: 下划线命名的字符串
    :return: 驼峰命名的字符串
    """
    components = snake_str.split('_')
    # 将第一个单词首字母小写，其他单词首字母大写
    return components[0] + ''.join(x.capitalize() for x in components[1:])

def success_response(data=None, message='success', code=200):
    """
    成功响应
    
    :param data: 返回的数据
    :param message: 返回的消息
    :param code: 状态码
    :return: JsonResponse
    """
    return JsonResponse({
        'code': code,
        'message': message,
        'data': data or {}
    })

def error_response(message='服务器内部错误', code=500, data=None):
    """
    错误响应
    
    :param message: 错误消息
    :param code: 状态码
    :param data: 返回的数据
    :return: JsonResponse
    """
    return JsonResponse({
        'code': code,
        'message': message,
        'data': data or {}
    })

def format_datetime(dt):
    """
    格式化日期时间
    
    :param dt: datetime对象
    :return: 格式化后的字符串或None
    """
    if dt:
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    return None

def model_to_dict(instance, fields=None, camel_case=True):
    """
    将模型实例转换为字典，专门处理日期字段
    
    :param instance: 模型实例
    :param fields: 需要包含的字段列表
    :param camel_case: 是否转换为驼峰命名
    :return: 字典
    """
    data = {}
    fields = fields or [field.name for field in instance._meta.fields]
    
    for field in fields:
        value = getattr(instance, field)
        # 处理字段名转换
        key = to_camel_case(field) if camel_case else field
        # 处理日期时间字段
        if isinstance(value, datetime):
            data[key] = format_datetime(value)
        else:
            data[key] = value
            
    return data

def paginate_response(items, page, page_size, total, extra_data=None):
    """
    分页响应
    
    :param items: 分页数据项列表
    :param page: 当前页码
    :param page_size: 页面大小
    :param total: 总数
    :param extra_data: 额外数据
    :return: JsonResponse
    """
    data = {
        'items': items,
        'page': page,
        'pageSize': page_size,
        'total': total,
    }
    
    if extra_data:
        data.update(extra_data)
        
    return success_response(data=data)
