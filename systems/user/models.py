from django.db import models


class SysUser(models.Model):
    username = models.CharField(max_length=100, unique=True, verbose_name="用户名")
    password = models.CharField(max_length=255, verbose_name="密码")
    name = models.CharField(max_length=100, null=True, blank=True, verbose_name="姓名")
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name="手机号")
    email = models.CharField(max_length=100, null=True, blank=True, verbose_name="邮箱")
    status = models.IntegerField(default=1, verbose_name="状态 1=启用 0=禁用")
    is_deleted = models.IntegerField(default=0, verbose_name="是否删除")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="删除时间")
    create_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    roles = models.ManyToManyField("role.SysRole", db_table="sys_user_role", blank=True, verbose_name="角色")

    class Meta:
        db_table = "sys_user"
        verbose_name = "用户"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.username}({self.name})"
