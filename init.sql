-- 开始事务
START TRANSACTION;


-- 插入用户表数据（密码已加密，明文为 admin123）
INSERT INTO `user` (username, password, email, status, created_at, updated_at) 
VALUES 
    ('admin', 'pbkdf2_sha256$1000000$salt_value$SDPUcXVJks+NKuGoEH1iHjxzS1eVsWtkYnzFWSxm3AY=', 'admin@example.com', 1, '2025-01-01 00:00:00', '2025-01-01 00:00:00'),
    ('user1', 'pbkdf2_sha256$600000$AbCdEfGh123$Y2ZzZ...', 'user1@example.com', 1, '2025-01-01 00:00:00', '2025-01-01 00:00:00');

-- 插入角色表数据
INSERT INTO `role` (name, description, created_at, updated_at, is_deleted)
VALUES 
    ('admin', '系统管理员', '2025-01-01 00:00:00', '2025-01-01 00:00:00', 0),
    ('user', '普通用户', '2025-01-01 00:00:00', '2025-01-01 00:00:00', 0);

INSERT INTO `permission` (name, description, created_at, updated_at)
VALUES 
    ('/dashboard', '查看仪表盘', '2025-01-01 00:00:00', '2025-01-01 00:00:00'),
    ('/demo', '查看示例菜单', '2025-01-01 00:00:00', '2025-01-01 00:00:00'),
    ('/demo/copy', '复制菜单', '2025-01-01 00:00:00', '2025-01-01 00:00:00'),
    ('/demo/editor', '编辑示例菜单', '2025-01-01 00:00:00', '2025-01-01 00:00:00'),
    ('/demo/wangEditor', 'WangEditor 示例', '2025-01-01 00:00:00', '2025-01-01 00:00:00'),
    ('/demo/virtualScroll', '虚拟滚动示例', '2025-01-01 00:00:00', '2025-01-01 00:00:00'),
    ('/demo/watermark', '水印示例', '2025-01-01 00:00:00', '2025-01-01 00:00:00'),
    ('/authority/user', '用户管理', '2025-01-01 00:00:00', '2025-01-01 00:00:00'),
    ('/authority/user/index', '用户列表', '2025-01-01 00:00:00', '2025-01-01 00:00:00'),
    ('/authority/user/create', '创建用户', '2025-01-01 00:00:00', '2025-01-01 00:00:00'),
    ('/authority/user/update', '更新用户', '2025-01-01 00:00:00', '2025-01-01 00:00:00'),
    ('/authority/user/view', '查看用户', '2025-01-01 00:00:00', '2025-01-01 00:00:00'),
    ('/authority/user/delete', '删除用户', '2025-01-01 00:00:00', '2025-01-01 00:00:00'),
    ('/authority/user/authority', '用户权限配置', '2025-01-01 00:00:00', '2025-01-01 00:00:00'),
    ('/authority/role', '角色管理', '2025-01-01 00:00:00', '2025-01-01 00:00:00'),
    ('/authority/role/index', '角色列表', '2025-01-01 00:00:00', '2025-01-01 00:00:00'),
    ('/authority/role/create', '创建角色', '2025-01-01 00:00:00', '2025-01-01 00:00:00'),
    ('/authority/role/update', '更新角色', '2025-01-01 00:00:00', '2025-01-01 00:00:00'),
    ('/authority/role/view', '查看角色', '2025-01-01 00:00:00', '2025-01-01 00:00:00'),
    ('/authority/role/delete', '删除角色', '2025-01-01 00:00:00', '2025-01-01 00:00:00'),
    ('/authority/menu', '菜单管理', '2025-01-01 00:00:00', '2025-01-01 00:00:00'),
    ('/authority/menu/index', '菜单列表', '2025-01-01 00:00:00', '2025-01-01 00:00:00'),
    ('/authority/menu/create', '创建菜单', '2025-01-01 00:00:00', '2025-01-01 00:00:00'),
    ('/authority/menu/update', '更新菜单', '2025-01-01 00:00:00', '2025-01-01 00:00:00'),
    ('/authority/menu/view', '查看菜单', '2025-01-01 00:00:00', '2025-01-01 00:00:00'),
    ('/authority/menu/delete', '删除菜单', '2025-01-01 00:00:00', '2025-01-01 00:00:00'),
    ('/content/article', '文章管理', '2025-01-01 00:00:00', '2025-01-01 00:00:00'),
    ('/content/article/index', '文章列表', '2025-01-01 00:00:00', '2025-01-01 00:00:00'),
    ('/content/article/create', '创建文章', '2025-01-01 00:00:00', '2025-01-01 00:00:00'),
    ('/content/article/update', '更新文章', '2025-01-01 00:00:00', '2025-01-01 00:00:00'),
    ('/content/article/view', '查看文章', '2025-01-01 00:00:00', '2025-01-01 00:00:00'),
    ('/content/article/delete', '删除文章', '2025-01-01 00:00:00', '2025-01-01 00:00:00');

-- 关联用户与角色
INSERT INTO `user_role` (user_id, role_id) 
VALUES 
    ((SELECT id FROM `user` WHERE username='admin'), (SELECT id FROM `role` WHERE name='admin')),
    ((SELECT id FROM `user` WHERE username='user1'), (SELECT id FROM `role` WHERE name='user'));

-- 关联角色与权限
INSERT INTO `role_permission` (role_id, permission_id) 
VALUES
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `permission` WHERE name='/dashboard')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `permission` WHERE name='/demo')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `permission` WHERE name='/demo/copy')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `permission` WHERE name='/demo/editor')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `permission` WHERE name='/demo/wangEditor')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `permission` WHERE name='/demo/virtualScroll')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `permission` WHERE name='/demo/watermark')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `permission` WHERE name='/authority/user')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `permission` WHERE name='/authority/user/index')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `permission` WHERE name='/authority/user/create')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `permission` WHERE name='/authority/user/update')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `permission` WHERE name='/authority/user/view')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `permission` WHERE name='/authority/user/delete')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `permission` WHERE name='/authority/user/authority')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `permission` WHERE name='/authority/role')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `permission` WHERE name='/authority/role/index')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `permission` WHERE name='/authority/role/create')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `permission` WHERE name='/authority/role/update')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `permission` WHERE name='/authority/role/view')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `permission` WHERE name='/authority/role/delete')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `permission` WHERE name='/authority/menu')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `permission` WHERE name='/authority/menu/index')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `permission` WHERE name='/authority/menu/create')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `permission` WHERE name='/authority/menu/update')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `permission` WHERE name='/authority/menu/view')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `permission` WHERE name='/authority/menu/delete')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `permission` WHERE name='/content/article')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `permission` WHERE name='/content/article/index')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `permission` WHERE name='/content/article/create')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `permission` WHERE name='/content/article/update')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `permission` WHERE name='/content/article/view')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `permission` WHERE name='/content/article/delete'));

-- 禁用外键约束检查
SET FOREIGN_KEY_CHECKS = 0;

-- 删除现有菜单数据（如果存在）
DELETE FROM menu WHERE router IN (
    '/dashboard',
    '/demo',
    '/demo/copy',
    '/demo/watermark',
    '/demo/virtualScroll',
    '/demo/editor',
    '/demo/123/dynamic',
    '/demo/level1',
    '/demo/level1/level2',
    '/demo/level1/level2/level3',
    '/system',
    '/system/user',
    '/system/menu',
    '/content',
    '/content/article',
    'https://ant-design.antgroup.com'
);

-- 重新启用外键约束检查
SET FOREIGN_KEY_CHECKS = 1;

-- 插入顶级菜单项
INSERT INTO menu (label, label_en, type, icon, router, rule, `order`, state, created_at, updated_at, parent_id, is_deleted) VALUES
('仪表盘', 'Dashboard', 2, 'la:tachometer-alt', '/dashboard', '/dashboard', 0, 1, NOW(), NOW(), NULL, 0),
('组件', 'Components', 1, 'fluent:box-20-regular', '/demo', NULL, 1, 1, NOW(), NOW(), NULL, 0),
('系统管理', 'System Management', 1, 'ion:settings-outline', '/system', NULL, 2, 1, NOW(), NOW(), NULL, 0),
('内容管理', 'Content Management', 1, 'majesticons:article-search-line', '/content', NULL, 3, 1, NOW(), NOW(), NULL, 0),
('外部链接', 'External Link', 2, 'material-symbols:link', 'https://ant-design.antgroup.com', '/dashboard', 4, 1, NOW(), NOW(), NULL, 0);

-- 插入组件子菜单（使用派生表解决子查询问题）
INSERT INTO menu (label, label_en, type, icon, router, rule, `order`, state, created_at, updated_at, parent_id, is_deleted)
SELECT '剪切板', 'Copy', 2, NULL, '/demo/copy', '/demo/copy', 0, 1, NOW(), NOW(), parent_menu.id, 0
FROM (SELECT id FROM menu WHERE router = '/demo') AS parent_menu;

INSERT INTO menu (label, label_en, type, icon, router, rule, `order`, state, created_at, updated_at, parent_id, is_deleted)
SELECT '水印', 'Watermark', 2, NULL, '/demo/watermark', '/demo/watermark', 1, 1, NOW(), NOW(), parent_menu.id, 0
FROM (SELECT id FROM menu WHERE router = '/demo') AS parent_menu;

INSERT INTO menu (label, label_en, type, icon, router, rule, `order`, state, created_at, updated_at, parent_id, is_deleted)
SELECT '虚拟滚动', 'Virtual Scroll', 2, NULL, '/demo/virtualScroll', '/demo/virtualScroll', 2, 1, NOW(), NOW(), parent_menu.id, 0
FROM (SELECT id FROM menu WHERE router = '/demo') AS parent_menu;

INSERT INTO menu (label, label_en, type, icon, router, rule, `order`, state, created_at, updated_at, parent_id, is_deleted)
SELECT '富文本', 'Editor', 2, NULL, '/demo/editor', '/demo/editor', 3, 1, NOW(), NOW(), parent_menu.id, 0
FROM (SELECT id FROM menu WHERE router = '/demo') AS parent_menu;

INSERT INTO menu (label, label_en, type, icon, router, rule, `order`, state, created_at, updated_at, parent_id, is_deleted)
SELECT '动态路由参数', 'Dynamic', 2, NULL, '/demo/123/dynamic', '/demo/dynamic', 4, 1, NOW(), NOW(), parent_menu.id, 0
FROM (SELECT id FROM menu WHERE router = '/demo') AS parent_menu;

INSERT INTO menu (label, label_en, type, icon, router, rule, `order`, state, created_at, updated_at, parent_id, is_deleted)
SELECT '层级1', 'Level1', 1, NULL, '/demo/level1', NULL, 5, 1, NOW(), NOW(), parent_menu.id, 0
FROM (SELECT id FROM menu WHERE router = '/demo') AS parent_menu;

-- 插入层级子菜单
INSERT INTO menu (label, label_en, type, icon, router, rule, `order`, state, created_at, updated_at, parent_id, is_deleted)
SELECT '层级2', 'Level2', 1, NULL, '/demo/level1/level2', NULL, 0, 1, NOW(), NOW(), parent_menu.id, 0
FROM (SELECT id FROM menu WHERE router = '/demo/level1') AS parent_menu;

INSERT INTO menu (label, label_en, type, icon, router, rule, `order`, state, created_at, updated_at, parent_id, is_deleted)
SELECT '层级3', 'Level3', 2, NULL, '/demo/level1/level2/level3', '/demo/watermark', 0, 1, NOW(), NOW(), parent_menu.id, 0
FROM (SELECT id FROM menu WHERE router = '/demo/level1/level2') AS parent_menu;

-- 插入系统管理子菜单
INSERT INTO menu (label, label_en, type, icon, router, rule, `order`, state, created_at, updated_at, parent_id, is_deleted)
SELECT '用户管理', 'User Management', 2, NULL, '/system/user', '/authority/user', 0, 1, NOW(), NOW(), parent_menu.id, 0
FROM (SELECT id FROM menu WHERE router = '/system') AS parent_menu;

INSERT INTO menu (label, label_en, type, icon, router, rule, `order`, state, created_at, updated_at, parent_id, is_deleted)
SELECT '菜单管理', 'Menu Management', 2, NULL, '/system/menu', '/authority/menu', 1, 1, NOW(), NOW(), parent_menu.id, 0
FROM (SELECT id FROM menu WHERE router = '/system') AS parent_menu;

INSERT INTO menu (label, label_en, type, icon, router, rule, `order`, state, created_at, updated_at, parent_id, is_deleted)
SELECT '角色管理', 'Role Management', 2, NULL, '/system/role', '/authority/role', 1, 1, NOW(), NOW(), parent_menu.id, 0
FROM (SELECT id FROM menu WHERE router = '/system') AS parent_menu;

-- 插入内容管理子菜单
INSERT INTO menu (label, label_en, type, icon, router, rule, `order`, state, created_at, updated_at, parent_id, is_deleted)
SELECT '文章管理', 'Article Management', 2, NULL, '/content/article', '/content/article', 0, 1, NOW(), NOW(), parent_menu.id, 0
FROM (SELECT id FROM menu WHERE router = '/content') AS parent_menu;

-- 为type=2的菜单添加CRUD子菜单项
-- 为用户管理添加CRUD操作
INSERT INTO menu (label, label_en, type, router, rule, `order`, state, created_at, updated_at, parent_id, is_deleted)
SELECT '新增', 'Create', 3, NULL, CONCAT(parent_menu.rule, '/create'), 0, 1, NOW(), NOW(), parent_menu.id, 0
FROM menu parent_menu WHERE parent_menu.router = '/system/user';

INSERT INTO menu (label, label_en, type, router, rule, `order`, state, created_at, updated_at, parent_id, is_deleted)
SELECT '删除', 'Delete', 3, NULL, CONCAT(parent_menu.rule, '/delete'), 1, 1, NOW(), NOW(), parent_menu.id, 0
FROM menu parent_menu WHERE parent_menu.router = '/system/user';

INSERT INTO menu (label, label_en, type, router, rule, `order`, state, created_at, updated_at, parent_id, is_deleted)
SELECT '修改', 'Update', 3, NULL, CONCAT(parent_menu.rule, '/update'), 2, 1, NOW(), NOW(), parent_menu.id, 0
FROM menu parent_menu WHERE parent_menu.router = '/system/user';

INSERT INTO menu (label, label_en, type, router, rule, `order`, state, created_at, updated_at, parent_id, is_deleted)
SELECT '查看', 'View', 3, NULL, CONCAT(parent_menu.rule, '/view'), 3, 1, NOW(), NOW(), parent_menu.id, 0
FROM menu parent_menu WHERE parent_menu.router = '/system/user';

-- 为菜单管理添加CRUD操作
INSERT INTO menu (label, label_en, type, router, rule, `order`, state, created_at, updated_at, parent_id, is_deleted)
SELECT '新增', 'Create', 3, NULL, CONCAT(parent_menu.rule, '/create'), 0, 1, NOW(), NOW(), parent_menu.id, 0
FROM menu parent_menu WHERE parent_menu.router = '/system/menu';

INSERT INTO menu (label, label_en, type, router, rule, `order`, state, created_at, updated_at, parent_id, is_deleted)
SELECT '删除', 'Delete', 3, NULL, CONCAT(parent_menu.rule, '/delete'), 1, 1, NOW(), NOW(), parent_menu.id, 0
FROM menu parent_menu WHERE parent_menu.router = '/system/menu';

INSERT INTO menu (label, label_en, type, router, rule, `order`, state, created_at, updated_at, parent_id, is_deleted)
SELECT '修改', 'Update', 3, NULL, CONCAT(parent_menu.rule, '/update'), 2, 1, NOW(), NOW(), parent_menu.id, 0
FROM menu parent_menu WHERE parent_menu.router = '/system/menu';

INSERT INTO menu (label, label_en, type, router, rule, `order`, state, created_at, updated_at, parent_id, is_deleted)
SELECT '查看', 'View', 3, NULL, CONCAT(parent_menu.rule, '/view'), 3, 1, NOW(), NOW(), parent_menu.id, 0
FROM menu parent_menu WHERE parent_menu.router = '/system/menu';

-- 为角色管理添加CRUD操作
INSERT INTO menu (label, label_en, type, router, rule, `order`, state, created_at, updated_at, parent_id, is_deleted)
SELECT '新增', 'Create', 3, NULL, CONCAT(parent_menu.rule, '/create'), 0, 1, NOW(), NOW(), parent_menu.id, 0
FROM menu parent_menu WHERE parent_menu.router = '/system/role';

INSERT INTO menu (label, label_en, type, router, rule, `order`, state, created_at, updated_at, parent_id, is_deleted)
SELECT '删除', 'Delete', 3, NULL, CONCAT(parent_menu.rule, '/delete'), 1, 1, NOW(), NOW(), parent_menu.id, 0
FROM menu parent_menu WHERE parent_menu.router = '/system/role';

INSERT INTO menu (label, label_en, type, router, rule, `order`, state, created_at, updated_at, parent_id, is_deleted)
SELECT '修改', 'Update', 3, NULL, CONCAT(parent_menu.rule, '/update'), 2, 1, NOW(), NOW(), parent_menu.id, 0
FROM menu parent_menu WHERE parent_menu.router = '/system/role';

INSERT INTO menu (label, label_en, type, router, rule, `order`, state, created_at, updated_at, parent_id, is_deleted)
SELECT '查看', 'View', 3, NULL, CONCAT(parent_menu.rule, '/view'), 3, 1, NOW(), NOW(), parent_menu.id, 0
FROM menu parent_menu WHERE parent_menu.router = '/system/role';

-- 为文章管理添加CRUD操作
INSERT INTO menu (label, label_en, type, router, rule, `order`, state, created_at, updated_at, parent_id, is_deleted)
SELECT '新增', 'Create', 3, NULL, CONCAT(parent_menu.rule, '/create'), 0, 1, NOW(), NOW(), parent_menu.id, 0
FROM menu parent_menu WHERE parent_menu.router = '/content/article';

INSERT INTO menu (label, label_en, type, router, rule, `order`, state, created_at, updated_at, parent_id, is_deleted)
SELECT '删除', 'Delete', 3, NULL, CONCAT(parent_menu.rule, '/delete'), 1, 1, NOW(), NOW(), parent_menu.id, 0
FROM menu parent_menu WHERE parent_menu.router = '/content/article';

INSERT INTO menu (label, label_en, type, router, rule, `order`, state, created_at, updated_at, parent_id, is_deleted)
SELECT '修改', 'Update', 3, NULL, CONCAT(parent_menu.rule, '/update'), 2, 1, NOW(), NOW(), parent_menu.id, 0
FROM menu parent_menu WHERE parent_menu.router = '/content/article';

INSERT INTO menu (label, label_en, type, router, rule, `order`, state, created_at, updated_at, parent_id, is_deleted)
SELECT '查看', 'View', 3, NULL, CONCAT(parent_menu.rule, '/view'), 3, 1, NOW(), NOW(), parent_menu.id, 0
FROM menu parent_menu WHERE parent_menu.router = '/content/article';

-- 关联角色与菜单
INSERT INTO `role_menu` (role_id, menu_id) 
VALUES
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `menu` WHERE label='仪表盘')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `menu` WHERE label='组件')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `menu` WHERE label='系统管理')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `menu` WHERE label='内容管理')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `menu` WHERE label='外部链接')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `menu` WHERE label='剪切板')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `menu` WHERE label='水印')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `menu` WHERE label='虚拟滚动')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `menu` WHERE label='富文本')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `menu` WHERE label='动态路由参数')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `menu` WHERE label='层级1')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `menu` WHERE label='层级2')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `menu` WHERE label='层级3')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `menu` WHERE label='用户管理')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `menu` WHERE label='菜单管理')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `menu` WHERE label='角色管理')),
    ((SELECT id FROM `role` WHERE name='admin'), (SELECT id FROM `menu` WHERE label='文章管理'));
    

-- 提交事务
COMMIT;