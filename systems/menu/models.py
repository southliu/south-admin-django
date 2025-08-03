from django.db import models
from django.utils import timezone

class Menu(models.Model):
    label = models.CharField(max_length=50, verbose_name='菜单名称')
    labelEn = models.CharField(max_length=50, verbose_name='英文名称')
    icon = models.CharField(max_length=50, verbose_name='图标')
    key = models.CharField(max_length=100, verbose_name='菜单标识')
    rule = models.CharField(max_length=100, verbose_name='路由规则')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, 
                              null=True, blank=True, verbose_name='父菜单')
    order = models.IntegerField(default=0, verbose_name='显示顺序')
    is_visible = models.BooleanField(default=True, verbose_name='是否可见')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'menu'
        verbose_name = '菜单'
        verbose_name_plural = '菜单管理'
        ordering = ['order']

    def __str__(self):
        return self.label