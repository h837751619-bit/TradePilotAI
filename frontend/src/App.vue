<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { approveQuote as approveQuoteApi, fetchAgentRuns, fetchCustomers, fetchEvaluation, fetchQuotes, runInquiryWorkflow, searchProducts } from './api'
import type { AgentRun, CustomerRecord, EvaluationMetrics, QuoteRecord } from './api'
import type { Product, QuoteDraft } from './types'

const inquiry = ref('We need 120 aluminum outdoor chairs for a hotel project in Germany.')
const search = ref('')
const products = ref<Product[]>([])
const loading = ref(false)
const error = ref('')
const workflowResult = ref<Awaited<ReturnType<typeof runInquiryWorkflow>> | null>(null)
const quotes = ref<QuoteRecord[]>([])
const quotesLoading = ref(false)
const agentRuns = ref<AgentRun[]>([])
const evaluation = ref<EvaluationMetrics | null>(null)
const customers = ref<CustomerRecord[]>([])
const customerSearch = ref('')
const selectedCustomer = ref<CustomerRecord | null>(null)
const customerName = ref('')
const selectedProduct = ref<Product | null>(null)
const locale = ref<'zh' | 'en' | 'it'>('en')
const quote = ref<QuoteDraft>({
  sku: 'NOVA-CHAIR-001',
  quantity: 120,
  unitPrice: 40.38,
  total: 4845.6,
  status: 'draft',
})

const navKeys = ['inquiryWorkspace', 'products', 'quotes', 'agentTrace', 'customers'] as const
const initialNav = window.location.hash.slice(1) as (typeof navKeys)[number]
const activeNav = ref<(typeof navKeys)[number]>(navKeys.includes(initialNav) ? initialNav : 'inquiryWorkspace')
const translations = {
  zh: { inquiryWorkspace: '询盘工作台', products: '产品库', quotes: '报价单', agentTrace: 'Agent 追踪', salesOps: '销售运营', inquiryTitle: '询盘工作台', inquiry: '客户询盘', inquiryHint: '粘贴客户询盘，开始工作流。', new: '新建', detected: '已识别英语', edited: '刚刚编辑', analyze: '运行分析', requirements: '提取的需求', requirementsHint: '从客户消息中结构化提取。', complete: '已完成', quantity: '数量', destination: '目的地', project: '项目类型', signals: '产品信号', hotel: '酒店项目', matches: '产品匹配', matchesHint: '从产品知识库检索。', found: '个结果', search: '搜索', loading: '正在加载产品目录…', quote: '报价草稿', quoteHint: '根据实时定价规则生成。', selected: '已选产品', unitPrice: '单价', discount: '批量折扣', total: '预计总价', approval: '需要人工审批', approvalHint: '折扣报价发送前必须审核。', approved: '报价已批准', approve: '批准报价', activity: 'Agent 活动', activityHint: '透明的工作流追踪。', operational: '系统运行正常', demo: '演示工作区', parsed: '询盘已解析', searched: '产品知识已搜索', checked: '库存与价格已检查', waiting: '等待人工审批', next: '需要下一步操作', live: '实时', unit: '件', projectHotel: '酒店项目', aluminumChair: '铝制 · 户外椅', english: '中文', quoteReview: '报价审核', customer: '客户', sku: 'SKU', status: '状态', action: '操作', refresh: '刷新', noQuotes: '暂无报价', reviewHint: '查看已生成的客户报价。' },
  en: { inquiryWorkspace: 'Inquiry Workspace', products: 'Products', quotes: 'Quotes', agentTrace: 'Agent Trace', salesOps: 'SALES OPERATIONS', inquiryTitle: 'Inquiry workspace', inquiry: 'Customer inquiry', inquiryHint: 'Paste an incoming inquiry to start the workflow.', new: 'NEW', detected: 'English detected', edited: 'Last edited just now', analyze: 'Run analysis', requirements: 'Extracted requirements', requirementsHint: 'Structured from the customer message.', complete: 'COMPLETE', quantity: 'QUANTITY', destination: 'DESTINATION', project: 'PROJECT TYPE', signals: 'PRODUCT SIGNALS', hotel: 'Hotel project', matches: 'Product matches', matchesHint: 'Retrieved from the product knowledge base.', found: 'FOUND', search: 'Search', loading: 'Loading product catalog…', quote: 'Quote draft', quoteHint: 'Generated from live pricing rules.', selected: 'SELECTED PRODUCT', unitPrice: 'Unit price', discount: 'Volume discount', total: 'Estimated total', approval: 'Human approval required', approvalHint: 'Discounted quote must be reviewed before sending.', approved: 'Quote approved', approve: 'Approve quote', activity: 'Agent activity', activityHint: 'Transparent workflow trace.', operational: 'System operational', demo: 'Demo workspace', parsed: 'Inquiry parsed', searched: 'Product knowledge searched', checked: 'Inventory and pricing checked', waiting: 'Awaiting human approval', next: 'Next action required', live: 'LIVE', unit: 'units', projectHotel: 'Hotel project', aluminumChair: 'Aluminum · Outdoor chair', english: 'English', quoteReview: 'Quote review', customer: 'Customer', sku: 'SKU', status: 'Status', action: 'Action', refresh: 'Refresh', noQuotes: 'No quotes yet', reviewHint: 'Review previously generated customer quotations.' },
  it: { inquiryWorkspace: 'Area richieste', products: 'Prodotti', quotes: 'Preventivi', agentTrace: 'Traccia Agent', salesOps: 'OPERAZIONI VENDITE', inquiryTitle: 'Area richieste', inquiry: 'Richiesta cliente', inquiryHint: 'Incolla una richiesta per avviare il flusso.', new: 'NUOVA', detected: 'Inglese rilevato', edited: 'Modificato ora', analyze: 'Avvia analisi', requirements: 'Requisiti estratti', requirementsHint: 'Strutturati dal messaggio del cliente.', complete: 'COMPLETATO', quantity: 'QUANTITÀ', destination: 'DESTINAZIONE', project: 'TIPO PROGETTO', signals: 'SEGNALI PRODOTTO', hotel: 'Progetto alberghiero', matches: 'Prodotti compatibili', matchesHint: 'Recuperati dalla knowledge base prodotti.', found: 'TROVATI', search: 'Cerca', loading: 'Caricamento catalogo…', quote: 'Bozza preventivo', quoteHint: 'Generata dalle regole di prezzo.', selected: 'PRODOTTO SELEZIONATO', unitPrice: 'Prezzo unitario', discount: 'Sconto volume', total: 'Totale stimato', approval: 'Approvazione richiesta', approvalHint: 'Il preventivo scontato deve essere approvato.', approved: 'Preventivo approvato', approve: 'Approva preventivo', activity: 'Attività Agent', activityHint: 'Traccia trasparente del flusso.', operational: 'Sistema operativo', demo: 'Area demo', parsed: 'Richiesta analizzata', searched: 'Ricerca prodotti completata', checked: 'Scorte e prezzi verificati', waiting: 'In attesa di approvazione', next: 'Azione richiesta', live: 'LIVE', unit: 'unità', projectHotel: 'Progetto alberghiero', aluminumChair: 'Alluminio · Sedia da esterno', english: 'Italiano', quoteReview: 'Revisione preventivi', customer: 'Cliente', sku: 'SKU', status: 'Stato', action: 'Azione', refresh: 'Aggiorna', noQuotes: 'Nessun preventivo', reviewHint: 'Rivedi i preventivi generati.' },
} as const
const t = (key: keyof typeof translations.en) => translations[locale.value][key]
const navItems = computed(() => navKeys.map((key) => ({ key, label: key === 'customers' ? (locale.value === 'zh' ? '客户' : locale.value === 'it' ? 'Clienti' : 'Customers') : t(key) })))
const customerLabels = computed(() => ({
  title: locale.value === 'zh' ? '客户识别' : locale.value === 'it' ? 'Identificazione cliente' : 'Customer match',
  hint: locale.value === 'zh' ? '从询盘内容中识别。' : locale.value === 'it' ? 'Identificato dal contesto della richiesta.' : 'Identified from the inquiry context.',
  existing: locale.value === 'zh' ? '已有客户' : locale.value === 'it' ? 'ESISTENTE' : 'EXISTING',
  newCustomer: locale.value === 'zh' ? '新客户' : locale.value === 'it' ? 'NUOVO' : 'NEW',
  matched: locale.value === 'zh' ? '已匹配' : locale.value === 'it' ? 'Abbinato' : 'Matched',
  create: locale.value === 'zh' ? '创建档案' : locale.value === 'it' ? 'Crea profilo' : 'Create profile',
  unknownCountry: locale.value === 'zh' ? '未识别国家' : locale.value === 'it' ? 'Paese non identificato' : 'Country not identified',
}))
const formattedTotal = computed(() => `$${quote.value.total.toLocaleString('en-US', { minimumFractionDigits: 2 })}`)
const isBusy = computed(() => loading.value || quotesLoading.value)

async function loadProducts() {
  loading.value = true
  error.value = ''
  try {
    products.value = await searchProducts(search.value)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Unable to load products'
  } finally {
    loading.value = false
  }
}

async function selectNav(key: (typeof navKeys)[number]) {
  activeNav.value = key
  window.history.pushState({}, '', `#${key}`)
  error.value = ''
  if (key === 'quotes') {
    quotesLoading.value = true
    try {
      quotes.value = await fetchQuotes()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unable to load quotes'
    } finally {
      quotesLoading.value = false
    }
  }
  if (key === 'agentTrace') {
    try {
      const [runs, metrics] = await Promise.all([fetchAgentRuns(), fetchEvaluation()])
      agentRuns.value = runs
      evaluation.value = metrics
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unable to load agent runs'
    }
  }
  if (key === 'products') await loadProducts()
  if (key === 'customers') {
    try { customers.value = await fetchCustomers(customerSearch.value) } catch (err) { error.value = err instanceof Error ? err.message : 'Unable to load customers' }
  }
}

async function loadCustomers() {
  error.value = ''
  try { customers.value = await fetchCustomers(customerSearch.value) } catch (err) { error.value = err instanceof Error ? err.message : 'Unable to load customers' }
}

function clearError() {
  error.value = ''
}

async function runWorkflow() {
  loading.value = true
  error.value = ''
  try {
    workflowResult.value = await runInquiryWorkflow(inquiry.value, customerName.value)
    quote.value = {
      id: workflowResult.value.quote.id,
      sku: workflowResult.value.quote.sku,
      quantity: workflowResult.value.quote.quantity,
      unitPrice: workflowResult.value.quote.unit_price_usd,
      total: workflowResult.value.quote.total_price_usd,
      status: workflowResult.value.quote.status,
    }
    await loadProducts()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Unable to analyze inquiry'
  } finally {
    loading.value = false
  }
}

async function approveQuote() {
  if (!quote.value.id) return
  try {
    await approveQuoteApi(quote.value.id)
    quote.value.status = 'approved'
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Unable to approve quote'
  }
}

async function approveQuoteRecord(record: QuoteRecord) {
  try {
    await approveQuoteApi(record.id)
    record.status = 'approved'
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Unable to approve quote'
  }
}

onMounted(() => {
  window.addEventListener('popstate', () => {
    const key = window.location.hash.slice(1) as (typeof navKeys)[number]
    if (navKeys.includes(key)) void selectNav(key)
  })
  if (activeNav.value === 'inquiryWorkspace') void loadProducts()
  else void selectNav(activeNav.value)
})
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand"><span class="brand-mark">TP</span><span>TradePilot <em>AI</em></span></div>
      <div class="workspace-label">NOVA OUTDOOR CO.</div>
      <nav>
        <button v-for="item in navItems" :key="item.key" :class="['nav-item', { active: activeNav === item.key }]" @click="selectNav(item.key)">
          <span class="nav-dot" />{{ item.label }}
        </button>
      </nav>
      <div class="sidebar-footer"><span class="status-dot" />{{ t('operational') }}<br /><small>{{ t('demo') }}</small></div>
    </aside>

    <main class="main-content">
      <div v-if="isBusy" class="global-loading"><span class="spinner" /> Loading…</div>
      <div v-if="error" class="global-error"><span>{{ error }}</span><button aria-label="Dismiss error" @click="clearError">×</button></div>
      <header class="topbar"><div><p class="eyebrow">{{ t('salesOps') }} / {{ navItems.find((item) => item.key === activeNav)?.label.toUpperCase() }}</p><h1>{{ t('inquiryTitle') }}</h1></div><div class="user-chip"><select v-model="locale" class="language-select" aria-label="Language"><option value="zh">中文</option><option value="en">English</option><option value="it">Italiano</option></select><span class="avatar">JD</span><span>Jordan Davis</span><span class="chevron">⌄</span></div></header>

      <section v-if="!['quotes', 'products', 'agentTrace'].includes(activeNav)" class="workspace-grid">
        <div class="left-column">
          <section class="panel inquiry-panel">
            <div class="panel-header"><div><span class="step">01</span><div><h2>{{ t('inquiry') }}</h2><p>{{ t('inquiryHint') }}</p></div></div><span class="badge neutral">{{ t('new') }}</span></div>
            <textarea v-model="inquiry" :aria-label="t('inquiry')" />
            <input v-model="customerName" class="customer-input" placeholder="Customer company (optional)" />
            <div class="inquiry-meta"><span>✦ {{ t('detected') }}</span><span>{{ t('edited') }}</span></div>
            <button class="primary-button" @click="runWorkflow">{{ t('analyze') }} <span>→</span></button>
          </section>

          <section class="panel requirements-panel">
            <div class="panel-header"><div><span class="step">02</span><div><h2>{{ t('requirements') }}</h2><p>{{ t('requirementsHint') }}</p></div></div><span class="badge success">{{ t('complete') }}</span></div>
            <div class="requirement-grid"><div><label>{{ t('quantity') }}</label><strong>{{ workflowResult?.inquiry.quantity ?? '—' }} {{ workflowResult ? t('unit') : '' }}</strong></div><div><label>{{ t('destination') }}</label><strong>{{ workflowResult?.inquiry.destination_country ?? '—' }}</strong></div><div><label>{{ t('project') }}</label><strong>{{ workflowResult?.inquiry.project_type ?? '—' }}</strong></div><div><label>{{ t('signals') }}</label><strong>{{ workflowResult?.inquiry.product_keywords.join(' · ') || '—' }}</strong></div></div>
          </section>

          <section v-if="workflowResult" class="panel customer-panel">
            <div class="panel-header"><div><span class="step">02A</span><div><h2>{{ customerLabels.title }}</h2><p>{{ customerLabels.hint }}</p></div></div><span :class="['badge', workflowResult.customer.matched ? 'success' : 'warning']">{{ workflowResult.customer.matched ? customerLabels.existing : customerLabels.newCustomer }}</span></div>
            <div class="customer-summary"><div class="customer-avatar">{{ workflowResult.customer.company_name.slice(0, 2).toUpperCase() || '??' }}</div><div><strong>{{ workflowResult.customer.company_name || customerLabels.newCustomer }}</strong><span>{{ workflowResult.customer.country || customerLabels.unknownCountry }}</span><span v-if="workflowResult.customer.contact_name">{{ workflowResult.customer.contact_name }} · {{ workflowResult.customer.email }}</span></div><div class="match-check">{{ workflowResult.customer.matched ? '✓ ' + customerLabels.matched : '＋ ' + customerLabels.create }}</div></div>
          </section>

          <section class="panel product-panel">
            <div class="panel-header"><div><span class="step">03</span><div><h2>{{ t('matches') }}</h2><p>{{ t('matchesHint') }}</p></div></div><span class="badge success">{{ products.length }} {{ t('found') }}</span></div>
            <div class="search-row"><input v-model="search" placeholder="Search products or SKU" @keyup.enter="loadProducts" /><button class="secondary-button" @click="loadProducts">{{ t('search') }}</button></div>
            <p v-if="loading" class="muted">{{ t('loading') }}</p><p v-else-if="error" class="error-message">{{ error }}</p>
            <div v-else class="product-list"><article v-for="product in products.slice(0, 3)" :key="product.sku" class="product-card"><div class="product-icon">◒</div><div class="product-info"><strong>{{ product.name }}</strong><span>{{ product.sku }} · {{ product.material }}</span></div><div class="product-price">${{ product.unit_price_usd.toFixed(2) }}<small>/ unit</small></div></article></div>
          </section>
        </div>

        <div class="right-column">
          <section class="panel quote-panel"><div class="panel-header"><div><span class="step">04</span><div><h2>{{ t('quote') }}</h2><p>{{ t('quoteHint') }}</p></div></div><span :class="['badge', quote.status === 'approved' ? 'success' : 'warning']">{{ quote.status.toUpperCase() }}</span></div><div class="quote-summary"><div><span>{{ t('selected') }}</span><strong>{{ quote.sku }}</strong></div><div><span>{{ t('quantity') }}</span><strong>{{ quote.quantity }} {{ t('unit') }}</strong></div></div><div class="price-lines"><div><span>{{ t('unitPrice') }}</span><strong>${{ quote.unitPrice.toFixed(2) }}</strong></div><div><span>{{ t('discount') }}</span><strong class="discount">− 5%</strong></div><div class="total-line"><span>{{ t('total') }}</span><strong>{{ formattedTotal }}</strong></div></div><div class="risk-callout"><span class="risk-icon">!</span><div><strong>{{ t('approval') }}</strong><p>{{ t('approvalHint') }}</p></div></div><button class="approve-button" :disabled="quote.status === 'approved'" @click="approveQuote">{{ quote.status === 'approved' ? t('approved') : t('approve') }} <span>✓</span></button></section>
          <section class="panel trace-panel"><div class="panel-header"><div><span class="step">05</span><div><h2>{{ t('activity') }}</h2><p>{{ t('activityHint') }}</p></div></div><span class="live-dot">● {{ t('live') }}</span></div><div class="trace-list"><div class="trace-item done"><span>✓</span><div><strong>{{ t('parsed') }}</strong><small>{{ t('edited') }}</small></div></div><div class="trace-item done"><span>✓</span><div><strong>{{ t('searched') }}</strong><small>3 {{ t('found') }}</small></div></div><div class="trace-item done"><span>✓</span><div><strong>{{ t('checked') }}</strong><small>SKU {{ quote.sku }}</small></div></div><div class="trace-item current"><span>4</span><div><strong>{{ t('waiting') }}</strong><small>{{ t('next') }}</small></div></div></div></section>
        </div>
      </section>
      <section v-else-if="activeNav === 'quotes'" class="panel quotes-page">
        <div class="panel-header"><div><h2>{{ t('quoteReview') }}</h2><p>{{ t('reviewHint') }}</p></div><button class="secondary-button" @click="selectNav('quotes')">{{ t('refresh') }}</button></div>
        <p v-if="quotesLoading" class="muted">{{ t('loading') }}</p>
        <p v-else-if="!quotes.length" class="muted">{{ t('noQuotes') }}</p>
        <div v-else class="quotes-table-wrap"><table class="quotes-table"><thead><tr><th>{{ t('customer') }}</th><th>{{ t('sku') }}</th><th>{{ t('quantity') }}</th><th>{{ t('total') }}</th><th>{{ t('status') }}</th><th>{{ t('action') }}</th></tr></thead><tbody><tr v-for="record in quotes" :key="record.id"><td>{{ record.customer_name || '—' }}</td><td>{{ record.sku }}</td><td>{{ record.quantity }}</td><td>${{ record.total_price_usd.toFixed(2) }}</td><td><span :class="['badge', record.status === 'approved' ? 'success' : 'warning']">{{ record.status.toUpperCase() }}</span></td><td><button v-if="record.status === 'draft'" class="table-action" @click="approveQuoteRecord(record)">{{ t('approve') }}</button><span v-else class="approved-mark">✓</span></td></tr></tbody></table></div>
      </section>
      <section v-else-if="activeNav === 'agentTrace'" class="panel quotes-page">
        <div class="panel-header"><div><h2>{{ t('activity') }}</h2><p>{{ t('activityHint') }}</p></div><button class="secondary-button" @click="selectNav('agentTrace')">{{ t('refresh') }}</button></div>
        <div v-if="evaluation" class="metrics-grid"><div><small>CASES</small><strong>{{ evaluation.cases }}</strong></div><div><small>REQUIREMENTS</small><strong>{{ (evaluation.requirement_accuracy * 100).toFixed(0) }}%</strong></div><div><small>PRODUCT MATCH</small><strong>{{ (evaluation.product_match_rate * 100).toFixed(0) }}%</strong></div><div><small>FAILURE DETECTION</small><strong>{{ (evaluation.failure_detection_rate * 100).toFixed(0) }}%</strong></div></div>
        <p v-if="!agentRuns.length" class="muted">{{ t('noQuotes') }}</p>
        <div v-for="run in agentRuns" :key="run.run_id" class="run-card"><div class="run-header"><strong>Run {{ run.run_id }}</strong><span class="muted">{{ run.inquiry_text }}</span></div><div class="run-steps"><div v-for="step in run.steps" :key="step.name" class="trace-item" :class="step.status === 'complete' ? 'done' : 'current'"><span>{{ step.status === 'complete' ? '✓' : '!' }}</span><div><strong>{{ step.name }}</strong><small>{{ step.status === 'complete' ? t('complete') : t('waiting') }}</small></div></div></div></div>
      </section>
      <section v-else-if="activeNav === 'products'" class="panel quotes-page">
        <div class="panel-header"><div><h2>{{ t('products') }}</h2><p>Browse the Nova Outdoor product catalog.</p></div><button class="secondary-button" @click="loadProducts">{{ t('refresh') }}</button></div>
        <div class="search-row"><input v-model="search" placeholder="Search products or SKU" @keyup.enter="loadProducts" /><button class="secondary-button" @click="loadProducts">{{ t('search') }}</button></div>
        <div class="catalog-grid"><button v-for="product in products" :key="product.sku" class="catalog-card" :class="{ selected: selectedProduct?.sku === product.sku }" @click="selectedProduct = product"><div class="product-icon">◒</div><strong>{{ product.name }}</strong><span>{{ product.category }}</span><small>{{ product.sku }}</small><b>${{ product.unit_price_usd.toFixed(2) }} / {{ t('unit') }}</b></button></div>
        <div v-if="selectedProduct" class="product-detail"><div><span class="step">DETAIL</span><h3>{{ selectedProduct.name }}</h3><p>{{ selectedProduct.description }}</p></div><div class="detail-grid"><span><small>SKU</small><strong>{{ selectedProduct.sku }}</strong></span><span><small>MATERIAL</small><strong>{{ selectedProduct.material }}</strong></span><span><small>MOQ</small><strong>{{ selectedProduct.min_order_quantity }} {{ t('unit') }}</strong></span><span><small>LEAD TIME</small><strong>{{ selectedProduct.lead_time_days }} days</strong></span></div></div>
      </section>
      <section v-else-if="activeNav === 'customers'" class="panel quotes-page">
        <div class="panel-header"><div><h2>Customers</h2><p>Customer profiles identified from sales inquiries.</p></div><button class="secondary-button" @click="loadCustomers">Refresh</button></div>
        <div class="search-row"><input v-model="customerSearch" placeholder="Search company name" @keyup.enter="loadCustomers" /><button class="secondary-button" @click="loadCustomers">Search</button></div>
        <div class="customer-list"><article v-for="customer in customers" :key="customer.id" class="customer-row" :class="{ selected: selectedCustomer?.id === customer.id }" @click="selectedCustomer = customer"><div class="customer-avatar">{{ customer.company_name.slice(0, 2).toUpperCase() }}</div><div class="customer-row-main"><strong>{{ customer.company_name }}</strong><span>{{ customer.contact_name }} · {{ customer.email }}</span></div><span class="customer-country">{{ customer.country }}</span></article></div>
        <div v-if="selectedCustomer" class="product-detail customer-detail"><div><span class="step">DETAIL</span><h3>{{ selectedCustomer.company_name }}</h3><p>{{ selectedCustomer.contact_name }} · {{ selectedCustomer.email }}</p></div><div class="detail-actions"><button class="secondary-button" @click="customerName = selectedCustomer?.company_name || ''; selectNav('inquiryWorkspace')">Use in inquiry</button></div></div>
      </section>
    </main>
  </div>
</template>

<style scoped>
:global(body) { min-width: 0; }
.quotes-page { min-height: 420px; }
.quotes-table-wrap { overflow-x: auto; }
.quotes-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.quotes-table th { color: #8b9995; font-size: 10px; letter-spacing: .08em; text-align: left; padding: 12px 10px; border-bottom: 1px solid #e6ebe9; }
.quotes-table td { padding: 15px 10px; border-bottom: 1px solid #edf1ef; color: #40504f; }
.quotes-table td:nth-child(4) { font-weight: 700; color: #1e5149; }
.table-action { border: 0; border-radius: 5px; background: #e3f4ee; color: #31836f; padding: 6px 8px; font: 600 10px inherit; cursor: pointer; }
.approved-mark { color: #4d9e89; font-weight: 700; }
.run-card { border: 1px solid #e7edeb; border-radius: 9px; padding: 16px; margin-top: 12px; }
.run-header { display: flex; flex-direction: column; gap: 6px; padding-bottom: 10px; border-bottom: 1px solid #edf1ef; }
.run-steps { display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; }
.run-steps .trace-item { padding: 13px 4px 4px; }
.catalog-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.catalog-card { border: 1px solid #e7edeb; background: #fff; border-radius: 9px; padding: 15px; text-align: left; display: flex; flex-direction: column; gap: 7px; cursor: pointer; color: #40504f; }
.catalog-card:hover, .catalog-card.selected { border-color: #65cdb4; box-shadow: 0 5px 16px rgba(55, 135, 116, .1); }
.catalog-card strong { font-size: 12px; color: #263b37; }
.catalog-card span, .catalog-card small { color: #8b9995; font-size: 10px; }
.catalog-card b { color: #31836f; font-size: 13px; margin-top: 4px; }
.product-detail { margin-top: 22px; padding: 18px; background: #f5f8f7; border-radius: 9px; display: flex; justify-content: space-between; gap: 24px; }
.product-detail h3 { margin: 8px 0 5px; font-size: 16px; }
.product-detail p { max-width: 500px; color: #71807c; font-size: 12px; line-height: 1.5; }
.detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px 22px; min-width: 230px; }
.detail-grid span { display: flex; flex-direction: column; gap: 5px; }
.detail-grid small { color: #8b9995; font-size: 9px; letter-spacing: .1em; }
.detail-grid strong { font-size: 11px; }
.customer-summary { display: flex; align-items: center; gap: 12px; padding: 13px; border-radius: 8px; background: #f5f8f7; }
.customer-avatar { display: grid; place-items: center; width: 38px; height: 38px; border-radius: 50%; background: #d9eee8; color: #287b6b; font-size: 11px; font-weight: 800; }
.customer-summary > div:nth-child(2) { flex: 1; display: flex; flex-direction: column; gap: 4px; }
.customer-summary strong { font-size: 13px; }
.customer-summary span { color: #8b9995; font-size: 11px; }
.match-check { color: #3e9a83; font-size: 11px; font-weight: 700; }
.customer-list { display: flex; flex-direction: column; gap: 9px; }
.customer-row { display: flex; align-items: center; gap: 12px; padding: 13px; border: 1px solid #e7edeb; border-radius: 8px; }
.customer-row-main { flex: 1; display: flex; flex-direction: column; gap: 4px; }
.customer-row-main strong { font-size: 13px; }
.customer-row-main span, .customer-country { color: #8b9995; font-size: 11px; }
.customer-row { cursor: pointer; }
.customer-row.selected { border-color: #65cdb4; background: #f5fbf9; }
.customer-input { width: 100%; margin-top: 9px; border: 1px solid #dce4e1; border-radius: 7px; padding: 10px 12px; font: 12px inherit; outline: none; }
.customer-detail { align-items: center; }
.detail-actions { min-width: 120px; }
.global-error { display: flex; justify-content: space-between; align-items: center; gap: 16px; margin-bottom: 16px; padding: 11px 14px; border: 1px solid #f0c9c4; border-radius: 8px; background: #fff2f0; color: #a34e47; font-size: 12px; }
.global-error button { border: 0; background: transparent; color: #a34e47; font-size: 18px; cursor: pointer; }
.global-loading { display: inline-flex; align-items: center; gap: 8px; margin-bottom: 14px; color: #4b9f8b; font-size: 11px; }
.spinner { width: 13px; height: 13px; border: 2px solid #d3eee6; border-top-color: #4fa892; border-radius: 50%; animation: spin .8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.metrics-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 18px; }
.metrics-grid div { padding: 13px; background: #f5f8f7; border-radius: 8px; display: flex; flex-direction: column; gap: 6px; }
.metrics-grid small { color: #8b9995; font-size: 9px; letter-spacing: .08em; }
.metrics-grid strong { color: #287b6b; font-size: 20px; }
@media (max-width: 900px) {
  body { min-width: 0; }
  .app-shell { display: block; }
  .sidebar { width: 100%; padding: 14px 18px; display: block; }
  .workspace-label, .sidebar-footer { display: none; }
  .sidebar nav { display: flex; gap: 4px; margin-top: 14px; overflow-x: auto; }
  .nav-item { width: auto; white-space: nowrap; padding: 9px 11px; }
  .main-content { padding: 24px 18px 40px; }
  .topbar { align-items: flex-start; gap: 12px; }
  .user-chip > span:not(.avatar) { display: none; }
  .workspace-grid { grid-template-columns: 1fr; }
  .right-column { display: flex; }
  .catalog-grid { grid-template-columns: repeat(2, 1fr); }
  .product-detail { flex-direction: column; }
  .run-steps { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 560px) {
  .main-content { padding: 18px 12px 30px; }
  h1 { font-size: 23px; }
  .topbar { flex-direction: column; margin-bottom: 22px; }
  .user-chip { align-self: stretch; justify-content: flex-end; }
  .panel { padding: 17px; }
  .requirement-grid, .quote-summary { grid-template-columns: 1fr; }
  .catalog-grid { grid-template-columns: 1fr; }
  .customer-summary { align-items: flex-start; flex-wrap: wrap; }
  .match-check { width: 100%; margin-left: 50px; }
  .quotes-table { min-width: 620px; }
  .run-steps { grid-template-columns: 1fr; }
}
</style>
