// lib/api.ts — Cliente HTTP para el backend

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

type FetchOptions = {
  method?: string
  body?: unknown
  token?: string
}

async function apiFetch<T>(endpoint: string, opts: FetchOptions = {}): Promise<T> {
  const { method = "GET", body, token } = opts

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  }
  if (token) {
    headers["Authorization"] = `Bearer ${token}`
  }

  const res = await fetch(`${API_URL}/api${endpoint}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Error de conexion" }))
    throw new Error(error.detail || `Error ${res.status}`)
  }

  return res.json()
}

// ── Auth ──────────────────────────────────────────────────

export type AuthResponse = {
  access_token: string
  user_id: string
  tenant_id: string
}

export type UserResponse = {
  id: string
  email: string
  name: string
  role: string
  tenant_id: string
  tenant_name: string
}

export function register(data: { email: string; password: string; name: string; business_name: string }) {
  return apiFetch<AuthResponse>("/auth/register", { method: "POST", body: data })
}

export function login(data: { email: string; password: string }) {
  return apiFetch<AuthResponse>("/auth/login", { method: "POST", body: data })
}

export function getMe(token: string) {
  return apiFetch<UserResponse>("/auth/me", { token })
}

// ── Config ────────────────────────────────────────────────

export type AgentConfig = {
  business_name: string
  business_description: string
  business_address: string
  business_phone: string
  business_website: string
  business_hours: Record<string, string>
  agent_name: string
  agent_tone: string
  use_cases: string[]
  system_prompt: string
  fallback_message: string
  error_message: string
  knowledge_base: string
  whatsapp_provider: string
  ai_provider: string
  ai_model: string
  is_setup_complete: boolean
}

export function getConfig(token: string) {
  return apiFetch<AgentConfig>("/config", { token })
}

export function updateConfig(token: string, data: Partial<AgentConfig>) {
  return apiFetch("/config", { method: "PUT", body: data, token })
}

export function updateWhatsApp(token: string, data: { provider: string; credentials: Record<string, string> }) {
  return apiFetch("/config/whatsapp", { method: "PUT", body: data, token })
}

export function updateAI(token: string, data: { provider: string; api_key: string; model: string }) {
  return apiFetch("/config/ai", { method: "PUT", body: data, token })
}

export function generatePrompt(token: string) {
  return apiFetch<{ system_prompt: string }>("/config/generate-prompt", { method: "POST", token })
}

export function completeSetup(token: string, system_prompt: string) {
  return apiFetch("/config/complete-setup", { method: "POST", body: { system_prompt }, token })
}

export function getWebhookUrl(token: string) {
  return apiFetch<{ webhook_url: string; instructions: string }>("/config/webhook-url", { token })
}

// ── Conversations ─────────────────────────────────────────

export type ConversationSummary = {
  id: string
  phone_number: string
  contact_name: string | null
  status: string
  is_ai_active: boolean
  last_message: string | null
  last_message_at: string | null
  message_count: number
}

export type MessageData = {
  id: string
  role: string
  content: string
  created_at: string
}

export type ConversationDetail = {
  id: string
  phone_number: string
  contact_name: string | null
  status: string
  is_ai_active: boolean
  created_at: string
  messages: MessageData[]
}

export function getConversations(token: string, params?: { status?: string; search?: string }) {
  const query = new URLSearchParams(params as Record<string, string>).toString()
  return apiFetch<ConversationSummary[]>(`/conversations${query ? `?${query}` : ""}`, { token })
}

export function getConversation(token: string, id: string) {
  return apiFetch<ConversationDetail>(`/conversations/${id}`, { token })
}

export function toggleAI(token: string, id: string) {
  return apiFetch<{ is_ai_active: boolean }>(`/conversations/${id}/toggle-ai`, { method: "PATCH", token })
}

// ── Analytics ─────────────────────────────────────────────

export type AnalyticsSummary = {
  total_conversations: number
  active_conversations: number
  total_messages_today: number
  total_messages_week: number
  total_messages_month: number
  daily_usage: { date: string; messages_received: number; messages_sent: number }[]
}

export function getAnalytics(token: string, days = 30) {
  return apiFetch<AnalyticsSummary>(`/analytics/summary?days=${days}`, { token })
}
