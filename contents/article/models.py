from django.db import models
from django.utils import timezone
from rest_framework import serializers

class Article(models.Model):
    id = models.BigAutoField(primary_key=True, verbose_name='文章ID')
    title = models.CharField(max_length=200, verbose_name='文章标题')
    author = models.CharField(max_length=100, null=True, blank=True, verbose_name='作者')
    content = models.TextField(null=True, blank=True, verbose_name='文章内容')
    status = models.SmallIntegerField(default=1, choices=((1, '发布'), (0, '草稿')), verbose_name='状态')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    creator = models.CharField(max_length=100, null=True, blank=True, verbose_name='创建者')
    updater = models.CharField(max_length=100, null=True, blank=True, verbose_name='更新者')
    
    # 添加软删除标识字段
    is_deleted = models.IntegerField(default=0, verbose_name='是否删除')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='删除时间')

    class Meta:
        db_table = 'article'
        verbose_name = '文章'
        verbose_name_plural = '文章管理'
        app_label = 'article'  # 显式声明app_label
        
    def __str__(self):
        return self.title
        
    # 重写delete方法实现软删除
    def delete(self, using=None, keep_parents=False):
        self.is_deleted = 1
        self.deleted_at = timezone.now()
        self.save()
    
    # 真实删除方法
    def hard_delete(self, using=None, keep_parents=False):
        super(Article, self).delete(using, keep_parents)
    
    # 恢复被软删除的记录
    def restore(self):
        self.is_deleted = 0
        self.deleted_at = None
        self.save()


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = '__all__'
        # exclude = ()