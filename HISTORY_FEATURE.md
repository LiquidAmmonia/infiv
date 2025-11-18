# 历史记录功能说明

## 功能概述

现在项目已支持查看历史上每天生成的markdown文档。每次运行时会：
1. 将当天的报告保存到 `history/YYYY-MM-DD.md`
2. 自动生成 `index.md` 索引页面，列出所有历史报告
3. 提交到Git仓库保存
4. 部署到GitHub Pages供浏览

## 使用方法

### 在GitHub Pages上查看

访问你的GitHub Pages网站，左侧导航栏会显示：
- **History Archive** - 历史归档索引页
- **Latest Daily News** - 最新的每日报告

点击History Archive可以看到所有历史报告的列表，按日期倒序排列。

### 本地测试

```bash
# 1. 生成报告（会自动保存到history目录）
python -m infiv build --use_embed

# 2. 生成历史索引
python -m infiv gen_history_index

# 3. 本地预览
myst start
```

### 文件结构

```
infiv/
├── history/              # 历史报告目录
│   ├── 2025-11-19.md
│   ├── 2025-11-18.md
│   └── ...
├── index.md             # 历史索引页（自动生成）
├── output.md            # 最新报告
└── _build/html/         # 构建的网站
```

## 技术细节

### 修改的文件

1. **infiv/build.py** - 添加了保存历史文件的逻辑
2. **infiv/generate_history_index.py** - 新增历史索引生成脚本
3. **infiv/__main__.py** - 添加了 `gen_history_index` 子命令
4. **.github/workflows/daily_flow.yaml** - 工作流中添加了提交历史记录的步骤
5. **myst.yml** - 更新了目录配置

### GitHub Actions工作流

每次运行时会：
1. 生成当天报告
2. 保存到history目录
3. 生成索引页面
4. 提交更改到仓库
5. 部署到GitHub Pages

### 权限说明

已将GitHub Actions的权限从 `contents: read` 改为 `contents: write`，以允许提交历史文件。

## 注意事项

- 历史文件会永久保存在Git仓库中
- 如果仓库过大，可考虑定期清理旧文件或使用Git LFS
- 每次运行都会覆盖当天的历史文件（如果存在）
