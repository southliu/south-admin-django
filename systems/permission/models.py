from django.db import models
from django.utils import timezone

class Permission(models.Model):
    id = models.BigAutoField(primary_key=True, verbose_name='权限ID')
    name = models.CharField(max_length=100, unique=True, verbose_name='权限名')
    description = models.CharField(max_length=200, null=True, blank=True, verbose_name='权限描述')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    def get_menu_data(self):
        return {
            "id": self.menu.id if self.menu else None,
            "label": self.menu.label if self.menu else "",
            "labelEn": self.menu.labelEn if self.menu else "",
            "icon": self.menu.icon if self.menu else "",
            "key": self.menu.key if self.menu else "",
            "rule": self.menu.rule if self.menu else ""
        }

    class Meta:
        db_table = 'permission'
        verbose_name = '权限'
        verbose_name_plural = '权限管理'
        
    def __str__(self):
        return self.name
