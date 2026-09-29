import type { Product } from './types'

export interface WorkflowResult {
  inquiry: { quantity: number | null; destination_country: string | null; project_type: string | null; product_keywords: string[] }
  customer: { matched: boolean; company_name: string; country: string | null; contact_name: string | null; email: string | null }
  quote: { id: number; sku: string; quantity: number; unit_price_usd: number; total_price_usd: number; status: 'draft' | 'approved' }
  risk: { requires_approval: boolean; reasons: string[] }
}

export async function searchProducts(query: string): Promise<Product[]> {
  const params = new URLSearchParams()
  if (query.trim()) params.set('q', query.trim())
  const response = await fetch(`/api/products?${params.toString()}`)
  if (!response.ok) throw new Error('Unable to load products')
  return response.json() as Promise<Product[]>
}

export async function runInquiryWorkflow(inquiry: string, customerName = ''): Promise<WorkflowResult> {
  const response = await fetch('/api/workflow/inquiry-to-quote', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ inquiry, customer_name: customerName }),
  })
  if (!response.ok) {
    const detail = await response.json().catch(() => ({})) as { detail?: string; error?: { message?: string } }
    throw new Error(detail.error?.message ?? detail.detail ?? 'Unable to analyze inquiry')
  }
  return response.json() as Promise<WorkflowResult>
}

export async function approveQuote(quoteId: number): Promise<{ id: number; status: 'approved' }> {
  const response = await fetch(`/api/quotes/${quoteId}/approve`, { method: 'POST' })
  if (!response.ok) throw new Error('Unable to approve quote')
  return response.json() as Promise<{ id: number; status: 'approved' }>
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
  status: 'draft' | 'approved'
}

export async function fetchQuotes(): Promise<QuoteRecord[]> {
  const response = await fetch('/api/quotes')
  if (!response.ok) throw new Error('Unable to load quotes')
  return response.json() as Promise<QuoteRecord[]>
}

export interface AgentRun {
  run_id: string
  inquiry_text: string
  steps: { name: string; status: 'complete' | 'waiting' }[]
}

export async function fetchAgentRuns(): Promise<AgentRun[]> {
  const response = await fetch('/api/agent-runs')
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
  const response = await fetch(`/api/customers?${params.toString()}`)
  if (!response.ok) throw new Error('Unable to load customers')
  return response.json() as Promise<CustomerRecord[]>
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
  const response = await fetch('/api/evaluation')
  if (!response.ok) throw new Error('Unable to load evaluation metrics')
  return response.json() as Promise<EvaluationMetrics>
}
