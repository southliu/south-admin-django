## 添加sql数据
```sql
-- 开启事务确保原子性
START TRANSACTION;

-- 插入用户表数据（密码已加密，明文为 admin123）
INSERT INTO `user` (username, password, email, status) 
VALUES 
    ('admin', 'pbkdf2_sha256$1000000$GG2TQhyoZuwk6N9ZmvvffO$1s4bY4KNeIo9kJHLdyCpc8oapd4B1TiYaZ4iiHk52Io=', 'admin@example.com', 1),
    ('user1', 'pbkdf2_sha256$600000$AbCdEfGh123$Y2ZzZ...', 'user1@example.com', 1);

-- 插入角色表数据
INSERT INTO `role` (name, description) 
VALUES 
    ('admin', '系统管理员'),
    ('user', '普通用户');

-- 插入权限表数据
INSERT INTO `permission` (name, description) 
VALUES 
    ('user:add', '添加用户权限'),
    ('menu:view', '查看菜单权限');

-- 插入菜单表数据
INSERT INTO `menu` (label, labelEn, icon, `key`, rule) 
VALUES 
    ('仪表盘', 'Dashboard', 'la:tachometer-alt', '/dashboard', '/dashboard');

-- 关联用户与角色
INSERT INTO `user_role` (user_id, role_id) 
VALUES 
    ((SELECT id FROM `user` WHERE username='admin'), (SELECT id FROM `role` WHERE name='admin')),
    ((SELECT id FROM `user` WHERE username='user1'), (SELECT id FROM `role` WHERE name='user'));

-- 关联角色与权限
INSERT INTO `role_permission` (role_id, permission_id) 
VALUES 
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `permission` WHERE name='user:add')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `permission` WHERE name='menu:view'));

-- 提交事务
COMMIT;
```