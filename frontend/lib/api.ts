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
  niche: string
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
  onboarding_questions: string[]
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

export type AutoSetupResult = {
  agent_name: string
  agent_tone: string
  business_name: string
  business_description: string
  business_phone: string
  business_website: string
  business_address: string
  business_hours: Record<string, string>
  system_prompt: string
  services: { name: string; niche: string; resources: { name: string; type: string; capacity: number; duration_minutes: number; description: string }[] }[]
}

export function autoSetup(token: string, data: { description: string; url?: string }) {
  return apiFetch<AutoSetupResult>("/config/auto-setup", { method: "POST", body: data, token })
}

export function applySetup(token: string, data: AutoSetupResult) {
  return apiFetch<{ status: string }>("/config/apply-setup", { method: "POST", body: data, token })
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

// ── Bookings / Resources ─────────────────────────────────

export type ServiceData = {
  id: string
  name: string
  niche: string
  description: string
  is_active: boolean
  resource_count: number
}

export type ResourceData = {
  id: string
  service_id: string
  service_name: string
  name: string
  resource_type: string
  capacity: number
  duration_minutes: number
  description: string
  is_active: boolean
}

export type BookingData = {
  id: string
  resource_name: string
  resource_type: string
  service_name: string
  contact_phone: string
  contact_name: string
  date: string
  time_start: string
  time_end: string
  guests: number
  status: string
  notes: string
  created_at: string
}

export function getServices(token: string) {
  return apiFetch<ServiceData[]>("/bookings/services", { token })
}

export function createService(token: string, data: { name: string; niche: string; description?: string }) {
  return apiFetch<ServiceData>("/bookings/services", { method: "POST", body: data, token })
}

export function deleteService(token: string, id: string) {
  return apiFetch(`/bookings/services/${id}`, { method: "DELETE", token })
}

export function getResources(token: string, serviceId?: string) {
  const q = serviceId ? `?service_id=${serviceId}` : ""
  return apiFetch<ResourceData[]>(`/bookings/resources${q}`, { token })
}

export function createResource(token: string, data: { service_id: string; name: string; resource_type: string; capacity: number; duration_minutes: number; description?: string }) {
  return apiFetch<ResourceData>("/bookings/resources", { method: "POST", body: data, token })
}

export function deleteResource(token: string, id: string) {
  return apiFetch(`/bookings/resources/${id}`, { method: "DELETE", token })
}

export function getBookings(token: string, params?: { date_from?: string; date_to?: string; status?: string }) {
  const query = params ? new URLSearchParams(params as Record<string, string>).toString() : ""
  return apiFetch<BookingData[]>(`/bookings${query ? `?${query}` : ""}`, { token })
}

export function cancelBooking(token: string, id: string) {
  return apiFetch(`/bookings/${id}/cancel`, { method: "PATCH", token })
}

export type DetectedService = {
  niche: string
  label: string
  resources: { name: string; type: string; capacity: number; duration_minutes: number; description: string }[]
}

export function detectServices(token: string) {
  return apiFetch<{ services: DetectedService[] }>("/bookings/detect-services", { method: "POST", token })
}

export function applyServices(token: string, services: DetectedService[]) {
  return apiFetch<{ created: string[]; count: number }>("/bookings/apply-services", { method: "POST", body: { services }, token })
}
