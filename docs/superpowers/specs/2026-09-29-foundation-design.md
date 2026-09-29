# TradePilot AI Foundation Design

## Goal

建立 TradePilot AI 的第一阶段可运行基础：使用 FastAPI 暴露产品查询接口，使用 SQLAlchemy 管理本地 SQLite 数据库，导入一组可重复的 Nova Outdoor 模拟产品数据，并用 pytest 验证核心行为。

## Scope

### Included

- Python 3.12+ 后端项目骨架
- FastAPI 应用入口与健康检查接口
- SQLAlchemy 2 数据库配置
- SQLite 默认本地数据库
- Product 数据模型
- 产品初始化数据
- 按关键词和基础筛选条件查询产品
- Pydantic 请求/响应模型
- 产品查询 API 测试与数据层测试
- Ruff 配置和基础项目说明

### Excluded

- LangGraph、多 Agent 和 LLM 调用
- RAG、Embedding 和 ChromaDB
- Redis、MCP、LangSmith
- Vue 前端
- 真实 ERP、CRM、邮件和支付系统
- 用户登录、权限和多租户
- 生产环境部署

## Architecture

```text
FastAPI routes
      │
      ▼
Product service / query logic
      │
      ▼
SQLAlchemy session
      │
      ▼
SQLite products table
```

产品查询逻辑放在独立 service 层，路由只负责 HTTP 参数和响应转换。这样后续 Product Agent、RAG 检索和其他工具可以复用同一查询接口，不直接依赖 FastAPI。

## Data model

Product 至少包含：

- `id`: integer primary key
- `sku`: unique product identifier
- `name`: product name
- `category`: product category
- `description`: searchable description
- `material`: material information
- `colors`: comma-separated demo values for the first phase
- `min_order_quantity`: MOQ
- `lead_time_days`: lead time in days
- `unit_price_usd`: demo base price
- `is_active`: availability flag

价格在第一阶段只作为产品基础字段保存，不能被理解为正式报价规则。阶梯价格、Incoterms、汇率和库存会在后续工具阶段实现。

## API

### `GET /health`

Returns a simple service status response.

### `GET /api/products`

Optional query parameters:

- `q`: case-insensitive search over SKU, name, category and description
- `category`: exact category filter
- `limit`: positive result limit with a safe default and maximum

The response returns a stable JSON list of product records. An invalid limit returns a validation error.

## Error handling

- Invalid request parameters use FastAPI/Pydantic validation responses.
- Missing database records produce an empty result list, not a server error.
- Database initialization is explicit and repeatable.
- No API key or secret is required for this phase.

## Testing strategy

Tests are written before implementation for:

1. Product seed data creates the expected active products.
2. Keyword search is case-insensitive and matches product content.
3. Category filtering narrows results.
4. The API returns product data and validates the limit.
5. The health endpoint reports service availability.

Tests use a temporary SQLite database and do not depend on a developer's local database file.

## Completion criteria

- A new checkout can install the backend dependencies.
- Database initialization creates the products table and seeds deterministic data.
- `GET /health` succeeds.
- `GET /api/products` supports keyword and category filtering.
- The full pytest suite passes.
- No credentials or generated database files are committed.
