from django.db import models
from django.utils import timezone

class Menu(models.Model):
    label = models.CharField(max_length=50, verbose_name='菜单名称')
    label_en = models.CharField(max_length=50, verbose_name='英文名称')
    icon = models.CharField(max_length=50, null=True, blank=True, verbose_name='图标')
    type = models.IntegerField(default=1, verbose_name='菜单类型,1为目录,2为菜单,3为按钮')
    router = models.CharField(max_length=100, null=True, blank=True, verbose_name='菜单路由')
    rule = models.CharField(max_length=100, null=True, verbose_name='路由规则')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, 
                              null=True, blank=True, verbose_name='父菜单',
                              related_name='children')
    order = models.IntegerField(default=0, verbose_name='显示顺序')
    state = models.IntegerField(default=1, verbose_name='状态,0为隐藏,1为显示')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    # 添加软删除标识字段
    is_deleted = models.IntegerField(default=0, verbose_name='是否删除')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='删除时间')
    
    # 添加默认管理器，只返回未被软删除的记录
    objects = models.Manager()
    
    # 添加一个自定义管理器，用于包含被软删除的记录
    objects_with_deleted = models.Manager()
    
    # 默认管理器只返回未被软删除的记录
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=0)
    
    # 重写delete方法实现软删除
    def delete(self):
        self.is_deleted = 1
        self.deleted_at = timezone.now()
        self.save()
    
    # 真实删除方法
    def hard_delete(self, using=None, keep_parents=False):
        super(Menu, self).delete(using, keep_parents)
    
    # 恢复被软删除的记录
    def restore(self):
        self.is_deleted = 0
        self.deleted_at = None
        self.save()
    
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
        return self.children.filter(state=True).order_by('order')

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
            'labelEn': self.label_en,
            'icon': self.icon,
            'router': self.router,
            'rule': self.rule,
            'type': self.type,
            'order': self.order,
            'state': self.state,
            'parentId': self.parent_id,
            'children': children_data if children_data else []
        }
        return data
