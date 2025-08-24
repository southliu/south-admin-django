from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from common.decorators import auth_required

'''
仪表盘统计接口，请根据自身需求进行添加
'''
@csrf_exempt
@auth_required('GET')
def list(request):
    try:
        return JsonResponse({
            'code': 200,
            'message': 'success',
            'data': {}
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': f'服务器内部错误: {str(e)}',
            'data': {}
        })