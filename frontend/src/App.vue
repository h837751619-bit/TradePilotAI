<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { approveQuote as approveQuoteApi, cancelQuote as cancelQuoteApi, createCustomer, createProduct, createUser, deleteCustomer, deleteProduct, fetchAgentRuns, fetchAIProviders, fetchAuthStatus, fetchCustomerQuotes, fetchCustomers, fetchEvaluation, fetchProductInventoryMovements, fetchQuoteDetail, fetchQuotes, fetchUsers, getAuthRole, getAuthToken, login, logout as logoutSession, runInquiryWorkflow, searchProducts, setAIProvider, suggestProductTags, updateCustomer, updateProduct, updateProductInventory, updateUser } from './api'
import type { AgentRun, AIProviderId, CustomerRecord, EvaluationMetrics, InventoryMovement, QuoteDetail, QuoteRecord, UserRecord } from './api'
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
const approvalLoading = ref(false)
const cancelLoading = ref(false)
const operatorId = 'jordan-davis'
const authEnabled = ref(false)
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
const userError = ref('')
const aiStatus = ref('idle')
const quote = ref<QuoteDraft>({
  sku: '—',
  quantity: 120,
  unitPrice: 0,
  total: 0,
  status: 'pending_selection',
})

const navKeys = ['inquiryWorkspace', 'products', 'quotes', 'agentTrace', 'customers', 'users'] as const
const initialNav = window.location.hash.slice(1) as (typeof navKeys)[number]
const activeNav = ref<(typeof navKeys)[number]>(navKeys.includes(initialNav) ? initialNav : 'inquiryWorkspace')
const translations = {
  zh: { inquiryWorkspace: '询盘工作台', products: '产品库', quotes: '报价单', agentTrace: 'Agent 追踪', salesOps: '销售运营', inquiryTitle: '询盘工作台', inquiry: '客户询盘', inquiryHint: '粘贴客户询盘，开始工作流。', new: '新建', detected: '已识别英语', edited: '刚刚编辑', analyze: '运行分析', requirements: '提取的需求', requirementsHint: '从客户消息中结构化提取。', complete: '已完成', quantity: '数量', destination: '目的地', project: '项目类型', signals: '产品信号', hotel: '酒店项目', matches: '产品匹配', matchesHint: '从产品知识库检索。', found: '个结果', search: '搜索', loading: '正在加载产品目录…', quote: '报价草稿', quoteHint: '选择产品后生成正式报价。', selected: '已选产品', unitPrice: '单价', discount: '批量折扣', total: '预计总价', approval: '需要人工审批', approvalHint: '折扣报价发送前必须审核。', selectProduct: '请先选择产品', selectProductHint: '选择产品后才会生成报价单。', approved: '报价已批准', approve: '批准报价', activity: 'Agent 活动', activityHint: '透明的工作流追踪。', operational: '系统运行正常', demo: '演示工作区', parsed: '询盘已解析', searched: '产品知识已搜索', checked: '库存与价格已检查', waiting: '等待人工审批', next: '需要下一步操作', live: '实时', unit: '件', projectHotel: '酒店项目', aluminumChair: '铝制 · 户外椅', english: '中文', quoteReview: '报价审核', customer: '客户', sku: 'SKU', status: '状态', action: '操作', refresh: '刷新', noQuotes: '暂无报价', reviewHint: '查看已生成的客户报价。' },
  en: { inquiryWorkspace: 'Inquiry Workspace', products: 'Products', quotes: 'Quotes', agentTrace: 'Agent Trace', salesOps: 'SALES OPERATIONS', inquiryTitle: 'Inquiry workspace', inquiry: 'Customer inquiry', inquiryHint: 'Paste an incoming inquiry to start the workflow.', new: 'NEW', detected: 'English detected', edited: 'Last edited just now', analyze: 'Run analysis', requirements: 'Extracted requirements', requirementsHint: 'Structured from the customer message.', complete: 'COMPLETE', quantity: 'QUANTITY', destination: 'DESTINATION', project: 'PROJECT TYPE', signals: 'PRODUCT SIGNALS', hotel: 'Hotel project', matches: 'Product matches', matchesHint: 'Retrieved from the product knowledge base.', found: 'FOUND', search: 'Search', loading: 'Loading product catalog…', quote: 'Quote draft', quoteHint: 'Select a product to generate the formal quote.', selected: 'SELECTED PRODUCT', unitPrice: 'Unit price', discount: 'Volume discount', total: 'Estimated total', approval: 'Human approval required', approvalHint: 'Discounted quote must be reviewed before sending.', selectProduct: 'Select a product first', selectProductHint: 'A quote is generated only after product selection.', approved: 'Quote approved', approve: 'Approve quote', activity: 'Agent activity', activityHint: 'Transparent workflow trace.', operational: 'System operational', demo: 'Demo workspace', parsed: 'Inquiry parsed', searched: 'Product knowledge searched', checked: 'Inventory and pricing checked', waiting: 'Awaiting human approval', next: 'Next action required', live: 'LIVE', unit: 'units', projectHotel: 'Hotel project', aluminumChair: 'Aluminum · Outdoor chair', english: 'English', quoteReview: 'Quote review', customer: 'Customer', sku: 'SKU', status: 'Status', action: 'Action', refresh: 'Refresh', noQuotes: 'No quotes yet', reviewHint: 'Review previously generated customer quotations.' },
  it: { inquiryWorkspace: 'Area richieste', products: 'Prodotti', quotes: 'Preventivi', agentTrace: 'Traccia Agent', salesOps: 'OPERAZIONI VENDITE', inquiryTitle: 'Area richieste', inquiry: 'Richiesta cliente', inquiryHint: 'Incolla una richiesta per avviare il flusso.', new: 'NUOVA', detected: 'Inglese rilevato', edited: 'Modificato ora', analyze: 'Avvia analisi', requirements: 'Requisiti estratti', requirementsHint: 'Strutturati dal messaggio del cliente.', complete: 'COMPLETATO', quantity: 'QUANTITÀ', destination: 'DESTINAZIONE', project: 'TIPO PROGETTO', signals: 'SEGNALI PRODOTTO', hotel: 'Progetto alberghiero', matches: 'Prodotti compatibili', matchesHint: 'Recuperati dalla knowledge base prodotti.', found: 'TROVATI', search: 'Cerca', loading: 'Caricamento catalogo…', quote: 'Bozza preventivo', quoteHint: 'Seleziona un prodotto per generare il preventivo.', selected: 'PRODOTTO SELEZIONATO', unitPrice: 'Prezzo unitario', discount: 'Sconto volume', total: 'Totale stimato', approval: 'Approvazione richiesta', approvalHint: 'Il preventivo scontato deve essere approvato.', selectProduct: 'Seleziona prima un prodotto', selectProductHint: 'Il preventivo viene generato dopo la selezione.', approved: 'Preventivo approvato', approve: 'Approva preventivo', activity: 'Attività Agent', activityHint: 'Traccia trasparente del flusso.', operational: 'Sistema operativo', demo: 'Area demo', parsed: 'Richiesta analizzata', searched: 'Ricerca prodotti completata', checked: 'Scorte e prezzi verificati', waiting: 'In attesa di approvazione', next: 'Azione richiesta', live: 'LIVE', unit: 'unità', projectHotel: 'Progetto alberghiero', aluminumChair: 'Alluminio · Sedia da esterno', english: 'Italiano', quoteReview: 'Revisione preventivi', customer: 'Cliente', sku: 'SKU', status: 'Stato', action: 'Azione', refresh: 'Aggiorna', noQuotes: 'Nessun preventivo', reviewHint: 'Rivedi i preventivi generati.' },
} as const
const t = (key: keyof typeof translations.en) => translations[locale.value][key]
const navItems = computed(() => navKeys.filter((key) => key !== 'users' || (authEnabled.value && authRole.value === 'admin')).map((key) => ({ key, label: key === 'customers' ? (locale.value === 'zh' ? '客户' : locale.value === 'it' ? 'Clienti' : 'Customers') : key === 'users' ? (locale.value === 'zh' ? '用户管理' : locale.value === 'it' ? 'Utenti' : 'Users') : t(key) })))
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
  if (key === 'users' && authRole.value === 'admin') await loadUsers()
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
    workflowResult.value = await runInquiryWorkflow(inquiry.value, customerName.value, sku)
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

onMounted(() => {
  window.addEventListener('popstate', () => {
    const key = window.location.hash.slice(1) as (typeof navKeys)[number]
    if (navKeys.includes(key)) void selectNav(key)
  })
  void fetchAIProviders().then((status) => { aiProvider.value = status.active; aiProviderOptions.value = status.providers }).catch(() => undefined)
  void fetchAuthStatus().then((status) => { authEnabled.value = status.enabled; if (status.enabled && authRole.value === 'admin' && activeNav.value === 'users') void loadUsers() }).catch(() => undefined)
  if (activeNav.value === 'inquiryWorkspace') void loadProducts()
  else void selectNav(activeNav.value)
})
</script>

<template>
  <div class="app-shell">
    <div v-if="authEnabled && !authToken" class="auth-gate">
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

      <section v-if="!['quotes', 'products', 'agentTrace', 'customers', 'users'].includes(activeNav)" class="workspace-grid">
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
            <div v-if="workflowResult?.product_matches.length" class="candidate-list"><h3>{{ candidateLabels.title }}</h3><article v-for="match in workflowResult.product_matches" :key="match.sku" class="candidate-card" :class="{ selected: selectedCandidateSku === match.sku }" @click="selectCandidate(match.sku)"><div><strong>{{ match.name }}</strong><span>{{ match.sku }} · {{ match.inventory_sufficient ? `${match.inventory_available} ${candidateLabels.available}` : candidateLabels.insufficient }}</span><small>${{ match.unit_price_usd.toFixed(2) }} · {{ match.lead_time_days }} days</small></div><b>{{ match.score }}%</b><small>{{ match.reasons.join(' · ') || candidateLabels.partial }}<em v-if="match.unmet_conditions.length"> · ⚠ {{ match.unmet_conditions.join(' · ') }}</em></small><button class="table-action" :disabled="loading || !match.inventory_sufficient" @click.stop="selectProductForQuote(match.sku)">{{ match.inventory_sufficient ? candidateLabels.use : candidateLabels.unavailable }}</button><div v-if="selectedCandidateSku === match.sku && productBySku.get(match.sku)" class="candidate-detail inline" @click.stop><div><span class="step">DETAIL</span><h3>{{ productBySku.get(match.sku)?.name }}</h3><p>{{ productBySku.get(match.sku)?.description }}</p><span class="candidate-tags">{{ productBySku.get(match.sku)?.match_tags || '—' }}</span></div><div class="detail-grid"><span><small>SKU</small><strong>{{ productBySku.get(match.sku)?.sku }}</strong></span><span><small>MATERIAL</small><strong>{{ productBySku.get(match.sku)?.material || '—' }}</strong></span><span><small>COLORS</small><strong>{{ productBySku.get(match.sku)?.colors || '—' }}</strong></span><span><small>MOQ</small><strong>{{ productBySku.get(match.sku)?.min_order_quantity }} {{ t('unit') }}</strong></span><span><small>INVENTORY</small><strong>{{ match.inventory_available }}</strong></span><span><small>LEAD TIME</small><strong>{{ productBySku.get(match.sku)?.lead_time_days }} days</strong></span></div></div></article></div>
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
        <p v-if="!agentRuns.length" class="muted">{{ t('noQuotes') }}</p>
        <div v-for="run in agentRuns" :key="run.run_id" class="run-card"><div class="run-header"><strong>Run {{ run.run_id }}</strong><small class="muted">{{ run.created_at ? new Date(run.created_at).toLocaleString(locale === 'zh' ? 'zh-CN' : locale === 'it' ? 'it-IT' : 'en-US') : '—' }}</small><span class="muted">{{ run.inquiry_text }}</span></div><div class="run-steps"><div v-for="step in run.steps" :key="step.name" class="trace-item" :class="step.status === 'complete' ? 'done' : 'current'"><span>{{ step.status === 'complete' ? '✓' : '!' }}</span><div><strong>{{ step.name }}</strong><small>{{ step.status === 'complete' ? t('complete') : t('waiting') }}</small></div></div></div></div>
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
      <section v-else-if="activeNav === 'users' && authRole === 'admin'" class="panel quotes-page">
        <div class="panel-header"><div><h2>User management</h2><p>Manage access, roles, and active accounts.</p></div><div class="detail-actions"><button class="secondary-button" @click="loadUsers">Refresh</button><button class="primary-button compact" @click="openUserForm">＋ New user</button></div></div>
        <p v-if="userError" class="error-message">{{ userError }}</p>
        <p v-if="usersLoading" class="muted">Loading users…</p>
        <div v-else class="users-table-wrap"><table class="quotes-table"><thead><tr><th>USERNAME</th><th>ROLE</th><th>STATUS</th><th>ACTION</th></tr></thead><tbody><tr v-for="user in users" :key="user.id"><td>{{ user.username }}</td><td><select :value="user.role" @change="changeUserRole(user, ($event.target as HTMLSelectElement).value as UserRecord['role'])"><option value="admin">admin</option><option value="approver">approver</option><option value="viewer">viewer</option></select></td><td><span :class="['badge', user.is_active ? 'success' : 'warning']">{{ user.is_active ? 'ACTIVE' : 'INACTIVE' }}</span></td><td><button class="table-action" :disabled="user.username === loginForm.username" @click="toggleUser(user)">{{ user.is_active ? 'Deactivate' : 'Activate' }}</button></td></tr></tbody></table></div>
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
  .product-detail.inline { grid-template-columns: 1fr; }
  .product-detail.inline .detail-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .product-panel .candidate-detail.inline { grid-template-columns: 1fr; }
  .product-panel .candidate-detail.inline .detail-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
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
  .product-detail.inline .detail-grid { grid-template-columns: 1fr 1fr; }
  .product-panel .candidate-detail.inline .detail-grid { grid-template-columns: 1fr 1fr; }
  .customer-summary { align-items: flex-start; flex-wrap: wrap; }
  .match-check { width: 100%; margin-left: 50px; }
  .quotes-table { min-width: 620px; }
  .quote-detail-grid { grid-template-columns: 1fr; }
  .run-steps { grid-template-columns: 1fr; }
}
</style>
