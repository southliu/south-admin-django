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
python manage.py runserver
```

## CLI创建项目
```bash
python manage.py startapp xxx
```

## 设置数据库
编辑`south_admin/settings.py`修改`DATABASES`对应mysql参数。

## CLI生成数据库表
```bash
python manage.py makemigrations
python manage.py migrate
```

## 数据库操作
数据库导入`init.sql`文件。

## 前端项目
react: [react-admin](https://github.com/southliu/south-admin-react)

## 前后端联调
启动dajgo项目之后需要将react-admin项目中的`.env.development`改成：
```
VITE_ENV = "development"

# 端口号
VITE_SERVER_PORT = 7000

# 跨域
# VITE_PROXY = [["/api", "https://mock.mengxuegu.com/mock/63f830b1c5a76a117cab185e/v1"], ["/test", "https://www.baidu.com"]]

VITE_PROXY = [["/api", "http://127.0.0.1:8000/"]]
```
