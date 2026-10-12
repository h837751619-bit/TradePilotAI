import type { Product } from './types'

export type AIProviderId = 'rules' | 'ollama' | 'openai_compatible' | 'deepseek' | 'kimi'
export interface AIProviderStatus { active: AIProviderId; providers: { id: AIProviderId; name: string; model?: string; available: boolean }[] }
export interface AuthStatus { enabled: boolean }
export interface UserRecord { id: number; username: string; role: 'admin' | 'approver' | 'viewer'; is_active: boolean }

let authToken = sessionStorage.getItem('tradepilot_access_token') ?? ''
let refreshToken = sessionStorage.getItem('tradepilot_refresh_token') ?? ''

function clearStoredAuth(): void {
  authToken = ''
  refreshToken = ''
  sessionStorage.removeItem('tradepilot_access_token')
  sessionStorage.removeItem('tradepilot_refresh_token')
  sessionStorage.removeItem('tradepilot_role')
}

async function apiFetch(input: RequestInfo | URL, init: RequestInit = {}, retry = true): Promise<Response> {
  const response = await fetch(input, init)
  const url = String(input)
  if (response.status !== 401 || !retry || !refreshToken || url.includes('/api/auth/')) return response
  try {
    await refreshSession()
    const headers = new Headers(init.headers)
    headers.set('Authorization', `Bearer ${authToken}`)
    return apiFetch(input, { ...init, headers }, false)
  } catch {
    clearStoredAuth()
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
  sessionStorage.setItem('tradepilot_access_token', authToken)
  sessionStorage.setItem('tradepilot_refresh_token', refreshToken)
  sessionStorage.setItem('tradepilot_role', result.role)
  return result
}

export async function refreshSession(): Promise<{ access_token: string; refresh_token: string; role: UserRecord['role'] }> {
  const response = await fetch('/api/auth/refresh', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ refresh_token: refreshToken }) })
  if (!response.ok) throw await apiError(response, 'Unable to refresh session')
  const result = await response.json() as { access_token: string; refresh_token: string; role: UserRecord['role'] }
  authToken = result.access_token
  refreshToken = result.refresh_token
  sessionStorage.setItem('tradepilot_access_token', authToken)
  sessionStorage.setItem('tradepilot_refresh_token', refreshToken)
  sessionStorage.setItem('tradepilot_role', result.role)
  return result
}

export async function logout(): Promise<void> {
  if (refreshToken) await fetch('/api/auth/logout', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ refresh_token: refreshToken }) })
  clearStoredAuth()
}

function authHeaders(): Record<string, string> {
  return authToken ? { Authorization: `Bearer ${authToken}` } : {}
}

export function getAuthRole(): UserRecord['role'] | '' { return (sessionStorage.getItem('tradepilot_role') as UserRecord['role'] | null) ?? '' }

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

export interface WorkflowResult {
  inquiry: { quantity: number | null; destination_country: string | null; project_type: string | null; product_keywords: string[]; budget_usd: number | null; max_lead_time_days: number | null; ai_provider: string }
  customer: { matched: boolean; company_name: string; country: string | null; contact_name: string | null; email: string | null }
  quote: { id: number | null; sku: string; quantity: number; unit_price_usd: number; total_price_usd: number; status: 'pending_selection' | 'draft' | 'approved' }
  risk: { requires_approval: boolean; reasons: string[] }
  product_matches: { sku: string; name: string; score: number; reasons: string[]; unmet_conditions: string[]; inventory_available: number; inventory_sufficient: boolean; unit_price_usd: number; lead_time_days: number }[]
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

export async function runInquiryWorkflow(inquiry: string, customerName = '', selectedSku?: string): Promise<WorkflowResult> {
  const response = await apiFetch('/api/workflow/inquiry-to-quote', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ inquiry, customer_name: customerName, selected_sku: selectedSku }),
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
  product_matches: { sku: string; name: string; score: number; reasons: string[]; unmet_conditions: string[] }[]
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
