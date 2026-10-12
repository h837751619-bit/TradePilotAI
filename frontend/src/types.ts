export interface Product {
  id: number
  sku: string
  name: string
  category: string
  description: string
  material: string
  colors: string
  match_tags: string
  min_order_quantity: number
  lead_time_days: number
  unit_price_usd: number
  is_active: boolean
  on_hand_quantity?: number
  reserved_quantity?: number
  available_quantity?: number
}

export interface QuoteDraft {
  id?: number
  sku: string
  quantity: number
  unitPrice: number
  total: number
  status: 'pending_selection' | 'draft' | 'approved'
}
