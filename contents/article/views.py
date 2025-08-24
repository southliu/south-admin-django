from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q
from common.decorators import auth_required
from .models import Article, ArticleSerializer
import json
from datetime import datetime

# 文章分页接口
@csrf_exempt
@auth_required('GET')
def page(request):
    try:
        # 获取查询参数
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('pageSize', 10))
        title = request.GET.get('title', '').strip()
        status = request.GET.get('status', '')

        # 构建查询条件
        articles = Article.objects.filter(is_deleted=0)
        
        # 根据标题进行过滤
        if title:
            articles = articles.filter(title__icontains=title)
            
        # 根据状态进行过滤
        if status:
            articles = articles.filter(status=status)
        
        # 获取总数
        total = articles.count()
        
        # 分页处理
        paginator = Paginator(articles, page_size)
        paginated_articles = paginator.get_page(page)
        
        # 构建返回数据
        article_items = []
        for article in paginated_articles:
            article_items.append({
                'id': article.id,
                'title': article.title,
                'author': article.author,
                'status': article.status,
                'createdAt': article.created_at.strftime('%Y-%m-%d %H:%M:%S') if article.created_at else None,
                'updatedAt': article.updated_at.strftime('%Y-%m-%d %H:%M:%S') if article.updated_at else None,
                'creator': article.creator,
                'updater': article.updater,
            })
        
        return JsonResponse({
            'code': 200,
            'message': 'success',
            'data': {
                'items': article_items,
                'page': page,
                'pageSize': page_size,
                'total': total,
                'totalPage': paginator.num_pages,
            }
        })
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': f'服务器内部错误: {str(e)}',
            'data': {}
        })


# 文章详情接口
@csrf_exempt
@auth_required('GET')
def detail(request):
    try:
        # 获取文章ID参数
        article_id = request.GET.get('id')
        if not article_id:
            return JsonResponse({
                'code': 400,
                'message': '缺少参数: id',
                'data': {}
            })
        
        # 检查文章是否存在
        try:
            article = Article.objects.get(id=article_id, is_deleted=0)
        except Article.DoesNotExist:
            return JsonResponse({
                'code': 404,
                'message': '文章不存在',
                'data': {}
            })
        
        # 返回文章详情
        article_data = {
            'id': article.id,
            'title': article.title,
            'author': article.author,
            'content': article.content,
            'status': article.status,
            'createdAt': article.created_at.strftime('%Y-%m-%d %H:%M:%S') if article.created_at else None,
            'updatedAt': article.updated_at.strftime('%Y-%m-%d %H:%M:%S') if article.updated_at else None,
            'creator': article.creator,
            'updater': article.updater,
        }
        
        return JsonResponse({
            'code': 200,
            'message': 'success',
            'data': article_data
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': f'服务器内部错误: {str(e)}',
            'data': {}
        })


# 文章创建接口
@csrf_exempt
@auth_required('POST')
def create(request):
    try:
        # 解析请求体中的JSON数据
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'code': 400,
                'message': '请求数据格式错误',
                'data': {}
            })
        
        # 获取参数
        title = data.get('title')
        author = data.get('author')
        content = data.get('content')
        status = data.get('status', 1)
        # 获取创建者信息
        creator = data.get('creator', request.current_user.username if hasattr(request, 'current_user') else None)
        
        # 参数校验
        if not title:
            return JsonResponse({
                'code': 400,
                'message': '文章标题不能为空',
                'data': {}
            })
        
        # 创建文章
        article = Article.objects.create(
            title=title,
            author=author,
            content=content,
            status=status,
            creator=creator,
            updater=creator,
        )
        
        # 返回成功响应
        return JsonResponse({
            'code': 200,
            'message': '文章创建成功',
            'data': {
                'id': article.id,
                'title': article.title,
                'author': article.author,
                'content': article.content,
                'status': article.status,
                'createdAt': article.created_at.strftime('%Y-%m-%d %H:%M:%S') if article.created_at else None,
                'updatedAt': article.updated_at.strftime('%Y-%m-%d %H:%M:%S') if article.updated_at else None,
                'creator': article.creator,
                'updater': article.updater,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': f'服务器内部错误: {str(e)}',
            'data': {}
        })


# 文章更新接口
@csrf_exempt
@auth_required('PUT')
def update(request, article_id):
    try:
        # 检查文章是否存在
        try:
            article = Article.objects.get(id=article_id, is_deleted=0)
        except Article.DoesNotExist:
            return JsonResponse({
                'code': 404,
                'message': '文章不存在',
                'data': {}
            })
        
        # 解析请求体中的JSON数据
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'code': 400,
                'message': '请求数据格式错误',
                'data': {}
            })
        
        # 获取参数
        title = data.get('title')
        author = data.get('author')
        content = data.get('content')
        status = data.get('status')
        # 获取更新者信息
        updater = data.get('updater', request.current_user.username if hasattr(request, 'current_user') else None)
        
        # 参数校验
        if not title:
            return JsonResponse({
                'code': 400,
                'message': '文章标题不能为空',
                'data': {}
            })
        
        # 更新文章信息
        article.title = title
        if author is not None:
            article.author = author
        if content is not None:
            article.content = content
        if status is not None:
            article.status = status
        # 设置更新者
        if updater is not None:
            article.updater = updater
        article.updated_at = datetime.now()
        article.save()
        
        # 返回成功响应
        return JsonResponse({
            'code': 200,
            'message': '文章更新成功',
            'data': {
                'id': article.id,
                'title': article.title,
                'author': article.author,
                'content': article.content,
                'status': article.status,
                'createdAt': article.created_at.strftime('%Y-%m-%d %H:%M:%S') if article.created_at else None,
                'updatedAt': article.updated_at.strftime('%Y-%m-%d %H:%M:%S') if article.updated_at else None,
                'creator': article.creator,
                'updater': article.updater,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': f'服务器内部错误: {str(e)}',
            'data': {}
        })


# 文章删除接口
@csrf_exempt
@auth_required('DELETE')
def delete(request, article_id):
    try:
        # 检查文章是否存在
        try:
            article = Article.objects.get(id=article_id, is_deleted=0)
        except Article.DoesNotExist:
            return JsonResponse({
                'code': 404,
                'message': '文章不存在',
                'data': {}
            })
        
        # 执行软删除
        article.delete()
        
        # 返回成功响应
        return JsonResponse({
            'code': 200,
            'message': '文章删除成功',
            'data': {}
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': f'服务器内部错误: {str(e)}',
            'data': {}
        })


# 获取全部未被软删除文章列表接口
@csrf_exempt
@auth_required('GET')
def list_articles(request):
    try:
        # 获取所有未被软删除的文章
        articles = Article.objects.filter(is_deleted=0)
        
        # 构建返回数据
        article_items = []
        for article in articles:
            article_items.append({
                'id': article.id,
                'title': article.title,
                'author': article.author,
                'status': article.status,
                'createdAt': article.created_at.strftime('%Y-%m-%d %H:%M:%S') if article.created_at else None,
                'updatedAt': article.updated_at.strftime('%Y-%m-%d %H:%M:%S') if article.updated_at else None,
                'creator': article.creator,
                'updater': article.updater,
            })
        
        return JsonResponse({
            'code': 200,
            'message': 'success',
            'data': article_items
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': f'服务器内部错误: {str(e)}',
            'data': {}
        })