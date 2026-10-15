# TradePilot AI 项目进度与问题记录

> 本文件用于持续记录 TradePilot AI 项目的开发流程、功能进度、测试结果、已遇到的问题，以及问题的原因和解决方式。下方按日期记录的内容是历史开发日志；遇到与本节冲突时，以本节当前状态和 README/DEPLOYMENT.md 为准。

## 1. 项目概述

TradePilot AI 是一个面向外贸销售场景的 AI Agent MVP，目标是将客户询盘转换为产品匹配、库存检查、报价草稿和后续销售动作。

项目目录：仓库根目录（本文档中的路径均相对于仓库根目录）。

当前阶段：核心业务功能已实现，项目已采用 Docker Compose + MySQL 持久化；正在进行公开发布前的文档、安全与部署检查。此状态记录于 2026-10-12，后续请随开发更新。

## 2. 技术栈

- 前端：Vue 3、TypeScript、Vite
- 后端：FastAPI、SQLAlchemy、Alembic
- 数据库：Docker Compose 使用 MySQL 8.4；SQLite 用于轻量本地开发和自动化测试
- 本地模型：Ollama `qwen3:8b`
- AI 接口：规则引擎、Ollama，以及可配置的 OpenAI-compatible、DeepSeek、Kimi/Moonshot API
- 后端地址：`http://127.0.0.1:8000`
- Docker Compose 前端地址：`http://127.0.0.1:8080`；Vite 开发地址：`http://127.0.0.1:5173`
- Ollama 地址：`http://127.0.0.1:11434`
- 数据迁移和备份说明：见 [DEPLOYMENT.md](DEPLOYMENT.md)。本机 `.env`、数据库和备份不得提交。

## 3. 当前运行方式

### 3.1 启动后端

```bash
cd backend
source .venv/bin/activate
PYTHONPATH=src uvicorn tradepilot.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3.2 启动前端

```bash
cd frontend
npm run dev -- --host 127.0.0.1
```

### 3.3 检查服务

```bash
curl http://127.0.0.1:8000/health
ollama list
curl http://127.0.0.1:11434/api/tags
```

## 4. 功能完成情况

### 4.1 后端

- [x] FastAPI 服务和健康检查
- [x] SQLite、SQLAlchemy 和 Alembic 基础结构
- [x] 产品模型、产品种子数据和关键词检索
- [x] 基础 RAG 产品检索
- [x] 库存检查和定价工具
- [x] 报价生成与 Quote 持久化
- [x] 询盘解析
- [x] 询盘到报价工作流
- [x] Email draft 生成
- [x] 报价风险检查和人工审批
- [x] 客户查询、客户 CRUD、客户历史报价
- [x] Agent Run Trace
- [x] Evaluation 数据集和指标
- [x] API 限流、CORS、统一 API 错误格式和请求日志
- [x] API 文档开关
- [x] Docker 健康检查和迁移启动逻辑
- [x] AI Provider 抽象
- [x] 规则引擎 Provider
- [x] Ollama Provider
- [x] Provider 切换接口
- [x] AI 询盘解析和 Ollama 失败后的规则引擎回退
- [x] 产品匹配评分、候选产品排序、匹配原因和未满足条件
- [x] 候选产品库存状态、库存不足标记和候选 SKU 手动选报价
- [x] 产品新增、编辑和软删除/停用
- [x] `match_tags` AI 匹配标签字段
- [x] AI 产品标签建议和应用
- [x] Qwen 返回 JSON 的容错解析

主要接口：

```text
GET    /health
GET    /api/products
POST   /api/products
PATCH  /api/products/{sku}
DELETE /api/products/{sku}
GET    /api/customers
POST   /api/customers
GET    /api/customers/{id}
PATCH  /api/customers/{id}
DELETE /api/customers/{id}
GET    /api/customers/{id}/quotes
POST   /api/workflow/inquiry-to-quote
GET    /api/quotes
POST   /api/quotes/{id}/approve
GET    /api/agent-runs
GET    /api/evaluation
GET    /api/ai/providers
POST   /api/ai/providers
POST   /api/products/{sku}/suggest-tags
```

### 4.2 前端

已完成页面和功能：

- [x] 询盘工作台
- [x] 产品库
- [x] 报价单
- [x] Agent Trace
- [x] 客户管理
- [x] 中文、English、Italiano 三种语言切换
- [x] 产品搜索、详情、编辑、新增和停用
- [x] AI 标签建议与应用
- [x] 客户搜索、新增、编辑、删除和历史报价
- [x] 将客户信息带入询盘
- [x] 报价审批
- [x] 匹配分数和匹配解释展示
- [x] 候选产品选择后重新生成报价
- [x] AI Provider 选择：Rules / Qwen local
- [x] AI 分析状态展示
- [x] 响应式布局
- [x] 使用 URL hash 保持页面状态

### 4.3 AI 与 Ollama

当前已接入本机 Ollama 模型：

```text
模型：qwen3:8b
能力：completion、tools、thinking
```

当前 AI 流程：

1. 前端提交客户询盘。
2. 后端根据当前 Provider 选择规则引擎或 Ollama。
3. Ollama 对询盘提取数量、国家、项目类型、产品关键词等信息。
4. 后端将 AI 关键词与规则关键词合并，用于产品候选筛选。
5. 对候选产品进行匹配评分、库存检查和报价计算。
6. 如果 Ollama 不可用或输出无法解析，则自动回退到规则引擎。

已验证的真实询盘：

```json
{
  "inquiry": "We need 120 aluminum outdoor chairs for a hotel project in Germany.",
  "customer_name": "Acme Hotels"
}
```

验证结果：

```text
ai_provider: ollama
quantity: 120
destination_country: Germany
quote SKU: NOVA-CHAIR-001
quote quantity: 120
HTTP 状态：200
```

## 5. 数据库和迁移

早期 SQLite 数据库记录（历史，不代表当前运行数据库）：

```text
backend/tradepilot.db
```

当前 Docker Compose 正式运行配置使用 MySQL 8.4；SQLite 仅用于本地轻量开发/测试。SQLite 到 MySQL 的迁移历史和步骤见 [DEPLOYMENT.md](DEPLOYMENT.md)。

产品表后来增加了 `match_tags` 字段，用于保存 AI 产品匹配标签。

一次旧数据库升级中，数据库已经存在业务表，但没有 `alembic_version` 记录。直接执行 `alembic upgrade head` 会尝试重复创建已有表并失败。为保留原有数据，采用了以下处理方式：

```sql
ALTER TABLE products ADD COLUMN match_tags VARCHAR(500) NOT NULL DEFAULT '';
```

然后将已有数据库标记为当前迁移版本：

```bash
alembic stamp head
```

后续数据库结构变更应优先编写新的 Alembic migration，并在执行前确认当前数据库的迁移版本。

## 6. 问题与解决记录

### 6.1 前端按钮无反应

现象：前端点击按钮后没有看到预期结果。

原因：后端或前端旧进程仍在运行，端口虽然可访问，但加载的不是包含最新路由和逻辑的新代码。

解决方式：

1. 检查 `8000` 和 `5173` 端口对应的进程。
2. 重启服务，或触发 Uvicorn reload。
3. 通过 API 和浏览器确认新接口已经加载。

验证：新接口可以正常响应，前端询盘、客户和产品操作恢复正常。

### 6.2 `POST /api/customers` 返回 405

现象：新增客户接口返回 `405 Method Not Allowed`。

原因：旧后端进程没有加载新增的客户 CRUD 路由。

解决方式：重启后端服务，确认当前进程加载最新代码。

验证：`POST /api/customers` 路由可用，客户新增、编辑和删除功能可以继续测试。

### 6.3 AI 解析显示失败或返回 500

现象：前端提示 AI 分析失败，后端日志显示数据库字段相关错误。

原因：旧 SQLite 数据库中缺少新增加的 `match_tags` 字段。

解决方式：补充字段，并将数据库迁移状态标记到当前版本：

```sql
ALTER TABLE products ADD COLUMN match_tags VARCHAR(500) NOT NULL DEFAULT '';
```

```bash
alembic stamp head
```

验证：后端健康检查正常，产品读取和询盘到报价流程恢复。

### 6.4 Alembic 重复建表

现象：执行 `alembic upgrade head` 时，迁移尝试创建已经存在的表。

原因：旧数据库没有迁移版本记录，Alembic 无法知道已有表是历史结构。

解决方式：确认数据库结构后补齐缺少字段，再执行 `alembic stamp head`，不删除旧数据库、不重置业务数据。

### 6.5 Qwen JSON 解析失败

现象：Ollama 能够返回内容，但应用无法将返回内容解析为询盘结构。

原因：Qwen 可能返回 Markdown JSON 代码块、JSON 前后的解释文字，或者将 `product_keywords` 返回成字符串而不是数组。

解决方式：

- 移除 ```json 和 ``` 包裹。
- 从第一个 `{` 到最后一个 `}` 提取 JSON。
- 将字符串形式的 `product_keywords` 自动包装成数组。
- JSON 解析失败时自动回退规则引擎。

验证：Qwen 真实调用成功，询盘字段和报价结果均能生成。

### 6.6 Qwen 项目类型影响产品匹配

现象：Qwen 返回 `hotel project` 时，产品文本虽然包含 `hotel`，但精确匹配没有命中。

原因：原有评分逻辑要求项目类型完全相等，没有处理自然语言中的项目后缀。

解决方式：对项目类型做标准化：

- `hotel project` → `hotel`
- `resort project` → `resort`

验证：酒店项目询盘能够匹配 `NOVA-CHAIR-001`。

### 6.7 Qwen 关键词导致产品匹配失败

现象：AI 返回 `aluminum outdoor chairs`、复数或自然语言短语时，没有找到产品。

原因：原有规则检索只识别有限的标准关键词。

解决方式：将 AI 关键词与规则引擎识别出的标准关键词合并，统一转小写、去重，并保留规则关键词作为兜底。

### 6.8 报价审批返回 409

现象：审批报价时返回：

```json
{
  "error": {
    "code": "HTTP_409",
    "message": "Only draft quotes can be approved"
  }
}
```

原因：用于测试的报价已经审批过。该接口只允许审批 `draft` 状态报价，因此属于符合设计的业务冲突，不是程序错误。

解决方式：创建新的草稿报价后再测试审批，或在前端根据报价状态禁用重复审批按钮。

### 6.9 后端启动时报 `Address already in use`

现象：启动 Uvicorn 时出现：

```text
[Errno 48] Address already in use
```

原因：`8000` 端口已经有后端进程在运行，通常是之前启动的 Uvicorn 或 reload 子进程。

解决方式：先确认已有服务是否可用；如果需要加载最新代码，则停止占用端口的旧进程后再启动。不要在服务已经正常运行时重复启动第二个实例。

验证：

```bash
curl http://127.0.0.1:8000/health
```

返回 `{"status":"ok"}` 即表示已有服务正常。

## 7. 测试记录

最近一次代码验证结果：

```text
后端 pytest：54 passed
Ruff：All checks passed
前端 vue-tsc：通过
Vite build：通过
```

最近一次真实联调结果：

```text
GET /health：正常
前端首页：HTTP 200
Ollama qwen3:8b：正常
Ollama Provider：正常
真实询盘到报价：HTTP 200
报价产品：NOVA-CHAIR-001
```

每次后续修改后，至少应重新运行后端测试、前端类型检查和前端构建；涉及 AI 或 API 的改动还应执行一次真实接口联调。

## 8. 当前已知限制（2026-10-12）

- Docker Compose 面向单机演示/自托管，不等同于高可用生产部署；对外部署前必须启用认证、HTTPS、强密钥并限制 CORS。
- 使用 Ollama 时依赖可访问的 Ollama 服务和已下载模型；在线模型需要用户自行配置服务商 API Key 并承担相关费用。
- 库存并发预留的 MySQL 行锁/原子更新行为尚未验证；高并发或真实订单场景上线前需补充保护和并发测试。
- AI 输出属于辅助解析，仍需要规则校验和人工审批。
- 产品匹配依赖产品名称、关键词、`match_tags` 和项目类型信息，复杂语义匹配仍可继续增强。
- GitHub 仓库已创建并配置为公开，但目前尚未推送本地项目；MIT 许可证已添加。发布前仍需完成敏感信息/历史扫描、测试和最终 diff 审核。
- API Key 或其他敏感凭证不得直接写入代码、提交记录或本文档。

## 9. 下一步计划

以下为 2026-10-09 的历史路线图；已完成项请结合后续记录和当前实现判断，不应视为当前待办清单：

1. 继续进行前后端联合测试，覆盖正常输入、空输入、无匹配产品、库存不足和重复审批等场景。
2. 为 AI 解析、产品匹配和回退逻辑补充更多自动化测试。
3. 完善前端错误提示，区分网络错误、AI 回退、无匹配产品和业务冲突。
4. 增强产品匹配标签和多语言关键词。
5. 评估 SQLite 到 MySQL 的迁移方案，但在确认需求前保持当前 SQLite 不变。
6. 补充 Docker、环境变量、生产部署和安全配置文档。
7. 完成 Git 状态检查、敏感信息扫描和 README 更新后，再由用户确认是否上传 GitHub。

## 10. 关键文件

后端：

- `backend/src/tradepilot/api.py`
- `backend/src/tradepilot/inquiry.py`
- `backend/src/tradepilot/workflow.py`
- `backend/src/tradepilot/ai_provider.py`
- `backend/src/tradepilot/product_matching.py`
- `backend/src/tradepilot/models.py`
- `backend/src/tradepilot/schemas.py`
- `backend/src/tradepilot/config.py`
- `backend/alembic/versions/20261007_product_match_tags.py`

前端：

- `frontend/src/App.vue`
- `frontend/src/api.ts`
- `frontend/src/types.ts`

数据库：

- `backend/tradepilot.db`（历史 SQLite 文件路径；不要提交数据库文件）

## 11. 后续记录模板

后续每完成一项任务，可按以下格式追加：

```markdown
### YYYY-MM-DD：任务名称

任务目标：

实现内容：

遇到的问题：

报错信息：

原因：

解决方式：

验证结果：

下一步：
```

## 12. 2026-10-09：重启与全流程冒烟测试

### 12.1 重启结果

- [x] 停止旧的后端和前端进程
- [x] 使用最新代码启动后端
- [x] 使用最新代码启动前端
- [x] 后端监听 `127.0.0.1:8000`
- [x] 前端监听 `127.0.0.1:5173`
- [x] Ollama `qwen3:8b` 可访问

### 12.2 自动化验证

```text
后端 pytest：54 passed
Ruff：All checks passed
前端 vue-tsc：通过
Vite build：通过
```

### 12.3 接口冒烟测试

通过的接口和场景：

- [x] `GET /health`
- [x] 前端首页 HTTP 200
- [x] 产品列表
- [x] 客户列表
- [x] 报价列表
- [x] Agent Run 列表
- [x] Evaluation 指标，所有指标为 `1.0`
- [x] AI Provider 查询和切换
- [x] 规则引擎产品标签建议
- [x] 无匹配产品时返回结构化 404 错误
- [x] 报价审批

### 12.4 Ollama 真实联调

使用 `qwen3:8b` 处理以下询盘成功：

```text
We need 120 aluminum outdoor chairs for a hotel project in Germany.
```

结果：

- AI Provider：`ollama`
- 数量：`120`
- 目的地：`Germany`
- 项目类型：`hotel`
- 产品：`NOVA-CHAIR-001`
- 报价状态：先生成 `draft`，随后成功审批为 `approved`

### 12.5 本次发现的问题

#### Ollama 模式的 AI 标签建议超时

现象：

```text
POST /api/products/NOVA-CHAIR-001/suggest-tags
HTTP 503
AI tag suggestion unavailable: timed out
```

对比结果：切换到规则 Provider 后，同一接口正常返回标签建议。因此问题范围限定在 Ollama 标签建议调用的响应耗时或超时阈值，不影响规则标签建议和询盘到报价主流程。

当前状态：已修复并完成真实验证。标签建议现在使用专用 90 秒超时、关闭 Qwen thinking，并兼容模型返回的 Markdown JSON 和附带说明文字。

#### 报价单详情接口不存在

测试 `GET /api/quotes/35` 返回 404。当前后端只提供报价列表接口 `GET /api/quotes` 和审批接口 `POST /api/quotes/{quote_id}/approve`，前端当前使用列表数据，因此这不是本次主流程故障。如需要单条报价详情，应作为独立接口需求补充。

### 12.6 当前服务状态

本次测试结束时保持：

```text
后端：运行中，http://127.0.0.1:8000
前端：运行中，http://127.0.0.1:5173
AI Provider：ollama
Ollama：运行中，http://127.0.0.1:11434
```

## 13. 2026-10-09：修复 Ollama 标签建议超时

### 问题

产品标签建议接口使用默认 30 秒请求超时。Qwen3 在生成标签时可能进行 thinking，导致接口返回 503 超时；同时模型可能返回 Markdown JSON 或 JSON 外附带解释文字。

### 修复内容

- 为 Ollama Provider 增加可选 `think` 参数。
- 标签建议请求使用 `think=False`，减少不必要的推理耗时。
- 增加 `ollama_tag_timeout_seconds` 配置，默认 90 秒，仅用于标签建议接口。
- 增加统一 JSON 对象解析，支持代码块和前后附带文字。
- 询盘解析复用同一 JSON 容错解析逻辑。
- 增加 Provider、JSON 解析和标签建议接口自动化测试。

### 修复后验证

```text
后端 pytest：57 passed
Ruff：All checks passed
前端构建：通过
真实 Ollama 标签建议：HTTP 200
返回模型：qwen3:8b
健康检查：HTTP 200
```

真实返回示例包含：

```text
stackable outdoor chair
hotel outdoor seating
aluminum patio chair
powder coated outdoor chair
restaurant outdoor seating
```

## 14. 2026-10-09：前后端错误处理与状态反馈

### 实现内容

- [x] 前端统一解析后端结构化错误信息，优先展示 `error.message` 或 `detail`。
- [x] 产品新增、编辑、停用增加 loading 和重复点击保护。
- [x] AI 产品标签建议增加 loading 状态。
- [x] 客户新增、编辑、删除增加 loading 和重复点击保护。
- [x] 报价审批增加 loading 和重复审批保护。
- [x] 询盘分析按钮在请求期间禁用，避免重复提交。
- [x] 产品标签建议超时、无权限、产品不存在等错误可以直接反馈后端原因。

### 验证结果

```text
前端 vue-tsc：通过
Vite build：通过
git diff --check：通过
```

## 32. 2026-10-11：预算与交期条件解析

### 实现内容

- [x] 从询盘规则中提取预算上限。
- [x] 从询盘规则中提取最大交期天数。
- [x] 将预算和交期条件纳入候选产品未满足条件和评分。
- [x] Ollama JSON 提示词支持返回预算与交期字段。

### 验证结果

```text
后端 pytest：67 passed
Ruff：All checks passed
前端 Vite build：通过
git diff --check：通过
```

## 30. 2026-10-11：审批后风险提示同步

### 实现内容

- [x] 报价草稿显示人工审批风险提示。
- [x] 报价批准后隐藏叹号风险提示并显示批准状态。
- [x] 报价详情接口在已批准状态下不再标记为待审批。

### 验证结果

```text
后端 pytest：68 passed
Ruff：All checks passed
前端 Vite build：通过
git diff --check：通过
```

## 33. 2026-10-11：预算与交期参与自动选品

### 实现内容

- [x] 自动报价默认从匹配候选中选择满足库存、预算和交期的最高分产品。
- [x] 用户指定 `selected_sku` 时保留手动选品优先级。
- [x] 没有产品满足硬性条件时返回明确业务错误。
- [x] 新增预算与交期自动选品测试。

### 验证结果

```text
后端 pytest：68 passed
Ruff：All checks passed
前端 Vite build：通过
git diff --check：通过
```

## 30. 2026-10-11：产品候选区域多语言完善

### 实现内容

- [x] 候选产品标题、库存状态和报价按钮支持中文、英语、意大利语。
- [x] 移除候选产品区域新增功能的英文硬编码。

### 验证结果

```text
前端 Vite build：通过
git diff --check：通过
```

## 31. 2026-10-11：产品候选排序与商务信息

### 实现内容

- [x] 库存充足的候选产品优先排序。
- [x] 候选产品展示美元单价和交期天数。
- [x] 新增候选返回字段测试。

### 验证结果

```text
后端 pytest：67 passed
Ruff：All checks passed
前端 Vite build：通过
git diff --check：通过
```

本次仅修改前端错误处理和交互状态，没有修改数据库数据。

## 15. 2026-10-09：报价详情与邮件草稿

### 实现内容

- [x] 新增 `GET /api/quotes/{quote_id}` 单条报价详情接口。
- [x] 返回报价基础信息、当前状态和询盘原文。
- [x] 返回风险判断及需要审批的原因。
- [x] 返回根据报价生成的邮件草稿。
- [x] 返回产品匹配候选、匹配分数和匹配原因。
- [x] 前端报价列表支持点击查看详情。
- [x] 前端详情面板展示风险、Top 产品匹配和邮件草稿。
- [x] 报价审批按钮继续保留重复点击保护。

### 验证结果

```text
后端 pytest：58 passed
Ruff：All checks passed
前端 vue-tsc：通过
Vite build：通过
GET /api/quotes/35：HTTP 200
前端首页：HTTP 200
```

说明：当前 `QuoteRecord` 没有独立的审批历史表，因此详情页展示当前审批状态和风险判断，不虚构历史审批记录。

## 16. 2026-10-09：报价审批审计记录

### 实现内容

- [x] 新增 `approval_history` 数据表和 SQLAlchemy 模型。
- [x] 新增 Alembic migration：`20261009_approval_history.py`。
- [x] 报价审批成功时记录原状态、目标状态、操作人和时间。
- [x] 报价详情接口返回 `approval_history`。
- [x] 前端报价详情面板展示审批历史。
- [x] 重复审批仍返回 HTTP 409，不会重复写入历史记录。

当前默认操作人标识为 `manual-review`。在接入用户登录和权限系统后，应替换为真实用户 ID。

### 验证结果

```text
后端 pytest：58 passed
Ruff：All checks passed
前端 vue-tsc：通过
Vite build：通过
现有报价详情只读接口：HTTP 200
```

已有历史报价由于审批发生在审计表创建前，历史列表为空是预期结果；新创建并审批的报价会产生完整审计记录。本次未直接修改现有报价状态。

## 17. 2026-10-09：操作人身份传递

### 实现内容

- [x] 前端审批请求携带 `X-Actor-Id` 请求头。
- [x] 当前工作台操作人 ID 为 `jordan-davis`。
- [x] 后端审批接口读取操作人 ID 并写入 `approval_history.actor`。
- [x] 未携带请求头时继续使用 `manual-review` 作为兼容默认值。
- [x] 增加带操作人 ID 的审批接口测试。

### 验证结果

```text
后端 pytest：58 passed
Ruff：All checks passed
前端 vue-tsc：通过
Vite build：通过
```

### 安全说明

`X-Actor-Id` 目前只是身份传递机制，不是安全认证。客户端仍可伪造该请求头，因此正式上线前必须接入 JWT、SSO 或其他服务端可验证的登录凭证，并在后端实现审批权限校验。

## 18. 2026-10-09：可配置认证基础

### 实现内容

- [x] 新增签名令牌生成和验证模块。
- [x] 新增 `POST /api/auth/login` 登录接口。
- [x] 支持配置用户名、密码、签名密钥和令牌有效期。
- [x] 开启认证后，报价审批必须携带有效的 Bearer token。
- [x] 审批历史中的操作人使用令牌中的用户标识。
- [x] 本地开发默认关闭认证，保持现有演示环境可用。
- [x] 更新 `backend/.env.example`，未写入真实凭证。

### 配置方式

在生产环境通过环境变量开启：

```env
AUTH_ENABLED=true
AUTH_SECRET=由部署环境生成的高强度随机值
AUTH_USERNAME=管理员用户名
AUTH_PASSWORD_HASH=通过安全方式注入的 PBKDF2 密码哈希
AUTH_TOKEN_TTL_SECONDS=3600
```

### 验证结果

```text
后端 pytest：59 passed
Ruff：All checks passed
前端 vue-tsc：通过
Vite build：通过
认证关闭时登录接口：HTTP 503（预期）
健康检查：HTTP 200
```

当前限制：这是 MVP 级认证基础，不包含刷新令牌和 SSO。正式部署前应继续升级为完整身份系统。

## 19. 2026-10-09：前端登录与 Token 会话

### 实现内容

- [x] 新增 `GET /api/auth/status`，前端可判断是否开启认证。
- [x] 新增前端登录表单，认证开启时未登录用户显示登录页。
- [x] 登录成功后将短期访问令牌保存到 `sessionStorage`。
- [x] 审批请求自动携带 `Authorization: Bearer <token>`。
- [x] 认证关闭时继续显示原有工作台，不影响本地演示。
- [x] 登录失败显示后端返回的具体错误信息。

### 验证结果

```text
后端 pytest：59 passed
Ruff：All checks passed
前端 vue-tsc：通过
Vite build：通过
认证状态接口：HTTP 200，enabled=false
健康检查：HTTP 200
前端首页：HTTP 200
```

当前认证默认关闭。启用认证前，需要在部署环境配置 `AUTH_SECRET`、`AUTH_USERNAME` 和 `AUTH_PASSWORD_HASH`，并进行一次真实登录和审批联调。

## 20. 2026-10-09：认证端到端测试

### 测试覆盖

- [x] 错误密码返回 HTTP 401。
- [x] 认证开启时未携带 Token 的审批返回 HTTP 401。
- [x] 正确用户名和密码可以获得 Bearer Token。
- [x] 携带 Token 可以完成报价审批。
- [x] 审批历史使用 Token 中的用户 ID，而不是信任可伪造的 `X-Actor-Id`。
- [x] 未开启认证的本地演示流程保持兼容。

### 验证结果

```text
后端 pytest：60 passed
Ruff：All checks passed
前端 vue-tsc：通过
Vite build：通过
```

## 21. 2026-10-09：密码哈希与角色权限

### 实现内容

- [x] 使用 PBKDF2-SHA256 校验登录密码，不再要求配置明文密码。
- [x] Token 增加角色字段。
- [x] `admin` 和 `approver` 角色允许审批报价。
- [x] 其他角色登录可以成功，但审批返回 HTTP 403。
- [x] Token 中的用户 ID 作为审批历史操作人。
- [x] 更新 `.env.example` 使用 `AUTH_PASSWORD_HASH`。

生成密码哈希可以通过后端 Python 环境调用 `tradepilot.auth.hash_password` 完成，生成结果只应写入部署环境变量，不应提交到 Git。

### 验证结果

```text
后端 pytest：62 passed
Ruff：All checks passed
前端构建：通过
```

## 22. 2026-10-09：多用户数据表基础

### 实现内容

- [x] 新增 `users` 数据表。
- [x] 保存用户名、PBKDF2 密码哈希、角色和启用状态。
- [x] 登录接口改为从用户表查询账号，不再直接读取配置中的登录密码。
- [x] 认证配置中的账号信息只用于首次初始化管理员/审批员账号。
- [x] 已存在用户不会被启动过程覆盖。
- [x] 新增幂等 Alembic migration：`20261009_users.py`。
- [x] 保留角色审批校验：`admin`、`approver` 可以审批，其他角色禁止审批。

### 验证结果

```text
后端 pytest：62 passed
Ruff：All checks passed
前端构建：通过
```

当前仍未提供用户管理界面和刷新令牌；后续应增加管理员创建、停用用户和角色变更功能。

## 23. 2026-10-09：管理员用户管理 API

### 实现内容

- [x] `GET /api/users`：管理员查看用户列表。
- [x] `POST /api/users`：管理员创建用户，密码以 PBKDF2 哈希保存。
- [x] `PATCH /api/users/{id}`：管理员修改角色、重置密码和停用/启用用户。
- [x] 只有 `admin` 角色可以访问用户管理接口。
- [x] 管理员不能停用自己，避免系统失去管理入口。
- [x] 用户接口不会返回 `password_hash`。

### 验证结果

```text
后端 pytest：63 passed
Ruff：All checks passed
前端构建：通过
```

当前用户管理仅提供后端 API，尚未加入前端管理员页面；刷新令牌机制也尚未实现。

## 24. 2026-10-09：管理员用户管理页面

### 实现内容

- [x] 管理员导航中新增用户管理页面。
- [x] 用户列表展示用户名、角色和启用状态。
- [x] 支持新建用户并选择 `admin`、`approver`、`viewer` 角色。
- [x] 支持修改用户角色。
- [x] 支持停用和重新启用用户。
- [x] 当前登录管理员不能停用自己。
- [x] 用户管理页面仅在认证开启且当前角色为 `admin` 时显示。
- [x] 用户管理 API 自动携带 Bearer Token。

### 验证结果

```text
后端 pytest：63 passed
Ruff：All checks passed
前端 vue-tsc：通过
Vite build：通过
```

当前本地认证默认关闭，因此开发环境导航不会显示用户管理入口；启用认证并以管理员登录后即可使用。

## 25. 2026-10-09：刷新令牌与退出登录

### 实现内容

- [x] 新增 `refresh_tokens` 数据表，只保存刷新令牌哈希。
- [x] 登录返回 access token 和 refresh token。
- [x] 新增 `POST /api/auth/refresh`。
- [x] 刷新令牌采用轮换机制，旧令牌立即撤销。
- [x] 新增 `POST /api/auth/logout`，撤销当前刷新令牌。
- [x] 前端在 `sessionStorage` 保存会话令牌。
- [x] 前端增加退出登录按钮和会话清理逻辑。
- [x] 新增幂等 Alembic migration：`20261009_refresh_tokens.py`。

### 验证结果

```text
后端 pytest：63 passed
Ruff：All checks passed
前端 vue-tsc：通过
Vite build：通过
```

刷新令牌接口已覆盖登录、轮换、旧令牌失效和退出后不可再次刷新等场景。后续可继续增加 access token 过期时的前端自动刷新拦截器。

## 26. 2026-10-09：前端 Token 自动刷新

### 实现内容

- [x] 统一前端 API 请求封装。
- [x] 收到 HTTP 401 时自动尝试 refresh token。
- [x] 刷新成功后自动更新 access token 并重试原请求。
- [x] 刷新失败时清理 sessionStorage 会话，回到登录状态。
- [x] 登录、刷新和退出接口不会进入自动重试循环。
- [x] 普通业务接口、审批接口和管理员用户接口统一使用请求封装。

### 验证结果

```text
前端 vue-tsc：通过
Vite build：通过
```

## 27. 2026-10-09：认证真实隔离联调

使用临时 SQLite、临时 8001 端口和临时测试账号完成真实服务联调，未影响当前 8000 服务和正式数据库。

验证结果：

- [x] `GET /api/auth/status` 返回认证开启。
- [x] 错误密码返回 HTTP 401。
- [x] 正确登录返回 admin 角色和 refresh token。
- [x] refresh token 轮换成功。
- [x] 旧 refresh token 轮换返回 HTTP 401。
- [x] 携带 access token 审批成功，返回 HTTP 200。
- [x] 退出登录成功。
- [x] 退出后再次使用 refresh token 返回 HTTP 401。
- [x] 临时测试服务已停止。

## 28. 2026-10-09：部署与安全文档

### 实现内容

- [x] 新增 [DEPLOYMENT.md](DEPLOYMENT.md)。
- [x] 记录本地、Docker 和认证开启方式。
- [x] 说明密码哈希、Token、CORS、API 文档和 Ollama 配置要求。
- [x] 增加上线前安全检查清单。
- [x] 增加 GitHub 上传前敏感信息扫描命令。
- [x] 更新 README 的认证、报价详情和用户管理接口说明。

### 验证结果

```text
git diff --check：通过
```

本次只新增和更新文档，没有推送 GitHub，也没有写入任何真实密钥。

## 29. 2026-10-11：产品候选选择与库存提示

### 实现内容

- [x] 候选产品返回可用库存数量和库存是否充足。
- [x] 库存不足的候选产品显示不可用状态。
- [x] 询盘工作台支持点击候选 SKU 重新生成对应报价。
- [x] 后端工作流新增 `selected_sku` 参数并校验产品有效性。
- [x] 新增候选 SKU 报价接口测试。

### 验证结果

```text
后端 pytest：67 passed
Ruff：All checks passed
前端 Vite build：通过
git diff --check：通过
```

## 34. 2026-10-11：Agent 活动审批状态同步

### 实现内容

- [x] 报价草稿中的 Agent 活动步骤根据报价状态动态显示。
- [x] 草稿状态显示“等待人工审批”。
- [x] 批准后显示“报价已批准”和完成标记，不再显示等待状态或叹号。

### 验证结果

```text
前端 Vite build：通过
git diff --check：通过
```

## 35. 2026-10-11：防止重复报价记录

### 问题与原因

- 重复点击“运行分析”会重复创建 `QuoteRecord`，导致报价单出现相同记录。

### 实现内容

- [x] 相同客户、询盘、SKU、数量、价格和折扣参数的报价复用已有记录。
- [x] 已批准的相同报价重复分析时保留已批准状态。
- [x] 新增重复工作流不会创建重复报价的回归测试。
- [x] 报价列表和客户报价列表对历史重复记录只展示最新一条，不删除原始数据。

### 验证结果

```text
后端 pytest：69 passed
Ruff：All checks passed
前端 Vite build：通过
git diff --check：通过
```

## 36. 2026-10-11：解析与正式报价分阶段

### 实现内容

- [x] 运行询盘分析时只返回产品匹配预览，不创建报价单记录。
- [x] 用户选择具体产品后才创建正式报价草稿。
- [x] 未选择产品时禁用报价审批按钮并提示先选择产品。
- [x] 更新中英文和意大利语提示文案。
- [x] 更新相关工作流测试，确保解析结果不会进入报价单列表。

### 验证结果

```text
后端 pytest：69 passed
Ruff：All checks passed
前端 Vite build：通过
git diff --check：通过
```

## 37. 2026-10-11：询盘工作台产品详情展示

### 实现内容

- [x] 点击产品匹配候选后高亮当前产品。
- [x] 展示产品描述、SKU、材质、颜色、MOQ、库存和交期等详细信息。
- [x] 查看详情与“按此产品报价”分离，点击详情不会自动生成报价。

### 验证结果

```text
前端 Vite build：通过
git diff --check：通过
```

## 38. 2026-10-11：产品详情改为卡片内联展开

### 实现内容

- [x] 点击候选产品后，在对应产品卡片内部展开详情。
- [x] 不再将详情统一显示在候选列表底部。
- [x] 保留产品详情查看与正式报价生成的独立操作。

### 验证结果

```text
前端 Vite build：通过
git diff --check：通过
```

## 39. 2026-10-11：搜索结果支持产品详情

### 问题与原因

- 产品匹配区域的搜索结果卡片只有展示效果，没有点击事件。

### 实现内容

- [x] 搜索结果产品卡片支持点击选中。
- [x] 在对应搜索结果卡片内部展开产品详情。
- [x] 查看搜索结果详情不会自动生成报价。

### 验证结果

```text
前端 Vite build：通过
git diff --check：通过
```

## 40. 2026-10-11：普通品类询盘解析修复

### 问题与原因

- 规则引擎回退时只识别 `outdoor chair` 等完整短语，无法识别普通的 `chairs`。
- 中国未在规则引擎的国家列表中，导致 AI 不可用时目的地无法识别。

### 实现内容

- [x] 增加 chair、table、sofa、umbrella 的单复数品类识别。
- [x] 增加 China 国家识别。
- [x] 前端网络连接错误显示具体的后端连接提示。
- [x] 增加该询盘的回归测试。

### 验证结果

```text
后端 pytest：69 passed
Ruff：All checks passed
前端 Vite build：通过
git diff --check：通过
本地接口验证：解析数量 50、目的地 China、返回产品候选
```

## 41. 2026-10-11：扩展目的地国家识别

### 实现内容

- [x] 规则引擎增加挪威、北欧、欧洲、北美、亚太、中东和南美等常用目的地国家。
- [x] 澳大利亚继续支持，并增加挪威和澳大利亚回归测试。
- [x] 后端已重启并加载新的国家识别列表。

### 说明

- Ollama/Qwen 模式可以识别更多自然语言国家名称。
- 规则引擎模式现在覆盖常见外贸目的地；遇到未列出的国家仍会保留 AI 识别结果，若 AI 不可用则需要继续补充别名。

### 验证结果

```text
后端 pytest：70 passed
Ruff：All checks passed
后端已重启
```

## 42. 2026-10-11：库存方案 B 与产品库存手动编辑

### 实现内容

- [x] 正式报价生成时预留库存，不再在询盘分析阶段扣减库存。
- [x] 报价审批时正式扣减 `on_hand_quantity`，同时释放对应预留数量。
- [x] 草稿报价取消时释放预留库存。
- [x] 增加 `inventory_movements` 流水记录，记录预留、扣减和释放动作。
- [x] 增加 `PATCH /api/products/{sku}/inventory`，支持在产品库中手动修改现有产品的实际库存。
- [x] 产品库详情显示现有库存、预留库存和可用库存。
- [x] 修改库存时禁止将实际库存设置为低于当前预留库存的数量。

### 验证结果

```text
后端 pytest：73 passed
前端 npm run build：通过
git diff --check：通过
库存迁移文件已加入：`20261011_inventory_movements`；当前既有 SQLite 数据库的 Alembic 版本仍保留在历史版本，服务启动时通过 `Base.metadata.create_all` 补齐了新表，后续迁移整理时需先采用 `stamp` 或编写兼容迁移，避免重复建表。
后端已重启：http://127.0.0.1:8000
```

## 46. 2026-10-11：库存流水筛选

### 实现内容

- [x] 产品详情库存历史增加动作类型筛选：全部、预留、扣减、释放。
- [x] 增加报价编号搜索，便于定位某一条报价产生的库存变化。
- [x] 筛选条件在切换产品时自动重置。
- [x] 筛选在前端即时生效，不重复请求数据库。

### 验证结果

```text
后端 pytest：74 passed
前端 npm run build：通过
git diff --check：通过
```

## 47. 2026-10-11：手动库存调整审计

### 实现内容

- [x] 产品库编辑库存时支持填写调整原因。
- [x] 记录调整前数量、调整后数量、变化数量、操作人和时间。
- [x] 库存流水新增 `adjustment` 类型，并支持筛选。
- [x] 新增 `inventory_adjustments` 表及 Alembic 迁移文件。
- [x] 同数量保存不会产生无意义的调整流水。

### 验证结果

```text
后端 pytest：74 passed
前端 npm run build：通过
git diff --check：通过
后端已重启：http://127.0.0.1:8000
库存编辑接口验证成功，库存保持 500
```

## 48. 2026-10-11：库存编辑权限控制

### 实现内容

- [x] 启用认证后，库存修改仅允许 `admin` 和 `approver` 角色。
- [x] 未登录请求返回 401，viewer 角色返回 403。
- [x] 前端库存编辑请求自动携带登录后的 Bearer Token。
- [x] 开发环境关闭认证时保留库存测试和本地调试能力。

### 验证结果

```text
后端 pytest：75 passed
前端 npm run build：通过
git diff --check：通过
后端已重启：http://127.0.0.1:8000
```

## 49. 2026-10-11：产品目录权限控制

### 实现内容

- [x] 启用认证后，新增产品、编辑产品和停用产品仅允许 `admin` 或 `approver`。
- [x] 产品编辑、创建、停用请求统一携带 Bearer Token。
- [x] viewer 角色无法修改产品基础信息。
- [x] 产品查询和库存流水查询继续保持只读访问。

### 验证结果

```text
后端 pytest：76 passed
前端 npm run build：通过
git diff --check：通过
后端已重启：http://127.0.0.1:8000
```

## 50. 2026-10-12：前端按角色隐藏产品管理入口

### 实现内容

- [x] `admin` 和 `approver` 可以看到新增、编辑、停用和应用 AI 标签入口。
- [x] `viewer` 只看到产品查询、详情和库存流水，只读操作保持可用。
- [x] 前端入口控制与后端权限校验保持一致。
- [x] 未启用认证的本地开发环境继续显示完整测试入口。

### 验证结果

```text
后端 pytest：76 passed
前端 npm run build：通过
git diff --check：通过
```

## 52. 2026-10-12：已停用产品可查询与恢复

### 问题与原因

- 停用产品采用软删除，只将 `is_active` 设为 `false`。
- 产品列表查询默认只返回 `is_active = true`，因此停用后看起来像从列表消失。

### 实现内容

- [x] 产品列表新增 `include_inactive` 查询参数。
- [x] 产品库增加“显示已停用产品”开关，默认关闭。
- [x] 停用产品显示灰色状态和“已停用”标记。
- [x] 打开开关后可以查看停用产品，并通过编辑表单重新启用。
- [x] 停用产品仍不会参与产品匹配和新报价。

### 验证结果

```text
后端 pytest：76 passed
前端 npm run build：通过
git diff --check：通过
真实接口验证：include_inactive=true 可查询 NOVA-CHAIR-001（is_active=false）
后端已重启：http://127.0.0.1:8000
```

## 53. 2026-10-12：增加停用产品直接启用按钮

### 问题与原因

- 之前只能进入编辑表单，通过“启用产品”复选框恢复产品，界面没有明确的启用按钮。

### 实现内容

- [x] 停用产品详情中的编辑按钮自动变为“启用产品”。
- [x] 点击后直接调用产品更新接口，将 `is_active` 恢复为 `true`。
- [x] 启用成功后立即更新当前详情和产品列表状态。
- [x] 继续遵循 `admin`、`approver` 权限控制。

### 验证结果

```text
前端 npm run build：通过
git diff --check：通过
```

## 51. 2026-10-12：产品表单字段标签优化

### 问题与原因

- 编辑产品表单之前主要依赖 placeholder；字段有值后无法直观看出每个输入框对应的内容。

### 实现内容

- [x] 编辑产品表单增加固定字段标签：材质、颜色、AI 标签、MOQ、交期、单价、现有库存、库存调整原因和启用状态。
- [x] 新建产品表单也增加 SKU、名称、类别、描述等固定字段标签。
- [x] 标签随中文、English、Italiano 界面切换。
- [x] 保留原有输入和保存逻辑，不改变已有产品数据。

### 验证结果

```text
后端 pytest：76 passed
前端 npm run build：通过
git diff --check：通过
```

真实 API 联调使用一条测试报价完成：

```text
生成测试报价：on_hand=500, reserved=50, available=450
取消测试报价：on_hand=500, reserved=0, available=500
手动编辑库存接口：保存成功，最终数量保持为 500
```

### 注意事项

- 以下两条记录的是 MySQL 迁移前的 SQLite 开发阶段状态，不代表当前数据库配置。
- 历史报价是在库存预留功能加入前创建的，可能没有对应的预留流水；新生成的报价按方案 B 工作正常。
- 库存并发下的事务/行级锁行为仍需单独验证；仅切换到 MySQL 不代表并发安全已得到验证。

## 43. 2026-10-11：报价单页面接入取消报价

### 实现内容

- [x] 前端新增取消报价 API 调用：`POST /api/quotes/{id}/cancel`。
- [x] 报价单列表中，草稿报价同时显示“批准报价”和“取消报价”按钮。
- [x] 取消成功后更新列表状态，并刷新报价详情和审批历史。
- [x] 已取消报价显示为中性状态，不再显示批准操作。
- [x] 支持中文、English、Italiano 三种界面文案。

### 验证结果

```text
后端 pytest：73 passed
前端 npm run build：通过
git diff --check：通过
```

## 44. 2026-10-11：报价详情展示库存流水

### 实现内容

- [x] 报价详情 API 增加 `inventory_movements` 字段。
- [x] 展示每次库存动作的类型、数量、SKU、操作人和时间。
- [x] 支持查看 `reserve`、`deduct`、`release` 三种库存动作。
- [x] 前端报价详情卡片增加库存流水区域。
- [x] 后端已重启并验证历史测试报价可以返回预留和释放记录。

### 验证结果

```text
后端 pytest：73 passed
前端 npm run build：通过
git diff --check：通过
报价详情接口：inventory_movements 返回正常
后端地址：http://127.0.0.1:8000
```

## 45. 2026-10-11：产品库查询库存流水

### 实现内容

- [x] 新增 `GET /api/products/{sku}/inventory/movements` 接口。
- [x] 产品库选择产品后自动加载该 SKU 的库存历史。
- [x] 产品详情展示预留、扣减、释放动作，以及报价编号、操作人和时间。
- [x] 按最新动作倒序展示，方便测试库存变化。
- [x] 增加产品库存流水接口回归测试。

### 验证结果

```text
后端 pytest：74 passed
前端 npm run build：通过
git diff --check：通过
真实接口验证：NOVA-CHAIR-001 返回 2 条库存流水
后端已重启：http://127.0.0.1:8000
```

## 46. 2026-10-12：报价单行内展开详情

### 实现内容

- [x] 点击报价单行后，在对应报价行的正下方展示详情。
- [x] 再次点击当前报价单行隐藏详情。
- [x] 点击报价页面空白区域隐藏详情。
- [x] 删除页面底部重复的报价详情区域，避免详情显示两次。
- [x] 行内详情适配表格样式，横向占满报价单列并保持原有风险、匹配、邮件、审批历史和库存流水信息。

### 验证计划

- 前端 `npm run build`
- 后端 `pytest -q`
- `git diff --check`

## 47. 2026-10-12：产品库行内展开详情

### 实现内容

- [x] 点击产品卡片后，在对应产品卡片下方展示产品详情。
- [x] 再次点击当前产品卡片隐藏详情。
- [x] 点击产品库空白区域隐藏详情。
- [x] 移除产品库底部重复详情区域。
- [x] 保留产品编辑、启用/停用、AI 标签、库存数据和库存流水操作。

## 48. 2026-10-12：优化产品详情展开布局

### 实现内容

- [x] 展开产品详情时自动占满产品库整行，避免受单张卡片宽度限制。
- [x] 详情采用自适应双栏布局，产品信息与库存/价格信息分区展示。
- [x] 库存流水横跨详情区域底部，避免内容挤压或横向溢出。
- [x] 在平板和手机宽度下自动切换为单栏/紧凑网格布局。

## 49. 2026-10-12：统一产品卡片高度

### 实现内容

- [x] 为产品卡片设置统一的最小高度和盒模型。
- [x] 统一卡片内部内容的纵向分布，避免因产品字段长度不同导致卡片高低不齐。
- [x] 展开详情时只增加下方详情区域，不改变卡片本身的统一高度。

## 50. 2026-10-12：询盘工作台产品匹配布局统一

### 实现内容

- [x] 询盘工作台的产品匹配卡片统一基础高度。
- [x] 点击匹配产品后，在对应卡片下方展开详情。
- [x] 再次点击当前产品收起详情，点击匹配区域空白处隐藏详情。
- [x] 展开详情改为自适应双栏布局，窄屏自动切换为单栏，避免横向溢出。
- [x] 点击详情内部操作时保持详情展开状态。

## 51. 2026-10-12：简化询盘工作台

### 实现内容

- [x] 移除询盘工作台右侧重复的 Agent 活动窗口。
- [x] 保留独立的 Agent 追踪页面，用于查看运行记录、步骤状态和时间日期。
- [x] 主工作区聚焦询盘解析、客户识别、产品匹配和报价操作。

## 52. 2026-10-12：产品匹配后定位报价草稿

### 实现内容

- [x] 点击“按此产品报价”完成产品选择和报价更新后，自动滚动到报价草稿区域。
- [x] 报价草稿增加稳定定位标识，兼容桌面端和窄屏布局。

## 53. 2026-10-12：取消报价同步清理询盘草稿

### 问题与原因

- 报价单页面取消报价后，只更新了报价列表状态。
- 询盘工作台内存中的报价草稿仍保留原报价编号和金额，因此返回工作台时看起来仍存在报价草稿。

### 修复内容

- [x] 取消当前询盘对应报价后，清除草稿报价编号、单价和总价。
- [x] 将询盘工作台恢复为“待选择产品”状态，避免误认为仍存在有效报价。
- [x] 清除当前产品选中状态，允许重新选择产品生成新报价。

## 54. 2026-10-12：产品编辑表单行内展示

### 实现内容

- [x] 产品详情中的“编辑产品”表单移动到当前产品详情下方。
- [x] 编辑表单显示当前产品名称，避免不清楚正在编辑哪一项。
- [x] 删除页面底部重复的编辑表单。
- [x] 编辑表单横跨详情区域，保持与产品详情布局一致。

## 55. 2026-10-12：GitHub 上传内容安全检查

> 以下记录的是当时的检查快照；之后已配置 `origin`，并在 2026-10-12 添加 MIT 许可证。

### 检查结果

- [x] 当前 Git 仓库没有配置 `origin` 远程地址，尚未连接到具体 GitHub 仓库。
- [x] 检查时工作区有 42 项未提交变更，包含代码、迁移脚本、部署文档和项目进度记录；尚未提交或推送。
- [x] `.env`、本地 SQLite 数据库、`node_modules`、虚拟环境、构建目录及缓存均被 Git 忽略。
- [x] Git 跟踪文件中只有 `.env.example` 示例文件，没有跟踪真实环境配置或数据库文件。
- [x] 增加 SQLite 辅助文件和测试覆盖率输出的忽略规则。
- [x] 源码敏感信息扫描未发现真实密钥；README、环境示例和部署文档中的密钥项为变量名或占位说明。

### 后续注意

- 首次推送前仍需审查全部 42 项未提交变更，并确认最终目标 GitHub 仓库和远程地址。
- 若历史提交中曾经放入过真实密钥，即使当前文件已忽略或删除，也需要轮换密钥并检查 Git 历史。

## 56. 2026-10-12：Docker 部署配置审查与修正

### 审查发现

- Docker Compose 原来将前后端端口发布到所有网卡。
- 容器中的 Ollama 地址默认是 `127.0.0.1`，指向后端容器自身，不是宿主机服务。
- Compose 未显式选择演示用 AI 提供方，默认值可能造成无 Ollama 时分析失败或回退。
- 前端使用相对 `/api` 地址并由 Nginx 代理，`VITE_API_BASE` 示例配置没有作用。

### 修正内容

- [x] Docker Compose 默认只绑定 `127.0.0.1`，并允许设置端口和绑定地址。
- [x] Docker 演示默认使用规则引擎，不要求部署 Ollama。
- [x] 为宿主机 Ollama 配置 `host.docker.internal` 地址选项。
- [x] Compose 支持通过根目录 `.env` 配置 CORS、认证和 Ollama 参数。
- [x] 更新 `.env.example`、README 和部署说明，区分本地演示与对外部署配置。
- [x] 移除未使用的根环境示例变量 `OPENAI_API_KEY`、`REDIS_URL` 和 `VITE_API_BASE`。

## 57. 2026-10-12：接入 OpenAI 兼容在线模型

### 实现内容

- [x] 新增 OpenAI 兼容 Chat Completions 提供方，配置 API Key、Base URL、模型名和超时。
- [x] 询盘解析可切换到在线模型，并继续沿用规则解析兜底。
- [x] 产品 AI 标签建议复用当前选定的在线模型提供方。
- [x] AI 提供方接口只返回模型名和可用状态，不返回 API Key。
- [x] 未配置 API Key 时在线提供方显示不可用，后端拒绝切换。
- [x] 前端模型选择器根据后端配置动态显示可用模型；密钥不会进入前端。
- [x] Docker Compose 与环境变量示例支持安全地由后端读取在线 API 配置。
- [x] 更新部署文档和 README 的在线模型配置说明。

### 使用方式

在后端环境配置 `OPENAI_COMPATIBLE_API_KEY`、`OPENAI_COMPATIBLE_BASE_URL`、`OPENAI_COMPATIBLE_MODEL`，并将 `AI_PROVIDER` 设为 `openai_compatible`；配置后重启后端即可在界面切换模型。

## 58. 2026-10-12：增加 DeepSeek 与 Kimi 服务商

- [x] 复用 OpenAI 兼容 Chat Completions 客户端，增加 DeepSeek 和 Kimi/Moonshot 独立服务商配置与模型选择。
- [x] 默认 API 地址分别为 `https://api.deepseek.com/v1`、`https://api.moonshot.cn/v1`；模型可配置覆盖。
- [x] 后端只返回服务商可用状态，不返回 API Key；未配置密钥时禁止切换。
- [x] 更新中英文/意大利文界面标签、环境变量示例、README 和部署说明。
- [x] 重启本机后端并检查健康状态（见本次操作结果）。

配置方式：在 `backend/.env` 中设置 `DEEPSEEK_API_KEY` 或 `KIMI_API_KEY`，然后在前端模型下拉框切换；不需要把密钥发到聊天中或放入前端。

## 59. 2026-10-12：MySQL 正式数据库与数据保留方案

- [x] 增加 PyMySQL 驱动，Docker 使用 MySQL 8.4；数据库不暴露主机端口，使用独立持久卷。
- [x] Compose 后端启动依赖 MySQL 健康检查，容器入口执行 `alembic upgrade head` 后再启动 API。
- [x] 服务数据库不再由 SQLAlchemy `create_all` 自动建表，统一由 Alembic 管理；SQLite 开发/测试路径不变。
- [x] 增加 SQLite 到空 MySQL 的数据复制脚本，目标已有记录时拒绝合并；源库不修改。
- [x] 文档说明发现两份 SQLite 数据库时先选定数据源，迁移前备份，配置卷持久化及 MySQL 逻辑备份/恢复。
- [x] 已在本机被 Git 忽略的根目录 `.env` 中设置不同的随机 MySQL 用户与 root 密码（未写入日志/聊天内容）。
- [x] 已启动 Compose MySQL 8.4 容器，健康检查通过，数据存放于 Compose named volume。
- [x] 已将选定的 SQLite 业务数据源导入 MySQL；迁移前创建了本地一致性备份，备份目录已加入 `.gitignore`。
- [x] 已核对关键业务表和 Alembic 迁移版本；本机数据量及备份文件名不作为公开项目文档内容。
- [x] 根目录旧库 `tradepilot.db` 保持原样，未合并。
- [x] Docker Hub 初次连接不稳定（认证端点 TCP reset/timeout）；单独重试拉取 Python 3.12、Node 22、Nginx Alpine 后成功，前后端镜像均已构建。
- [x] 已停止占用 8000 端口的旧本机 Uvicorn，启动 Compose 后端和前端。
- [x] 修正前端健康检查 IPv6 localhost 误判：改为检查 `127.0.0.1`，三个 Compose 容器现均 healthy。
- [x] 运行验证：`/health` 返回 ok；前端 `:8080` 返回 HTTP 200；经前端代理请求产品接口读到 MySQL 中 6 个产品。
- [x] 修复 Agent 追踪评估接口：容器缺少 `data/evaluation/inquiries.json`，导致 `/api/evaluation` 500；在 Compose 为后端增加只读 `./data:/data` 挂载。接口现返回 6 个评估案例且指标正常，三项服务保持 healthy。

迁移说明：项目中曾有多份 SQLite 数据库。迁移时选择了后端运行所用数据库作为业务数据源，另一份旧库未合并并保持原样。具体本机数据库路径、数据量和卷名称不写入公开文档。

## 60. 2026-10-12：客户详情行内展开

- [x] 客户详情从列表外移入当前客户条目中，点击客户行后详情直接显示在该客户下方。
- [x] 再次点击已选客户行可收起详情；切换客户时先清空旧报价列表，避免内容短暂串位。
- [x] Docker 前端生产构建通过，Compose 三项服务均 healthy，前端 HTTP 200、后端 `/health` 正常。

## 61. 2026-10-12：GitHub 上传前自动化检查

- [x] 增加 GitHub Actions CI：push/PR 自动运行 Python 3.12 后端测试及 Node 22 前端类型检查/构建。
- [x] 增加后端和前端 `.dockerignore`，排除本地环境文件、数据库、虚拟环境、依赖目录和构建产物。
- [x] 本机后端测试 76 项通过；前端 Docker 生产构建通过。
- [x] 已配置 Git remote 并添加 MIT License；本地项目仍未提交或推送。

## 62. 2026-10-12：认证保护覆盖修复

### 修复内容

- [x] 启用认证时，业务 API 默认要求登录；健康检查、认证状态、登录、刷新和退出接口保持公开。
- [x] 客户、产品、库存、报价、询盘工作流、Agent 记录、评估和 AI Provider 查询按角色保护。
- [x] `viewer` 仅可读取业务数据；客户/产品/库存修改、询盘报价及报价审批/取消需要 `approver` 或 `admin`；用户管理和全局 AI Provider 切换仅允许 `admin`。
- [x] 报价审批与取消均校验数据库中的有效用户状态；库存审计操作者在认证启用时取已验证账号，不信任 `X-Actor-Id`。
- [x] 在部署文档中记录认证开启后的接口与角色规则，并强调认证关闭仅适用于本机演示。

### 验证结果

```text
后端 pytest：78 passed
Ruff：All checks passed
前端 vue-tsc 与 Vite production build：通过
```

### 遗留注意事项

- `AUTH_ENABLED=false` 时接口保持本地演示的无认证行为；不得将此配置暴露到公网。
- MySQL 库存并发一致性仍需单独处理和压力/并发测试，本次认证修复未改变库存事务逻辑。

## 63. 2026-10-12：修正 README 启动前置步骤

- [x] Docker 快速启动前增加 `.env` 初始化及替换 MySQL 用户/root 密码的说明，并提醒勿覆盖已有本机配置。
- [x] 本地 Alembic 命令显式指定 SQLite `DATABASE_URL`，避免使用 `alembic.ini` 的 MySQL 示例连接。
- [x] 仅修改文档；未改数据库配置、业务代码或运行数据。

## 64. 2026-10-12：MySQL 库存并发一致性

### 修复内容

- [x] 库存预留、审批扣减、取消释放均先对报价行执行 `SELECT ... FOR UPDATE`，串行化同一报价单的状态变更和幂等流水检查。
- [x] 库存数量变更和人工库存调整对 SKU 对应的库存行加行锁，确保可用库存校验与更新在同一事务中执行。
- [x] 保持报价行在库存行之前加锁，减少审批、取消和预留之间的锁顺序冲突。
- [x] 新增 MySQL 方言编译测试，确认报价与库存查询确实生成 `FOR UPDATE`。

### 验证与限制

- SQLite 不实现行级 `FOR UPDATE` 语义；SQLite 单测只覆盖业务流程，MySQL 方言检查用于确认 SQL 锁语句生成。尚未对本机业务数据库做压力或并发写入测试。
- 不对现有 Compose/MySQL 数据卷执行并发实验，避免触及用户业务数据。

## 65. 2026-10-12：修正上传前文档与复核配置

- [x] 合并 README 中重复的数据库章节。
- [x] 让 Alembic `upgrade head` 和 `current` 共用显式 MySQL `DATABASE_URL`，避免 `current` 意外读取示例连接。
- [x] 复核 Git 忽略规则、Compose 配置与敏感文件候选；未发现已跟踪的本地密钥或数据库文件。
- [x] 复核结果：后端现有虚拟环境测试、Ruff、前端类型检查/生产构建及 Compose 配置检查通过；本机 Python 3.12 未安装 pytest，无法在该解释器下本地重跑测试。CI 使用 Python 3.12 并负责发布前验证。

## 66. 2026-10-12：增加中文界面使用指南

- [x] 将询盘工作台与产品库截图归档到 `docs/screenshots/`。
- [x] 新增中文界面指南，说明询盘解析、产品选择后生成报价、产品搜索/停用项显示、模型语言选择及部署配置注意事项。
- [x] 在 README 添加使用指南入口并直接嵌入两张界面截图；本次变更仅涉及文档和截图。

## 67. 2026-10-14：产品语义检索第一阶段

- [x] 增加本地 Hugging Face embedding 适配器（使用 FastEmbed，默认多语言 MiniLM），并保留 Ollama embedding 配置选项。
- [x] Compose 增加 Qdrant 及持久化卷；新增产品索引、同步及管理员重建接口。
- [x] 询盘产品匹配融合语义召回与原有规则评分，仍由 MySQL 校验实时库存、MOQ、价格和交期。
- [x] 前端显示语义检索或规则回退状态；当前阶段尚未让聊天模型依据候选文档生成引用式解释。
- [x] 模型文件需首次下载；部署者启用后须执行一次索引重建。配置、费用与许可证说明见 `DEPLOYMENT.md`。
- [x] 验证：后端测试 83 项通过，Ruff 通过，前端类型检查及生产构建通过，Compose 配置解析通过。
- [x] 通过单独审批后完成 Compose 实测：Qdrant 和本地 Hugging Face 模型启动成功，现有启用产品已建立索引；无既有关键词的测试询盘返回 `retrieval_mode=semantic`，首位为椅子，报价仍是 `pending_selection` 且未生成报价记录。
- [x] 构建时发现 Sentence Transformers 的新版本依赖会拉取不必要的 CUDA 组件；已换用 FastEmbed 的多语言 ONNX 模型，降低镜像与磁盘占用。

## 68. 2026-10-14：RAG 有据解释第二阶段

- [x] 将询盘和候选产品资料作为受限上下文交给当前聊天模型，一次生成所有候选产品的简短匹配解释。
- [x] 模型只返回候选 SKU 与证据字段名；后端过滤未知 SKU/字段，并从 MySQL 回填原始证据值。
- [x] API 增加解释模式、模型信息、候选解释和证据；前端在候选卡片中显示 AI/规则来源及证据标签。
- [x] 模型不可用、超时或响应格式错误时自动回退规则解释，不中断产品匹配和报价预览。
- [x] 真实 Qwen 测试发现模型可能把询盘形容词扩展为产品事实；已改为由模型选择证据字段，后端用 MySQL 原值构造展示解释，并保留模型原文供审计。

## 69. 2026-10-14：RAG 召回评测

- [x] 新增 3 条刻意避开产品库原词的模糊询盘评测数据。
- [x] 新增规则/语义两种模式的 Top-1 与 Top-3 产品召回率。
- [x] 新增 `GET /api/evaluation/rag?mode=rules|semantic`，用于比较语义检索相对于规则检索的提升。
- [x] 评测只验证候选 SKU 排名，不会创建报价或修改库存。

### 实测结果

- [x] 后端 pytest：87 passed。
- [x] Ruff：All checks passed。
- [x] 前端 vue-tsc 与 Vite production build：通过。
- [x] Compose 配置检查、后端镜像重建及服务健康检查：通过。
- [x] Qdrant 索引重建：6 个启用产品成功建立索引。
- [x] 规则模式：Top-1 召回率 33.3%，Top-3 召回率 100%。
- [x] 语义模式：Top-1 召回率 33.3%，Top-3 召回率 100%。

### 结果解释与后续限制

- 当前评测证明语义检索链路已实际调用 FastEmbed + Qdrant，并能返回候选产品；但这组 3 条询盘中，项目类型规则已经能把目标产品放入 Top-3，因此暂时没有观察到相对于规则基线的召回提升。
- 当前结果不能据此宣称语义检索优于规则检索。下一步应扩大包含中文、意大利语、同义词、材质和用途改写的评测集，并记录 MRR、Recall@K 和误召回样本，再调整 embedding 模型与阈值。

## 70. 2026-10-14：扩充 RAG 评测指标

- [x] 将评测集扩充为 8 条，覆盖英语、中文、意大利语和西班牙语的产品用途改写。
- [x] 增加 `mrr`（Mean Reciprocal Rank）和 `misses`（未进入 Top-3 的误召回样本）字段。
- [x] 后端测试保持 87 passed，Ruff 和前端生产构建通过。
- [x] 线上规则基线为 Top-1 25%、Top-3 75%、MRR 0.49375，并发现 2 条 Top-3 漏召回样本。
- [x] 线上语义结果为 Top-1 62.5%、Top-3 100%、MRR 0.77083，Top-1 相对规则基线提升 37.5 个百分点，且没有 Top-3 漏召回。
- [x] 评测接口仍为 `GET /api/evaluation/rag?mode=rules|semantic`，只读评测数据，不创建报价、不修改库存。

## 71. 2026-10-14：混合检索排序可审计化

- [x] 产品候选结果新增结构化 `semantic_score` 字段，保留原始语义相似度，便于前端和审计记录使用。
- [x] 当库存可用性和总分相同时，排序使用语义相似度作为第二排序信号，再使用 SKU 作为稳定的最终排序键。
- [x] 前端 TypeScript 类型已同步支持 `semantic_score`，现有“Semantic match 0.xx”原因仍保持兼容显示。
- [x] 后端测试：88 passed；Ruff、前端生产构建和 Compose 健康检查通过。
- [x] 重启后线上 RAG 评测仍为语义 Top-1 62.5%、Top-3 100%、MRR 0.77083。

## 72. 2026-10-14：前端 RAG 评测面板

- [x] Agent 追踪页面新增 RAG 评测区域，可切换规则检索/语义检索模式。
- [x] 前端展示 Top-1 Recall、Top-3 Recall、MRR、评测案例数和 Top-3 漏召回样本。
- [x] 新增 `fetchRagEvaluation` API 类型与调用封装，保持认证刷新逻辑一致。
- [x] 前端生产构建通过，Compose 前端已重建，`http://127.0.0.1:8080/` 返回 HTTP 200。

## 73. 2026-10-14：RAG 评测历史持久化

- [x] MySQL 新增 `rag_evaluation_runs` 表，保存模式、案例数、Recall@1/3、MRR、漏召回样本和运行时间。
- [x] 新增 `POST /api/evaluation/rag/run?mode=rules|semantic`，执行评测并写入 MySQL。
- [x] 新增 `GET /api/evaluation/rag/history`，读取最近评测记录。
- [x] Agent 追踪页改为执行评测并显示最近历史记录，刷新或重启后仍可查看。
- [x] Compose 实测：规则和语义两次运行均成功写入数据库；迁移 `20261011_inventory_adjustments -> 20261014_rag_evaluation_runs` 执行成功。
- [x] 后端测试：89 passed；Ruff、前端构建和容器健康检查通过。

## 74. 2026-10-14：RAG 评测趋势图

- [x] Agent 追踪页新增 SVG 趋势图，绘制最近 12 次评测的 Top-1、Top-3 和 MRR。
- [x] 趋势图直接读取 MySQL 历史记录，不引入额外图表依赖。
- [x] 前端构建通过，Compose 前端已重建，`http://127.0.0.1:8080/` 返回 HTTP 200。

## 75. 2026-10-14：RAG 评测实验元数据与筛选

- [x] 评测历史新增 embedding 提供商、embedding 模型和检索配置字段。
- [x] 新增 MySQL 迁移 `20261014_rag_eval_metadata`；针对 MySQL JSON 默认值限制采用幂等迁移和空对象回填，未删除或覆盖业务数据。
- [x] 前端历史记录增加“全部/语义检索/规则检索”筛选，并显示每次实验使用的 embedding 模型。
- [x] Compose 实测记录：`huggingface / sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`，语义 Top-1 62.5%、Top-3 100%、MRR 0.77083。
- [x] 后端 89 个测试、Ruff、前端构建通过，前端服务返回 HTTP 200。

## 76. 2026-10-14：Embedding Profile 切换

- [x] 新增 `GET /api/settings/embeddings`，返回当前启用的 embedding profile 和可选 profile 列表。
- [x] 新增 `POST /api/settings/embeddings`，管理员切换 profile 后重建 Qdrant 产品索引；不删除或重置 MySQL 业务数据。
- [x] 新增 `EMBEDDING_PROFILES_JSON` 配置，支持在根目录或 `backend/.env` 中声明多个 Hugging Face embedding profile。
- [x] Agent 追踪页 RAG 评测面板新增 embedding profile 下拉选择，切换后自动刷新评测数据。
- [x] 修复 embedding 设置查询接口遗漏数据库会话依赖导致的 HTTP 500 错误。
- [x] 验证结果：后端 pytest 89 passed，Ruff 通过，前端生产构建通过；Compose 后端、前端重建成功。
- [x] 线上健康检查通过：`/health` 返回 `{"status":"ok"}`，embedding 设置接口返回当前默认 profile，前端 `http://127.0.0.1:8080/` 返回 HTTP 200。

## 77. 2026-10-14：多 Embedding Profile 配置验证

- [x] 根目录 `.env` 增加第二个免费多语言 profile：`minishlab/potion-multilingual-128M`（MIT 许可，FastEmbed 支持）。
- [x] `docker-compose.yml` 增加 `EMBEDDING_PROFILES_JSON` 环境变量映射，容器接口现已返回两个可选 profile。
- [x] 已验证已缓存的默认 profile 可以通过切换接口重建 6 个启用产品的独立 Qdrant 索引。
- [x] 发现首次下载第二个模型时 Hugging Face 未认证连接长期无进度；请求已安全终止，未修改 MySQL 数据，第二个 profile 配置仍保留，待网络可用后首次切换会自动下载模型。

## 78. 2026-10-14：Embedding 切换状态与超时提示

- [x] 前端切换 embedding 时显示“下载模型并重建索引”状态，成功后显示已索引产品数。
- [x] 前端为切换请求增加 120 秒超时，超时后明确提示检查 Hugging Face 网络并重试。
- [x] 后端错误信息会显示在 embedding 评测面板附近，避免用户误以为按钮无响应。
- [x] 前端 API 支持将 `AbortSignal` 传递给切换请求。
- [x] 前端生产构建和 Docker 前端镜像构建通过，网页 `http://127.0.0.1:8080/` 已重新部署。

## 79. 2026-10-14：Embedding 异步重建任务

- [x] embedding 切换接口改为立即创建后台任务，避免 HTTP 请求被模型下载和索引重建长时间占用。
- [x] 新增 `GET /api/settings/embeddings/jobs/{job_id}`，支持查询 `queued`、`running`、`succeeded`、`failed` 状态及错误信息。
- [x] 后台任务使用独立 SQLAlchemy 会话读取产品，不复用请求会话，不修改 MySQL 业务数据。
- [x] 前端改为提交任务并轮询状态，成功后刷新 RAG 评测；失败时显示后端错误。
- [x] 实测默认 embedding profile：任务提交成功，状态轮询返回 `succeeded`，6 个产品索引完成；前端 HTTP 200。
- [x] 后端 pytest：89 passed；Ruff 和前端生产构建通过；Compose 后端、前端已重建。

## 80. 2026-10-14：Embedding 重建进度显示

- [x] 后台任务状态新增 `processed_products`、`total_products` 和 `progress_percent` 字段。
- [x] Qdrant 重建过程每完成一个产品即更新任务进度。
- [x] 前端轮询期间显示产品处理进度和百分比。
- [x] 实测状态从 `running / 0/6 / 0%` 到 `succeeded / 6/6 / 100%`，前端 HTTP 200。

## 81. 2026-10-14：Embedding 任务 MySQL 持久化

- [x] 新增 MySQL 表 `embedding_rebuild_jobs`，记录任务 ID、profile、状态、进度、索引数量、错误和创建/更新时间。
- [x] 新增迁移 `20261014_embedding_rebuild_jobs`，Compose 启动时已执行，未删除或覆盖现有业务数据。
- [x] 服务启动时将上次未完成的 `queued/running` 任务标记为 `failed`，并记录服务重启原因。
- [x] 任务状态接口改为从 MySQL 读取，服务重启后仍可查询已完成任务。
- [x] 线上实测：任务 `succeeded`，6 个产品索引完成，状态从 MySQL 正常读回；后端健康、前端 HTTP 200。

## 82. 2026-10-14：Embedding 重建历史列表

- [x] 新增 `GET /api/settings/embeddings/jobs?limit=20`，按创建时间倒序返回最近任务。
- [x] Agent 追踪页 RAG 面板新增 Embedding 重建历史，显示模型、时间、状态、进度、索引数量和错误信息。
- [x] 页面启动时加载历史，任务完成后自动刷新列表。
- [x] 线上验证历史接口从 MySQL 返回已完成任务，前端 HTTP 200；后端 89 项测试、Ruff 和前端构建通过。

## 83. 2026-10-14：Embedding 历史分页

- [x] 历史接口支持 `limit` 和 `offset`，返回 `items`、`total`、`limit`、`offset`。
- [x] 前端增加上一页/下一页，历史记录增多后不会无限延长页面。
- [x] 暂不自动清理历史记录，避免未经确认删除任务审计数据。
- [x] 线上验证分页响应正常，前端 HTTP 200；后端 89 项测试、Ruff 和前端构建通过。

## 84. 2026-10-14：AI 配置中心第一阶段

- [x] 新增 `GET /api/settings/ai`，按 Provider 返回 Base URL、模型、超时、可用状态和 API Key 是否已配置。
- [x] API Key 只返回 `api_key_configured` 布尔值，GET 接口不会返回明文密钥。
- [x] 新增 `PATCH /api/settings/ai`，仅管理员可修改；支持运行时更新 Provider、Base URL、模型、超时和 API Key。
- [x] API Key 更新仅保留在当前后端进程内，不写入 MySQL、不回显；正式部署仍应使用根目录 `.env` 或 Docker secrets 持久化。
- [x] 前端新增三语言 AI 配置页面，可查看服务商配置状态、编辑连接参数、切换 Provider，并提供 API Key 不回显提示。
- [x] 支持规则引擎、Ollama/Qwen、OpenAI-compatible、DeepSeek 和 Kimi/Moonshot 配置入口。
- [x] 验证结果：Ruff 通过，后端 pytest 91 passed，前端 TypeScript 检查和生产构建通过。
- [x] 部署后接口复测发现并修复 rules/Ollama 超时字段映射错误；当前后端测试为 91 passed。

## 85. 2026-10-14：AI Provider 连接测试

- [x] 新增 `POST /api/settings/ai/test`，支持测试规则引擎、Ollama、OpenAI-compatible、DeepSeek 和 Kimi/Moonshot。
- [x] 测试请求使用最小探测提示词，不触发询盘分析；返回 Provider、模型、耗时和成功/失败原因。
- [x] 未配置 API Key 或连接失败时返回明确状态，不泄露 API Key；认证开启时仅管理员可测试。
- [x] AI 配置页面新增“测试连接”按钮和三语言状态提示。
- [x] 验证结果：后端 pytest 92 passed，Ruff 通过，Docker 前端生产构建通过；Compose 后端健康、规则引擎测试成功、前端 HTTP 200。

## 86. 2026-10-14：AI 配置持久化部署方案

- [x] 完整补齐 Compose 对 Ollama 标签请求超时的环境变量注入：`OLLAMA_TAG_TIMEOUT_SECONDS`。
- [x] 更新根目录和后端 `.env.example`，覆盖 Provider、模型、Base URL、超时和 API Key 的持久化配置入口。
- [x] 更新 README 与 DEPLOYMENT，明确 `.env`/部署 Secret 是正式持久化来源，MySQL 不保存 AI 密钥。
- [x] 明确前端 AI 配置页的保存是当前进程运行时覆盖；长期配置需写入 `.env` 后重启 Compose，避免 Web 页面写入密钥。

## 87. 2026-10-14：启动配置诊断

- [x] 新增 `GET /api/settings/ai/diagnostics`，检查 MySQL、Qdrant、Ollama 和在线 Provider 配置状态。
- [x] MySQL 使用 `SELECT 1` 检查，Qdrant/Ollama 使用轻量健康请求；在线服务商只检查 API Key 配置，不自动消耗模型额度。
- [x] 诊断结果不返回任何 API Key 明文；认证开启时读取接口仍受登录保护。
- [x] AI 配置页面新增诊断卡片和刷新按钮，显示状态、说明与响应耗时。
- [x] Compose 实测：MySQL、Qdrant、Ollama/qwen3:8b 均正常；后端 pytest 93 passed，Ruff 和前端 Docker 生产构建通过，前端 HTTP 200。

## 88. 2026-10-14：Compose 部署验收与重启保留验证

- [x] Compose 四项服务检查通过：backend、database、frontend healthy，Qdrant 正常运行。
- [x] 询盘工作流验收通过：Qwen 解析出数量 50、目的地 China、hotel 项目，客户匹配 Acme Hotels，Top-1 产品为 `NOVA-CHAIR-001`。
- [x] 验证未选择产品时不创建正式报价：返回 `quote.id=null`、`status=pending_selection`，符合先选产品再生成报价的规则。
- [x] 验证 AI 来源：`ai_provider=ollama`，解释模型为 `qwen3:8b`。
- [x] 重启 backend 后 MySQL 中产品、客户和 Agent 运行记录仍可读取，产品库存保持 200；前端 HTTP 200、后端 `/health` 正常。

## 89. 2026-10-14：认证权限验收

- [x] 隔离认证测试通过：登录、错误密码、Access Token、Refresh Token 轮换、Logout 撤销均正常。
- [x] 权限测试通过：viewer 可读业务数据但不能创建/审批，approver 可执行业务审批，admin 可管理用户和全局 AI Provider。
- [x] 当前 Compose 配置检查结果：`AUTH_ENABLED=false`，认证密钥、管理员用户名和密码哈希均为空，因此未在现有运行环境中强行开启，避免把用户锁在系统外。
- [x] 公开部署前仍需由部署者生成并注入 `AUTH_SECRET`、`AUTH_USERNAME`、`AUTH_PASSWORD_HASH`，设置 `AUTH_ENABLED=true` 后重启 Compose，再执行登录验收。

## 90. 2026-10-14：本机认证配置启用

- [x] 根目录 `.env` 已配置随机 `AUTH_SECRET`、管理员账号 `admin`、PBKDF2 密码哈希和 `AUTH_ENABLED=true`；`.env` 未纳入 Git。
- [x] 修复 Compose 对 PBKDF2 哈希 `$` 字符的插值问题，使用 `$$` 保证容器内收到真实哈希。
- [x] 修复启动引导账号同步：当环境中的密码哈希或角色变化时，启动会更新同名引导账号，避免首次错误配置残留。
- [x] 实测认证已开启：未登录产品请求返回 401，管理员登录返回 200，管理员用户管理和 AI 诊断接口返回 200，前端 HTTP 200。

## 91. 2026-10-14：角色账号与权限验收

- [x] 创建本机验收账号 `viewer-test`（角色 `viewer`）和 `approver-test`（角色 `approver`），密码仅用于本机测试，不写入 Git。
- [x] `viewer-test` 可读取产品（200），访问用户管理（403），执行询盘工作流（403），符合只读权限设计。
- [x] `approver-test` 访问用户管理（403），审批不存在报价返回 404，说明角色权限校验已通过后才进入报价业务校验。
- [x] 管理员继续具备用户管理、AI 诊断和 Provider 配置权限；认证与角色权限验收完成。
- [ ] 首次正式使用后修改管理员及测试账号密码；测试完成后可按需删除两个测试账号，当前暂不自动删除以保留复测能力。

## 92. 2026-10-15：公开部署前敏感配置检查

- [x] 根目录 `.env` 已被 `.gitignore` 忽略，且未被 Git 跟踪；仅 `.env.example` 和 `backend/.env.example` 纳入版本控制。
- [x] 对已跟踪文件执行敏感信息扫描，未发现真实 API Key、数据库密码或认证哈希；部署文档中的 `AUTH_PASSWORD_HASH` 仅为说明占位符。
- [x] `git diff --check` 通过，当前改动无空白错误。
- [x] Compose 默认仅绑定 `127.0.0.1`；只有显式设置 `TRADEPILOT_BIND=0.0.0.0` 才会对外暴露，符合本机默认安全策略。
- [ ] 推送 GitHub 前仍需由用户审阅并提交当前改动；不得提交根目录 `.env` 或其他部署密钥。

## 93. 2026-10-15：前端用户管理增加修改密码

- [x] 用户管理列表新增按账号修改密码入口，管理员可直接为任意用户设置新密码。
- [x] 修改表单支持两次密码确认，前端校验至少 8 位；取消后会清空输入内容。
- [x] 复用现有管理员保护的 `PATCH /api/users/{id}` 接口，密码仍以 PBKDF2 哈希写入 MySQL，不保存明文。
- [x] 前端 `vue-tsc` 类型检查和生产构建通过。

## 94. 2026-10-15：用户管理操作按钮布局优化

- [x] 将 `Change password` 和 `Deactivate/Activate` 放入独立操作容器，增加 8px 间距。
- [x] 操作按钮支持换行并保持文字不折断，窄屏下更容易区分和点击。
- [x] 前端 TypeScript 检查和生产构建再次通过。

## 95. 2026-10-15：MySQL 与 Qdrant 产品索引自动同步增强

- [x] 产品新增、编辑时自动更新对应 Qdrant 向量；产品停用时明确删除对应向量。
- [x] 单个产品同步发生临时故障时，自动排队执行一次完整索引重建，避免错误被静默吞掉后长期不一致。
- [x] Compose 后端启动时在后台执行一次 MySQL→Qdrant 校准，覆盖数据库与向量卷独立恢复、服务重启等场景。
- [x] 保持 MySQL 为产品事实源，Qdrant 作为可重建的检索索引，不影响产品保存流程。
- [x] 相关后端测试 17 passed，Ruff 和 `git diff --check` 通过。

## 96. 2026-10-15：修复认证刷新竞态导致的前端红色错误页

- [x] 定位到浏览器多个并发请求同时刷新同一个 Refresh Token，首个请求轮换成功后其余请求使用旧 Token 返回 401。
- [x] 前端增加单例刷新锁，同一时刻只允许一个 Refresh Token 刷新请求，其余请求复用刷新结果。
- [x] 认证状态确认完成后再加载业务数据，避免页面初始化阶段因认证状态尚未读取而产生大量 401 错误。
- [x] Refresh Token 失效时自动清理前端会话并显示登录页，避免持续显示红色错误内容。
- [x] 已重建 Compose 前端和后端；前端 HTTP 200、后端健康接口 HTTP 200，前端生产构建通过。

## 97. 2026-10-15：登录会话持久化

- [x] 将前端认证令牌从仅限标签页的 `sessionStorage` 迁移到 `localStorage`，页面刷新或内嵌浏览器重新加载后可保持登录。
- [x] 兼容并自动迁移已有 `sessionStorage` 会话，退出登录时同时清理两种存储。
- [x] 已重新构建并重启 Compose 前端；前端 HTTP 200，生产构建通过。
- [ ] 正式互联网部署时建议进一步改为 HttpOnly Secure Cookie，以降低浏览器脚本读取持久 Refresh Token 的风险。

## 98. 2026-10-15：选品后报价快速路径

- [x] 首次询盘分析结果中的数量、国家、项目类型、关键词、预算和交期会随选品请求传回后端。
- [x] 已选产品报价不再重复调用 Qwen 解析、Qdrant 语义检索和 AI 产品解释，只执行库存、价格和报价写入。
- [x] 保留旧客户端兼容：未携带已解析需求时仍使用原有完整流程。
- [x] 实测优化前约 12 秒，优化后约 0.02 秒；报价创建成功后已取消测速用临时报价并恢复库存。
- [x] 报价相关测试 8 passed，前端生产构建和 Compose 重建通过。

## 99. 2026-10-15：新增前端 RAG 实验室

- [x] 新增 `POST /api/rag/playground`，支持规则检索和语义检索两种模式，以及 Top-K、相似度阈值配置。
- [x] 返回结构化解析结果、检索模式、候选产品、Semantic Score、最终匹配分、匹配原因、未满足条件和各阶段耗时。
- [x] 实验接口仅执行解析、向量检索和产品排序，不创建报价、不扣减/预留库存、不写入 Agent 活动记录。
- [x] 前端新增三语言“RAG 实验室”页面，可直接输入任意询盘并查看候选产品和评分明细。
- [x] 语义检索异常时显示规则回退状态和错误原因，便于定位 Qdrant/Embedding 服务问题。
- [x] 新增后端只读回归测试；后端 pytest 94 passed，Ruff 通过，前端 `vue-tsc` 与 Vite production build 通过。
- [x] 已重建并启动 Compose backend/frontend；backend healthy，`http://127.0.0.1:8000/health` 返回 `{"status":"ok"}`，前端 `http://127.0.0.1:8080/` 返回 HTTP 200。
- [ ] 待在浏览器登录后验证页面交互；该步骤需要有效登录会话。

## 100. 2026-10-15：RAG 产品知识与同义词优化

- [x] 产品向量文档增加结构化字段和稳定的行业同义词，包括 weatherproof seating、patio chair、dining surface、hospitality lounge 等。
- [x] 规则排序复用与 Qdrant 一致的标准化产品文档，避免规则检索和语义检索使用不同产品词汇。
- [x] 询盘解析增加中英文、意大利语和场景同义词归一化，例如“耐候户外座椅”、`sedute`、`tavoli` 会转换为标准产品关键词。
- [x] RAG 规则评测基线由 Top-1 25% 提升至 87.5%，Top-3 由 75% 提升至 87.5%，MRR 提升至 0.9。
- [x] 针对性回归测试 10 passed，Ruff 通过，前端生产构建通过；完整测试中的语义服务测试因外部 Qdrant/Embedding 等待超时，未继续阻塞验证。
- [x] 已重新构建 Compose backend/frontend；后端 healthy，健康接口返回正常，前端返回 HTTP 200；未删除 MySQL/Qdrant 数据卷。

## 101. 2026-10-15：扩充 RAG 评测集

- [x] 评测集从 8 条扩展到 16 条，新增中文、意大利语、家具组合、遮阳伞、沙发、露台和酒店场景表达。
- [x] 增加 `户外椅`、`家具组合`、`divani`、`parasol`、`couch` 等领域同义词归一化。
- [x] 新评测规则基线：Top-1 Recall 87.5%、Top-3 Recall 93.75%、MRR 0.91875。
- [x] 相关回归测试 10 passed，Ruff 和前端生产构建通过。
- [x] 已重建后端 Compose 容器；后端 healthy，`/health` 返回正常，MySQL 和 Qdrant 数据卷保持不变。
- [ ] 当前仍有 1 条规则 Top-3 漏召回样本，下一步应增加候选重排和“无可靠匹配”判断。

## 102. 2026-10-15：RAG 候选重排与低可信提示

- [x] 增加 `stackable outdoor seats`、`outdoor seats`、`metal seats` 等同义词，解决座椅被家具组合、沙发和桌子挤出 Top-3 的问题。
- [x] 规则评测达到 Top-1 93.75%、Top-3 100%、MRR 0.96875，16 条样本没有 Top-3 漏召回。
- [x] RAG 实验室增加匹配可信度状态：高可信、建议人工确认、未找到可靠匹配。
- [x] 低于 45 分的结果不会被标记为可靠匹配，避免实验页面误导用户；该提示不改变正式报价流程。
- [x] 后端回归测试 24 passed，Ruff、前端生产构建和 `git diff --check` 通过。
- [x] 已重建 backend/frontend Compose 服务；backend、frontend、MySQL、Qdrant 均正常运行，健康接口返回正常。

## 103. 2026-10-15：可选 Cross-Encoder Reranker

- [x] 新增懒加载 `ProductReranker`，使用 FastEmbed `TextCrossEncoder` 对询盘与产品文档成对重排。
- [x] RAG 实验室支持先召回最多 10 个候选，再使用 Reranker 重排并返回 Top-K；最终分数融合基础匹配分和 Reranker 分数。
- [x] 前端显示 Reranker 是否启用、模型名、重排耗时和异常回退信息。
- [x] 增加 `RERANKER_ENABLED`、`RERANKER_MODEL` 配置；默认关闭，避免部署时自动下载模型，模型不可用时自动回退基础排序。
- [x] 相关后端测试 6 passed，Ruff、前端构建和 Compose 健康检查通过。
- [ ] 若要正式启用，需要在根目录 `.env` 设置 `RERANKER_ENABLED=true`，首次运行会下载 `BAAI/bge-reranker-v2-m3`，随后在 RAG 实验室观察重排效果和耗时。

## 104. 2026-10-15：扩充产品库与库存种子

- [x] 产品种子由 5 个扩展为 28 个，覆盖户外椅、桌、沙发、遮阳伞和家具组合五类场景。
- [x] 新产品补充 SKU、描述、材质、颜色、匹配标签、MOQ、交期和价格，便于产品库展示、询盘匹配和 RAG 检索。
- [x] 为全部新增 SKU 增加差异化初始库存，覆盖库存充足、库存较少和不同 MOQ/交期的测试场景。
- [x] 保持现有 `seed_products()` 与 `seed_inventory()` 的幂等行为：只新增数据库中不存在的 SKU，不覆盖已有产品编辑结果或库存调整结果。
- [x] 扩展产品种子回归测试，确认产品数量、类别覆盖、库存覆盖和重复执行稳定性。
- [x] 产品匹配增加类别一致性加分，避免产品描述中提到配套桌椅时，家具组合因文本重叠压过用户明确请求的独立产品类别。
- [x] 更新产品筛选和 RAG 评测测试断言，反映扩充目录后的多产品候选结果。
- [x] 已重建 Compose backend/frontend；MySQL 当前产品记录 30 条、库存记录 30 条，Qdrant 当前 embedding 集合已同步 30 个向量，未删除任何数据卷。
- [x] 增加新增产品的属性检索回归测试，验证“可伸缩柚木桌”和“方形悬臂遮阳伞”等具体款式可被 RAG 直接检索。
- [x] 增加产品 API 回归测试，验证前端产品库可按具体属性搜索新增产品，并同时读取对应可用库存和价格。
- [x] 在根 README 和 backend README 增加产品种子、库存种子、幂等同步和 Qdrant 校准维护说明，并修正产品检索能力描述。

## 105. 2026-10-15：GitHub 上传前安全与部署检查

- [x] 确认 `.env`、backend 本地环境文件、数据库缓存、pytest/ruff 缓存和前端依赖目录均未被 Git 跟踪；仅保留 `.env.example` 模板文件。
- [x] Compose 配置校验通过，backend、frontend、MySQL、Qdrant 当前均正常运行，其中 backend/frontend 状态为 healthy。
- [x] `git diff --check` 通过，未发现已跟踪文件中的常见 `sk-...` API Key 形态。
- [x] 确认 MIT License 和 README 中的部署、产品库、Qdrant 说明均存在。
- [x] 已完成 `git add/commit/push`；提交 `92c22e1` 已推送到 `origin/main`（`https://github.com/h837751619-bit/TradePilotAI.git`）。
