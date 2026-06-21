from django.db import models


class SysPermission(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="权限名称")
    description = models.TextField(null=True, blank=True, verbose_name="描述")
    is_deleted = models.IntegerField(default=0, verbose_name="是否删除")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="删除时间")
    create_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "sys_permission"
        verbose_name = "权限"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name
