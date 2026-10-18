<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { approveQuote as approveQuoteApi, cancelQuote as cancelQuoteApi, createCustomer, createProduct, createUser, deleteCustomer, deleteProduct, fetchAgentRuns, fetchAIDiagnostics, fetchAIProviders, fetchAISettings, fetchAuthStatus, fetchCustomerQuotes, fetchCustomers, fetchEmbeddingJob, fetchEmbeddingJobs, fetchEmbeddingSettings, fetchEvaluation, fetchProductInventoryMovements, fetchQuoteDetail, fetchQuotes, fetchRagEvaluationHistory, fetchUsers, getAuthRole, getAuthToken, login, logout as logoutSession, runInquiryWorkflow, runRagEvaluation, runRagPlayground, searchProducts, setAIProvider, suggestProductTags, switchEmbeddingProfile, testAIConnection, updateAISettings, updateCustomer, updateProduct, updateProductInventory, updateUser } from './api'
import type { AgentRun, AIDiagnostics, AIProviderId, AISettings, CustomerRecord, EmbeddingSettings, EvaluationMetrics, InventoryMovement, QuoteDetail, QuoteRecord, RagEvaluationMetrics, RagPlaygroundResult, UserRecord } from './api'
import type { Product, QuoteDraft } from './types'

const inquiry = ref('We need 120 aluminum outdoor chairs for a hotel project in Germany.')
const search = ref('')
const includeInactiveProducts = ref(false)
const products = ref<Product[]>([])
const loading = ref(false)
const error = ref('')
const workflowResult = ref<Awaited<ReturnType<typeof runInquiryWorkflow>> | null>(null)
const quotes = ref<QuoteRecord[]>([])
const quotesLoading = ref(false)
const quoteDetail = ref<QuoteDetail | null>(null)
const quoteDetailLoading = ref(false)
const agentRuns = ref<AgentRun[]>([])
const evaluation = ref<EvaluationMetrics | null>(null)
const ragEvaluation = ref<RagEvaluationMetrics | null>(null)
const ragEvaluationMode = ref<RagEvaluationMetrics['mode']>('semantic')
const ragEvaluationLoading = ref(false)
const ragEvaluationHistory = ref<RagEvaluationMetrics[]>([])
const ragHistoryFilter = ref<'all' | 'rules' | 'semantic'>('all')
const ragPlaygroundInquiry = ref('We need 50 weatherproof seats for a hotel project in China.')
const ragPlaygroundMode = ref<'rules' | 'semantic'>('semantic')
const ragPlaygroundTopK = ref(5)
const ragPlaygroundThreshold = ref(0.45)
const ragPlaygroundLoading = ref(false)
const ragPlaygroundResult = ref<RagPlaygroundResult | null>(null)
const customers = ref<CustomerRecord[]>([])
const customerSearch = ref('')
const selectedCustomer = ref<CustomerRecord | null>(null)
const customerQuotes = ref<Awaited<ReturnType<typeof fetchCustomerQuotes>>>([])
const customerFormOpen = ref(false)
const customerSaving = ref(false)
const customerDeleting = ref(false)
const editingCustomerId = ref<number | null>(null)
const customerForm = ref({ company_name: '', contact_name: '', country: '', email: '' })
const customerName = ref('')
const selectedProduct = ref<Product | null>(null)
const inventoryMovements = ref<InventoryMovement[]>([])
const inventoryMovementFilter = ref<'all' | InventoryMovement['movement_type']>('all')
const inventoryQuoteFilter = ref('')
const selectedCandidateSku = ref('')
const productEditOpen = ref(false)
const productCreateOpen = ref(false)
const tagSuggestions = ref<string[]>([])
const productSaving = ref(false)
const productCreating = ref(false)
const productTagLoading = ref(false)
const productDeleting = ref(false)
const applyingTags = ref(false)
const productEdit = ref({ material: '', colors: '', match_tags: '', min_order_quantity: 1, lead_time_days: 1, unit_price_usd: 0, on_hand_quantity: 0, inventory_reason: 'manual adjustment', is_active: true })
const productCreate = ref({ sku: '', name: '', category: '', description: '', material: '', colors: '', match_tags: '', min_order_quantity: 1, lead_time_days: 1, unit_price_usd: 0, is_active: true })
const locale = ref<'zh' | 'en' | 'it'>('zh')
const aiProvider = ref<AIProviderId>('rules')
const aiProviderOptions = ref<{ id: AIProviderId; name: string; model?: string; available: boolean }[]>([])
const aiProviderLoading = ref(false)
const aiSettings = ref<AISettings | null>(null)
const aiDiagnostics = ref<AIDiagnostics | null>(null)
const aiDiagnosticsLoading = ref(false)
const aiConfigProvider = ref<AIProviderId>('ollama')
const aiConfigForm = ref({ base_url: '', model: '', timeout_seconds: 30, api_key: '' })
const aiConfigSaving = ref(false)
const aiTestLoading = ref(false)
const aiTestStatus = ref('')
const embeddingSettings = ref<EmbeddingSettings | null>(null)
const embeddingLoading = ref(false)
const embeddingStatus = ref('')
const embeddingJobs = ref<Awaited<ReturnType<typeof fetchEmbeddingJobs>>>({ items: [], total: 0, limit: 6, offset: 0 })
const embeddingJobPage = ref(0)
const embeddingJobPageSize = 6
const approvalLoading = ref(false)
const cancelLoading = ref(false)
const operatorId = 'jordan-davis'
const authEnabled = ref(false)
const authReady = ref(false)
const authToken = ref(getAuthToken())
const authLoading = ref(false)
const authError = ref('')
const loginForm = ref({ username: '', password: '' })
const authRole = ref<UserRecord['role'] | ''>(getAuthRole())
const canManageCatalog = computed(() => !authEnabled.value || authRole.value === 'admin' || authRole.value === 'approver')
const users = ref<UserRecord[]>([])
const usersLoading = ref(false)
const userSaving = ref(false)
const userFormOpen = ref(false)
const userForm = ref({ username: '', password: '', role: 'viewer' as UserRecord['role'] })
const passwordEditingUserId = ref<number | null>(null)
const passwordSaving = ref(false)
const passwordForm = ref({ password: '', confirm: '' })
const userError = ref('')
const aiStatus = ref('idle')
const quote = ref<QuoteDraft>({
  sku: '—',
  quantity: 120,
  unitPrice: 0,
  total: 0,
  status: 'pending_selection',
})

const navKeys = ['inquiryWorkspace', 'products', 'quotes', 'agentTrace', 'ragPlayground', 'customers', 'aiSettings', 'users'] as const
const initialNav = window.location.hash.slice(1) as (typeof navKeys)[number]
const activeNav = ref<(typeof navKeys)[number]>(navKeys.includes(initialNav) ? initialNav : 'inquiryWorkspace')
const translations = {
  zh: { inquiryWorkspace: '询盘工作台', products: '产品库', quotes: '报价单', agentTrace: 'Agent 追踪', ragPlayground: 'RAG 实验室', aiSettings: 'AI 配置', salesOps: '销售运营', inquiryTitle: '询盘工作台', inquiry: '客户询盘', inquiryHint: '粘贴客户询盘，开始工作流。', new: '新建', detected: '已识别英语', edited: '刚刚编辑', analyze: '运行分析', requirements: '提取的需求', requirementsHint: '从客户消息中结构化提取。', complete: '已完成', quantity: '数量', destination: '目的地', project: '项目类型', signals: '产品型号', hotel: '酒店项目', matches: '产品匹配', matchesHint: '从产品知识库检索。', found: '个结果', search: '搜索', loading: '正在加载产品目录…', quote: '报价草稿', quoteHint: '选择产品后生成正式报价。', selected: '已选产品', unitPrice: '单价', discount: '批量折扣', total: '预计总价', approval: '需要人工审批', approvalHint: '折扣报价发送前必须审核。', selectProduct: '请先选择产品', selectProductHint: '选择产品后才会生成报价单。', approved: '报价已批准', approve: '批准报价', activity: 'Agent 活动', activityHint: '透明的工作流追踪。', operational: '系统运行正常', demo: '演示工作区', parsed: '询盘已解析', searched: '产品知识已搜索', checked: '库存与价格已检查', waiting: '等待人工审批', next: '需要下一步操作', live: '实时', unit: '件', projectHotel: '酒店项目', aluminumChair: '铝制 · 户外椅', english: '中文', quoteReview: '报价审核', customer: '客户', sku: 'SKU', status: '状态', action: '操作', refresh: '刷新', noQuotes: '暂无报价', reviewHint: '查看已生成的客户报价。' },
  en: { inquiryWorkspace: 'Inquiry Workspace', products: 'Products', quotes: 'Quotes', agentTrace: 'Agent Trace', ragPlayground: 'RAG Playground', aiSettings: 'AI Settings', salesOps: 'SALES OPERATIONS', inquiryTitle: 'Inquiry workspace', inquiry: 'Customer inquiry', inquiryHint: 'Paste an incoming inquiry to start the workflow.', new: 'NEW', detected: 'English detected', edited: 'Last edited just now', analyze: 'Run analysis', requirements: 'Extracted requirements', requirementsHint: 'Structured from the customer message.', complete: 'COMPLETE', quantity: 'QUANTITY', destination: 'DESTINATION', project: 'PROJECT TYPE', signals: 'PRODUCT SIGNALS', hotel: 'Hotel project', matches: 'Product matches', matchesHint: 'Retrieved from the product knowledge base.', found: 'FOUND', search: 'Search', loading: 'Loading product catalog…', quote: 'Quote draft', quoteHint: 'Select a product to generate the formal quote.', selected: 'SELECTED PRODUCT', unitPrice: 'Unit price', discount: 'Volume discount', total: 'Estimated total', approval: 'Human approval required', approvalHint: 'Discounted quote must be reviewed before sending.', selectProduct: 'Select a product first', selectProductHint: 'A quote is generated only after product selection.', approved: 'Quote approved', approve: 'Approve quote', activity: 'Agent activity', activityHint: 'Transparent workflow trace.', operational: 'System operational', demo: 'Demo workspace', parsed: 'Inquiry parsed', searched: 'Product knowledge searched', checked: 'Inventory and pricing checked', waiting: 'Awaiting human approval', next: 'Next action required', live: 'LIVE', unit: 'units', projectHotel: 'Hotel project', aluminumChair: 'Aluminum · Outdoor chair', english: 'English', quoteReview: 'Quote review', customer: 'Customer', sku: 'SKU', status: 'Status', action: 'Action', refresh: 'Refresh', noQuotes: 'No quotes yet', reviewHint: 'Review previously generated customer quotations.' },
  it: { inquiryWorkspace: 'Area richieste', products: 'Prodotti', quotes: 'Preventivi', agentTrace: 'Traccia Agent', ragPlayground: 'Laboratorio RAG', aiSettings: 'Configurazione AI', salesOps: 'OPERAZIONI VENDITE', inquiryTitle: 'Area richieste', inquiry: 'Richiesta cliente', inquiryHint: 'Incolla una richiesta per avviare il flusso.', new: 'NUOVA', detected: 'Inglese rilevato', edited: 'Modificato ora', analyze: 'Avvia analisi', requirements: 'Requisiti estratti', requirementsHint: 'Strutturati dal messaggio del cliente.', complete: 'COMPLETATO', quantity: 'QUANTITÀ', destination: 'DESTINAZIONE', project: 'TIPO PROGETTO', signals: 'SEGNALI PRODOTTO', hotel: 'Progetto alberghiero', matches: 'Prodotti compatibili', matchesHint: 'Recuperati dalla knowledge base prodotti.', found: 'TROVATI', search: 'Cerca', loading: 'Caricamento prodotti…', quote: 'Bozza preventivo', quoteHint: 'Seleziona un prodotto per generare il preventivo.', selected: 'PRODOTTO SELEZIONATO', unitPrice: 'Prezzo unitario', discount: 'Sconto volume', total: 'Totale stimato', approval: 'Approvazione richiesta', approvalHint: 'Il preventivo scontato deve essere approvato.', selectProduct: 'Seleziona prima un prodotto', selectProductHint: 'Il preventivo viene generato dopo la selezione.', approved: 'Preventivo approvato', approve: 'Approva preventivo', activity: 'Attività Agent', activityHint: 'Traccia trasparente del flusso.', operational: 'Sistema operativo', demo: 'Area demo', parsed: 'Richiesta analizzata', searched: 'Ricerca prodotti completata', checked: 'Scorte e prezzi verificati', waiting: 'In attesa di approvazione', next: 'Azione richiesta', live: 'LIVE', unit: 'unità', projectHotel: 'Progetto alberghiero', aluminumChair: 'Alluminio · Sedia da esterno', english: 'Italiano', quoteReview: 'Revisione preventivi', customer: 'Cliente', sku: 'SKU', status: 'Stato', action: 'Azione', refresh: 'Aggiorna', noQuotes: 'Nessun preventivo', reviewHint: 'Rivedi i preventivi generati.' },
} as const
const t = (key: keyof typeof translations.en) => translations[locale.value][key]
const navItems = computed(() => navKeys.filter((key) => (key !== 'users' || (authEnabled.value && authRole.value === 'admin')) && (key !== 'aiSettings' || !authEnabled.value || authRole.value === 'admin')).map((key) => ({ key, label: key === 'customers' ? (locale.value === 'zh' ? '客户' : locale.value === 'it' ? 'Clienti' : 'Customers') : key === 'users' ? (locale.value === 'zh' ? '用户管理' : locale.value === 'it' ? 'Utenti' : 'Users') : t(key) })))
const customerLabels = computed(() => ({
  title: locale.value === 'zh' ? '客户识别' : locale.value === 'it' ? 'Identificazione cliente' : 'Customer match',
  hint: locale.value === 'zh' ? '从询盘内容中识别。' : locale.value === 'it' ? 'Identificato dal contesto della richiesta.' : 'Identified from the inquiry context.',
  existing: locale.value === 'zh' ? '已有客户' : locale.value === 'it' ? 'ESISTENTE' : 'EXISTING',
  newCustomer: locale.value === 'zh' ? '新客户' : locale.value === 'it' ? 'NUOVO' : 'NEW',
  matched: locale.value === 'zh' ? '已匹配' : locale.value === 'it' ? 'Abbinato' : 'Matched',
  create: locale.value === 'zh' ? '创建档案' : locale.value === 'it' ? 'Crea profilo' : 'Create profile',
  unknownCountry: locale.value === 'zh' ? '未识别国家' : locale.value === 'it' ? 'Paese non identificato' : 'Country not identified',
  pageTitle: locale.value === 'zh' ? '客户' : locale.value === 'it' ? 'Clienti' : 'Customers',
  pageHint: locale.value === 'zh' ? '管理销售询盘中的客户档案。' : locale.value === 'it' ? 'Gestisci i profili cliente dalle richieste.' : 'Manage customer profiles from sales inquiries.',
  companyPlaceholder: locale.value === 'zh' ? '搜索公司名称' : locale.value === 'it' ? 'Cerca nome azienda' : 'Search company name',
  createCustomerLabel: locale.value === 'zh' ? '新建客户' : locale.value === 'it' ? 'Nuovo cliente' : 'New customer',
  editTitle: locale.value === 'zh' ? '编辑客户' : locale.value === 'it' ? 'Modifica cliente' : 'Edit customer',
  company: locale.value === 'zh' ? '公司名称' : locale.value === 'it' ? 'Nome azienda' : 'Company name',
  contact: locale.value === 'zh' ? '联系人' : locale.value === 'it' ? 'Referente' : 'Contact name',
  country: locale.value === 'zh' ? '国家' : locale.value === 'it' ? 'Paese' : 'Country',
  email: locale.value === 'zh' ? '邮箱' : locale.value === 'it' ? 'Email' : 'Email',
  deleteConfirm: locale.value === 'zh' ? '确定停用该客户？' : locale.value === 'it' ? 'Disattivare questo cliente?' : 'Deactivate this customer?',
}))
const productLabels = computed(() => locale.value === 'zh'
  ? { browse: '浏览产品目录。', newProduct: '新建产品', searchPlaceholder: '搜索产品或 SKU', showInactive: '显示已停用产品', inactive: '已停用', detail: '详情', edit: '编辑产品', activate: '启用产品', suggest: '生成 AI 标签', apply: '应用建议', deactivate: '停用', currentTags: '当前标签', none: '无', newTitle: '新建产品', save: '保存', cancel: '取消', sku: 'SKU', name: '产品名称', category: '产品类别', description: '产品描述', material: '材质', colors: '颜色', tags: 'AI 匹配标签（逗号分隔）', moq: '最小起订量', lead: '交期天数', price: '美元单价', inventory: '现有库存', reason: '库存调整原因', active: '启用产品' }
  : locale.value === 'it'
    ? { browse: 'Sfoglia il catalogo prodotti.', newProduct: 'Nuovo prodotto', searchPlaceholder: 'Cerca prodotto o SKU', showInactive: 'Mostra prodotti disattivati', inactive: 'Disattivato', detail: 'DETTAGLI', edit: 'Modifica prodotto', activate: 'Attiva prodotto', suggest: 'Genera tag AI', apply: 'Applica suggerimenti', deactivate: 'Disattiva', currentTags: 'Tag attuali', none: 'Nessuno', newTitle: 'Nuovo prodotto', save: 'Salva', cancel: 'Annulla', sku: 'SKU', name: 'Nome prodotto', category: 'Categoria', description: 'Descrizione', material: 'Materiale', colors: 'Colori', tags: 'Tag AI (separati da virgole)', moq: 'Quantità minima', lead: 'Giorni di consegna', price: 'Prezzo unitario USD', inventory: 'Scorte disponibili', reason: 'Motivo modifica scorte', active: 'Prodotto attivo' }
    : { browse: 'Browse the Nova Outdoor product catalog.', newProduct: 'New product', searchPlaceholder: 'Search product or SKU', showInactive: 'Show inactive products', inactive: 'Inactive', detail: 'DETAIL', edit: 'Edit product', activate: 'Activate product', suggest: 'Suggest AI tags', apply: 'Apply suggestions', deactivate: 'Deactivate', currentTags: 'Current tags', none: 'None', newTitle: 'New product', save: 'Save', cancel: 'Cancel', sku: 'SKU', name: 'Product name', category: 'Category', description: 'Description', material: 'Material', colors: 'Colors', tags: 'AI match tags (comma separated)', moq: 'Minimum order quantity', lead: 'Lead time days', price: 'Unit price USD', inventory: 'On-hand inventory', reason: 'Inventory adjustment reason', active: 'Active product' })
const candidateLabels = computed(() => locale.value === 'zh'
  ? { title: '候选产品排序', available: '可用', insufficient: '库存不足', use: '按此产品报价', unavailable: '不可用', partial: '部分匹配' }
  : locale.value === 'it'
    ? { title: 'Candidati classificati', available: 'disponibili', insufficient: 'Scorte insufficienti', use: 'Usa per preventivo', unavailable: 'Non disponibile', partial: 'Corrispondenza parziale' }
    : { title: 'Ranked candidates', available: 'available', insufficient: 'Insufficient inventory', use: 'Use for quote', unavailable: 'Unavailable', partial: 'Partial match' })
const quoteActionLabels = computed(() => locale.value === 'zh'
  ? { cancel: '取消报价', cancelled: '报价已取消' }
  : locale.value === 'it'
    ? { cancel: 'Annulla preventivo', cancelled: 'Preventivo annullato' }
    : { cancel: 'Cancel quote', cancelled: 'Quote cancelled' })
const filteredInventoryMovements = computed(() => inventoryMovements.value.filter((item) => {
  const typeMatches = inventoryMovementFilter.value === 'all' || item.movement_type === inventoryMovementFilter.value
  const quoteMatches = !inventoryQuoteFilter.value.trim() || String(item.quote_id ?? '').includes(inventoryQuoteFilter.value.trim())
  return typeMatches && quoteMatches
}))
const formattedTotal = computed(() => `$${quote.value.total.toLocaleString('en-US', { minimumFractionDigits: 2 })}`)
const isBusy = computed(() => loading.value || quotesLoading.value)
const productMatches = computed(() => new Map((workflowResult.value?.product_matches ?? []).map((match) => [match.sku, match])))
const productBySku = computed(() => new Map(products.value.map((product) => [product.sku, product])))
const filteredRagHistory = computed(() => ragEvaluationHistory.value.filter((run) => ragHistoryFilter.value === 'all' || run.mode === ragHistoryFilter.value))
const ragTrendRuns = computed(() => [...filteredRagHistory.value].filter((run) => run.created_at).slice(0, 12).reverse())
const trendX = (index: number) => ragTrendRuns.value.length <= 1 ? 300 : 24 + (index * 552) / (ragTrendRuns.value.length - 1)
const trendY = (value: number) => 156 - Math.max(0, Math.min(1, value)) * 132
const trendPoints = (metric: 'top1_recall' | 'top3_recall' | 'mrr') => ragTrendRuns.value.map((run, index) => `${trendX(index)},${trendY(run[metric])}`).join(' ')
function selectCandidate(sku: string) {
  selectedCandidateSku.value = selectedCandidateSku.value === sku ? '' : sku
}
const aiStatusLabel = computed(() => {
  if (aiStatus.value === 'running') return locale.value === 'zh' ? 'AI 正在分析…' : locale.value === 'it' ? 'Analisi AI in corso…' : 'AI is analyzing…'
  if (aiStatus.value === 'ollama') return locale.value === 'zh' ? '已使用本地 Qwen' : locale.value === 'it' ? 'Qwen locale utilizzato' : 'Local Qwen used'
  if (aiStatus.value === 'online') return locale.value === 'zh' ? '已使用在线模型 API' : locale.value === 'it' ? 'API modello online utilizzata' : 'Online model API used'
  if (aiStatus.value === 'fallback') return locale.value === 'zh' ? '已回退到规则引擎' : locale.value === 'it' ? 'Fallback al motore regole' : 'Fell back to rule engine'
  if (aiStatus.value === 'error') return locale.value === 'zh' ? 'AI 分析失败' : locale.value === 'it' ? 'Analisi AI fallita' : 'AI analysis failed'
  return ''
})
function aiProviderLabel(provider: AIProviderId): string {
  if (provider === 'rules') return locale.value === 'zh' ? '规则引擎' : locale.value === 'it' ? 'Motore regole' : 'Rule engine'
  if (provider === 'ollama') return 'Ollama / Qwen'
  if (provider === 'deepseek') return 'DeepSeek'
  if (provider === 'kimi') return 'Kimi / Moonshot'
  return locale.value === 'zh' ? '在线模型 API' : locale.value === 'it' ? 'API modello online' : 'Online model API'
}

function updateAiStatus(provider: string) {
  aiStatus.value = provider === 'ollama' ? 'ollama' : ['openai_compatible', 'deepseek', 'kimi'].includes(provider) ? 'online' : 'fallback'
}

async function switchAIProvider(provider: AIProviderId) {
  aiProviderLoading.value = true
  try { aiProvider.value = (await setAIProvider(provider)).active } catch (err) { error.value = err instanceof Error ? err.message : 'Unable to switch AI provider' } finally { aiProviderLoading.value = false }
}

function selectAIConfigProvider(provider: AIProviderId) {
  aiConfigProvider.value = provider
  const config = aiSettings.value?.providers.find((item) => item.id === provider)
  aiConfigForm.value = {
    base_url: config?.base_url ?? '',
    model: config?.model ?? '',
    timeout_seconds: config?.timeout_seconds ?? 30,
    api_key: '',
  }
  aiTestStatus.value = ''
}

async function loadAISettings() {
  try {
    const [result, diagnostics] = await Promise.all([fetchAISettings(), fetchAIDiagnostics()])
    aiSettings.value = result
    aiDiagnostics.value = diagnostics
    aiProvider.value = result.active
    aiProviderOptions.value = result.providers.map(({ id, name, model, available }) => ({ id, name, model, available }))
    if (!result.providers.some((item) => item.id === aiConfigProvider.value)) aiConfigProvider.value = result.active
    selectAIConfigProvider(aiConfigProvider.value)
  } catch (err) { error.value = err instanceof Error ? err.message : 'Unable to load AI settings' }
}

async function loadAIDiagnostics() {
  aiDiagnosticsLoading.value = true
  try { aiDiagnostics.value = await fetchAIDiagnostics() } catch (err) { error.value = err instanceof Error ? err.message : 'Unable to load AI diagnostics' } finally { aiDiagnosticsLoading.value = false }
}

async function saveAISettings() {
  aiConfigSaving.value = true
  error.value = ''
  try {
    await updateAISettings({ provider: aiConfigProvider.value, base_url: aiConfigForm.value.base_url, model: aiConfigForm.value.model, timeout_seconds: aiConfigForm.value.timeout_seconds, ...(aiConfigForm.value.api_key ? { api_key: aiConfigForm.value.api_key } : {}) })
    aiConfigForm.value.api_key = ''
    await loadAISettings()
  } catch (err) { error.value = err instanceof Error ? err.message : 'Unable to save AI settings' } finally { aiConfigSaving.value = false }
}

async function testSelectedAIProvider() {
  aiTestLoading.value = true
  aiTestStatus.value = locale.value === 'zh' ? '正在测试连接…' : locale.value === 'it' ? 'Test della connessione…' : 'Testing connection…'
  try {
    const result = await testAIConnection(aiConfigProvider.value)
    aiTestStatus.value = result.success
      ? `${locale.value === 'zh' ? '连接成功' : locale.value === 'it' ? 'Connessione riuscita' : 'Connection succeeded'} · ${result.model || aiProviderLabel(result.provider)} · ${result.latency_ms} ms`
      : result.message
  } catch (err) { aiTestStatus.value = err instanceof Error ? err.message : 'Unable to test AI connection' } finally { aiTestLoading.value = false }
}

async function switchEmbedding(profileId: string) {
  if (!embeddingSettings.value || profileId === embeddingSettings.value.active.id) return
  embeddingLoading.value = true
  embeddingStatus.value = locale.value === 'zh' ? '正在下载模型并重建产品索引，请稍候…' : locale.value === 'it' ? 'Download del modello e ricostruzione dell’indice…' : 'Downloading the model and rebuilding the product index…'
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), 120000)
  try {
    let result = await switchEmbeddingProfile(profileId, controller.signal)
    while (result.status === 'queued' || result.status === 'running') {
      await new Promise((resolve) => window.setTimeout(resolve, 1000))
      result = await fetchEmbeddingJob(result.job_id, controller.signal)
      if (result.status === 'running' && result.total_products !== null) {
        embeddingStatus.value = locale.value === 'zh' ? `正在重建索引：${result.processed_products}/${result.total_products} 个产品（${result.progress_percent}%）` : locale.value === 'it' ? `Indice in ricostruzione: ${result.processed_products}/${result.total_products} prodotti (${result.progress_percent}%)` : `Rebuilding index: ${result.processed_products}/${result.total_products} products (${result.progress_percent}%)`
      }
    }
    if (result.status === 'failed') throw new Error(result.error || 'Embedding profile rebuild failed')
    embeddingSettings.value.active = result.profile
    embeddingStatus.value = locale.value === 'zh' ? `切换完成，已索引 ${result.indexed_products ?? 0} 个产品。` : locale.value === 'it' ? `Cambio completato: ${result.indexed_products ?? 0} prodotti indicizzati.` : `Switched successfully; ${result.indexed_products ?? 0} products indexed.`
    await loadRagEvaluation()
    embeddingJobs.value = await fetchEmbeddingJobs(embeddingJobPageSize, embeddingJobPage.value * embeddingJobPageSize)
  } catch (err) {
    const message = err instanceof DOMException && err.name === 'AbortError' ? (locale.value === 'zh' ? '模型下载或索引重建超时，请检查 Hugging Face 网络后重试。' : locale.value === 'it' ? 'Timeout durante il download o la ricostruzione; controlla la rete Hugging Face.' : 'Model download or index rebuild timed out; check Hugging Face connectivity and retry.') : err instanceof Error ? err.message : 'Unable to switch embedding profile'
    embeddingStatus.value = message
    error.value = message
  } finally { window.clearTimeout(timeout); embeddingLoading.value = false }
}

function switchEmbeddingFromEvent(event: Event) {
  const target = event.target as HTMLSelectElement
  void switchEmbedding(target.value)
}

async function loadProducts() {
  loading.value = true
  error.value = ''
  try {
    products.value = await searchProducts(search.value, includeInactiveProducts.value)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Unable to load products'
  } finally {
    loading.value = false
  }
}

function openProductEdit(product: Product) {
  selectedProduct.value = product
  productEdit.value = { material: product.material, colors: product.colors, match_tags: product.match_tags, min_order_quantity: product.min_order_quantity, lead_time_days: product.lead_time_days, unit_price_usd: product.unit_price_usd, on_hand_quantity: product.on_hand_quantity ?? 0, inventory_reason: 'manual adjustment', is_active: product.is_active }
  productEditOpen.value = true
}

async function selectProduct(product: Product) {
  if (selectedProduct.value?.sku === product.sku) {
    selectedProduct.value = null
    return
  }
  selectedProduct.value = product
  inventoryMovementFilter.value = 'all'
  inventoryQuoteFilter.value = ''
  try {
    inventoryMovements.value = await fetchProductInventoryMovements(product.sku)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Unable to load inventory history'
  }
}

async function saveProduct() {
  if (!selectedProduct.value) return
  productSaving.value = true
  error.value = ''
  try {
    const updated = await updateProduct(selectedProduct.value.sku, productEdit.value)
    const inventory = await updateProductInventory(selectedProduct.value.sku, productEdit.value.on_hand_quantity, productEdit.value.inventory_reason)
    selectedProduct.value = { ...selectedProduct.value, ...updated, ...inventory }
    products.value = products.value.map((product) => product.sku === selectedProduct.value?.sku ? selectedProduct.value : product)
    productEditOpen.value = false
  } catch (err) { error.value = err instanceof Error ? err.message : 'Unable to update product' } finally { productSaving.value = false }
}

async function saveNewProduct() {
  productCreating.value = true
  error.value = ''
  try { const created = await createProduct(productCreate.value); products.value = [...products.value, created]; selectedProduct.value = created; productCreateOpen.value = false; productCreate.value = { sku: '', name: '', category: '', description: '', material: '', colors: '', match_tags: '', min_order_quantity: 1, lead_time_days: 1, unit_price_usd: 0, is_active: true } } catch (err) { error.value = err instanceof Error ? err.message : 'Unable to create product' } finally { productCreating.value = false }
}

async function removeProduct(product: Product) {
  if (!window.confirm(`Deactivate ${product.name}?`)) return
  productDeleting.value = true
  error.value = ''
  try { await deleteProduct(product.sku); products.value = products.value.filter((item) => item.sku !== product.sku); selectedProduct.value = null } catch (err) { error.value = err instanceof Error ? err.message : 'Unable to delete product' } finally { productDeleting.value = false }
}

async function activateProduct(product: Product) {
  productSaving.value = true
  error.value = ''
  try {
    const updated = await updateProduct(product.sku, { is_active: true })
    selectedProduct.value = { ...product, ...updated, is_active: true }
    products.value = products.value.map((item) => item.sku === product.sku ? selectedProduct.value as Product : item)
  } catch (err) { error.value = err instanceof Error ? err.message : 'Unable to activate product' } finally { productSaving.value = false }
}

async function generateProductTags(product: Product) {
  productTagLoading.value = true
  error.value = ''
  try { tagSuggestions.value = (await suggestProductTags(product.sku)).suggestions } catch (err) { error.value = err instanceof Error ? err.message : 'Unable to suggest product tags' } finally { productTagLoading.value = false }
}

async function applyProductTags(product: Product) {
  if (!tagSuggestions.value.length) return
  applyingTags.value = true
  try {
    const existing = product.match_tags.split(',').map((tag) => tag.trim()).filter(Boolean)
    const merged = [...new Set([...existing, ...tagSuggestions.value])].join(', ')
    const updated = await updateProduct(product.sku, { match_tags: merged })
    selectedProduct.value = updated
    products.value = products.value.map((item) => item.sku === updated.sku ? updated : item)
    tagSuggestions.value = []
  } catch (err) { error.value = err instanceof Error ? err.message : 'Unable to apply product tags' } finally { applyingTags.value = false }
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
      const [runs, metrics, ragMetrics, history] = await Promise.all([fetchAgentRuns(), fetchEvaluation(), runRagEvaluation(ragEvaluationMode.value), fetchRagEvaluationHistory()])
      agentRuns.value = runs
      evaluation.value = metrics
      ragEvaluation.value = ragMetrics
      ragEvaluationHistory.value = history
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unable to load agent runs'
    }
  }
  if (key === 'products') await loadProducts()
  if (key === 'customers') {
    try { customers.value = await fetchCustomers(customerSearch.value) } catch (err) { error.value = err instanceof Error ? err.message : 'Unable to load customers' }
  }
  if (key === 'users' && authRole.value === 'admin') await loadUsers()
  if (key === 'aiSettings') await loadAISettings()
}

async function runRagPlaygroundQuery() {
  if (!ragPlaygroundInquiry.value.trim()) return
  ragPlaygroundLoading.value = true
  error.value = ''
  try {
    ragPlaygroundResult.value = await runRagPlayground({
      inquiry: ragPlaygroundInquiry.value,
      mode: ragPlaygroundMode.value,
      top_k: ragPlaygroundTopK.value,
      score_threshold: ragPlaygroundThreshold.value,
    })
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Unable to run RAG playground'
  } finally {
    ragPlaygroundLoading.value = false
  }
}

async function loadRagEvaluation() {
  ragEvaluationLoading.value = true
  try {
    const [metrics, history] = await Promise.all([runRagEvaluation(ragEvaluationMode.value), fetchRagEvaluationHistory()])
    ragEvaluation.value = metrics
    ragEvaluationHistory.value = history
  } catch (err) { error.value = err instanceof Error ? err.message : 'Unable to load RAG evaluation metrics' } finally { ragEvaluationLoading.value = false }
}

async function loadUsers() {
  usersLoading.value = true
  userError.value = ''
  try { users.value = await fetchUsers() } catch (err) { userError.value = err instanceof Error ? err.message : 'Unable to load users' } finally { usersLoading.value = false }
}

function openUserForm() {
  userForm.value = { username: '', password: '', role: 'viewer' }
  userFormOpen.value = true
}

async function saveUser() {
  userSaving.value = true
  userError.value = ''
  try {
    const created = await createUser(userForm.value)
    users.value = [...users.value, created].sort((left, right) => left.username.localeCompare(right.username))
    userFormOpen.value = false
  } catch (err) { userError.value = err instanceof Error ? err.message : 'Unable to create user' } finally { userSaving.value = false }
}

async function toggleUser(user: UserRecord) {
  userError.value = ''
  try {
    const updated = await updateUser(user.id, { is_active: !user.is_active })
    users.value = users.value.map((item) => item.id === updated.id ? updated : item)
  } catch (err) { userError.value = err instanceof Error ? err.message : 'Unable to update user' }
}

async function changeUserRole(user: UserRecord, role: UserRecord['role']) {
  userError.value = ''
  try {
    const updated = await updateUser(user.id, { role })
    users.value = users.value.map((item) => item.id === updated.id ? updated : item)
  } catch (err) { userError.value = err instanceof Error ? err.message : 'Unable to update user' }
}

function openPasswordForm(user: UserRecord) {
  passwordEditingUserId.value = user.id
  passwordForm.value = { password: '', confirm: '' }
  userError.value = ''
}

function closePasswordForm() {
  passwordEditingUserId.value = null
  passwordForm.value = { password: '', confirm: '' }
}

async function saveUserPassword(user: UserRecord) {
  userError.value = ''
  if (passwordForm.value.password.length < 8) {
    userError.value = locale.value === 'zh' ? '密码至少需要 8 位。' : locale.value === 'it' ? 'La password deve contenere almeno 8 caratteri.' : 'Password must be at least 8 characters.'
    return
  }
  if (passwordForm.value.password !== passwordForm.value.confirm) {
    userError.value = locale.value === 'zh' ? '两次输入的密码不一致。' : locale.value === 'it' ? 'Le password non coincidono.' : 'Passwords do not match.'
    return
  }
  passwordSaving.value = true
  try {
    await updateUser(user.id, { password: passwordForm.value.password })
    closePasswordForm()
  } catch (err) { userError.value = err instanceof Error ? err.message : 'Unable to update password' } finally { passwordSaving.value = false }
}

async function selectQuote(record: QuoteRecord) {
  if (quoteDetail.value?.id === record.id && !quoteDetailLoading.value) {
    quoteDetail.value = null
    return
  }
  quoteDetailLoading.value = true
  error.value = ''
  try { quoteDetail.value = await fetchQuoteDetail(record.id) } catch (err) { error.value = err instanceof Error ? err.message : 'Unable to load quote detail' } finally { quoteDetailLoading.value = false }
}

async function loadCustomers() {
  error.value = ''
  try { customers.value = await fetchCustomers(customerSearch.value) } catch (err) { error.value = err instanceof Error ? err.message : 'Unable to load customers' }
}

function openCustomerForm(customer?: CustomerRecord) {
  editingCustomerId.value = customer?.id ?? null
  customerForm.value = customer ? { company_name: customer.company_name, contact_name: customer.contact_name, country: customer.country, email: customer.email } : { company_name: '', contact_name: '', country: '', email: '' }
  customerFormOpen.value = true
}

function createCustomerFromInquiry() {
  const companyName = workflowResult.value?.customer.company_name || ''
  activeNav.value = 'customers'
  window.history.pushState({}, '', '#customers')
  customerFormOpen.value = true
  editingCustomerId.value = null
  customerForm.value = { company_name: companyName, contact_name: '', country: workflowResult.value?.inquiry.destination_country || '', email: '' }
}

async function saveCustomer() {
  customerSaving.value = true
  error.value = ''
  try {
    if (editingCustomerId.value) await updateCustomer(editingCustomerId.value, customerForm.value)
    else await createCustomer(customerForm.value)
    customerFormOpen.value = false
    await loadCustomers()
  } catch (err) { error.value = err instanceof Error ? err.message : 'Unable to save customer' } finally { customerSaving.value = false }
}

async function removeCustomer(customer: CustomerRecord) {
  if (!window.confirm(`${customerLabels.value.deleteConfirm} ${customer.company_name}`)) return
  customerDeleting.value = true
  error.value = ''
  try { await deleteCustomer(customer.id); selectedCustomer.value = null; customerQuotes.value = []; await loadCustomers() } catch (err) { error.value = err instanceof Error ? err.message : 'Unable to delete customer' } finally { customerDeleting.value = false }
}

async function selectCustomer(customer: CustomerRecord) {
  if (selectedCustomer.value?.id === customer.id) {
    selectedCustomer.value = null
    customerQuotes.value = []
    return
  }
  selectedCustomer.value = customer
  customerQuotes.value = []
  try { customerQuotes.value = await fetchCustomerQuotes(customer.id) } catch (err) { error.value = err instanceof Error ? err.message : 'Unable to load customer quotes' }
}

function clearError() {
  error.value = ''
}

async function runWorkflow() {
  loading.value = true
  aiStatus.value = 'running'
  error.value = ''
  try {
    workflowResult.value = await runInquiryWorkflow(inquiry.value, customerName.value)
    updateAiStatus(workflowResult.value.inquiry.ai_provider)
    quote.value = {
      id: workflowResult.value.quote.id ?? undefined,
      sku: workflowResult.value.quote.id ? workflowResult.value.quote.sku : '—',
      quantity: workflowResult.value.quote.quantity,
      unitPrice: workflowResult.value.quote.id ? workflowResult.value.quote.unit_price_usd : 0,
      total: workflowResult.value.quote.id ? workflowResult.value.quote.total_price_usd : 0,
      status: workflowResult.value.quote.status,
    }
    await loadProducts()
  } catch (err) {
    aiStatus.value = 'error'
    error.value = err instanceof TypeError
      ? (locale.value === 'zh' ? '无法连接后端服务，请确认 8000 端口正在运行。' : locale.value === 'it' ? 'Impossibile connettersi al backend: verifica la porta 8000.' : 'Unable to connect to the backend. Check port 8000.')
      : err instanceof Error ? err.message : 'Unable to analyze inquiry'
  } finally {
    loading.value = false
  }
}

async function selectProductForQuote(sku: string) {
  const match = workflowResult.value?.product_matches.find((item) => item.sku === sku)
  if (!match?.inventory_sufficient) return
  loading.value = true
  error.value = ''
  try {
    workflowResult.value = await runInquiryWorkflow(inquiry.value, customerName.value, sku, workflowResult.value?.inquiry)
    quote.value = { id: workflowResult.value.quote.id ?? undefined, sku: workflowResult.value.quote.sku, quantity: workflowResult.value.quote.quantity, unitPrice: workflowResult.value.quote.unit_price_usd, total: workflowResult.value.quote.total_price_usd, status: workflowResult.value.quote.status }
    updateAiStatus(workflowResult.value.inquiry.ai_provider)
    await nextTick()
    document.getElementById('quote-draft-panel')?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  } catch (err) { error.value = err instanceof Error ? err.message : 'Unable to select product' } finally { loading.value = false }
}

async function approveQuote() {
  if (!quote.value.id) return
  approvalLoading.value = true
  error.value = ''
  try {
    await approveQuoteApi(quote.value.id, operatorId)
    quote.value.status = 'approved'
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Unable to approve quote'
  } finally { approvalLoading.value = false }
}

async function approveQuoteRecord(record: QuoteRecord) {
  approvalLoading.value = true
  error.value = ''
  try {
    await approveQuoteApi(record.id, operatorId)
    record.status = 'approved'
    if (quoteDetail.value?.id === record.id) {
      quoteDetail.value.status = 'approved'
      quoteDetail.value.risk.requires_approval = false
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Unable to approve quote'
  } finally { approvalLoading.value = false }
}

function clearCancelledQuoteDraft(quoteId: number) {
  if (quote.value.id !== quoteId) return
  quote.value = {
    id: undefined,
    sku: '—',
    quantity: workflowResult.value?.inquiry.quantity ?? 0,
    unitPrice: 0,
    total: 0,
    status: 'pending_selection',
  }
  selectedCandidateSku.value = ''
}

async function cancelQuoteRecord(record: QuoteRecord) {
  cancelLoading.value = true
  error.value = ''
  try {
    await cancelQuoteApi(record.id, operatorId)
    record.status = 'cancelled'
    if (quoteDetail.value?.id === record.id) quoteDetail.value = await fetchQuoteDetail(record.id)
    clearCancelledQuoteDraft(record.id)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Unable to cancel quote'
  } finally { cancelLoading.value = false }
}

async function signIn() {
  authLoading.value = true
  authError.value = ''
  try {
    const result = await login(loginForm.value.username, loginForm.value.password)
    authToken.value = getAuthToken()
    authRole.value = result.role
    loginForm.value.password = ''
  } catch (err) { authError.value = err instanceof Error ? err.message : 'Unable to sign in' } finally { authLoading.value = false }
}

async function signOut() {
  await logoutSession()
  authToken.value = ''
  authRole.value = ''
}

async function initializeApp() {
  try {
    const status = await fetchAuthStatus()
    authEnabled.value = status.enabled
  } catch {
    authEnabled.value = false
  } finally {
    authReady.value = true
  }
  if (authEnabled.value && !authToken.value) return
  void fetchAISettings().then((status) => { aiSettings.value = status; aiProvider.value = status.active; aiProviderOptions.value = status.providers.map(({ id, name, model, available }) => ({ id, name, model, available })); selectAIConfigProvider(status.active) }).catch(() => fetchAIProviders().then((status) => { aiProvider.value = status.active; aiProviderOptions.value = status.providers }).catch(() => undefined))
  void Promise.all([fetchEmbeddingSettings(), fetchEmbeddingJobs(embeddingJobPageSize, 0)]).then(([status, jobs]) => { embeddingSettings.value = status; embeddingJobs.value = jobs }).catch(() => undefined)
  if (authEnabled.value && authRole.value === 'admin' && activeNav.value === 'users') void loadUsers()
  if (activeNav.value === 'inquiryWorkspace') void loadProducts()
  else void selectNav(activeNav.value)
}

onMounted(() => {
  window.addEventListener('tradepilot-auth-invalid', () => {
    authToken.value = ''
    authRole.value = ''
  })
  window.addEventListener('popstate', () => {
    const key = window.location.hash.slice(1) as (typeof navKeys)[number]
    if (navKeys.includes(key)) void selectNav(key)
  })
  void initializeApp()
})

async function loadEmbeddingJobPage(page: number) {
  const nextPage = Math.max(0, page)
  embeddingJobs.value = await fetchEmbeddingJobs(embeddingJobPageSize, nextPage * embeddingJobPageSize)
  embeddingJobPage.value = nextPage
}
</script>

<template>
  <div class="app-shell">
    <div v-if="authReady && authEnabled && !authToken" class="auth-gate">
      <form class="auth-card" @submit.prevent="signIn">
        <span class="brand-mark">TP</span><h1>TradePilot AI</h1><p>Sign in to approve quotations.</p>
        <input v-model="loginForm.username" autocomplete="username" placeholder="Username" required />
        <input v-model="loginForm.password" autocomplete="current-password" type="password" placeholder="Password" required />
        <p v-if="authError" class="auth-error">{{ authError }}</p>
        <button class="primary-button" :disabled="authLoading">{{ authLoading ? '…' : 'Sign in' }}</button>
      </form>
    </div>
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
      <header class="topbar"><div><p class="eyebrow">{{ t('salesOps') }} / {{ navItems.find((item) => item.key === activeNav)?.label.toUpperCase() }}</p><h1>{{ t('inquiryTitle') }}</h1></div><div class="user-chip"><select v-model="aiProvider" class="language-select" aria-label="AI model" :disabled="aiProviderLoading" @change="switchAIProvider(aiProvider)"><option v-for="provider in aiProviderOptions" :key="provider.id" :value="provider.id" :disabled="!provider.available">{{ aiProviderLabel(provider.id) }}{{ !provider.available && ['openai_compatible', 'deepseek', 'kimi'].includes(provider.id) ? (locale === 'zh' ? '（未配置）' : locale === 'it' ? ' (non configurato)' : ' (not configured)') : '' }}{{ provider.model ? ` · ${provider.model}` : '' }}</option></select><select v-model="locale" class="language-select" aria-label="Language"><option value="zh">中文</option><option value="en">English</option><option value="it">Italiano</option></select><span class="avatar">JD</span><span>Jordan Davis</span><button v-if="authEnabled && authToken" class="logout-button" @click="signOut">Sign out</button><span class="chevron">⌄</span></div></header>

      <section v-if="!['quotes', 'products', 'agentTrace', 'ragPlayground', 'customers', 'aiSettings', 'users'].includes(activeNav)" class="workspace-grid">
        <div class="left-column">
          <section class="panel inquiry-panel">
            <div class="panel-header"><div><span class="step">01</span><div><h2>{{ t('inquiry') }}</h2><p>{{ t('inquiryHint') }}</p></div></div><span class="badge neutral">{{ t('new') }}</span></div>
            <textarea v-model="inquiry" :aria-label="t('inquiry')" />
            <input v-model="customerName" class="customer-input" placeholder="Customer company (optional)" />
            <div class="inquiry-meta"><span>✦ {{ t('detected') }}</span><span>{{ t('edited') }}</span><span v-if="aiStatusLabel" class="ai-status" :class="aiStatus">● {{ aiStatusLabel }}</span></div>
            <button class="primary-button" :disabled="loading" @click="runWorkflow">{{ loading ? '…' : t('analyze') }} <span>→</span></button>
          </section>

          <section class="panel requirements-panel">
            <div class="panel-header"><div><span class="step">02</span><div><h2>{{ t('requirements') }}</h2><p>{{ t('requirementsHint') }}</p></div></div><span class="badge success">{{ t('complete') }}</span></div>
            <div class="requirement-grid"><div><label>{{ t('quantity') }}</label><strong>{{ workflowResult?.inquiry.quantity ?? '—' }} {{ workflowResult ? t('unit') : '' }}</strong></div><div><label>{{ t('destination') }}</label><strong>{{ workflowResult?.inquiry.destination_country ?? '—' }}</strong></div><div><label>{{ t('project') }}</label><strong>{{ workflowResult?.inquiry.project_type ?? '—' }}</strong></div><div><label>{{ t('signals') }}</label><strong>{{ workflowResult?.inquiry.product_keywords.join(' · ') || '—' }}</strong></div></div>
          </section>

          <section v-if="workflowResult" class="panel customer-panel">
            <div class="panel-header"><div><span class="step">02A</span><div><h2>{{ customerLabels.title }}</h2><p>{{ customerLabels.hint }}</p></div></div><span :class="['badge', workflowResult.customer.matched ? 'success' : 'warning']">{{ workflowResult.customer.matched ? customerLabels.existing : customerLabels.newCustomer }}</span></div>
            <div class="customer-summary"><div class="customer-avatar">{{ workflowResult.customer.company_name.slice(0, 2).toUpperCase() || '??' }}</div><div><strong>{{ workflowResult.customer.company_name || customerLabels.newCustomer }}</strong><span>{{ workflowResult.customer.country || customerLabels.unknownCountry }}</span><span v-if="workflowResult.customer.contact_name">{{ workflowResult.customer.contact_name }} · {{ workflowResult.customer.email }}</span></div><button v-if="!workflowResult.customer.matched" class="secondary-button" @click="createCustomerFromInquiry">{{ customerLabels.create }}</button><div v-else class="match-check">✓ {{ customerLabels.matched }}</div></div>
          </section>

          <section class="panel product-panel" @click.self="selectedCandidateSku = ''">
            <div class="panel-header"><div><span class="step">03</span><div><h2>{{ t('matches') }}</h2><p>{{ t('matchesHint') }}</p></div></div><span class="badge success">{{ products.length }} {{ t('found') }}</span></div>
            <div class="search-row"><input v-model="search" placeholder="Search products or SKU" @keyup.enter="loadProducts" /><button class="secondary-button" @click="loadProducts">{{ t('search') }}</button></div>
            <p v-if="loading" class="muted">{{ t('loading') }}</p><p v-else-if="error" class="error-message">{{ error }}</p>
            <div v-else class="product-list"><article v-for="product in products.slice(0, 3)" :key="product.sku" class="product-card" :class="{ selected: selectedCandidateSku === product.sku }" @click="selectCandidate(product.sku)"><div class="product-icon">◒</div><div class="product-info"><strong>{{ product.name }}</strong><span>{{ product.sku }} · {{ product.material }}</span><div v-if="productMatches.get(product.sku)" class="match-explanation"><b>{{ productMatches.get(product.sku)?.score }}% match</b><span>{{ productMatches.get(product.sku)?.reasons.join(' · ') }}</span><em v-if="productMatches.get(product.sku)?.unmet_conditions.length">⚠ {{ productMatches.get(product.sku)?.unmet_conditions.join(' · ') }}</em></div></div><div class="product-price">${{ product.unit_price_usd.toFixed(2) }}<small>/ unit</small></div><div v-if="selectedCandidateSku === product.sku" class="candidate-detail inline" @click.stop><div><span class="step">DETAIL</span><h3>{{ product.name }}</h3><p>{{ product.description }}</p><span class="candidate-tags">{{ product.match_tags || '—' }}</span></div><div class="detail-grid"><span><small>SKU</small><strong>{{ product.sku }}</strong></span><span><small>MATERIAL</small><strong>{{ product.material || '—' }}</strong></span><span><small>COLORS</small><strong>{{ product.colors || '—' }}</strong></span><span><small>MOQ</small><strong>{{ product.min_order_quantity }} {{ t('unit') }}</strong></span><span><small>INVENTORY</small><strong>{{ productMatches.get(product.sku)?.inventory_available ?? '—' }}</strong></span><span><small>LEAD TIME</small><strong>{{ product.lead_time_days }} days</strong></span></div></div></article></div>
            <div v-if="workflowResult?.product_matches.length" class="candidate-list"><h3>{{ candidateLabels.title }} · {{ workflowResult.retrieval_mode === 'semantic' ? (locale === 'zh' ? '语义检索' : locale === 'it' ? 'Ricerca semantica' : 'Semantic search') : workflowResult.retrieval_mode === 'rules_fallback' ? (locale === 'zh' ? '语义服务不可用，已使用规则匹配' : locale === 'it' ? 'Ricerca semantica non disponibile; regole attive' : 'Semantic search unavailable; rules used') : (locale === 'zh' ? '规则匹配' : locale === 'it' ? 'Regole' : 'Rule matching') }} · {{ workflowResult.explanation_mode === 'grounded_ai' ? (locale === 'zh' ? 'AI 有据解释' : locale === 'it' ? 'Spiegazione AI verificata' : 'Grounded AI explanation') : (locale === 'zh' ? '规则解释' : locale === 'it' ? 'Spiegazione basata su regole' : 'Rule explanation') }}</h3><article v-for="match in workflowResult.product_matches" :key="match.sku" class="candidate-card" :class="{ selected: selectedCandidateSku === match.sku }" @click="selectCandidate(match.sku)"><div><strong>{{ match.name }}</strong><span>{{ match.sku }} · {{ match.inventory_sufficient ? `${match.inventory_available} ${candidateLabels.available}` : candidateLabels.insufficient }}</span><small>${{ match.unit_price_usd.toFixed(2) }} · {{ match.lead_time_days }} days</small></div><b>{{ match.score }}%</b><small>{{ match.reasons.join(' · ') || candidateLabels.partial }}<em v-if="match.unmet_conditions.length"> · ⚠ {{ match.unmet_conditions.join(' · ') }}</em></small><button class="table-action" :disabled="loading || !match.inventory_sufficient" @click.stop="selectProductForQuote(match.sku)">{{ match.inventory_sufficient ? candidateLabels.use : candidateLabels.unavailable }}</button><p class="rag-explanation"><strong>{{ workflowResult.explanation_mode === 'grounded_ai' ? 'AI' : 'RULE' }}</strong> {{ match.explanation }}<span v-for="item in match.evidence" :key="item.field" class="evidence-chip">{{ item.field }}: {{ item.value }}</span></p><div v-if="selectedCandidateSku === match.sku && productBySku.get(match.sku)" class="candidate-detail inline" @click.stop><div><span class="step">DETAIL</span><h3>{{ productBySku.get(match.sku)?.name }}</h3><p>{{ productBySku.get(match.sku)?.description }}</p><span class="candidate-tags">{{ productBySku.get(match.sku)?.match_tags || '—' }}</span></div><div class="detail-grid"><span><small>SKU</small><strong>{{ productBySku.get(match.sku)?.sku }}</strong></span><span><small>MATERIAL</small><strong>{{ productBySku.get(match.sku)?.material || '—' }}</strong></span><span><small>COLORS</small><strong>{{ productBySku.get(match.sku)?.colors || '—' }}</strong></span><span><small>MOQ</small><strong>{{ productBySku.get(match.sku)?.min_order_quantity }} {{ t('unit') }}</strong></span><span><small>INVENTORY</small><strong>{{ match.inventory_available }}</strong></span><span><small>LEAD TIME</small><strong>{{ productBySku.get(match.sku)?.lead_time_days }} days</strong></span></div></div></article></div>
          </section>
        </div>

        <div class="right-column">
          <section id="quote-draft-panel" class="panel quote-panel"><div class="panel-header"><div><span class="step">04</span><div><h2>{{ t('quote') }}</h2><p>{{ t('quoteHint') }}</p></div></div><span :class="['badge', quote.status === 'approved' ? 'success' : 'warning']">{{ quote.status.toUpperCase() }}</span></div><div class="quote-summary"><div><span>{{ t('selected') }}</span><strong>{{ quote.sku }}</strong></div><div><span>{{ t('quantity') }}</span><strong>{{ quote.quantity }} {{ t('unit') }}</strong></div></div><div class="price-lines"><div><span>{{ t('unitPrice') }}</span><strong>${{ quote.unitPrice.toFixed(2) }}</strong></div><div><span>{{ t('discount') }}</span><strong class="discount">− 5%</strong></div><div class="total-line"><span>{{ t('total') }}</span><strong>{{ formattedTotal }}</strong></div></div><div v-if="quote.status === 'pending_selection'" class="risk-callout"><span class="risk-icon">!</span><div><strong>{{ t('selectProduct') }}</strong><p>{{ t('selectProductHint') }}</p></div></div><div v-else-if="quote.status !== 'approved'" class="risk-callout"><span class="risk-icon">!</span><div><strong>{{ t('approval') }}</strong><p>{{ t('approvalHint') }}</p></div></div><div v-else class="approved-callout">✓ {{ t('approved') }}</div><button class="approve-button" :disabled="!quote.id || quote.status === 'approved' || approvalLoading" @click="approveQuote">{{ approvalLoading ? '…' : quote.status === 'pending_selection' ? t('selectProduct') : quote.status === 'approved' ? t('approved') : t('approve') }} <span>✓</span></button></section>
        </div>
      </section>
      <section v-else-if="activeNav === 'quotes'" class="panel quotes-page">
        <div class="panel-header"><div><h2>{{ t('quoteReview') }}</h2><p>{{ t('reviewHint') }}</p></div><button class="secondary-button" @click="selectNav('quotes')">{{ t('refresh') }}</button></div>
        <p v-if="quotesLoading" class="muted">{{ t('loading') }}</p>
        <p v-else-if="!quotes.length" class="muted">{{ t('noQuotes') }}</p>
        <div v-else class="quotes-table-wrap"><table class="quotes-table"><thead><tr><th>{{ t('customer') }}</th><th>{{ t('sku') }}</th><th>{{ t('quantity') }}</th><th>{{ t('total') }}</th><th>{{ t('status') }}</th><th>{{ t('action') }}</th></tr></thead><tbody><template v-for="record in quotes" :key="record.id"><tr class="quote-row" @click="selectQuote(record)"><td>{{ record.customer_name || '—' }}</td><td>{{ record.sku }}</td><td>{{ record.quantity }}</td><td>${{ record.total_price_usd.toFixed(2) }}</td><td><span :class="['badge', record.status === 'approved' ? 'success' : record.status === 'cancelled' ? 'cancelled' : 'warning']">{{ record.status.toUpperCase() }}</span></td><td><div v-if="record.status === 'draft'" class="quote-actions"><button class="table-action" :disabled="approvalLoading || cancelLoading" @click.stop="approveQuoteRecord(record)">{{ approvalLoading ? '…' : t('approve') }}</button><button class="table-action cancel-action" :disabled="approvalLoading || cancelLoading" @click.stop="cancelQuoteRecord(record)">{{ cancelLoading ? '…' : quoteActionLabels.cancel }}</button></div><span v-else class="approved-mark">{{ record.status === 'cancelled' ? '—' : '✓' }}</span></td></tr><tr v-if="quoteDetail?.id === record.id" class="quote-detail-row" @click.stop><td colspan="6"><div class="quote-detail-card"><div class="panel-header"><div><span class="step">DETAIL</span><div><h3>{{ quoteDetail.sku }} · {{ quoteDetail.customer_name || 'Unnamed customer' }}</h3><p>{{ quoteDetail.inquiry_text }}</p></div></div><span :class="['badge', quoteDetail.status === 'approved' ? 'success' : quoteDetail.status === 'cancelled' ? 'cancelled' : 'warning']">{{ quoteDetail.status === 'cancelled' ? quoteActionLabels.cancelled : quoteDetail.status.toUpperCase() }}</span></div><div class="quote-detail-grid"><div><small>RISK</small><strong>{{ quoteDetail.risk.requires_approval ? 'Approval required' : 'No blocking risk' }}</strong><span v-for="reason in quoteDetail.risk.reasons" :key="reason">{{ reason }}</span></div><div><small>TOP MATCH</small><strong>{{ quoteDetail.product_matches[0]?.name || quoteDetail.sku }}</strong><span>{{ quoteDetail.product_matches[0]?.score || 0 }}% · {{ quoteDetail.product_matches[0]?.reasons.join(' · ') }}</span></div><div><small>EMAIL DRAFT</small><strong>{{ quoteDetail.email.subject }}</strong><span>{{ quoteDetail.email.body }}</span></div><div><small>APPROVAL HISTORY</small><span v-if="!quoteDetail.approval_history.length">No approval actions recorded.</span><span v-for="item in quoteDetail.approval_history" :key="item.id">{{ item.from_status }} → {{ item.to_status }} · {{ item.actor }} · {{ new Date(item.created_at).toLocaleString() }}</span></div><div class="inventory-history"><small>INVENTORY MOVEMENTS</small><span v-if="!quoteDetail.inventory_movements.length">No inventory movements recorded.</span><span v-for="item in quoteDetail.inventory_movements" :key="item.id"><b>{{ item.movement_type.toUpperCase() }} {{ item.quantity }} units</b> · {{ item.actor }} · {{ item.created_at ? new Date(item.created_at).toLocaleString() : '—' }}</span></div></div></div></td></tr></template></tbody></table></div>
      </section>
      <section v-else-if="activeNav === 'agentTrace'" class="panel quotes-page">
        <div class="panel-header"><div><h2>{{ t('activity') }}</h2><p>{{ t('activityHint') }}</p></div><button class="secondary-button" @click="selectNav('agentTrace')">{{ t('refresh') }}</button></div>
        <div v-if="evaluation" class="metrics-grid"><div><small>CASES</small><strong>{{ evaluation.cases }}</strong></div><div><small>REQUIREMENTS</small><strong>{{ (evaluation.requirement_accuracy * 100).toFixed(0) }}%</strong></div><div><small>PRODUCT MATCH</small><strong>{{ (evaluation.product_match_rate * 100).toFixed(0) }}%</strong></div><div><small>FAILURE DETECTION</small><strong>{{ (evaluation.failure_detection_rate * 100).toFixed(0) }}%</strong></div></div>
        <section class="rag-evaluation-panel">
          <div class="panel-header"><div><h3>RAG 检索评测</h3><p>比较规则检索与语义检索的候选排序效果。</p><small v-if="embeddingStatus" :class="['embedding-status', embeddingLoading ? 'muted' : embeddingStatus.includes('超时') || embeddingStatus.includes('失败') ? 'error-message' : 'success-status']">{{ embeddingStatus }}</small></div><div class="detail-actions"><select v-if="embeddingSettings?.profiles.length" :value="embeddingSettings.active.id" class="language-select" :disabled="embeddingLoading" @change="switchEmbeddingFromEvent"><option v-for="profile in embeddingSettings.profiles" :key="profile.id" :value="profile.id">{{ profile.provider }} · {{ profile.model }}</option></select><select v-model="ragEvaluationMode" class="language-select" @change="loadRagEvaluation"><option value="semantic">语义检索</option><option value="rules">规则检索</option></select><button class="secondary-button" :disabled="ragEvaluationLoading || embeddingLoading" @click="loadRagEvaluation">{{ ragEvaluationLoading || embeddingLoading ? '…' : t('refresh') }}</button></div></div>
          <p v-if="ragEvaluationLoading" class="muted">正在加载 RAG 评测…</p>
          <template v-else-if="ragEvaluation">
            <div class="metrics-grid rag-metrics"><div><small>TOP-1 RECALL</small><strong>{{ (ragEvaluation.top1_recall * 100).toFixed(1) }}%</strong></div><div><small>TOP-3 RECALL</small><strong>{{ (ragEvaluation.top3_recall * 100).toFixed(1) }}%</strong></div><div><small>MRR</small><strong>{{ ragEvaluation.mrr.toFixed(3) }}</strong></div><div><small>CASES</small><strong>{{ ragEvaluation.evaluated_cases }}/{{ ragEvaluation.cases }}</strong></div></div>
            <div v-if="ragEvaluation.misses.length" class="rag-misses"><small>TOP-3 漏召回样本</small><div v-for="item in ragEvaluation.misses" :key="item.text" class="rag-miss"><span>{{ item.text }}</span><strong>{{ item.expected_sku }}</strong><em>返回：{{ item.returned_skus.join('、') }}</em></div></div>
            <p v-else class="rag-success">✓ 当前模式没有 Top-3 漏召回样本。</p>
            <div v-if="ragEvaluationHistory.length" class="rag-history"><div class="rag-history-title"><small>最近评测记录</small><select v-model="ragHistoryFilter" class="language-select"><option value="all">全部模式</option><option value="semantic">语义检索</option><option value="rules">规则检索</option></select></div><div v-for="run in filteredRagHistory.slice(0, 8)" :key="run.id" class="rag-history-row"><span>{{ run.created_at ? new Date(run.created_at).toLocaleString(locale === 'zh' ? 'zh-CN' : locale === 'it' ? 'it-IT' : 'en-US') : '—' }}</span><strong>{{ run.mode === 'semantic' ? '语义' : '规则' }}</strong><span>{{ run.embedding_model || 'rules' }}</span><span>Top-1 {{ (run.top1_recall * 100).toFixed(1) }}%</span><span>MRR {{ run.mrr.toFixed(3) }}</span></div></div>
            <div v-if="embeddingJobs.items.length" class="embedding-job-history"><div class="rag-history-title"><small>Embedding 重建历史（{{ embeddingJobs.total }}）</small><div class="detail-actions"><button class="table-action" :disabled="embeddingJobPage === 0" @click="loadEmbeddingJobPage(embeddingJobPage - 1)">上一页</button><button class="table-action" :disabled="(embeddingJobPage + 1) * embeddingJobs.limit >= embeddingJobs.total" @click="loadEmbeddingJobPage(embeddingJobPage + 1)">下一页</button></div></div><div v-for="job in embeddingJobs.items" :key="job.job_id" class="embedding-job-row"><span>{{ new Date(job.created_at).toLocaleString(locale === 'zh' ? 'zh-CN' : locale === 'it' ? 'it-IT' : 'en-US') }}</span><span>{{ job.profile.model }}</span><strong :class="job.status === 'succeeded' ? 'success-status' : job.status === 'failed' ? 'error-message' : 'muted'">{{ job.status === 'succeeded' ? '完成' : job.status === 'failed' ? '失败' : job.status === 'running' ? `${job.progress_percent}%` : '排队中' }}</strong><span v-if="job.status === 'failed'">{{ job.error }}</span><span v-else>{{ job.indexed_products ?? job.processed_products ?? 0 }}/{{ job.total_products ?? '—' }} products</span></div></div>
            <div v-if="ragTrendRuns.length" class="rag-trend"><div class="rag-trend-header"><small>评测趋势</small><span><i class="trend-key top1" />Top-1 <i class="trend-key top3" />Top-3 <i class="trend-key mrr" />MRR</span></div><svg viewBox="0 0 600 180" role="img" aria-label="RAG evaluation trend"><line x1="24" y1="24" x2="576" y2="24" /><line x1="24" y1="90" x2="576" y2="90" /><line x1="24" y1="156" x2="576" y2="156" /><polyline class="trend-line top1" :points="trendPoints('top1_recall')" /><polyline class="trend-line top3" :points="trendPoints('top3_recall')" /><polyline class="trend-line mrr" :points="trendPoints('mrr')" /><template v-for="(run, index) in ragTrendRuns" :key="`trend-${run.id}`"><circle class="trend-dot top1" :cx="trendX(index)" :cy="trendY(run.top1_recall)" r="3" /><circle class="trend-dot top3" :cx="trendX(index)" :cy="trendY(run.top3_recall)" r="3" /><circle class="trend-dot mrr" :cx="trendX(index)" :cy="trendY(run.mrr)" r="3" /></template></svg><div class="rag-trend-axis"><span>0%</span><span>50%</span><span>100%</span></div></div>
          </template>
        </section>
        <p v-if="!agentRuns.length" class="muted">{{ t('noQuotes') }}</p>
        <div v-for="run in agentRuns" :key="run.run_id" class="run-card"><div class="run-header"><strong>Run {{ run.run_id }}</strong><small class="muted">{{ run.created_at ? new Date(run.created_at).toLocaleString(locale === 'zh' ? 'zh-CN' : locale === 'it' ? 'it-IT' : 'en-US') : '—' }}</small><span class="muted">{{ run.inquiry_text }}</span></div><div class="run-steps"><div v-for="step in run.steps" :key="step.name" class="trace-item" :class="step.status === 'complete' ? 'done' : 'current'"><span>{{ step.status === 'complete' ? '✓' : '!' }}</span><div><strong>{{ step.name }}</strong><small>{{ step.status === 'complete' ? t('complete') : t('waiting') }}</small></div></div></div></div>
      </section>
      <section v-else-if="activeNav === 'ragPlayground'" class="panel quotes-page rag-playground-page">
        <div class="panel-header"><div><h2>{{ t('ragPlayground') }}</h2><p>{{ locale === 'zh' ? '用任意询盘单独测试检索效果，不会生成报价或修改库存。' : locale === 'it' ? 'Testa il recupero con qualsiasi richiesta senza creare preventivi o modificare le scorte.' : 'Test retrieval with any inquiry without creating quotes or changing inventory.' }}</p></div></div>
        <div class="rag-playground-form">
          <label class="form-field rag-playground-inquiry"><span>{{ locale === 'zh' ? '测试询盘' : locale === 'it' ? 'Richiesta di test' : 'Test inquiry' }}</span><textarea v-model="ragPlaygroundInquiry" rows="4" /></label>
          <label class="form-field"><span>{{ locale === 'zh' ? '检索模式' : locale === 'it' ? 'Modalità' : 'Mode' }}</span><select v-model="ragPlaygroundMode"><option value="semantic">{{ locale === 'zh' ? '语义检索' : locale === 'it' ? 'Semantico' : 'Semantic' }}</option><option value="rules">{{ locale === 'zh' ? '规则检索' : locale === 'it' ? 'Regole' : 'Rules' }}</option></select></label>
          <label class="form-field"><span>Top-K</span><input v-model.number="ragPlaygroundTopK" type="number" min="1" max="20" /></label>
          <label class="form-field"><span>{{ locale === 'zh' ? '相似度阈值' : locale === 'it' ? 'Soglia similarità' : 'Score threshold' }}</span><input v-model.number="ragPlaygroundThreshold" type="number" min="0" max="1" step="0.05" /></label>
          <button class="primary-button compact rag-playground-run" :disabled="ragPlaygroundLoading" @click="runRagPlaygroundQuery">{{ ragPlaygroundLoading ? '…' : (locale === 'zh' ? '开始检索' : locale === 'it' ? 'Esegui ricerca' : 'Run retrieval') }} <span>→</span></button>
        </div>
        <p class="muted rag-playground-note">{{ locale === 'zh' ? '解析使用确定性的规则抽取，语义模式使用当前 Embedding + Qdrant，结果只读。' : locale === 'it' ? 'L’estrazione usa regole deterministiche; la modalità semantica usa l’Embedding e Qdrant attivi.' : 'Parsing uses deterministic rules; semantic mode uses the active embedding profile and Qdrant. Results are read-only.' }}</p>
        <template v-if="ragPlaygroundResult">
          <div class="rag-playground-summary">
            <div><small>{{ locale === 'zh' ? '解析需求' : 'PARSED REQUIREMENTS' }}</small><strong>{{ ragPlaygroundResult.parsed.quantity ?? '—' }} {{ ragPlaygroundResult.parsed.product_keywords.join(' · ') || '—' }}</strong><span>{{ ragPlaygroundResult.parsed.destination_country || '—' }} · {{ ragPlaygroundResult.parsed.project_type || '—' }}</span></div>
            <div><small>{{ locale === 'zh' ? '检索状态' : 'RETRIEVAL' }}</small><strong>{{ ragPlaygroundResult.retrieval_mode }}</strong><span>{{ ragPlaygroundResult.candidates.length }} candidates</span></div>
            <div><small>{{ locale === 'zh' ? '耗时' : 'TIMINGS' }}</small><strong>{{ ragPlaygroundResult.timings.total_ms.toFixed(0) }} ms</strong><span>parse {{ ragPlaygroundResult.timings.parse_ms.toFixed(0) }} · retrieve {{ ragPlaygroundResult.timings.retrieval_ms.toFixed(0) }} · rank {{ ragPlaygroundResult.timings.ranking_ms.toFixed(0) }}<template v-if="ragPlaygroundResult.reranker.enabled"> · rerank {{ (ragPlaygroundResult.timings.reranker_ms ?? 0).toFixed(0) }}</template></span></div>
          </div>
          <div :class="['rag-match-status', `rag-match-${ragPlaygroundResult.match_status}`]"><strong>{{ ragPlaygroundResult.match_status === 'reliable' ? (locale === 'zh' ? '高可信匹配' : 'Reliable match') : ragPlaygroundResult.match_status === 'review' ? (locale === 'zh' ? '建议人工确认' : 'Human review recommended') : (locale === 'zh' ? '未找到可靠匹配' : 'No reliable match') }}</strong><span>{{ locale === 'zh' ? `最高匹配分 ${ragPlaygroundResult.candidates[0]?.score ?? 0}%，低于 ${ragPlaygroundResult.match_threshold}% 时不会视为可靠匹配。` : `Best score ${ragPlaygroundResult.candidates[0]?.score ?? 0}%; scores below ${ragPlaygroundResult.match_threshold}% are not reliable.` }}</span></div>
          <p class="rag-reranker-status">{{ ragPlaygroundResult.reranker.enabled ? `Cross-Encoder: ${ragPlaygroundResult.reranker.model} · ${ragPlaygroundResult.reranker.scores_returned} candidates reranked` : (locale === 'zh' ? 'Cross-Encoder 未启用：当前使用规则 + 语义混合排序。' : 'Cross-Encoder disabled: using hybrid rule and semantic ranking.') }}<span v-if="ragPlaygroundResult.reranker.error"> · {{ ragPlaygroundResult.reranker.error }}</span></p>
          <p v-if="ragPlaygroundResult.retrieval_error" class="error-message">{{ ragPlaygroundResult.retrieval_error }}</p>
          <div class="rag-playground-results"><div class="rag-playground-results-header"><strong>{{ locale === 'zh' ? '候选产品' : locale === 'it' ? 'Candidati' : 'Candidates' }}</strong><span>Top {{ ragPlaygroundTopK }} · threshold {{ ragPlaygroundThreshold.toFixed(2) }}</span></div><p v-if="!ragPlaygroundResult.candidates.length" class="muted">{{ locale === 'zh' ? '没有符合条件的产品。' : 'No matching products.' }}</p><article v-for="candidate in ragPlaygroundResult.candidates" :key="candidate.sku" class="rag-playground-card"><div class="rag-playground-card-head"><div><strong>{{ candidate.name }}</strong><span>{{ candidate.sku }} · ${{ candidate.unit_price_usd.toFixed(2) }} · {{ candidate.inventory_available }} available</span></div><div class="rag-score"><b>{{ candidate.score }}%</b><small>final score</small></div></div><div class="rag-score-row"><span>Semantic score <b>{{ candidate.semantic_score == null ? '—' : candidate.semantic_score.toFixed(3) }}</b></span><span>Inventory <b>{{ candidate.inventory_sufficient ? 'sufficient' : 'insufficient' }}</b></span><span>Lead time <b>{{ candidate.lead_time_days }} days</b></span></div><p v-if="candidate.reasons.length" class="rag-reasons">{{ candidate.reasons.join(' · ') }}</p><p v-if="candidate.unmet_conditions.length" class="rag-unmet">⚠ {{ candidate.unmet_conditions.join(' · ') }}</p></article></div>
        </template>
        <div v-else class="rag-playground-empty">{{ locale === 'zh' ? '输入询盘后点击“开始检索”查看 RAG 候选和评分。' : locale === 'it' ? 'Inserisci una richiesta e avvia la ricerca per vedere candidati e punteggi.' : 'Enter an inquiry and run retrieval to inspect candidates and scores.' }}</div>
      </section>
      <section v-else-if="activeNav === 'products'" class="panel quotes-page" @click.self="selectedProduct = null">
        <div class="panel-header"><div><h2>{{ t('products') }}</h2><p>{{ productLabels.browse }}</p></div><div class="detail-actions"><button class="secondary-button" @click="loadProducts">{{ t('refresh') }}</button><button v-if="canManageCatalog" class="primary-button compact" @click="productCreateOpen = true">＋ {{ productLabels.newProduct }}</button></div></div>
        <div class="search-row"><input v-model="search" :placeholder="productLabels.searchPlaceholder" @keyup.enter="loadProducts" /><button class="secondary-button" @click="loadProducts">{{ t('search') }}</button><label class="inactive-toggle"><input v-model="includeInactiveProducts" type="checkbox" @change="loadProducts" /> {{ productLabels.showInactive }}</label></div>
        <div class="catalog-grid"><div v-for="product in products" :key="product.sku" class="catalog-item" :class="{ expanded: selectedProduct?.sku === product.sku }"><button class="catalog-card" :class="{ selected: selectedProduct?.sku === product.sku, inactive: !product.is_active }" @click="selectProduct(product)"><div class="product-icon">◒</div><strong>{{ product.name }} <span v-if="!product.is_active" class="inactive-badge">{{ productLabels.inactive }}</span></strong><span>{{ product.category }}</span><small>{{ product.sku }}</small><b>${{ product.unit_price_usd.toFixed(2) }} / {{ t('unit') }}</b></button><div v-if="selectedProduct?.sku === product.sku" class="product-detail inline" @click.stop><div><span class="step">{{ productLabels.detail }}</span><h3>{{ selectedProduct.name }}</h3><p>{{ selectedProduct.description }}</p><div class="detail-actions"><button v-if="canManageCatalog" class="secondary-button" :disabled="productSaving || productTagLoading || productDeleting" @click="selectedProduct.is_active ? openProductEdit(selectedProduct) : activateProduct(selectedProduct)">{{ selectedProduct.is_active ? productLabels.edit : (productSaving ? "…" : productLabels.activate) }}</button><button class="secondary-button" :disabled="productTagLoading || productSaving || productDeleting" @click="generateProductTags(selectedProduct)">{{ productTagLoading ? '…' : productLabels.suggest }}</button><button v-if="canManageCatalog && tagSuggestions.length" class="primary-button compact" :disabled="applyingTags" @click="applyProductTags(selectedProduct)">{{ applyingTags ? '…' : productLabels.apply }}</button><button v-if="canManageCatalog" class="danger-button" :disabled="productDeleting || productSaving || productTagLoading" @click="removeProduct(selectedProduct)">{{ productDeleting ? '…' : productLabels.deactivate }}</button></div><p v-if="tagSuggestions.length" class="tag-suggestions">{{ productLabels.suggest }}: {{ tagSuggestions.join(', ') }}</p><p class="current-tags">{{ productLabels.currentTags }}: {{ selectedProduct.match_tags || productLabels.none }}</p></div><div class="detail-grid"><span><small>SKU</small><strong>{{ selectedProduct.sku }}</strong></span><span><small>MATERIAL</small><strong>{{ selectedProduct.material }}</strong></span><span><small>MOQ</small><strong>{{ selectedProduct.min_order_quantity }} {{ t('unit') }}</strong></span><span><small>LEAD TIME</small><strong>{{ selectedProduct.lead_time_days }} days</strong></span><span><small>PRICE</small><strong>${{ selectedProduct.unit_price_usd.toFixed(2) }}</strong></span><span><small>ON HAND</small><strong>{{ selectedProduct.on_hand_quantity ?? 0 }}</strong></span><span><small>RESERVED</small><strong>{{ selectedProduct.reserved_quantity ?? 0 }}</strong></span><span><small>AVAILABLE</small><strong>{{ selectedProduct.available_quantity ?? 0 }}</strong></span></div><div class="inventory-history product-inventory-history"><div class="inventory-history-toolbar"><small>INVENTORY HISTORY</small><select v-model="inventoryMovementFilter"><option value="all">ALL</option><option value="reserve">RESERVE</option><option value="deduct">DEDUCT</option><option value="release">RELEASE</option><option value="adjustment">ADJUSTMENT</option></select><input v-model="inventoryQuoteFilter" placeholder="Quote #" /></div><span v-if="!filteredInventoryMovements.length">No matching inventory movements.</span><span v-for="item in filteredInventoryMovements" :key="`${item.movement_type}-${item.id}`"><b>{{ item.movement_type.toUpperCase() }} {{ item.quantity > 0 ? '+' : '' }}{{ item.quantity }} units</b><template v-if="item.movement_type === 'adjustment'"> · {{ item.previous_quantity }} → {{ item.new_quantity }} · {{ item.reason }}</template><template v-else> · Quote #{{ item.quote_id ?? '—' }}</template> · {{ item.actor }} · {{ item.created_at ? new Date(item.created_at).toLocaleString() : '—' }}</span></div><div v-if="productEditOpen" class="customer-form product-edit-form"><h3>{{ productLabels.edit }} · {{ selectedProduct.name }}</h3><div class="form-grid"><label class="form-field"><span>{{ productLabels.material }}</span><input v-model="productEdit.material" /></label><label class="form-field"><span>{{ productLabels.colors }}</span><input v-model="productEdit.colors" /></label><label class="form-field"><span>{{ productLabels.tags }}</span><input v-model="productEdit.match_tags" /></label><label class="form-field"><span>{{ productLabels.moq }}</span><input v-model.number="productEdit.min_order_quantity" type="number" min="1" /></label><label class="form-field"><span>{{ productLabels.lead }}</span><input v-model.number="productEdit.lead_time_days" type="number" min="1" /></label><label class="form-field"><span>{{ productLabels.price }}</span><input v-model.number="productEdit.unit_price_usd" type="number" min="0" step="0.01" /></label><label class="form-field"><span>{{ productLabels.inventory }}</span><input v-model.number="productEdit.on_hand_quantity" type="number" min="0" /></label><label class="form-field"><span>{{ productLabels.reason }}</span><input v-model="productEdit.inventory_reason" /></label><label class="checkbox-field"><input v-model="productEdit.is_active" type="checkbox" /> {{ productLabels.active }}</label></div><div class="detail-actions"><button class="secondary-button" :disabled="productSaving" @click="productEditOpen = false">{{ productLabels.cancel }}</button><button class="primary-button compact" :disabled="productSaving" @click="saveProduct">{{ productSaving ? '…' : productLabels.save }}</button></div></div></div></div>
        </div>
        <div v-if="productCreateOpen" class="customer-form"><h3>{{ productLabels.newTitle }}</h3><div class="form-grid"><label class="form-field"><span>{{ productLabels.sku }}</span><input v-model="productCreate.sku" /></label><label class="form-field"><span>{{ productLabels.name }}</span><input v-model="productCreate.name" /></label><label class="form-field"><span>{{ productLabels.category }}</span><input v-model="productCreate.category" /></label><label class="form-field"><span>{{ productLabels.description }}</span><input v-model="productCreate.description" /></label><label class="form-field"><span>{{ productLabels.material }}</span><input v-model="productCreate.material" /></label><label class="form-field"><span>{{ productLabels.colors }}</span><input v-model="productCreate.colors" /></label><label class="form-field"><span>{{ productLabels.tags }}</span><input v-model="productCreate.match_tags" /></label><label class="form-field"><span>{{ productLabels.moq }}</span><input v-model.number="productCreate.min_order_quantity" type="number" min="1" /></label><label class="form-field"><span>{{ productLabels.lead }}</span><input v-model.number="productCreate.lead_time_days" type="number" min="1" /></label><label class="form-field"><span>{{ productLabels.price }}</span><input v-model.number="productCreate.unit_price_usd" type="number" min="0" step="0.01" /></label></div><div class="detail-actions"><button class="secondary-button" :disabled="productCreating" @click="productCreateOpen = false">{{ productLabels.cancel }}</button><button class="primary-button compact" :disabled="productCreating" @click="saveNewProduct">{{ productCreating ? '…' : productLabels.save }}</button></div></div>
      </section>
      <section v-else-if="activeNav === 'customers'" class="panel quotes-page">
        <div class="panel-header"><div><h2>{{ customerLabels.pageTitle }}</h2><p>{{ customerLabels.pageHint }}</p></div><div class="detail-actions"><button class="secondary-button" @click="loadCustomers">{{ t('refresh') }}</button><button class="primary-button compact" @click="openCustomerForm()">＋ {{ customerLabels.createCustomerLabel }}</button></div></div>
        <div class="search-row"><input v-model="customerSearch" :placeholder="customerLabels.companyPlaceholder" @keyup.enter="loadCustomers" /><button class="secondary-button" @click="loadCustomers">{{ t('search') }}</button></div>
        <div class="customer-list"><div v-for="customer in customers" :key="customer.id" class="customer-entry"><article class="customer-row" :class="{ selected: selectedCustomer?.id === customer.id }" @click="selectCustomer(customer)"><div class="customer-avatar">{{ customer.company_name.slice(0, 2).toUpperCase() }}</div><div class="customer-row-main"><strong>{{ customer.company_name }}</strong><span>{{ customer.contact_name }} · {{ customer.email }}</span></div><span class="customer-country">{{ customer.country }}</span></article><div v-if="selectedCustomer?.id === customer.id" class="product-detail customer-detail inline" @click.stop><div><span class="step">DETAIL</span><h3>{{ selectedCustomer.company_name }}</h3><p>{{ selectedCustomer.contact_name }} · {{ selectedCustomer.email }} · {{ selectedCustomer.country }}</p><h4>Quote history ({{ customerQuotes.length }})</h4><div v-if="customerQuotes.length" class="quote-history"><div v-for="record in customerQuotes" :key="record.id"><span>{{ record.sku }} · {{ record.quantity }} units</span><strong>${{ record.total_price_usd.toFixed(2) }}</strong></div></div><p v-else class="muted">No quotes for this customer yet.</p></div><div class="detail-actions"><button class="secondary-button" @click="customerName = selectedCustomer?.company_name || ''; selectNav('inquiryWorkspace')">Use in inquiry</button><button class="secondary-button" :disabled="customerDeleting || customerSaving" @click="openCustomerForm(selectedCustomer)">Edit</button><button class="danger-button" :disabled="customerDeleting || customerSaving" @click="removeCustomer(selectedCustomer)">{{ customerDeleting ? '…' : 'Delete' }}</button></div></div></div></div>
        <div v-if="customerFormOpen" class="customer-form"><h3>{{ editingCustomerId ? customerLabels.editTitle : customerLabels.createCustomerLabel }}</h3><div class="form-grid"><input v-model="customerForm.company_name" :placeholder="customerLabels.company" /><input v-model="customerForm.contact_name" :placeholder="customerLabels.contact" /><input v-model="customerForm.country" :placeholder="customerLabels.country" /><input v-model="customerForm.email" type="email" :placeholder="customerLabels.email" /></div><div class="detail-actions"><button class="secondary-button" :disabled="customerSaving" @click="customerFormOpen = false">{{ productLabels.cancel }}</button><button class="primary-button compact" :disabled="customerSaving" @click="saveCustomer">{{ customerSaving ? '…' : productLabels.save }}</button></div></div>
      </section>
      <section v-else-if="activeNav === 'aiSettings'" class="panel quotes-page">
        <div class="panel-header"><div><h2>{{ t('aiSettings') }}</h2><p>{{ locale === 'zh' ? '配置模型服务商、模型和连接地址。' : locale === 'it' ? 'Configura provider, modello e indirizzo di connessione.' : 'Configure providers, models, and connection endpoints.' }}</p></div><div class="detail-actions"><button class="secondary-button" :disabled="aiDiagnosticsLoading" @click="loadAIDiagnostics">{{ aiDiagnosticsLoading ? '…' : (locale === 'zh' ? '诊断' : locale === 'it' ? 'Diagnostica' : 'Diagnostics') }}</button><button class="secondary-button" @click="loadAISettings">{{ t('refresh') }}</button></div></div>
        <div v-if="aiDiagnostics" class="ai-diagnostics"><div class="ai-diagnostics-header"><strong>{{ locale === 'zh' ? '启动配置诊断' : locale === 'it' ? 'Diagnostica configurazione' : 'Startup configuration diagnostics' }}</strong><small>{{ locale === 'zh' ? '不消耗在线模型额度' : locale === 'it' ? 'Non consuma crediti del modello online' : 'Does not consume online model credits' }}</small></div><div class="ai-diagnostics-grid"><div v-for="check in aiDiagnostics.checks" :key="check.id" class="ai-diagnostic-item"><span :class="['diagnostic-dot', `diagnostic-${check.status}`]" /><div><strong>{{ check.name }}</strong><small>{{ check.message }}</small></div><em>{{ check.latency_ms ? `${check.latency_ms} ms` : check.status === 'disabled' ? 'OFF' : '—' }}</em></div></div></div>
        <div v-if="aiSettings" class="ai-settings-layout">
          <div class="ai-provider-list"><button v-for="provider in aiSettings.providers" :key="provider.id" class="ai-provider-card" :class="{ selected: aiConfigProvider === provider.id }" @click="selectAIConfigProvider(provider.id)"><span><strong>{{ aiProviderLabel(provider.id) }}</strong><small>{{ provider.model || '—' }}</small></span><em :class="provider.available ? 'success-status' : 'muted'">{{ provider.available ? (locale === 'zh' ? '可用' : locale === 'it' ? 'Disponibile' : 'Available') : (locale === 'zh' ? '未配置' : locale === 'it' ? 'Non configurato' : 'Not configured') }}</em></button></div>
          <div class="customer-form ai-config-form"><h3>{{ aiProviderLabel(aiConfigProvider) }}</h3><p v-if="aiConfigProvider === 'rules'" class="muted">{{ locale === 'zh' ? '规则引擎无需外部模型配置。' : locale === 'it' ? 'Il motore regole non richiede un modello esterno.' : 'The rule engine does not require an external model.' }}</p><div v-else class="form-grid"><label class="form-field"><span>Base URL</span><input v-model="aiConfigForm.base_url" placeholder="https://api.example.com/v1" /></label><label class="form-field"><span>{{ locale === 'zh' ? '模型' : locale === 'it' ? 'Modello' : 'Model' }}</span><input v-model="aiConfigForm.model" placeholder="model-name" /></label><label class="form-field"><span>{{ locale === 'zh' ? '超时（秒）' : locale === 'it' ? 'Timeout (secondi)' : 'Timeout (seconds)' }}</span><input v-model.number="aiConfigForm.timeout_seconds" type="number" min="1" max="300" /></label><label class="form-field"><span>API Key（{{ aiSettings.providers.find((item) => item.id === aiConfigProvider)?.api_key_configured ? (locale === 'zh' ? '已配置' : locale === 'it' ? 'configurata' : 'configured') : (locale === 'zh' ? '未配置' : locale === 'it' ? 'non configurata' : 'not configured') }}）</span><input v-model="aiConfigForm.api_key" type="password" autocomplete="new-password" :placeholder="locale === 'zh' ? '留空则保持不变，不会回显' : locale === 'it' ? 'Vuoto per mantenere la chiave' : 'Leave blank to keep the current key'" /></label></div><p class="muted ai-config-note">{{ locale === 'zh' ? 'API Key 仅在当前后端进程内更新，不会回显，也不会写入数据库；正式部署请写入 .env 或 Docker secrets。' : locale === 'it' ? 'La chiave viene aggiornata solo in memoria, non viene restituita né salvata nel database; per il deploy usa .env o Docker secrets.' : 'The key is updated in the current backend process only, never returned or stored in the database; use .env or Docker secrets for deployment.' }}</p><div class="detail-actions"><button class="secondary-button" :disabled="aiTestLoading" @click="testSelectedAIProvider">{{ aiTestLoading ? '…' : (locale === 'zh' ? '测试连接' : locale === 'it' ? 'Test connessione' : 'Test connection') }}</button><button class="primary-button compact" :disabled="aiConfigSaving" @click="saveAISettings">{{ aiConfigSaving ? '…' : (locale === 'zh' ? '保存配置' : locale === 'it' ? 'Salva configurazione' : 'Save configuration') }}</button></div><p v-if="aiTestStatus" class="ai-test-status" :class="{ error: aiTestStatus.includes('失败') || aiTestStatus.includes('failed') || aiTestStatus.includes('not configured') || aiTestStatus.includes('non configurata') }">{{ aiTestStatus }}</p></div>
        </div>
      </section>
      <section v-else-if="activeNav === 'users' && authRole === 'admin'" class="panel quotes-page">
        <div class="panel-header"><div><h2>User management</h2><p>Manage access, roles, and active accounts.</p></div><div class="detail-actions"><button class="secondary-button" @click="loadUsers">Refresh</button><button class="primary-button compact" @click="openUserForm">＋ New user</button></div></div>
        <p v-if="userError" class="error-message">{{ userError }}</p>
        <p v-if="usersLoading" class="muted">Loading users…</p>
        <div v-else class="users-table-wrap"><table class="quotes-table"><thead><tr><th>USERNAME</th><th>ROLE</th><th>STATUS</th><th>ACTION</th></tr></thead><tbody><template v-for="user in users" :key="user.id"><tr><td>{{ user.username }}</td><td><select :value="user.role" @change="changeUserRole(user, ($event.target as HTMLSelectElement).value as UserRecord['role'])"><option value="admin">admin</option><option value="approver">approver</option><option value="viewer">viewer</option></select></td><td><span :class="['badge', user.is_active ? 'success' : 'warning']">{{ user.is_active ? 'ACTIVE' : 'INACTIVE' }}</span></td><td><div class="user-actions"><button class="table-action" @click="openPasswordForm(user)">{{ passwordEditingUserId === user.id ? 'Cancel' : 'Change password' }}</button><button class="table-action" :disabled="user.username === loginForm.username" @click="toggleUser(user)">{{ user.is_active ? 'Deactivate' : 'Activate' }}</button></div></td></tr><tr v-if="passwordEditingUserId === user.id"><td colspan="4"><div class="password-form"><strong>Change password for {{ user.username }}</strong><div class="form-grid"><input v-model="passwordForm.password" type="password" minlength="8" placeholder="New password (8+ characters)" autocomplete="new-password" /><input v-model="passwordForm.confirm" type="password" minlength="8" placeholder="Confirm new password" autocomplete="new-password" /></div><div class="detail-actions"><button class="secondary-button" :disabled="passwordSaving" @click="closePasswordForm">Cancel</button><button class="primary-button compact" :disabled="passwordSaving" @click="saveUserPassword(user)">{{ passwordSaving ? '…' : 'Save password' }}</button></div></div></td></tr></template></tbody></table></div>
        <div v-if="userFormOpen" class="customer-form"><h3>New user</h3><div class="form-grid"><input v-model="userForm.username" placeholder="Username" autocomplete="off" /><input v-model="userForm.password" type="password" placeholder="Password (8+ characters)" autocomplete="new-password" /><select v-model="userForm.role"><option value="viewer">viewer</option><option value="approver">approver</option><option value="admin">admin</option></select></div><div class="detail-actions"><button class="secondary-button" :disabled="userSaving" @click="userFormOpen = false">Cancel</button><button class="primary-button compact" :disabled="userSaving" @click="saveUser">{{ userSaving ? '…' : 'Create' }}</button></div></div>
      </section>
    </main>
  </div>
</template>

<style scoped>
:global(body) { min-width: 0; }
.quotes-page { min-height: 420px; }
.auth-gate { position: fixed; inset: 0; z-index: 10; display: grid; place-items: center; background: rgba(244, 249, 247, .96); }
.auth-card { display: flex; width: min(360px, calc(100vw - 36px)); flex-direction: column; gap: 12px; padding: 30px; border: 1px solid #dce9e4; border-radius: 14px; background: #fff; box-shadow: 0 18px 60px rgba(41, 75, 67, .12); }
.auth-card h1 { margin: 0; color: #214e47; font-size: 24px; }
.auth-card p { margin: 0 0 8px; color: #71827d; font-size: 12px; }
.auth-card input { padding: 11px 12px; border: 1px solid #dbe7e2; border-radius: 7px; }
.auth-error { color: #a34e47 !important; }
.logout-button { border: 0; background: transparent; color: #5d7771; font-size: 11px; cursor: pointer; }
.quotes-table-wrap { overflow-x: auto; }
.users-table-wrap { overflow-x: auto; }
.users-table select { padding: 6px 8px; border: 1px solid #dbe7e2; border-radius: 6px; color: #40504f; background: #fff; }
.password-form { display: grid; gap: 12px; padding: 14px 16px; border: 1px solid #dbe7e2; border-radius: 10px; background: #f7fbf9; }
.password-form strong { color: #294b43; }
.user-actions { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; min-width: 190px; }
.user-actions .table-action { white-space: nowrap; }
.quotes-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.quotes-table th { color: #8b9995; font-size: 10px; letter-spacing: .08em; text-align: left; padding: 12px 10px; border-bottom: 1px solid #e6ebe9; }
.quotes-table td { padding: 15px 10px; border-bottom: 1px solid #edf1ef; color: #40504f; }
.quotes-table td:nth-child(4) { font-weight: 700; color: #1e5149; }
.quote-row { cursor: pointer; }
.quote-row:hover { background: #f6faf8; }
.quote-detail-row > td { padding: 0; background: #fbfefd; }
.quote-detail-row .quote-detail-card { margin: 0; border: 0; border-top: 1px solid #dce9e4; border-radius: 0; }
.quote-detail-card { margin-top: 20px; padding: 18px; border: 1px solid #dce9e4; border-radius: 10px; background: #fbfefd; }
.quote-detail-card h3 { margin: 0; color: #214e47; }
.quote-detail-card p { margin: 5px 0 0; color: #788985; font-size: 11px; }
.quote-detail-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 16px; }
.quote-detail-grid > div { display: flex; flex-direction: column; gap: 5px; padding: 12px; border-radius: 8px; background: #fff; border: 1px solid #e7efec; }
.quote-detail-grid small { color: #8b9995; font-size: 10px; letter-spacing: .08em; }
.quote-detail-grid strong { color: #315c54; font-size: 12px; }
.quote-detail-grid span { color: #6d7d79; font-size: 11px; white-space: pre-line; }
.inventory-history { grid-column: 1 / -1; }
.inventory-history span { display: block; margin-top: 4px; }
.inventory-history b { color: #315c54; }
.product-inventory-history { flex-basis: 100%; margin-top: 4px; }
.inventory-history-toolbar { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.inventory-history-toolbar small { margin-right: auto; }
.inventory-history-toolbar select, .inventory-history-toolbar input { border: 1px solid #dce4e1; border-radius: 5px; padding: 5px 7px; color: #40504f; background: #fff; font: 10px inherit; }
.table-action { border: 0; border-radius: 5px; background: #e3f4ee; color: #31836f; padding: 6px 8px; font: 600 10px inherit; cursor: pointer; }
.quote-actions { display: flex; gap: 6px; flex-wrap: wrap; }
.cancel-action { background: #fff2f0; color: #a34e47; }
.cancelled { background: #eef1f0; color: #6f7e79; }
.approved-mark { color: #4d9e89; font-weight: 700; }
.run-card { border: 1px solid #e7edeb; border-radius: 9px; padding: 16px; margin-top: 12px; }
.run-header { display: flex; flex-direction: column; gap: 6px; padding-bottom: 10px; border-bottom: 1px solid #edf1ef; }
.run-steps { display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; }
.run-steps .trace-item { padding: 13px 4px 4px; }
.catalog-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.catalog-item { min-width: 0; display: flex; flex-direction: column; }
.catalog-item.expanded { grid-column: 1 / -1; }
.catalog-card { min-height: 156px; box-sizing: border-box; border: 1px solid #e7edeb; background: #fff; border-radius: 9px; padding: 15px; text-align: left; display: flex; flex-direction: column; justify-content: space-between; gap: 7px; cursor: pointer; color: #40504f; }
.catalog-card:hover, .catalog-card.selected { border-color: #65cdb4; box-shadow: 0 5px 16px rgba(55, 135, 116, .1); }
.catalog-card.inactive { border-color: #d7dddb; background: #f5f6f5; opacity: .82; }
.inactive-toggle { display: inline-flex; align-items: center; gap: 6px; color: #667a75; font-size: 11px; white-space: nowrap; }
.inactive-badge { display: inline-block; margin-left: 4px; padding: 2px 5px; border-radius: 4px; background: #e7ecea; color: #71807c; font-size: 9px; font-weight: 600; }
.catalog-card strong { font-size: 12px; color: #263b37; }
.catalog-card span, .catalog-card small { color: #8b9995; font-size: 10px; }
.catalog-card b { color: #31836f; font-size: 13px; margin-top: 4px; }
.product-detail { margin-top: 22px; padding: 18px; background: #f5f8f7; border-radius: 9px; display: flex; justify-content: space-between; gap: 24px; }
.product-detail.inline { margin-top: 8px; padding: 14px; border: 1px solid #dce9e4; background: #fbfefd; }
.product-detail.inline { display: grid; grid-template-columns: minmax(0, 1.15fr) minmax(260px, .85fr); align-items: start; }
.product-detail.inline .detail-grid { min-width: 0; grid-template-columns: repeat(4, minmax(0, 1fr)); }
.product-detail.inline .product-inventory-history { grid-column: 1 / -1; }
.product-detail.inline .product-edit-form { grid-column: 1 / -1; margin-top: 0; }
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
.customer-entry { display: flex; flex-direction: column; gap: 7px; min-width: 0; }
.customer-row { display: flex; align-items: center; gap: 12px; padding: 13px; border: 1px solid #e7edeb; border-radius: 8px; }
.customer-row-main { flex: 1; display: flex; flex-direction: column; gap: 4px; }
.customer-row-main strong { font-size: 13px; }
.customer-row-main span, .customer-country { color: #8b9995; font-size: 11px; }
.customer-row { cursor: pointer; }
.customer-row.selected { border-color: #65cdb4; background: #f5fbf9; }
.customer-input { width: 100%; margin-top: 9px; border: 1px solid #dce4e1; border-radius: 7px; padding: 10px 12px; font: 12px inherit; outline: none; }
.customer-detail { align-items: center; }
.detail-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.primary-button.compact { width: auto; margin-top: 0; padding: 9px 12px; }
.danger-button { border: 1px solid #f0c9c4; border-radius: 6px; background: #fff7f6; color: #b55b50; padding: 9px 12px; font: 600 11px inherit; cursor: pointer; }
.customer-form { margin-top: 18px; padding: 18px; border: 1px solid #dce8e4; border-radius: 9px; background: #fbfdfc; }
.customer-form h3 { margin: 0 0 14px; font-size: 15px; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 9px; margin-bottom: 14px; }
.form-grid input { border: 1px solid #dce4e1; border-radius: 7px; padding: 10px 12px; font: 12px inherit; outline: none; }
.form-field { display: flex; flex-direction: column; gap: 5px; }
.form-field span { color: #667a75; font-size: 10px; font-weight: 700; }
.checkbox-field { display: flex; align-items: center; gap: 7px; color: #40504f; font-size: 11px; }
.checkbox-field input { width: auto; }
.tag-suggestions { color: #31836f !important; font-weight: 600; }
.current-tags { color: #8b9995 !important; }
.quote-history { display: flex; flex-direction: column; gap: 6px; margin-top: 9px; max-width: 480px; }
.quote-history div { display: flex; justify-content: space-between; padding: 8px 10px; background: #fff; border: 1px solid #e7edeb; border-radius: 6px; font-size: 11px; }
.ai-status { color: #31836f; font-weight: 600; }
.ai-status.running { color: #a87826; }
.ai-status.fallback, .ai-status.error { color: #b55b50; }
.match-explanation { display: flex; flex-wrap: wrap; gap: 5px 8px; margin-top: 6px; font-size: 10px; }
.match-explanation b { color: #31836f; }
.match-explanation span { color: #71807c; }
.match-explanation em { color: #b55b50; font-style: normal; }
.candidate-list { margin-top: 16px; }
.candidate-card { cursor: pointer; }
.candidate-card.selected { border-color: #65cdb4; background: #f5fbf9; }
.candidate-detail { display: flex; justify-content: space-between; gap: 24px; margin-top: 14px; padding: 16px; border: 1px solid #dce9e4; border-radius: 9px; background: #fbfefd; }
.candidate-detail.inline { grid-column: 1 / -1; }
.product-panel .product-card { min-height: 78px; box-sizing: border-box; flex-wrap: wrap; cursor: pointer; }
.product-panel .product-card .candidate-detail.inline { flex-basis: 100%; }
.product-panel .candidate-detail.inline { min-width: 0; display: grid; grid-template-columns: minmax(0, 1.15fr) minmax(240px, .85fr); align-items: start; }
.product-panel .candidate-detail.inline .detail-grid { min-width: 0; grid-template-columns: repeat(3, minmax(0, 1fr)); }
.candidate-detail h3 { margin: 8px 0 5px; color: #315c54; font-size: 14px; }
.candidate-detail p { max-width: 500px; margin: 0 0 8px; color: #71807c; font-size: 11px; line-height: 1.5; }
.candidate-tags { color: #31836f; font-size: 10px; }
.candidate-list h3 { margin: 0 0 8px; color: #40504f; font-size: 12px; }
.candidate-card { min-height: 78px; box-sizing: border-box; display: grid; grid-template-columns: 1fr auto; gap: 4px 12px; padding: 10px 12px; border: 1px solid #e7edeb; border-radius: 7px; margin-top: 7px; }
.candidate-card div { display: flex; flex-direction: column; gap: 3px; }
.candidate-card strong { color: #263b37; font-size: 11px; }
.candidate-card span, .candidate-card small { color: #8b9995; font-size: 10px; }
.candidate-card > b { color: #31836f; font-size: 13px; }
.candidate-card em { color: #b55b50; font-style: normal; }
.candidate-card .rag-explanation { grid-column: 1 / -1; margin: 5px 0 0; padding: 8px; border-radius: 6px; background: #f2f8f6; color: #536763; font-size: 10px; line-height: 1.45; }
.rag-explanation > strong { margin-right: 5px; color: #31836f; }
.rag-explanation .evidence-chip { display: inline-block; margin: 5px 5px 0 0; padding: 2px 5px; border: 1px solid #d5e6e1; border-radius: 4px; background: #fff; color: #526864; }
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
.rag-evaluation-panel { margin: 18px 0 22px; padding: 14px; border: 1px solid #e4ece9; border-radius: 9px; background: #fbfefd; }
.rag-evaluation-panel .panel-header { margin-bottom: 12px; }
.rag-evaluation-panel h3 { margin: 0 0 4px; color: #40504f; font-size: 13px; }
.rag-evaluation-panel p { margin: 0; color: #8b9995; font-size: 11px; }
.rag-metrics { grid-template-columns: repeat(4, 1fr); margin: 0; }
.rag-misses { display: flex; flex-direction: column; gap: 7px; margin-top: 12px; }
.rag-misses > small { color: #b55b50; font-weight: 700; }
.rag-miss { display: grid; grid-template-columns: 1.5fr auto 1fr; gap: 8px; align-items: center; padding: 8px 10px; border-radius: 6px; background: #fff5f3; color: #667571; font-size: 10px; }
.rag-miss strong { color: #a34e47; }
.rag-miss em { color: #8b9995; font-style: normal; }
.rag-success { margin-top: 12px !important; color: #31836f !important; font-weight: 600; }
.rag-history { display: flex; flex-direction: column; gap: 6px; margin-top: 14px; }
.rag-history > small { color: #71807c; font-weight: 700; }
.rag-history-title { display: flex; justify-content: space-between; align-items: center; }
.rag-history-row { display: grid; grid-template-columns: 1.5fr .6fr .7fr .7fr .7fr; gap: 8px; padding: 7px 9px; border-bottom: 1px solid #edf2f0; color: #71807c; font-size: 10px; }
.rag-history-row strong { color: #31836f; }
.embedding-job-history { display: flex; flex-direction: column; gap: 6px; margin-top: 14px; padding-top: 12px; border-top: 1px solid #edf2f0; }
.embedding-job-history > small { color: #71807c; font-weight: 700; }
.embedding-job-row { display: grid; grid-template-columns: 1.2fr 1.5fr .6fr 1fr; gap: 8px; padding: 7px 9px; border-bottom: 1px solid #edf2f0; color: #71807c; font-size: 10px; }
.rag-trend { margin-top: 16px; padding-top: 12px; border-top: 1px solid #edf2f0; }
.rag-trend-header { display: flex; justify-content: space-between; align-items: center; color: #71807c; font-size: 10px; }
.rag-trend-header > small { font-weight: 700; }
.rag-trend-header > span { display: inline-flex; align-items: center; gap: 5px; }
.trend-key { width: 14px; height: 3px; margin-left: 6px; border-radius: 3px; background: #31836f; }
.trend-key.top3 { background: #4f8fc1; }
.trend-key.mrr { background: #b27a3e; }
.rag-trend svg { display: block; width: 100%; height: 180px; margin-top: 4px; overflow: visible; }
.rag-trend svg line { stroke: #e8efed; stroke-width: 1; }
.trend-line { fill: none; stroke-width: 2.5; stroke-linejoin: round; stroke-linecap: round; }
.trend-line.top1, .trend-dot.top1 { stroke: #31836f; fill: #31836f; }
.trend-line.top3, .trend-dot.top3 { stroke: #4f8fc1; fill: #4f8fc1; }
.trend-line.mrr, .trend-dot.mrr { stroke: #b27a3e; fill: #b27a3e; }
.rag-trend-axis { display: flex; justify-content: space-between; color: #a0aaa7; font-size: 9px; }
.embedding-status { display: block; margin-top: 7px; font-size: 10px; line-height: 1.4; }
.rag-playground-form { display: grid; grid-template-columns: minmax(0, 1fr) 150px 90px 150px auto; gap: 10px; align-items: end; padding: 15px; border: 1px solid #e4ece9; border-radius: 9px; background: #fbfefd; }
.rag-playground-inquiry { grid-column: 1 / -1; }
.rag-playground-form textarea, .rag-playground-form select, .rag-playground-form input { box-sizing: border-box; width: 100%; border: 1px solid #dce4e1; border-radius: 7px; padding: 10px 12px; color: #40504f; background: #fff; font: 12px inherit; outline: none; }
.rag-playground-form textarea { resize: vertical; min-height: 78px; }
.rag-playground-run { white-space: nowrap; }
.rag-playground-note { margin: 10px 2px 16px; }
.rag-playground-summary { display: grid; grid-template-columns: 1.3fr 1fr 1.2fr; gap: 10px; margin-bottom: 16px; }
.rag-playground-summary > div { display: flex; flex-direction: column; gap: 5px; min-width: 0; padding: 12px; border: 1px solid #e7efec; border-radius: 8px; background: #f5f8f7; }
.rag-playground-summary small, .rag-playground-results-header span { color: #8b9995; font-size: 9px; letter-spacing: .08em; }
.rag-playground-summary strong { color: #287b6b; font-size: 14px; overflow-wrap: anywhere; }
.rag-playground-summary span { color: #71807c; font-size: 10px; overflow-wrap: anywhere; }
.rag-playground-results { display: flex; flex-direction: column; gap: 8px; }
.rag-playground-results-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px; color: #40504f; font-size: 12px; }
.rag-playground-card { padding: 13px; border: 1px solid #e7edeb; border-radius: 8px; background: #fff; }
.rag-playground-card-head { display: flex; justify-content: space-between; gap: 12px; align-items: start; }
.rag-playground-card-head > div:first-child { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.rag-playground-card-head strong { color: #263b37; font-size: 12px; }
.rag-playground-card-head span, .rag-score-row, .rag-playground-card p { color: #71807c; font-size: 10px; }
.rag-score { display: flex; flex-direction: column; align-items: end; white-space: nowrap; }
.rag-score b { color: #31836f; font-size: 16px; }
.rag-score small { color: #8b9995; font-size: 9px; }
.rag-score-row { display: flex; flex-wrap: wrap; gap: 6px 18px; margin-top: 10px; padding-top: 9px; border-top: 1px solid #edf2f0; }
.rag-score-row b { color: #40504f; }
.rag-reasons { margin: 9px 0 0; }
.rag-unmet { margin: 6px 0 0; color: #b55b50 !important; }
.rag-playground-empty { margin-top: 14px; padding: 28px; border: 1px dashed #dce8e4; border-radius: 8px; color: #8b9995; text-align: center; font-size: 11px; }
.rag-match-status { display: flex; flex-direction: column; gap: 4px; margin: 0 0 14px; padding: 11px 13px; border: 1px solid; border-radius: 8px; font-size: 10px; }
.rag-match-status strong { font-size: 11px; }
.rag-match-status span { opacity: .82; }
.rag-match-reliable { border-color: #b9dfd2; background: #f1fbf7; color: #287b6b; }
.rag-match-review { border-color: #ead6aa; background: #fffaf0; color: #927027; }
.rag-match-no_reliable_match { border-color: #f0c9c4; background: #fff5f3; color: #a34e47; }
.rag-reranker-status { margin: -4px 0 14px; color: #71807c; font-size: 10px; }
.success-status { color: #31836f; }
@media (max-width: 900px) {
  .rag-playground-form { grid-template-columns: 1fr 1fr; }
  .rag-playground-inquiry { grid-column: 1 / -1; }
  .rag-playground-run { grid-column: 1 / -1; justify-self: start; }
  .rag-playground-summary { grid-template-columns: 1fr; }
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
  .product-detail.inline { grid-template-columns: 1fr; }
  .product-detail.inline .detail-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .product-panel .candidate-detail.inline { grid-template-columns: 1fr; }
  .product-panel .candidate-detail.inline .detail-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .run-steps { grid-template-columns: 1fr 1fr; }
  .rag-miss { grid-template-columns: 1fr; }
}
@media (max-width: 560px) {
  .main-content { padding: 18px 12px 30px; }
  h1 { font-size: 23px; }
  .topbar { flex-direction: column; margin-bottom: 22px; }
  .user-chip { align-self: stretch; justify-content: flex-end; }
  .panel { padding: 17px; }
  .requirement-grid, .quote-summary { grid-template-columns: 1fr; }
  .catalog-grid { grid-template-columns: 1fr; }
  .product-detail.inline .detail-grid { grid-template-columns: 1fr 1fr; }
  .product-panel .candidate-detail.inline .detail-grid { grid-template-columns: 1fr 1fr; }
  .customer-summary { align-items: flex-start; flex-wrap: wrap; }
  .match-check { width: 100%; margin-left: 50px; }
  .quotes-table { min-width: 620px; }
  .quote-detail-grid { grid-template-columns: 1fr; }
  .run-steps { grid-template-columns: 1fr; }
}
</style>
