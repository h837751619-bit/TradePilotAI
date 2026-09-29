export interface Product {
  id: number
  sku: string
  name: string
  category: string
  description: string
  material: string
  colors: string
  min_order_quantity: number
  lead_time_days: number
  unit_price_usd: number
  is_active: boolean
}

export interface QuoteDraft {
  id?: number
  sku: string
  quantity: number
  unitPrice: number
  total: number
  status: 'draft' | 'approved'
}
