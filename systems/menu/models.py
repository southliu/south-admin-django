from django.db import models
from django.utils import timezone

class Menu(models.Model):
    label = models.CharField(max_length=50, verbose_name='菜单名称')
    labelEn = models.CharField(max_length=50, verbose_name='英文名称')
    icon = models.CharField(max_length=50, null=True, blank=True, verbose_name='图标')
    router = models.CharField(max_length=100, null=True, blank=True, verbose_name='菜单路由')
    rule = models.CharField(max_length=100, null=True, verbose_name='路由规则')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, 
                              null=True, blank=True, verbose_name='父菜单',
                              related_name='children')
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

    def get_children(self):
        """
        获取直接子菜单
        """
        return self.children.filter(is_visible=True).order_by('order')

    def get_descendants(self):
        """
        获取所有子孙菜单
        """
        descendants = []
        for child in self.get_children():
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants

    def get_ancestors(self):
        """
        获取所有祖先菜单
        """
        ancestors = []
        if self.parent:
            ancestors.append(self.parent)
            ancestors.extend(self.parent.get_ancestors())
        return ancestors

    def is_root(self):
        """
        判断是否为根节点
        """
        return self.parent is None

    def is_leaf(self):
        """
        判断是否为叶子节点
        """
        return not self.children.exists()

    def get_level(self):
        """
        获取菜单层级（根节点为0级）
        """
        level = 0
        current = self
        while current.parent:
            level += 1
            current = current.parent
        return level

    def get_full_path(self):
        """
        获取从根节点到当前节点的完整路径
        """
        path = []
        current = self
        while current:
            path.insert(0, current)
            current = current.parent
        return path

    def to_tree_dict(self):
        """
        将菜单转换为树形字典结构
        """
        children_data = [child.to_tree_dict() for child in self.get_children()]
        data = {
            'id': self.id,
            'label': self.label,
            'labelEn': self.labelEn,
            'icon': self.icon,
            'router': self.router,
            'rule': self.rule,
            'order': self.order,
            'is_visible': self.is_visible,
            'children': children_data if children_data else []
        }
        return data
