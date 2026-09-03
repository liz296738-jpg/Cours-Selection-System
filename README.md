# 招生就业处教师选课系统

面向 50 人以内短期选课场景的 Django 单体应用。管理员可以维护教师账号和课程、设置每位教师最多选课数量与开放时间；教师登录后完成选课或退选。系统支持 Excel 批量导入和结果导出。

## 主要功能

- 管理员与教师分角色登录
- 教师首次登录强制修改密码
- 管理员配置每位教师最多选课数
- 管理员配置选课开始/截止时间与开放状态
- 课程名额、启用/停用、Excel 批量导入
- 教师账号新增、编辑、停用与 Excel 批量导入
- 数据库事务保证课程名额和个人选课上限
- 教师选课、取消、查看个人选课
- 管理员按课程查看结果并导出 Excel
- 操作日志、CSRF 防护、安全 Cookie

## 本地运行

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

访问 `http://127.0.0.1:8000/`。超级管理员既可以使用业务管理页面，也可以访问 `/django-admin/` 进行底层数据维护。

需要快速查看完整界面时，可创建本地演示数据：

```powershell
python manage.py seed_demo
```

演示管理员为 `admin / Admin12345`，演示教师为 `teacher01 / Teacher12345`。这些账号只用于本机预览，不要在公网环境使用。

## Excel 模板

登录管理端后，从“课程”或“教师”页面进入 Excel 导入页并下载模板。

教师模板列：

```text
登录账号 | 姓名 | 部门 | 初始密码
```

课程模板列：

```text
课程编号 | 课程名称 | 课程类别 | 名额 | 课程说明
```

同编号课程和同登录账号教师会被更新。新建教师必须提供至少 8 位初始密码，教师首次登录后必须修改。

## 免费部署：GitHub + Render + Supabase

1. 在 GitHub 创建私有仓库并推送本目录。
2. 在 Supabase 创建免费项目，从数据库连接设置中取得 PostgreSQL 连接串。建议选择 Session Pooler 连接串，并将密码中的特殊字符正确进行 URL 编码。
3. 在 Render 创建 Blueprint，连接 GitHub 仓库；Render 会读取 `render.yaml`。
4. 设置 `DATABASE_URL`、`ADMIN_USERNAME` 和 `ADMIN_PASSWORD`。不要把这些值写进仓库。
5. 首次部署会自动执行数据库迁移并创建管理员。
6. 打开 Render 分配的 `onrender.com` 地址并登录。

Render 免费 Web Service 闲置后会休眠，第一位访问者需要等待冷启动。正式选课前应提前访问一次系统并确认健康检查正常。

## 免费版数据保障

免费数据库不应视为正式备份。短期试用建议：

1. 导入账号和课程后保留原 Excel。
2. 选课期间每天由管理员导出一次选课结果。
3. 选课截止后立即导出最终结果并离线保存。
4. 不在课程说明、账号字段中录入身份证号、手机号等非必要信息。

## 测试

```powershell
python manage.py test
```
