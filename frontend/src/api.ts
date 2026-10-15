import type { Product } from './types'

export type AIProviderId = 'rules' | 'ollama' | 'openai_compatible' | 'deepseek' | 'kimi'
export interface AIProviderStatus { active: AIProviderId; providers: { id: AIProviderId; name: string; model?: string; available: boolean }[] }
export interface AIProviderConfig { id: AIProviderId; name: string; base_url: string; model: string; timeout_seconds: number | null; api_key_configured: boolean; available: boolean }
export interface AISettings { active: AIProviderId; providers: AIProviderConfig[]; api_key_storage: 'runtime_only' }
export interface AuthStatus { enabled: boolean }
export interface UserRecord { id: number; username: string; role: 'admin' | 'approver' | 'viewer'; is_active: boolean }

const authStorage = window.localStorage
const legacyAuthStorage = window.sessionStorage

function readAuthValue(key: string): string {
  const value = authStorage.getItem(key) ?? legacyAuthStorage.getItem(key) ?? ''
  if (value && !authStorage.getItem(key)) authStorage.setItem(key, value)
  return value
}

let authToken = readAuthValue('tradepilot_access_token')
let refreshToken = readAuthValue('tradepilot_refresh_token')
let refreshInFlight: Promise<void> | null = null

function clearStoredAuth(): void {
  authToken = ''
  refreshToken = ''
  authStorage.removeItem('tradepilot_access_token')
  authStorage.removeItem('tradepilot_refresh_token')
  authStorage.removeItem('tradepilot_role')
  legacyAuthStorage.removeItem('tradepilot_access_token')
  legacyAuthStorage.removeItem('tradepilot_refresh_token')
  legacyAuthStorage.removeItem('tradepilot_role')
}

async function apiFetch(input: RequestInfo | URL, init: RequestInit = {}, retry = true): Promise<Response> {
  const response = await fetch(input, init)
  const url = String(input)
  if (response.status !== 401 || !retry || !refreshToken || url.includes('/api/auth/')) return response
  try {
    if (!refreshInFlight) {
      refreshInFlight = refreshSession().then(() => undefined).finally(() => { refreshInFlight = null })
    }
    await refreshInFlight
    const headers = new Headers(init.headers)
    headers.set('Authorization', `Bearer ${authToken}`)
    return apiFetch(input, { ...init, headers }, false)
  } catch {
    clearStoredAuth()
    window.dispatchEvent(new Event('tradepilot-auth-invalid'))
    return response
  }
}

export function getAuthToken(): string { return authToken }

export async function fetchAuthStatus(): Promise<AuthStatus> {
  const response = await fetch('/api/auth/status')
  if (!response.ok) throw await apiError(response, 'Unable to load authentication status')
  return response.json() as Promise<AuthStatus>
}

export async function login(username: string, password: string): Promise<{ access_token: string; refresh_token: string; expires_in: number; role: UserRecord['role'] }> {
  const response = await fetch('/api/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, password }) })
  if (!response.ok) throw await apiError(response, 'Unable to sign in')
  const result = await response.json() as { access_token: string; refresh_token: string; expires_in: number; role: UserRecord['role'] }
  authToken = result.access_token
  refreshToken = result.refresh_token
  authStorage.setItem('tradepilot_access_token', authToken)
  authStorage.setItem('tradepilot_refresh_token', refreshToken)
  authStorage.setItem('tradepilot_role', result.role)
  legacyAuthStorage.removeItem('tradepilot_access_token')
  legacyAuthStorage.removeItem('tradepilot_refresh_token')
  legacyAuthStorage.removeItem('tradepilot_role')
  return result
}

export async function refreshSession(): Promise<{ access_token: string; refresh_token: string; role: UserRecord['role'] }> {
  const response = await fetch('/api/auth/refresh', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ refresh_token: refreshToken }) })
  if (!response.ok) throw await apiError(response, 'Unable to refresh session')
  const result = await response.json() as { access_token: string; refresh_token: string; role: UserRecord['role'] }
  authToken = result.access_token
  refreshToken = result.refresh_token
  authStorage.setItem('tradepilot_access_token', authToken)
  authStorage.setItem('tradepilot_refresh_token', refreshToken)
  authStorage.setItem('tradepilot_role', result.role)
  return result
}

export async function logout(): Promise<void> {
  if (refreshToken) await fetch('/api/auth/logout', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ refresh_token: refreshToken }) })
  clearStoredAuth()
}

function authHeaders(): Record<string, string> {
  return authToken ? { Authorization: `Bearer ${authToken}` } : {}
}

export function getAuthRole(): UserRecord['role'] | '' { return (authStorage.getItem('tradepilot_role') ?? legacyAuthStorage.getItem('tradepilot_role') ?? '') as UserRecord['role'] | '' }

export async function fetchUsers(): Promise<UserRecord[]> {
  const response = await apiFetch('/api/users', { headers: authHeaders() })
  if (!response.ok) throw await apiError(response, 'Unable to load users')
  return response.json() as Promise<UserRecord[]>
}

export async function createUser(payload: { username: string; password: string; role: UserRecord['role'] }): Promise<UserRecord> {
  const response = await apiFetch('/api/users', { method: 'POST', headers: { ...authHeaders(), 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
  if (!response.ok) throw await apiError(response, 'Unable to create user')
  return response.json() as Promise<UserRecord>
}

export async function updateUser(id: number, payload: { role?: UserRecord['role']; password?: string; is_active?: boolean }): Promise<UserRecord> {
  const response = await apiFetch(`/api/users/${id}`, { method: 'PATCH', headers: { ...authHeaders(), 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
  if (!response.ok) throw await apiError(response, 'Unable to update user')
  return response.json() as Promise<UserRecord>
}

async function apiError(response: Response, fallback: string): Promise<Error> {
  const body = await response.json().catch(() => ({})) as { detail?: string; error?: { message?: string } }
  const message = body.error?.message ?? body.detail ?? `${fallback} (HTTP ${response.status})`
  return new Error(message)
}

export async function fetchAIProviders(): Promise<AIProviderStatus> {
  const response = await apiFetch('/api/ai/providers')
  if (!response.ok) throw new Error('Unable to load AI providers')
  return response.json() as Promise<AIProviderStatus>
}

export async function setAIProvider(provider: AIProviderId): Promise<{ active: AIProviderId }> {
  const response = await apiFetch('/api/ai/providers', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ provider }) })
  if (!response.ok) throw new Error('Unable to switch AI provider')
  return response.json() as Promise<{ active: AIProviderId }>
}

export async function fetchAISettings(): Promise<AISettings> {
  const response = await apiFetch('/api/settings/ai', { headers: authHeaders() })
  if (!response.ok) throw await apiError(response, 'Unable to load AI settings')
  return response.json() as Promise<AISettings>
}

export async function updateAISettings(payload: { provider: AIProviderId; base_url?: string; model?: string; timeout_seconds?: number; api_key?: string }): Promise<{ active: AIProviderId; updated: AIProviderId; api_key_configured: boolean }> {
  const response = await apiFetch('/api/settings/ai', { method: 'PATCH', headers: { ...authHeaders(), 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
  if (!response.ok) throw await apiError(response, 'Unable to save AI settings')
  return response.json()
}

export interface AIConnectionTestResult { provider: AIProviderId; success: boolean; model: string | null; latency_ms: number; message: string }

export async function testAIConnection(provider: AIProviderId): Promise<AIConnectionTestResult> {
  const response = await apiFetch('/api/settings/ai/test', { method: 'POST', headers: { ...authHeaders(), 'Content-Type': 'application/json' }, body: JSON.stringify({ provider }) })
  if (!response.ok) throw await apiError(response, 'Unable to test AI connection')
  return response.json() as Promise<AIConnectionTestResult>
}

export interface AIDiagnosticCheck { id: string; name: string; status: 'ok' | 'error' | 'disabled' | 'configured' | 'not_configured'; latency_ms: number; message: string }
export interface AIDiagnostics { active: AIProviderId; checks: AIDiagnosticCheck[] }

export async function fetchAIDiagnostics(): Promise<AIDiagnostics> {
  const response = await apiFetch('/api/settings/ai/diagnostics', { headers: authHeaders() })
  if (!response.ok) throw await apiError(response, 'Unable to load AI diagnostics')
  return response.json() as Promise<AIDiagnostics>
}

export interface EmbeddingProfile { id: string; provider: string; model: string }
export interface EmbeddingSettings { active: EmbeddingProfile; profiles: EmbeddingProfile[] }

export async function fetchEmbeddingSettings(): Promise<EmbeddingSettings> {
  const response = await apiFetch('/api/settings/embeddings')
  if (!response.ok) throw await apiError(response, 'Unable to load embedding profiles')
  return response.json() as Promise<EmbeddingSettings>
}

export interface EmbeddingSwitchJob { job_id: string; status: 'queued' | 'running' | 'succeeded' | 'failed'; profile: EmbeddingProfile; indexed_products: number | null; processed_products: number; total_products: number | null; progress_percent: number; error: string | null }

export async function switchEmbeddingProfile(profileId: string, signal?: AbortSignal): Promise<EmbeddingSwitchJob> {
  const response = await apiFetch('/api/settings/embeddings', { method: 'POST', headers: { ...authHeaders(), 'Content-Type': 'application/json' }, body: JSON.stringify({ profile_id: profileId }), signal })
  if (!response.ok) throw await apiError(response, 'Unable to switch embedding profile')
  return response.json() as Promise<EmbeddingSwitchJob>
}

export async function fetchEmbeddingJob(jobId: string, signal?: AbortSignal): Promise<EmbeddingSwitchJob> {
  const response = await apiFetch(`/api/settings/embeddings/jobs/${encodeURIComponent(jobId)}`, { signal })
  if (!response.ok) throw await apiError(response, 'Unable to load embedding job')
  return response.json() as Promise<EmbeddingSwitchJob>
}

export interface EmbeddingJobHistory { items: (EmbeddingSwitchJob & { created_at: string; updated_at: string })[]; total: number; limit: number; offset: number }

export async function fetchEmbeddingJobs(limit = 6, offset = 0): Promise<EmbeddingJobHistory> {
  const response = await apiFetch(`/api/settings/embeddings/jobs?limit=${limit}&offset=${offset}`)
  if (!response.ok) throw await apiError(response, 'Unable to load embedding job history')
  return response.json()
}

export interface WorkflowResult {
  retrieval_mode: 'rules' | 'semantic' | 'rules_fallback'
  explanation_mode: 'grounded_ai' | 'rules' | 'rules_fallback'
  explanation_provider: string
  explanation_model: string | null
  inquiry: { quantity: number | null; destination_country: string | null; project_type: string | null; product_keywords: string[]; budget_usd: number | null; max_lead_time_days: number | null; ai_provider: string }
  customer: { matched: boolean; company_name: string; country: string | null; contact_name: string | null; email: string | null }
  quote: { id: number | null; sku: string; quantity: number; unit_price_usd: number; total_price_usd: number; status: 'pending_selection' | 'draft' | 'approved' }
  risk: { requires_approval: boolean; reasons: string[] }
  product_matches: { sku: string; name: string; score: number; semantic_score?: number | null; reasons: string[]; explanation: string; model_explanation?: string | null; evidence: { field: string; value: string | number }[]; unmet_conditions: string[]; inventory_available: number; inventory_sufficient: boolean; unit_price_usd: number; lead_time_days: number }[]
}

export interface RagPlaygroundResult {
  mode: 'rules' | 'semantic'
  retrieval_mode: 'rules' | 'semantic' | 'semantic_empty' | 'rules_fallback'
  retrieval_error?: string
  match_status: 'reliable' | 'review' | 'no_reliable_match'
  match_threshold: number
  parsed: {
    quantity: number | null
    destination_country: string | null
    project_type: string | null
    product_keywords: string[]
    budget_usd: number | null
    max_lead_time_days: number | null
  }
  timings: { parse_ms: number; retrieval_ms: number; ranking_ms: number; reranker_ms?: number; total_ms: number }
  reranker: { enabled: boolean; model: string | null; scores_returned: number; error: string | null }
  candidates: {
    sku: string
    name: string
    score: number
    semantic_score?: number | null
    reasons: string[]
    explanation?: string
    unmet_conditions: string[]
    inventory_available: number
    inventory_sufficient: boolean
    unit_price_usd: number
    lead_time_days: number
    reranker_score?: number | null
  }[]
}

export async function runRagPlayground(payload: { inquiry: string; mode: 'rules' | 'semantic'; top_k: number; score_threshold: number }): Promise<RagPlaygroundResult> {
  const response = await apiFetch('/api/rag/playground', {
    method: 'POST',
    headers: { ...authHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw await apiError(response, 'Unable to run RAG playground')
  return response.json() as Promise<RagPlaygroundResult>
}

export async function searchProducts(query: string, includeInactive = false): Promise<Product[]> {
  const params = new URLSearchParams()
  if (query.trim()) params.set('q', query.trim())
  if (includeInactive) params.set('include_inactive', 'true')
  const response = await apiFetch(`/api/products?${params.toString()}`)
  if (!response.ok) throw new Error('Unable to load products')
  return response.json() as Promise<Product[]>
}

export async function updateProduct(sku: string, payload: Partial<Pick<Product, 'material' | 'colors' | 'match_tags' | 'min_order_quantity' | 'lead_time_days' | 'unit_price_usd' | 'is_active'>>): Promise<Product> {
  const response = await apiFetch(`/api/products/${encodeURIComponent(sku)}`, { method: 'PATCH', headers: { ...authHeaders(), 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
  if (!response.ok) throw await apiError(response, 'Unable to update product')
  return response.json() as Promise<Product>
}

export async function updateProductInventory(sku: string, onHandQuantity: number, reason = 'manual adjustment'): Promise<Pick<Product, 'sku' | 'on_hand_quantity' | 'reserved_quantity' | 'available_quantity'>> {
  const response = await apiFetch(`/api/products/${encodeURIComponent(sku)}/inventory`, { method: 'PATCH', headers: { ...authHeaders(), 'Content-Type': 'application/json' }, body: JSON.stringify({ on_hand_quantity: onHandQuantity, reason }) })
  if (!response.ok) throw await apiError(response, 'Unable to update inventory')
  return response.json()
}

export interface InventoryMovement { id: number; quote_id: number | null; sku: string; quantity: number; movement_type: 'reserve' | 'deduct' | 'release' | 'adjustment'; actor: string; reason: string | null; previous_quantity: number | null; new_quantity: number | null; created_at: string | null }

export async function fetchProductInventoryMovements(sku: string): Promise<InventoryMovement[]> {
  const response = await apiFetch(`/api/products/${encodeURIComponent(sku)}/inventory/movements`)
  if (!response.ok) throw await apiError(response, 'Unable to load inventory history')
  return response.json() as Promise<InventoryMovement[]>
}

export type ProductCreateInput = Omit<Product, 'id'>
export async function createProduct(payload: ProductCreateInput): Promise<Product> {
  const response = await apiFetch('/api/products', { method: 'POST', headers: { ...authHeaders(), 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
  if (!response.ok) throw await apiError(response, 'Unable to create product')
  return response.json() as Promise<Product>
}

export async function deleteProduct(sku: string): Promise<void> {
  const response = await apiFetch(`/api/products/${encodeURIComponent(sku)}`, { method: 'DELETE', headers: authHeaders() })
  if (!response.ok) throw await apiError(response, 'Unable to delete product')
}

export async function suggestProductTags(sku: string): Promise<{ sku: string; provider: string; model?: string; suggestions: string[] }> {
  const response = await apiFetch(`/api/products/${encodeURIComponent(sku)}/suggest-tags`, { method: 'POST' })
  if (!response.ok) throw await apiError(response, 'Unable to suggest product tags')
  return response.json()
}

export async function runInquiryWorkflow(inquiry: string, customerName = '', selectedSku?: string, parsedInquiry?: WorkflowResult['inquiry']): Promise<WorkflowResult> {
  const response = await apiFetch('/api/workflow/inquiry-to-quote', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ inquiry, customer_name: customerName, selected_sku: selectedSku, ...parsedInquiry }),
  })
  if (!response.ok) {
    const detail = await response.json().catch(() => ({})) as { detail?: string; error?: { message?: string } }
    throw new Error(detail.error?.message ?? detail.detail ?? 'Unable to analyze inquiry')
  }
  return response.json() as Promise<WorkflowResult>
}

export async function approveQuote(quoteId: number, actorId = 'jordan-davis'): Promise<{ id: number; status: 'approved' }> {
  const headers: Record<string, string> = { 'X-Actor-Id': actorId }
  if (authToken) headers.Authorization = `Bearer ${authToken}`
  const response = await apiFetch(`/api/quotes/${quoteId}/approve`, { method: 'POST', headers })
  if (!response.ok) throw await apiError(response, 'Unable to approve quote')
  return response.json() as Promise<{ id: number; status: 'approved' }>
}

export async function cancelQuote(quoteId: number, actorId = 'jordan-davis'): Promise<{ id: number; status: 'cancelled' }> {
  const headers: Record<string, string> = { 'X-Actor-Id': actorId }
  if (authToken) headers.Authorization = `Bearer ${authToken}`
  const response = await apiFetch(`/api/quotes/${quoteId}/cancel`, { method: 'POST', headers })
  if (!response.ok) throw await apiError(response, 'Unable to cancel quote')
  return response.json() as Promise<{ id: number; status: 'cancelled' }>
}

export interface QuoteRecord {
  id: number
  customer_name: string
  inquiry_text: string
  sku: string
  quantity: number
  unit_price_usd: number
  total_price_usd: number
  discount_percent: number
  status: 'draft' | 'approved' | 'cancelled'
}

export interface QuoteDetail extends QuoteRecord {
  risk: { requires_approval: boolean; reasons: string[] }
  email: { subject: string; body: string; status: string }
  product_matches: { sku: string; name: string; score: number; semantic_score?: number | null; reasons: string[]; unmet_conditions: string[] }[]
  approval_history: { id: number; from_status: string; to_status: string; actor: string; created_at: string }[]
  inventory_movements: { id: number; sku: string; quantity: number; movement_type: 'reserve' | 'deduct' | 'release'; actor: string; created_at: string | null }[]
}

export async function fetchQuotes(): Promise<QuoteRecord[]> {
  const response = await apiFetch('/api/quotes')
  if (!response.ok) throw new Error('Unable to load quotes')
  return response.json() as Promise<QuoteRecord[]>
}

export async function fetchQuoteDetail(id: number): Promise<QuoteDetail> {
  const response = await apiFetch(`/api/quotes/${id}`)
  if (!response.ok) throw await apiError(response, 'Unable to load quote detail')
  return response.json() as Promise<QuoteDetail>
}

export interface AgentRun {
  run_id: string
  inquiry_text: string
  created_at: string | null
  steps: { name: string; status: 'complete' | 'waiting' }[]
}

export async function fetchAgentRuns(): Promise<AgentRun[]> {
  const response = await apiFetch('/api/agent-runs')
  if (!response.ok) throw new Error('Unable to load agent runs')
  return response.json() as Promise<AgentRun[]>
}

export interface CustomerRecord {
  id: number
  company_name: string
  contact_name: string
  country: string
  email: string
}

export async function fetchCustomers(query = ''): Promise<CustomerRecord[]> {
  const params = new URLSearchParams()
  if (query.trim()) params.set('q', query.trim())
  const response = await apiFetch(`/api/customers?${params.toString()}`)
  if (!response.ok) throw new Error('Unable to load customers')
  return response.json() as Promise<CustomerRecord[]>
}

export type CustomerInput = Omit<CustomerRecord, 'id'>

export async function createCustomer(payload: CustomerInput): Promise<CustomerRecord> {
  const response = await apiFetch('/api/customers', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
  if (!response.ok) throw await apiError(response, 'Unable to create customer')
  return response.json() as Promise<CustomerRecord>
}

export async function updateCustomer(id: number, payload: Partial<CustomerInput>): Promise<CustomerRecord> {
  const response = await apiFetch(`/api/customers/${id}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
  if (!response.ok) throw await apiError(response, 'Unable to update customer')
  return response.json() as Promise<CustomerRecord>
}

export async function deleteCustomer(id: number): Promise<void> {
  const response = await apiFetch(`/api/customers/${id}`, { method: 'DELETE' })
  if (!response.ok) throw await apiError(response, 'Unable to delete customer')
}

export interface CustomerQuote { id: number; sku: string; quantity: number; total_price_usd: number; status: 'draft' | 'approved' | 'cancelled'; inquiry_text: string }

export async function fetchCustomerQuotes(id: number): Promise<CustomerQuote[]> {
  const response = await apiFetch(`/api/customers/${id}/quotes`)
  if (!response.ok) throw new Error('Unable to load customer quotes')
  return response.json() as Promise<CustomerQuote[]>
}

export interface EvaluationMetrics {
  cases: number
  requirement_accuracy: number
  product_match_rate: number
  quote_success_rate: number
  task_success_rate: number
  failure_detection_rate: number
  failure_reasons: Record<string, number>
}

export async function fetchEvaluation(): Promise<EvaluationMetrics> {
  const response = await apiFetch('/api/evaluation')
  if (!response.ok) throw new Error('Unable to load evaluation metrics')
  return response.json() as Promise<EvaluationMetrics>
}

export interface RagEvaluationMetrics {
  id?: number
  mode: 'rules' | 'semantic'
  embedding_provider?: string
  embedding_model?: string
  retrieval_config?: Record<string, unknown>
  cases: number
  evaluated_cases: number
  top1_recall: number
  top3_recall: number
  mrr: number
  misses: { text: string; expected_sku: string; returned_skus: string[]; rank: number | null }[]
  created_at?: string | null
}

export async function fetchRagEvaluation(mode: RagEvaluationMetrics['mode']): Promise<RagEvaluationMetrics> {
  const response = await apiFetch(`/api/evaluation/rag?mode=${mode}`)
  if (!response.ok) throw await apiError(response, 'Unable to load RAG evaluation metrics')
  return response.json() as Promise<RagEvaluationMetrics>
}

export async function runRagEvaluation(mode: RagEvaluationMetrics['mode']): Promise<RagEvaluationMetrics> {
  const response = await apiFetch(`/api/evaluation/rag/run?mode=${mode}`, { method: 'POST' })
  if (!response.ok) throw await apiError(response, 'Unable to run RAG evaluation')
  return response.json() as Promise<RagEvaluationMetrics>
}

export async function fetchRagEvaluationHistory(limit = 20): Promise<RagEvaluationMetrics[]> {
  const response = await apiFetch(`/api/evaluation/rag/history?limit=${limit}`)
  if (!response.ok) throw await apiError(response, 'Unable to load RAG evaluation history')
  return response.json() as Promise<RagEvaluationMetrics[]>
}
