from django.db import models
from django.utils import timezone

from systems.menu.models import Menu
from systems.permission.models import Permission

class Role(models.Model):
    id = models.BigAutoField(primary_key=True, verbose_name='角色ID')
    name = models.CharField(max_length=50, unique=True, verbose_name='角色名')
    description = models.CharField(max_length=200, null=True, blank=True, verbose_name='角色描述')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'role'
        verbose_name = '角色'
        verbose_name_plural = '角色管理'
        
    def __str__(self):
        return self.name

# 角色-权限关联表
class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, verbose_name='角色ID', db_column='role_id')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, verbose_name='权限ID', db_column='permission_id')

    class Meta:
        db_table = 'role_permission'
        verbose_name = '角色权限'
        verbose_name_plural = '角色权限管理'
        unique_together = (('role', 'permission'),)
        
    def __str__(self):
        return f"{self.role} - {self.permission}"

# 角色-菜单关联模型
class RoleMenu(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, verbose_name='角色')
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, verbose_name='菜单')

    class Meta:
        db_table = 'role_menu'
        verbose_name = '角色菜单关联'
        verbose_name_plural = '角色菜单关联管理'
        unique_together = (('role', 'menu'),)