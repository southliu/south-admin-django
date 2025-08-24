from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser
from rest_framework import serializers

from systems.role.models import Role

class User(AbstractBaseUser):
    id = models.BigAutoField(primary_key=True, verbose_name='用户ID')
    username = models.CharField(max_length=50, unique=True, verbose_name='用户名')
    name = models.CharField(max_length=100, null=True, blank=True, verbose_name='姓名')  # 添加姓名字段
    password = models.CharField(max_length=128, verbose_name='加密密码')  # 存储加密后的密码
    email = models.EmailField(max_length=100, null=True, blank=True, verbose_name='邮箱')
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name='电话')  # 添加电话字段
    status = models.SmallIntegerField(default=1, choices=((1, '启用'), (0, '禁用')), verbose_name='状态')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    roles = models.ManyToManyField(Role, related_name='users', through='UserRole')
    
    # 添加软删除标识字段
    is_deleted = models.IntegerField(default=0, verbose_name='是否删除')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='删除时间')

    USERNAME_FIELD = 'username'
    
    class Meta:
        db_table = 'user'
        verbose_name = '用户'
        verbose_name_plural = '用户管理'
        
    def __str__(self):
        return self.username
        
    # 重写delete方法实现软删除
    def delete(self, using=None, keep_parents=False):
        self.is_deleted = 1
        self.deleted_at = timezone.now()
        self.save()
    
    # 真实删除方法
    def hard_delete(self, using=None, keep_parents=False):
        super(User, self).delete(using, keep_parents)
    
    # 恢复被软删除的记录
    def restore(self):
        self.is_deleted = 0
        self.deleted_at = None
        self.save()
        
    # 获取未被软删除的角色
    def get_active_roles(self):
        return self.roles.filter(is_deleted=0)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ('password',)


# 用户-角色关联表
class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户ID', db_column='user_id')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, verbose_name='角色ID', db_column='role_id')

    class Meta:
        db_table = 'user_role'
        verbose_name = '用户角色'
        verbose_name_plural = '用户角色管理'
        unique_together = (('user', 'role'),)
        
    def __str__(self):
        return f"{self.user} - {self.role}"