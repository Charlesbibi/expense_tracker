# 家庭开支统计系统

基于 Django + MySQL 的家用开支记录与可视化网站。

## 快速启动

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置 MySQL

在 MySQL 中创建数据库：
```sql
CREATE DATABASE expense_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

修改 `expense_tracker/settings.py` 中的数据库账号：
```python
DATABASES = {
    'default': {
        ...
        'USER': '你的MySQL用户名',
        'PASSWORD': '你的MySQL密码',
    }
}
```

### 3. 初始化数据库
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. 启动开发服务器
```bash
conda activate homefinance
python manage.py runserver
```

访问 http://127.0.0.1:8000/ 即可使用。

## 功能

- **开支列表**：查看、筛选（按年/月）、删除开支记录
- **新增开支**：填写日期、类别、描述、金额
- **数据可视化**：
  - 月度开支趋势折线图
  - 各类别开支占比饼图
