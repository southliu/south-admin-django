from django.db import models


class SysMenu(models.Model):
    label = models.CharField(max_length=50, verbose_name="菜单名称")
    label_en = models.CharField(max_length=50, verbose_name="英文名称")
    icon = models.CharField(max_length=100, null=True, blank=True, verbose_name="图标")
    type = models.IntegerField(verbose_name="类型 1=目录 2=菜单 3=按钮")
    router = models.CharField(max_length=255, null=True, blank=True, verbose_name="路由地址")
    order = models.IntegerField(default=0, verbose_name="排序")
    state = models.IntegerField(default=1, verbose_name="状态 0=隐藏 1=显示")
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True,
                               related_name="children", verbose_name="父菜单")
    permission = models.ForeignKey("permission.SysPermission", on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="menus", verbose_name="权限")
    is_deleted = models.IntegerField(default=0, verbose_name="是否删除")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="删除时间")
    create_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "sys_menu"
        verbose_name = "菜单"
        verbose_name_plural = verbose_name
        ordering = ["order"]

    def __str__(self):
        return self.label
