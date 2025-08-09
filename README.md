## 安装uv
```bash
pip install uv
```

## 生成lock文件
```bash
uv lock
uv sync
```

## 启动项目
```bash
py manage.py runserver
```

## CLI创建项目
```bash
py manage.py startapp xxx
```

## 设置数据库
编辑`south_admin/settings.py`修改`DATABASES`对应参数。

## CLI生成数据库表
```bash
python manage.py makemigrations
python manage.py migrate
```

## 数据库操作
数据库导入`init.sql`文件。