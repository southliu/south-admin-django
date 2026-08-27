---
name: demo-create
description: 生成或修改增删改查(CRUD)模块时必须使用本skill。当用户要求新增业务模块、生成增删改查接口、创建xxx管理功能、或修改现有CRUD代码时，按本skill规定的文件结构、命名和接口契约生成，保证与项目现有格式一致。适用范围：新建 systems 子应用、Model/View/URL、批量删除、状态切换、分页过滤等。
---

# demo-create：django 项目 CRUD 模块生成规范

为 `south-admin-django`（Django + 原生 View + MySQL）生成增删改查模块时，**必须**按本文件的结构和契约执行。以模块名 `{{name}}`（表 `sys_{{name}}`，应用 `systems.{{name}}`）为例。

## 一、要创建/修改的文件

| 文件 | 作用 |
|---|---|
| `systems/{{name}}/__init__.py`、`apps.py`、`models.py`、`views.py`、`urls.py` | 新子应用（参照 `systems/log/`，最薄的一个） |
| `systems/{{name}}/migrations/__init__.py` | 迁移包（空文件即可，迁移命令自动生成） |
| `south_admin_django/settings.py` | INSTALLED_APPS 注册 `"systems.{{name}}.apps.{{Name}}Config"` |
| `south_admin_django/urls.py` | `path("system/{{name}}/", include("systems.{{name}}.urls"))` |
| `init.sql`（项目根） | 菜单/权限种子数据（`sys_permission`/`sys_menu`/`sys_role_menu`） |

## 二、接口契约（与 react-admin 前端对齐，违反即为 bug）

1. **响应结构**：一律用 `common/responses.py` 的 `success(data=None, message="success")` / `error(message)`（返回 `{code, message, data}`，HTTP 200）。
2. **分页参数名是 `pageSize`**：
   ```python
   page = int(request.GET.get("page", 1))
   page_size = int(request.GET.get("pageSize", 10))
   ```
3. **分页返回**：`{"items", "page", "pageSize", "total", "totalPages"}`（totalPages 用 `(total + page_size - 1) // page_size`）。
4. **JSON 键驼峰**：`createdAt/updatedAt/parentId/roleIds/labelEn`。时间输出 `strftime("%Y-%m-%d %H:%M:%S")`。**禁止** `created_at/role_ids` 下划线键名。
5. **零值合法**：`state=0/status=0` 有效。更新判断用 `"field" in data`（键存在性）而不是 `if data.get("field"):`（0/空串会被跳过）。
6. **请求体解析**：用项目统一的 `_parse_body(request)`（见 `systems/user/views.py` 顶部）。
7. **接口面**（认证中间件自动保护，无需每个视图处理）：
   `path("page")` GET、`path("detail")` GET、`path("create")` POST、`path("update/<int:xxx_id>")` PUT、`path("<int:xxx_id>")` DELETE、`path("batchDelete")` POST、（有状态时）`path("changeState")` POST、`path("list")` GET。
   注意 `batchDelete/changeState` 等具名路由要放在 `<int:xxx_id>` 之前。
8. **过滤参数**：`queryset.filter(field__icontains=xxx)` 模糊匹配，total 用同一 queryset `.count()`。
9. **不泄露密码**：响应不含 password。
10. **软删除**：`is_deleted=1` + `deleted_at=datetime.now()`；批量删除空 ids 报"请选择要删除的xx"。

## 三、文件模板

### 1. `systems/{{name}}/models.py`

```python
from django.db import models


class Sys{{Name}}(models.Model):
    # TODO: 业务字段
    name = models.CharField(max_length=50, verbose_name="名称")
    description = models.TextField(null=True, blank=True, verbose_name="描述")
    status = models.IntegerField(default=1, verbose_name="状态 1=启用 0=禁用")
    is_deleted = models.IntegerField(default=0, verbose_name="是否删除")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="删除时间")
    create_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "sys_{{name}}"
        verbose_name = "{{标签}}"
        verbose_name_plural = verbose_name
```

**多对多必须用显式 through 模型对齐列名**（表由共享 SQL 建立，列名是 `user_id/role_id` 这种短名，Django 隐式中间表会生成 `sysuser_id` 导致 Unknown column 500）：

```python
class Sys{{Name}}Xxx(models.Model):
    """中间表（显式声明以对齐 user_id/xxx_id 列名）"""
    user = models.ForeignKey("user.SysUser", db_column="user_id", on_delete=models.CASCADE)
    xxx = models.ForeignKey("{{name}}.Sys{{Name}}", db_column="xxx_id", on_delete=models.CASCADE)

    class Meta:
        db_table = "sys_user_{{name}}"
        unique_together = (("user", "xxx"),)
```
然后在主模型上：`ManyToManyField("xxx.SysXxx", through=Sys{{Name}}Xxx, through_fields=("user", "xxx"), blank=True)`。参照 `systems/user/models.py` 的 SysUserRole。

### 2. `systems/{{name}}/views.py`

参照 `systems/log/views.py`（最简）或 `systems/user/views.py`（最全）：每个视图 `@require_http_methods([...])`，返回 `success(...)/error(...)`；分页/过滤/软删按第二节契约写。

### 3. `systems/{{name}}/urls.py`

```python
from django.urls import path
from systems.{{name}} import views

urlpatterns = [
    path("page", views.get_{{name}}_page),
    path("detail", views.get_{{name}}_detail),
    path("create", views.create_{{name}}),
    path("list", views.get_{{name}}_list),
    path("batchDelete", views.batch_delete_{{name}}),
    path("changeState", views.change_{{name}}_state),  # 有状态字段时
    path("update/<int:{{name}}_id>", views.update_{{name}}),
    path("<int:{{name}}_id>", views.delete_{{name}}),
]
```

### 4. `systems/{{name}}/apps.py`

```python
from django.apps import AppConfig


class {{Name}}Config(AppConfig):
    name = "systems.{{name}}"
    verbose_name = "{{标签}}"
```

### 5. 注册、迁移、种子数据

- `settings.py` INSTALLED_APPS 追加；根 `urls.py` 挂 `system/{{name}}/`
- 迁移：`.venv/Scripts/python.exe manage.py makemigrations {{name}}`；若表已由 SQL 建好则 `manage.py migrate {{name}} --fake`
- `init.sql`：参照"日志管理"三件套追加 `sys_permission`/`sys_menu`/`sys_role_menu`（表名带 `sys_` 前缀，时间用 `NOW()`）

## 四、完成前自查

- [ ] `.venv/Scripts/python.exe manage.py check` 无问题
- [ ] curl 验证：pageSize 生效、过滤生效、增删改/批量删正常、无 500
- [ ] 响应键驼峰；M2M 若有用 through 模型
