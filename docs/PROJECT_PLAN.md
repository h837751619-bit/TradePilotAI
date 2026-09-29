# TradePilot AI — AI 外贸销售 Agent 完整构建方案

> 项目定位：面向跨境 B2B 外贸企业的 AI Sales Agent / AI FDE 作品集项目  
> 项目目标：完成“海外客户询盘 → 需求解析 → 客户识别 → 产品检索 → 产品推荐 → 库存/价格查询 → 报价 → 英文邮件 → 人工审批 → CRM 留痕”的端到端业务流程。  
> 适用求职方向：AI 应用开发、AI Solution Engineer、FDE、AI 产品经理、企业 AI 落地、Agent Engineer。  
> 第一版目标：4 周完成可演示 MVP；之后继续迭代到企业级 POC。

---

## 0. 使用方式

建议把本文件作为项目总设计文档，放在：

```text
tradepilot-ai/docs/PROJECT_PLAN.md
```

后续在桌面版 ChatGPT / Cursor / Codex 中开发时，始终以本文件作为项目上下文。

开发原则：

1. 先业务，后 Agent。
2. 先单 Agent/工具跑通，再做多 Agent。
3. 实时、结构化、准确性要求高的数据通过 Tool/API；非结构化知识使用 RAG。
4. LLM 不直接计算价格、库存、金额。
5. 高风险动作必须 Human-in-the-loop。
6. 所有 Agent 行为尽量可观测、可评估、可复现。
7. MCP 放在核心业务流程跑通之后，不要为了“有 MCP”而提前引入复杂度。
8. 所有指标必须来自真实 Evaluation，不允许为了简历编造数据。

---

# 1. 项目定位

## 1.1 项目名称

TradePilot AI

副标题：

> AI Export Sales Agent for B2B Cross-Border Trade

中文：

> 企业级 AI 外贸销售工作台

---

## 1.2 要解决的问题

传统外贸业务员收到海外询盘之后，通常需要人工完成：

```text
阅读邮件
  ↓
理解客户需求
  ↓
判断客户身份
  ↓
查 CRM
  ↓
查产品目录
  ↓
查产品规格
  ↓
查库存
  ↓
查价格
  ↓
判断 MOQ
  ↓
计算报价
  ↓
判断交期
  ↓
写英文邮件
  ↓
录入 CRM
```

TradePilot AI 的目标：

```text
客户询盘
  ↓
AI 自动解析
  ↓
客户画像
  ↓
产品匹配
  ↓
企业知识检索
  ↓
库存/价格/报价工具
  ↓
风险检查
  ↓
英文回复
  ↓
人工审批
  ↓
CRM 留痕
```

---

# 2. 模拟企业

建立一个虚拟企业作为 Demo 数据源。

## Hangzhou Nova Outdoor Co., Ltd.

行业：

> Outdoor Furniture / B2B Export

产品：

- Outdoor Chair
- Outdoor Table
- Outdoor Sofa
- Outdoor Umbrella
- Outdoor Furniture Set

主要市场：

- Italy
- Germany
- France
- UK
- USA
- Australia

主要业务：

- B2B wholesale
- Hotel projects
- Restaurant projects
- Commercial outdoor furniture
- OEM/ODM

---

# 3. MVP 功能范围

第一版只实现以下功能：

| 模块 | MVP |
|---|---|
| Inquiry Parser | 必须 |
| Customer Lookup | 必须 |
| Product RAG | 必须 |
| Product Recommendation | 必须 |
| Inventory Tool | 必须 |
| Pricing Tool | 必须 |
| Quote Generator | 必须 |
| Email Generator | 必须 |
| Human Approval | 必须 |
| Agent Trace | 必须 |
| Evaluation | 必须 |
| MCP | 第二阶段 |
| Email 真发送 | 暂不做 |
| ERP 真集成 | 暂不做 |
| 支付 | 不做 |
| 自动改价格 | 不做 |
| 自动下单 | 不做 |

---

# 4. 技术栈

## Backend

- Python 3.12+
- FastAPI
- Pydantic
- SQLAlchemy
- MySQL
- Redis

## AI

- LangGraph
- LangChain
- OpenAI / DeepSeek / Qwen 等兼容模型
- Embedding Model
- ChromaDB

## Frontend

推荐：

- Vue 3
- TypeScript
- Vite
- Tailwind CSS
- Element Plus

## Agent / Protocol

- LangGraph
- Tool Calling
- MCP

## Observability

- LangSmith
- 自建 agent_runs 表

## Deployment

- Docker
- Docker Compose

---

# 5. 总体架构

```text
                         Vue 3
                           │
                           ▼
                       FastAPI
                           │
                           ▼
                     LangGraph
                     Supervisor
                           │
       ┌───────────┬───────┼────────┬───────────┐
       ▼           ▼       ▼        ▼           ▼
 Requirement    Customer Product  Inventory   Quote
   Agent         Agent    Agent     Tool       Agent
       │           │       │         │          │
       └───────────┴───────┼─────────┴──────────┘
                           ▼
                       Email Agent
                           │
                           ▼
                    Human Approval
                           │
                           ▼
                       CRM Save
                           │
                           ▼
                          END

Product/Company/FAQ Knowledge
           │
           ▼
      RAG Pipeline
           │
           ▼
       ChromaDB

Customer/Product/Inventory/Pricing
           │
           ▼
        MySQL

Agent State / Session / Cache
           │
           ▼
         Redis

第二阶段：

Agent
  ↓
MCP Client
  ↓
MCP Server
  ↓
CRM / Product / Inventory / Pricing Tools
```

---

# 6. 数据分类原则

这是项目最重要的架构原则之一。

## 6.1 RAG 数据

适合：

- 产品描述
- 产品规格
- 产品使用场景
- FAQ
- 公司介绍
- 认证说明
- 付款政策
- 售后政策
- 贸易知识
- 产品手册

## 6.2 Tool / API 数据

适合：

- 当前价格
- 库存
- 客户信息
- 历史订单
- 客户等级
- MOQ
- 报价计算
- 订单状态
- CRM 信息

原则：

> 实时、结构化、强一致性数据不要依赖向量数据库。

---

# 7. 数据库设计

第一版建立 7 张核心表。

---

## 7.1 customers

```sql
CREATE TABLE customers (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    customer_code VARCHAR(50) UNIQUE,
    company_name VARCHAR(255) NOT NULL,
    contact_name VARCHAR(100),
    email VARCHAR(255),
    country VARCHAR(100),
    industry VARCHAR(100),
    customer_level VARCHAR(20),
    total_order_amount DECIMAL(12,2) DEFAULT 0,
    last_contact_time DATETIME,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

示例：

```text
C0001
Milano Living SRL
Marco Rossi
Italy
Furniture Distributor
A
82000 USD
```

---

## 7.2 products

```sql
CREATE TABLE products (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    sku VARCHAR(50) UNIQUE NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    material VARCHAR(100),
    color VARCHAR(255),
    application VARCHAR(255),
    moq INT,
    unit_price DECIMAL(10,2),
    currency VARCHAR(10) DEFAULT 'USD',
    lead_time_days INT,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 7.3 inventory

```sql
CREATE TABLE inventory (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    sku VARCHAR(50),
    warehouse VARCHAR(100),
    stock_quantity INT,
    reserved_quantity INT DEFAULT 0,
    updated_at DATETIME
);
```

可用库存：

```text
available = stock_quantity - reserved_quantity
```

---

## 7.4 inquiries

```sql
CREATE TABLE inquiries (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    customer_id BIGINT,
    inquiry_text TEXT,
    source VARCHAR(50),
    status VARCHAR(30),
    extracted_requirements JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 7.5 quotes

```sql
CREATE TABLE quotes (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    quote_no VARCHAR(50) UNIQUE,
    customer_id BIGINT,
    inquiry_id BIGINT,
    currency VARCHAR(10),
    incoterm VARCHAR(20),
    total_amount DECIMAL(12,2),
    status VARCHAR(30),
    valid_until DATE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 7.6 quote_items

```sql
CREATE TABLE quote_items (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    quote_id BIGINT,
    sku VARCHAR(50),
    quantity INT,
    unit_price DECIMAL(10,2),
    subtotal DECIMAL(12,2)
);
```

---

## 7.7 agent_runs

```sql
CREATE TABLE agent_runs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    session_id VARCHAR(100),
    inquiry_id BIGINT,
    agent_name VARCHAR(100),
    tool_name VARCHAR(100),
    input_data JSON,
    output_data JSON,
    latency_ms INT,
    token_usage INT,
    status VARCHAR(30),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

用途：

- Agent Trace
- 调试
- Observability
- Evaluation
- Token 成本统计
- Latency 统计
- Audit Trail

---

# 8. RAG 知识库设计

目录：

```text
data/
├── products/
│   ├── CH001.md
│   ├── CH002.md
│   ├── CH003.md
│   └── ...
│
├── company/
│   ├── company_profile.md
│   ├── payment_terms.md
│   ├── shipping_policy.md
│   └── certifications.md
│
├── faq/
│   ├── product_faq.md
│   ├── order_faq.md
│   └── after_sales.md
│
└── trade/
    ├── incoterms.md
    ├── export_process.md
    └── payment_methods.md
```

---

# 9. 产品知识文档模板

例如：

```markdown
# Nova Aluminum Outdoor Chair

SKU: CH001

## Product Overview

Nova Aluminum Outdoor Chair is designed for
commercial restaurant, hotel and outdoor use.

## Material

Powder-coated aluminum frame.

## Features

- Waterproof
- UV resistant
- Stackable
- Lightweight
- Commercial grade

## Colors

- Black
- White
- Grey

## Dimensions

W560 × D580 × H830 mm

## MOQ

100 units.

## Lead Time

25 days for standard orders.

## Certification

EN581 available.

## Suitable Scenarios

- Restaurant
- Café
- Hotel
- Garden
- Commercial outdoor spaces
```

---

# 10. RAG Pipeline

第一版：

```text
Documents
    ↓
Loader
    ↓
Cleaning
    ↓
Chunking
    ↓
Embedding
    ↓
ChromaDB
```

检索：

```text
User Inquiry
    ↓
Query Rewrite
    ↓
Vector Search
    ↓
Keyword / Metadata Filter
    ↓
Top K
    ↓
Rerank（可选）
    ↓
LLM
```

第二阶段可以增加：

- Hybrid Search
- Reranker
- Metadata Filtering
- Query Expansion

---

# 11. Inquiry Parser

目标：

把：

```text
自然语言询盘
```

变成：

```json
{
  "product_category": "outdoor chair",
  "quantity": 500,
  "material": "aluminum",
  "color": "black",
  "features": [
    "stackable",
    "waterproof"
  ],
  "use_case": "restaurant",
  "destination_country": "Italy",
  "incoterm": "FOB",
  "deadline": null
}
```

使用 Pydantic Structured Output。

```python
from pydantic import BaseModel
from typing import Optional, List


class InquiryRequirement(BaseModel):
    product_category: Optional[str] = None
    quantity: Optional[int] = None
    material: Optional[str] = None
    color: Optional[str] = None
    features: List[str] = []
    use_case: Optional[str] = None
    destination_country: Optional[str] = None
    incoterm: Optional[str] = None
    deadline: Optional[str] = None
```

要求：

- 不允许模型自由输出格式。
- 缺失字段返回 null。
- 不允许模型编造信息。

---

# 12. LangGraph State

```python
from typing import TypedDict, Optional, List


class TradeAgentState(TypedDict):
    session_id: str

    inquiry_text: str

    customer_email: Optional[str]

    requirements: dict

    customer_profile: Optional[dict]

    recommended_products: List[dict]

    selected_product: Optional[dict]

    inventory_result: Optional[dict]

    quote: Optional[dict]

    email_draft: Optional[str]

    approval_status: Optional[str]

    errors: List[str]
```

---

# 13. Agent 设计

第一版不要做“万能 Agent”。

采用：

```text
Supervisor
    │
    ├── Requirement Agent
    ├── Customer Agent
    ├── Product Agent
    ├── Inventory Tool
    ├── Quote Agent
    └── Email Agent
```

---

# 14. Requirement Agent

职责：

- 解析客户询盘
- 提取数量
- 产品类型
- 材质
- 颜色
- 特性
- 用途
- 国家
- Incoterm
- Deadline

不负责：

- 查价格
- 查库存
- 做报价

---

# 15. Customer Agent

工具：

```python
get_customer_by_email(email)
get_customer_by_company(company)
get_purchase_history(customer_id)
get_inquiry_history(customer_id)
```

返回：

```json
{
  "customer_code": "C0001",
  "company": "Milano Living SRL",
  "country": "Italy",
  "level": "A",
  "historical_orders": 3,
  "total_order_amount": 82000
}
```

---

# 16. Product Agent

流程：

```text
Requirements
    ↓
Query Rewrite
    ↓
RAG
    ↓
Candidate Products
    ↓
Database Filter
    ↓
Match Score
    ↓
Top 3
```

---

# 17. 产品匹配评分

不要让 LLM 随便生成 Match Score。

使用确定性规则。

示例：

```text
Category       25
Use Case       20
Features       20
Color          10
Material       10
MOQ            10
Lead Time       5
-------------------
Total         100
```

Python：

```python
def calculate_match_score(requirement, product):
    score = 0

    if requirement["product_category"] == product["category"]:
        score += 25

    if requirement["use_case"] in product["application"]:
        score += 20

    if requirement["color"] in product["colors"]:
        score += 10

    if requirement["quantity"] >= product["moq"]:
        score += 10

    return score
```

LLM 负责：

> 解释为什么推荐。

Python/规则负责：

> 计算分数。

---

# 18. Inventory Tool

```python
def get_inventory(sku: str):
    ...
```

返回：

```json
{
  "sku": "CH001",
  "warehouse": "Hangzhou Warehouse",
  "stock_quantity": 3200,
  "reserved_quantity": 500,
  "available_quantity": 2700
}
```

如果：

```text
requested_quantity > available_quantity
```

Agent 必须：

> 标记库存风险。

不得告诉客户“有货”。

---

# 19. Pricing Tool

价格规则示例：

```text
100-499       $38
500-999       $35
1000-2999     $32
3000+         $29
```

客户等级：

```text
A: -3%
B: -1%
C: 0%
```

计算全部使用 Python。

禁止：

```text
让 LLM 自己计算最终金额
```

---

# 20. Quote Agent

流程：

```text
Quote Agent
    ↓
get_product_price()
    ↓
calculate_discount()
    ↓
calculate_quote()
    ↓
generate_quote_summary()
```

输出：

```json
{
  "quote_no": "QT20260923001",
  "sku": "CH001",
  "quantity": 500,
  "unit_price": 33.95,
  "subtotal": 16975,
  "currency": "USD",
  "incoterm": "FOB Ningbo",
  "lead_time": "25 days",
  "validity": "15 days"
}
```

---

# 21. 外贸业务规则

加入以下业务概念：

## MOQ

客户：

```text
50 pcs
```

产品：

```text
MOQ = 100
```

系统：

```text
MOQ requirement not satisfied.
Recommended quantity: 100.
```

## Incoterms

第一版支持：

- EXW
- FOB
- CIF
- CFR
- DAP
- DDP

## Currency

支持：

- USD
- EUR
- GBP
- AUD

## Lead Time

考虑：

```text
Inventory
+
Production Lead Time
+
Shipping Information
```

第一版只做模拟。

---

# 22. Email Agent

输入：

```text
Customer Profile
+
Requirements
+
Product
+
Quote
```

输出英文商务邮件。

必须遵守：

```text
不能修改价格
不能编造认证
不能编造库存
不能编造交期
不能承诺未确认事项
```

模板：

```text
Subject:
Quotation for {quantity} {product}

Dear {customer_name},

Thank you for your inquiry.

Based on your requirements, we recommend...

Product:
Quantity:
Unit Price:
Total:
Incoterm:
Lead Time:

Please let us know if you would like us
to provide additional information.

Best regards,
Sales Team
```

---

# 23. Supervisor Workflow

第一版采用确定性 Workflow。

```text
START
  ↓
Parse Inquiry
  ↓
Identify Customer
  ↓
Retrieve Products
  ↓
Rank Products
  ↓
Check Inventory
  ↓
Generate Quote
  ↓
Risk Check
  ↓
Generate Email
  ↓
Human Approval
  ↓
Save CRM
  ↓
END
```

不要一开始做复杂自主规划。

原则：

> 企业 Agent 的可控性优先于炫技。

---

# 24. Human-in-the-loop

必须人工确认的动作：

- 最终报价
- 发送邮件
- 修改价格
- 承诺交期
- 创建订单
- 其他高风险业务动作

流程：

```text
AI Generate
    ↓
Risk Check
    ↓
Human Review
    ├── Approve
    └── Reject
```

第一版不要真的自动发送邮件。

---

# 25. Quote Risk Agent

建议作为 MVP 后半段加入。

检查：

```text
Price Risk
MOQ Risk
Inventory Risk
Lead Time Risk
Missing Information
Unsupported Claim
```

例如：

```text
库存不足：
WARNING

MOQ 不满足：
WARNING

价格低于底价：
BLOCK

交期超过客户要求：
WARNING

未经确认的认证：
BLOCK
```

---

# 26. MCP 第二阶段

核心业务跑通之后，再把工具封装成 MCP。

MCP Tools：

```text
search_customer
get_customer_history
search_product
get_product_detail
get_inventory
get_price
calculate_quote
save_crm_note
```

架构：

```text
LangGraph Agent
      ↓
MCP Client
      ↓
MCP Server
      ↓
Business Tools
      ↓
MySQL / APIs
```

目标不是为了展示 MCP，而是：

> 将 Agent 与企业业务系统解耦。

---

# 27. API 设计

第一版接口：

```text
POST /api/inquiries
POST /api/agent/run
GET  /api/agent/runs/{id}
GET  /api/products
GET  /api/customers/{id}
POST /api/quotes
POST /api/agent/{run_id}/approve
POST /api/agent/{run_id}/reject
```

---

# 28. 前端页面

## Dashboard

展示：

```text
Today's Inquiries
Quotes Generated
Potential Leads
Pending Approvals
Agent Success Rate
```

## Inquiry Workspace

左：

```text
Original Customer Inquiry
```

右：

```text
AI Analysis

Customer
Country
Quantity
Product
Color
Requirements
```

下方：

```text
Recommended Products
```

再下面：

```text
Quote
```

最后：

```text
Email Draft
```

---

# 29. Agent Trace

这是作品集重点。

显示：

```text
✓ Parse Inquiry
✓ Identify Customer
✓ Search Knowledge Base
✓ Rank Products
✓ Check Inventory
✓ Calculate Quote
✓ Risk Check
✓ Generate Email
● Awaiting Approval
```

点击节点可以查看：

```text
Agent
Tool
Input
Output
Latency
Token Usage
Status
```

---

# 30. Evaluation

建立：

```text
evaluation/
├── datasets/
├── evaluators/
└── reports/
```

第一版准备至少：

> 50 条 Inquiry

分类：

```text
10 简单询盘
10 信息缺失
10 多产品询盘
10 模糊表达
10 复杂询盘
```

---

# 31. Evaluation 指标

必须测试：

```text
Requirement Extraction Accuracy

Product Retrieval Recall@3

Product Match Accuracy

Tool Call Success Rate

Quote Calculation Accuracy

Agent Task Completion Rate

Average Latency

Average Token Usage

Average Cost
```

建议目标：

```text
Requirement Extraction >= 90%

Product Recall@3 >= 90%

Quote Calculation = 100%

Tool Success >= 95%

Workflow Completion >= 85%
```

这些是目标，不是预设结果。

最终 README 只能写真实测试结果。

---

# 32. Observability

每次 Agent Run 记录：

```text
session_id
agent_name
tool_name
input
output
latency
tokens
status
error
timestamp
```

建议接入 LangSmith。

同时保留自己的：

```text
agent_runs
```

表。

这样可以做：

```text
Cost Dashboard
Latency Dashboard
Failure Analysis
Agent Trace
```

---

# 33. 项目目录

最终：

```text
tradepilot-ai/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── agents/
│   │   │   ├── state.py
│   │   │   ├── graph.py
│   │   │   ├── requirement.py
│   │   │   ├── customer.py
│   │   │   ├── product.py
│   │   │   ├── inventory.py
│   │   │   ├── quote.py
│   │   │   └── email.py
│   │   │
│   │   ├── tools/
│   │   │   ├── customer_tools.py
│   │   │   ├── product_tools.py
│   │   │   ├── inventory_tools.py
│   │   │   └── pricing_tools.py
│   │   │
│   │   ├── rag/
│   │   │   ├── loader.py
│   │   │   ├── splitter.py
│   │   │   ├── embeddings.py
│   │   │   ├── retriever.py
│   │   │   └── reranker.py
│   │   │
│   │   ├── api/
│   │   │   ├── inquiry.py
│   │   │   ├── customer.py
│   │   │   └── agent.py
│   │   │
│   │   ├── db/
│   │   │   ├── mysql.py
│   │   │   └── models.py
│   │   │
│   │   └── schemas/
│   │       ├── inquiry.py
│   │       ├── quote.py
│   │       └── product.py
│   │
│   └── requirements.txt
│
├── frontend/
│
├── mcp-server/
│
├── evaluation/
│   ├── datasets/
│   ├── evaluators/
│   └── reports/
│
├── data/
│   ├── products/
│   ├── customers/
│   ├── faq/
│   ├── company/
│   └── trade/
│
├── docs/
│   ├── PRD.md
│   ├── architecture.md
│   ├── agent-design.md
│   └── evaluation.md
│
├── docker-compose.yml
├── .env.example
├── README.md
└── LICENSE
```

---

# 34. 开发阶段

## Phase 0 — Project Setup

目标：

```text
Git
Python
FastAPI
Vue
Docker
MySQL
Redis
```

验收：

```text
docker compose up
```

能够启动基础服务。

---

## Phase 1 — Database

完成：

- customers
- products
- inventory
- inquiries
- quotes
- quote_items
- agent_runs

准备：

- 20 个客户
- 30 个产品
- 30 条库存

验收：

> API 可以查询客户、产品、库存。

---

## Phase 2 — RAG

完成：

```text
Loader
Chunker
Embedding
Chroma
Retriever
```

验收：

> 给定产品需求，能够返回正确产品知识。

---

## Phase 3 — Tools

完成：

```text
Customer Tools
Product Tools
Inventory Tool
Pricing Tool
Quote Tool
```

验收：

> 不经过 LLM，也能准确执行核心业务计算。

---

## Phase 4 — Requirement Agent

完成：

> Inquiry → Structured Requirement

验收：

> 50 条测试数据中达到目标准确率。

---

## Phase 5 — Product Agent

完成：

```text
Requirement
→ RAG
→ Product Search
→ Ranking
```

验收：

> Top 3 推荐基本正确。

---

## Phase 6 — LangGraph

连接：

```text
Requirement
→ Customer
→ Product
→ Inventory
→ Quote
→ Risk
→ Email
```

验收：

> 一封询盘能够完整跑通。

---

## Phase 7 — Human Approval

完成：

```text
AI
↓
Approval
↓
Approve / Reject
```

验收：

> AI 无法直接执行高风险操作。

---

## Phase 8 — Frontend

完成：

- Dashboard
- Inquiry Workspace
- Product Recommendation
- Quote
- Email
- Agent Trace
- Approval

验收：

> 3 分钟内可以完整演示一次业务流程。

---

## Phase 9 — Evaluation

完成：

- 50+ 测试样本
- 指标
- 自动化测试
- Evaluation Report

验收：

> README 展示真实结果。

---

## Phase 10 — MCP

最后做：

```text
MCP Server
+
MCP Tools
+
Agent Integration
```

验收：

> Agent 可以通过 MCP 调用业务工具。

---

## Phase 11 — Docker / Deployment

完成：

```text
frontend
backend
mysql
redis
chromadb
mcp-server
```

Docker Compose 一键启动。

---

# 35. 4 周开发计划

## Week 1

```text
Day 1
项目初始化

Day 2
MySQL

Day 3
模拟数据

Day 4
FastAPI

Day 5
Product RAG

Day 6
RAG Evaluation

Day 7
修复
```

## Week 2

```text
Requirement Agent
Customer Agent
Product Agent
Inventory Tool
Pricing Tool
Quote Tool
```

目标：

> Inquiry → Quote

## Week 3

```text
LangGraph
Email Agent
Risk Agent
Human Approval
Vue UI
Agent Trace
```

目标：

> 完整 Demo

## Week 4

```text
MCP
Evaluation
LangSmith
Docker
README
Demo Video
```

目标：

> Portfolio-ready

---

# 36. Git Commit 规范

推荐：

```text
feat: add inquiry parser
feat: add product retrieval
feat: add inventory tool
feat: add quote calculation
feat: add langgraph workflow
feat: add human approval
feat: add agent trace
feat: add evaluation dataset
feat: add mcp server
fix: improve product ranking
fix: prevent unsupported claims
docs: update architecture
```

---

# 37. README 最终结构

```text
# TradePilot AI

## Problem

## Solution

## Demo

## Architecture

## Agent Workflow

## RAG

## Tool Calling

## MCP

## Human-in-the-loop

## Evaluation

## Observability

## Tech Stack

## Installation

## Quick Start

## API

## Project Structure

## Limitations

## Future Work
```

---

# 38. 面试 Demo 流程

准备一个 3 分钟 Demo。

输入：

```text
Hi,

We are a furniture distributor based in Milan.

We need approximately 500 stackable black
outdoor chairs for restaurant projects.

The chairs should be waterproof and preferably
aluminum.

Could you recommend suitable products and
provide FOB pricing?

Best regards,
Marco
```

然后点击：

> Analyze Inquiry

系统展示：

```text
Customer:
Milano Living SRL

Country:
Italy

Quantity:
500

Use Case:
Restaurant

Features:
Waterproof
Stackable

Material:
Aluminum

Incoterm:
FOB
```

然后：

```text
Recommended Products

CH001 — 95
CH004 — 82
CH006 — 71
```

然后：

```text
Inventory:
2700 available
```

然后：

```text
Quote:
500 × $33.95
Total: $16,975
FOB Ningbo
Lead Time: 25 days
```

然后：

```text
Risk:
No blocking risk detected.
```

然后生成：

> 英文商务邮件

最后：

```text
Awaiting Human Approval
```

点击：

> Approve

结束。

---

# 39. 作品集重点

不要只展示：

```text
LangGraph
LangChain
RAG
MCP
```

真正要展示：

```text
Business Problem
       ↓
Business Workflow
       ↓
AI Architecture
       ↓
Tools
       ↓
Human Approval
       ↓
Evaluation
       ↓
Observability
       ↓
Business Outcome
```

---

# 40. 与普通 AI Sales Agent 的差异化

GitHub 上已经有大量：

- AI Sales Agent
- SDR Agent
- CRM Agent
- RAG Sales Assistant
- Multi-Agent Sales System

因此 TradePilot 不应该只做：

```text
AI
+
RAG
+
LangGraph
+
Email
```

必须体现外贸业务：

```text
Inquiry
+
MOQ
+
Incoterms
+
Inventory
+
Tier Pricing
+
Lead Time
+
Quote
+
Export Knowledge
+
Human Approval
```

最终定位：

> **AI Export Sales Agent，而不是普通 AI Sales Chatbot。**

---

# 41. 项目与求职的对应关系

项目可以覆盖：

## AI Application Engineer

证明：

- Python
- FastAPI
- LangGraph
- RAG
- Tool Calling
- Frontend
- Docker

## FDE / AI Solution Engineer

证明：

- Business Process Analysis
- Enterprise Integration
- Tool/API Design
- MCP
- Human-in-the-loop
- Observability
- Evaluation

## AI Product Manager

证明：

- PRD
- Workflow
- User Journey
- AI Feature Design
- Evaluation
- Business Metrics

## AI 外贸 / 企业 AI 落地

证明：

- 外贸业务理解
- AI Workflow
- Product Knowledge
- CRM
- Quotation
- Lead Management

---

# 42. 第一版不要做的事情

不要一开始：

- 做几十个 Agent
- 做复杂 Memory
- 做自动发邮件
- 接真实 ERP
- 接真实支付
- 做复杂权限
- 做复杂微服务
- 做 Kubernetes
- 做大规模模型训练
- 做 Fine-tuning
- 为了 MCP 而 MCP
- 为了 Multi-Agent 而 Multi-Agent

目标：

> 一个完整、可运行、可解释、可评估的企业 AI Workflow。

---

# 43. 第一阶段完成标准

当以下全部满足时，Phase 1 才算结束：

```text
[ ] MySQL 正常运行
[ ] 20 个客户
[ ] 30 个产品
[ ] 30 条库存
[ ] Product API
[ ] Customer API
[ ] Inventory API
[ ] Pricing Tool
[ ] Quote Tool
[ ] Product RAG
[ ] Inquiry Parser
```

不要在 Phase 1 没完成时继续堆 Agent。

---

# 44. 第二阶段完成标准

```text
[ ] Requirement Agent
[ ] Customer Agent
[ ] Product Agent
[ ] Inventory Tool
[ ] Quote Agent
[ ] Email Agent
[ ] LangGraph Workflow
```

最终：

```text
Inquiry
→ Quote
```

必须跑通。

---

# 45. 第三阶段完成标准

```text
[ ] Web UI
[ ] Agent Trace
[ ] Human Approval
[ ] Risk Check
[ ] CRM Save
```

最终：

```text
Inquiry
→ AI Analysis
→ Recommendation
→ Quote
→ Email
→ Approval
→ CRM
```

---

# 46. 第四阶段完成标准

```text
[ ] Evaluation Dataset
[ ] Automated Evaluation
[ ] LangSmith
[ ] MCP
[ ] Docker
[ ] README
[ ] Demo Video
```

此时项目才进入求职作品集状态。

---

# 47. 后续 V2

完成 MVP 后再考虑：

## 多渠道

- Email
- WhatsApp
- WeChat
- Web Chat

## 外贸增强

- HS Code
- Freight Estimation
- Customs Knowledge
- Shipping Schedule
- Payment Risk
- Country Risk

## CRM

- Lead Pipeline
- Follow-up Reminder
- Customer Segmentation
- Sales Forecast

## AI

- Voice Agent
- Multimodal Product Search
- Image-to-Product
- Competitor Research
- Automatic Follow-up

---

# 48. 最终简历项目描述模板

项目完成并且真实测试后，可以根据实际数据修改成：

> **TradePilot AI — AI Export Sales Agent**
>
> 面向 B2B 跨境贸易场景设计并实现 AI 外贸销售 Agent，覆盖客户询盘解析、客户画像、产品知识检索、产品匹配、库存查询、阶梯价格计算、报价生成及英文商务邮件生成等核心业务流程。
>
> 基于 LangGraph 构建可控 Agent Workflow，通过 RAG 管理企业产品与贸易知识，并使用 Tool Calling / MCP 对接客户、产品、库存及报价等业务能力；针对价格、库存及交期等高风险业务设计 Human-in-the-loop 审批与 Risk Check 机制。
>
> 搭建 Agent Trace 与 Evaluation Pipeline，对需求抽取、Product Recall、Tool Success Rate、Quote Accuracy、Task Completion Rate、Latency 与 Token Cost 进行量化评估，并使用 Docker 完成项目部署。

注意：

> 只有项目实际完成并测试后才能填写具体数字。

---

# 49. 开发时给 AI 编程助手的总 Prompt

当你准备在桌面版 ChatGPT / Cursor / Codex 中正式开始开发时，可以先把本文件放入项目，然后使用下面的启动指令：

```text
你现在是 TradePilot AI 项目的 Principal AI Engineer。

请严格阅读 docs/PROJECT_PLAN.md，并将其作为当前项目的主要技术规格。

项目目标：
构建一个面向 B2B 跨境贸易企业的 AI Export Sales Agent。

核心业务流程：

客户询盘
→ 需求解析
→ 客户识别
→ 产品检索
→ 产品匹配
→ 库存查询
→ 价格计算
→ 报价
→ 风险检查
→ 英文邮件
→ Human Approval
→ CRM 留痕

技术栈：
Python
FastAPI
LangGraph
LangChain
MySQL
Redis
ChromaDB
Vue 3
TypeScript
Docker
MCP（第二阶段）

开发原则：
1. 不要跳过项目阶段。
2. 不要一次生成整个项目。
3. 每次只完成一个明确的开发任务。
4. 修改代码前先解释设计。
5. 每完成一个阶段都运行测试。
6. 不要编造业务数据或测试结果。
7. LLM 不负责价格、库存、金额等确定性计算。
8. 实时结构化数据优先使用 Tool/API。
9. 非结构化知识使用 RAG。
10. 高风险动作必须 Human-in-the-loop。
11. 保持代码简单、模块化、可测试。
12. 优先完成 MVP，再增加 MCP、复杂 Agent 和高级功能。

当前任务：
先检查项目目录。

如果项目为空：
1. 创建基础目录结构。
2. 创建 backend。
3. 创建 FastAPI 最小应用。
4. 创建 Docker Compose。
5. 创建 .env.example。
6. 创建 README.md。
7. 创建基础测试。
8. 不要马上实现 Agent。

完成后告诉我：
- 创建了哪些文件
- 每个文件的作用
- 如何启动
- 如何测试
- 下一步建议

不要一次修改多个未要求的模块。
```

---

# 50. 最终项目成功标准

TradePilot AI 最终不是为了证明：

> “我会用 LangGraph。”

而是证明：

> **我能够理解一个真实企业业务流程，并将 LLM、RAG、Agent、Tools、MCP、数据库、前端、Human-in-the-loop、Evaluation 和 Observability 组合成一个可以工作的 AI 产品。**

这是这个项目对你求职价值最高的地方。

---

# 51. 当前执行顺序

现在不要提前做后面的事情。

严格按照：

```text
01 Project Setup
        ↓
02 Database
        ↓
03 Mock Data
        ↓
04 RAG
        ↓
05 Tools
        ↓
06 Requirement Agent
        ↓
07 Product Agent
        ↓
08 LangGraph
        ↓
09 Quote
        ↓
10 Risk
        ↓
11 Email
        ↓
12 Human Approval
        ↓
13 Frontend
        ↓
14 Evaluation
        ↓
15 Observability
        ↓
16 MCP
        ↓
17 Docker
        ↓
18 README + Demo
```

第一开发目标：

> **先让“产品数据 + MySQL + Product RAG + Product Search Tool”跑通。**

完成这一阶段以后，再进入 Agent。

