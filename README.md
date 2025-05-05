# Rosetta

![Python版本](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Django版本](https://img.shields.io/badge/Django-4.2.11-green.svg)
![许可证](https://img.shields.io/badge/License-MIT-yellow.svg)

Rosetta是一个多功能的个人网站平台，基于Django框架开发，支持博客、视频站点分享和个人主页展示等功能。项目采用了现代化的设计理念，内置多语言支持、黑暗模式和响应式布局，为用户提供流畅的浏览体验。

## ✨ 功能特点

- 📝 **博客系统**：支持Markdown和富文本编辑器，标签分类，评论系统
- 🎬 **视频站点分享**：收集和分享优质影视资源网站，支持按类别筛选
- 👤 **个人主页**：可定制的个人信息展示，包含技能、社交链接等
- 🌓 **黑暗模式**：内置日/夜间模式切换，自动适应系统设置
- 🌐 **多语言支持**：内置中英文界面，易于扩展其他语言
- 📱 **响应式设计**：完美适配电脑、平板和手机等多种设备
- 🛠️ **管理后台**：基于Unfold的美观实用的管理界面

## 🔧 技术栈

- **后端**：Django 4.2，Python 3.8+
- **前端**：TailwindCSS，Alpine.js，Axios
- **数据库**：SQLite (开发)，支持PostgreSQL/MySQL (生产)
- **缓存**：Redis (生产环境)，内存缓存 (开发环境)
- **国际化**：Django i18n，Rosetta
- **管理界面**：Django Unfold

## 📋 安装步骤

### 前置要求

- Python 3.8+
- uv
- 虚拟环境 (推荐)
- Redis (生产环境需要)

### 安装过程

1. 克隆仓库
```bash
git clone https://github.com/ChuyuChoyeon/Rosetta.git
cd Rosetta
```

2. 创建并激活虚拟环境
```bash
uv sync
# Windows
uv sync
# Linux/Mac
uv sync
```

3. 创建环境变量文件
```bash
# 复制示例环境变量文件
cp .env.example .env
# 编辑.env文件，填写必要的配置
```

4. 运行迁移
```bash
python manage.py migrate
```

6. 创建超级用户
```bash
python manage.py createsuperuser
```

7. 运行开发服务器
```bash
python manage.py runserver
```

8. 访问网站
   - 前台：http://127.0.0.1:8000
   - 管理后台：http://127.0.0.1:8000/admin

## 🚀 部署指南

### 使用Docker部署

1. 确保安装了Docker和docker-compose
2. 配置环境变量
3. 运行容器
```bash
docker-compose up -d
```

### 传统部署

1. 设置生产环境配置（修改.env文件）
2. 收集静态文件
```bash
python manage.py collectstatic
```
3. 使用Gunicorn和Nginx配置项目（详见文档）

## 📝 使用说明

1. **管理内容**：通过管理后台 (/admin) 添加和管理所有内容
2. **个性化设置**：修改个人资料、添加社交链接
3. **发布博客**：使用内置编辑器创建博客文章
4. **添加视频站点**：在管理后台添加和分类视频资源站点

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

## 📜 许可证

本项目采用 MIT 许可证 - 详情请参阅 [LICENSE](LICENSE) 文件

## 📞 联系方式

作者 - [@ChuyuChoyeon](https://github.com/ChuyuChoyeon)

项目链接: [https://github.com/ChuyuChoyeon/Rosetta](https://github.com/ChuyuChoyeon/Rosetta)
