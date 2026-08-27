from django.db import models


class SysRoleMenu(models.Model):
    """角色-菜单中间表（显式声明以对齐 role_id/menu_id 列名）"""
    role = models.ForeignKey("SysRole", db_column="role_id", on_delete=models.CASCADE)
    menu = models.ForeignKey("menu.SysMenu", db_column="menu_id", on_delete=models.CASCADE)

    class Meta:
        db_table = "sys_role_menu"
        unique_together = (("role", "menu"),)


class SysRole(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="角色名称")
    description = models.TextField(null=True, blank=True, verbose_name="描述")
    is_deleted = models.IntegerField(default=0, verbose_name="是否删除")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="删除时间")
    create_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    menus = models.ManyToManyField(
        "menu.SysMenu", through=SysRoleMenu, through_fields=("role", "menu"), blank=True, verbose_name="菜单"
    )

    class Meta:
        db_table = "sys_role"
        verbose_name = "角色"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name
