from django.db import models


class SysLog(models.Model):
    username = models.CharField(max_length=100, null=True, blank=True, verbose_name="用户名")
    ip = models.CharField(max_length=50, null=True, blank=True, verbose_name="IP地址")
    method = models.CharField(max_length=10, null=True, blank=True, verbose_name="请求方法")
    url = models.CharField(max_length=500, null=True, blank=True, verbose_name="请求地址")
    params = models.TextField(null=True, blank=True, verbose_name="请求参数")
    user_agent = models.CharField(max_length=500, null=True, blank=True, verbose_name="User-Agent")
    status = models.CharField(max_length=20, null=True, blank=True, verbose_name="状态")
    error = models.TextField(null=True, blank=True, verbose_name="错误信息")
    latency = models.BigIntegerField(default=0, verbose_name="耗时(ms)")
    type = models.IntegerField(default=0, verbose_name="类型 0=后端错误 1=成功 2=警告 3=前端错误")
    create_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "sys_log"
        verbose_name = "日志"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.username} - {self.url}"
