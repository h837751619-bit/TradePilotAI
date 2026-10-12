# TradePilot AI 部署与安全检查

## 1. 本地开发

```bash
cd backend
source .venv/bin/activate
PYTHONPATH=src uvicorn tradepilot.main:app --host 127.0.0.1 --port 8000 --reload

cd frontend
npm run dev -- --host 127.0.0.1
```

正式 Docker 部署使用 MySQL 8.4 和 Docker named volume 保存数据；SQLite 仅保留给轻量本地开发和自动化测试。应用启动前会执行 Alembic 数据库迁移。Ollama 使用本机的 `qwen3:8b` 模型。本地认证默认关闭，仅适合开发；公开部署必须开启认证。

首次启动前复制 `.env.example` 为 `.env`，设置 `MYSQL_PASSWORD` 和 `MYSQL_ROOT_PASSWORD` 为彼此不同的长随机字母数字值，并设置认证凭据。数据库密码会进入 SQLAlchemy URL，所以 Compose 示例使用 URL 安全的字母数字密码。不要提交 `.env`。

```sh
cp .env.example .env
docker compose up -d --build
docker compose ps
```

数据库只在 Compose 内网开放，不映射主机端口。`tradepilot_mysql_data` 卷在容器重启和镜像更新后保留。不要使用 `docker compose down -v`，该命令会删除数据库卷。

### 从现有 SQLite 迁移

迁移前先停写并备份 SQLite 文件。项目内可能同时存在 `tradepilot.db` 与 `backend/tradepilot.db`；先核实哪份是当前正式数据，不能直接合并两份。启动 MySQL 使 Alembic 完成建表后，用以下脚本将选定源库复制到空的 MySQL 目标库；脚本会在目标业务表已有记录时拒绝执行，并保留源文件不变：

```sh
docker compose run --rm \
  -v "$PWD/backend/tradepilot.db:/tmp/tradepilot-source.db:ro" \
  backend sh -c 'python scripts/migrate_sqlite_to_mysql.py sqlite:////tmp/tradepilot-source.db "$DATABASE_URL"'
```

这里 `$DATABASE_URL` 在容器内由 Compose 注入；将挂载路径和 SQLite 文件名改为确认后的源库。迁移完成后抽查客户、产品、报价、库存和用户数量，再正常启动后端。若源库中的表结构落后，新字段按目标 schema 的默认值/可空规则处理。

### 备份与恢复

定期将 MySQL 逻辑备份复制到 Compose 卷之外的安全位置（加密并限制访问）：

```sh
mkdir -p backups
docker compose exec -T database sh -c 'exec mysqldump --single-transaction -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"' > backups/tradepilot-$(date +%F-%H%M%S).sql
```

恢复前先停后端写入，并确认目标数据库和备份文件；恢复会覆盖备份中同名表的数据：

```sh
docker compose stop backend
docker compose exec -T database sh -c 'exec mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"' < backups/选择的备份.sql
docker compose start backend
```

至少定期执行恢复演练；仅看到备份文件不等于已验证可恢复。

## 2. Docker 演示

```bash
cp .env.example .env
docker compose up --build
```

Docker 演示默认只监听本机 `127.0.0.1`，前端端口为 `8080`、后端端口为 `8000`；认证关闭、API 文档关闭，AI 使用规则引擎，不依赖容器内无法访问的本机 Ollama。前端通过 Nginx 将 `/api` 转发给后端，不需要设置 `VITE_API_BASE`。

需要使用宿主机 Ollama 时，在根目录 `.env` 中设置：

```env
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=qwen3:8b
```

也可以使用 OpenAI 兼容的在线聊天接口（例如 OpenAI 或提供兼容接口的其他服务）。在根目录 `.env` 或 `backend/.env` 中配置：

```env
AI_PROVIDER=openai_compatible
OPENAI_COMPATIBLE_API_KEY=由服务商提供的密钥
OPENAI_COMPATIBLE_BASE_URL=https://api.openai.com/v1
OPENAI_COMPATIBLE_MODEL=gpt-4o-mini
OPENAI_COMPATIBLE_TIMEOUT_SECONDS=45
```

服务商若提供不同的兼容 API 地址和模型名，替换 `BASE_URL` 与 `MODEL` 即可。密钥只配置在后端环境或部署密钥管理中；不要放进前端变量、截图或 Git 提交。未配置密钥时，界面会显示该提供方不可用，后端也会拒绝切换。设置环境变量后需重启后端或 Compose 容器。

选择在线模型后，询盘文本会发送到所配置的模型服务商，并按其账户规则计费；不要提交不允许发送到该服务商的客户或敏感信息。

也可以在界面中分别选择 DeepSeek 或 Kimi/Moonshot。分别设置 `DEEPSEEK_API_KEY`（默认模型 `deepseek-chat`）或 `KIMI_API_KEY`（默认模型 `moonshot-v1-8k`）；Base URL 和模型可通过对应的 `*_BASE_URL`、`*_MODEL` 环境变量覆盖。所有密钥仅由后端读取。

Compose 端口可以通过 `BACKEND_PORT`、`FRONTEND_PORT` 修改。默认绑定仅允许本机访问；如设置 `TRADEPILOT_BIND=0.0.0.0`，服务会暴露到网络接口。对外部署前必须开启认证、设置强随机 `AUTH_SECRET` 和管理员密码哈希、限定 `CORS_ORIGINS`，并通过 HTTPS 反向代理对外提供服务。当前 Compose 文件仍是单机演示方案，不构成完整的生产部署配置。

## 3. 开启认证

先生成密码哈希：

```bash
cd backend
source .venv/bin/activate
PYTHONPATH=src python -c 'from tradepilot.auth import hash_password; print(hash_password("替换为强密码"))'
```

将结果通过部署平台的密钥管理功能注入，不要提交到 Git：

```env
AUTH_ENABLED=true
AUTH_SECRET=随机生成的高强度密钥
AUTH_USERNAME=admin
AUTH_PASSWORD_HASH=PBKDF2哈希结果
AUTH_ROLE=admin
AUTH_TOKEN_TTL_SECONDS=3600
AUTH_REFRESH_TTL_SECONDS=604800
```

启用后：

- 登录：`POST /api/auth/login`
- 刷新：`POST /api/auth/refresh`
- 退出：`POST /api/auth/logout`
- 管理用户：`GET/POST /api/users`、`PATCH /api/users/{id}`
- 审批报价必须使用 `admin` 或 `approver` 角色。

授权规则：启用认证后，业务读取接口要求已登录的 `viewer`、`approver` 或 `admin`；客户/产品修改、库存调整、询盘报价及报价审批/取消要求 `approver` 或 `admin`；用户管理和全局 AI 服务商切换仅允许 `admin`。健康检查、认证状态和登录/刷新/退出接口保持公开。认证默认关闭仅供本机演示，不能将这种配置暴露到公网。

## 4. 环境变量检查

- `DATABASE_URL`：Docker Compose 中指向 MySQL 8.4；直接开发可用 SQLite。生产建议使用托管 MySQL 和平台 Secret 注入。
- `MYSQL_DATABASE`、`MYSQL_USER`、`MYSQL_PASSWORD`、`MYSQL_ROOT_PASSWORD`：Compose MySQL 初始化账户配置，不要提交真实凭据。
- `CORS_ORIGINS`：只填写实际前端域名，不要使用 `*`。
- `API_DOCS_ENABLED`：生产环境建议关闭。
- `WORKFLOW_RATE_LIMIT_PER_MINUTE`：按部署规模设置。
- `OLLAMA_BASE_URL`：确认后端容器可以访问 Ollama；容器内的 `127.0.0.1` 指向容器自身。
- `AI_PROVIDER`：Docker 演示默认为 `rules`；仅在 Ollama 可被后端容器访问时设置为 `ollama`。
- `OPENAI_COMPATIBLE_API_KEY`、`OPENAI_COMPATIBLE_BASE_URL`、`OPENAI_COMPATIBLE_MODEL`：在线聊天模型配置；API Key 仅由后端读取。
- `AUTH_SECRET`：每个环境使用不同的随机值。

## 5. 上线前检查

- [ ] 认证已开启。
- [ ] 已使用密码哈希，没有提交明文密码。
- [ ] 已配置强随机 `AUTH_SECRET`。
- [ ] CORS 只允许正式前端域名。
- [ ] API 文档在生产环境关闭。
- [ ] SQLite 数据文件或 MySQL 数据库已备份。
- [ ] Alembic migration 已执行并检查版本。
- [ ] Ollama 或官方模型服务可访问。
- [ ] Git 历史和待提交文件已完成敏感信息扫描。
- [ ] 已验证登录、刷新、退出、审批权限和重复审批场景。
- [ ] 未配置真实邮件自动发送，报价仍需人工审批。

## 6. GitHub 上传前检查

```bash
git status --short
rg -n "(sk-[A-Za-z0-9]|AKIA[0-9A-Z]{16}|AUTH_SECRET=.+|AUTH_PASSWORD=.+)" -S . --glob '!node_modules/**' --glob '!frontend/dist/**'
```

确认没有 `.env`、数据库文件、API Key、密码或本地日志后，再由项目负责人决定是否提交和推送 GitHub。
