"use client"

import { useEffect, useState } from "react"
import { getToken } from "@/lib/auth"
import {
  getConfig,
  getServices,
  getResources,
  detectServices,
  applyServices,
  type AgentConfig,
  type ServiceData,
  type ResourceData,
  type DetectedService,
} from "@/lib/api"
import {
  MessageSquare,
  Bot,
  CalendarDays,
  Zap,
  ClipboardList,
  ArrowDown,
  Sparkles,
  Check,
  Loader2,
  Settings,
  ChevronDown,
  ChevronUp,
  BedDouble,
  UtensilsCrossed,
  Clock,
  Box,
  GitBranch,
  Search,
  XCircle,
  CheckCircle,
} from "lucide-react"

// ── Tipos ────────────────────────────────────────────────

type FlowNode = {
  id: string
  label: string
  icon: typeof Bot
  color: string
  bgColor: string
  description: string
  details: string[]
  branches?: { label: string; color: string }[]
}

const NICHE_ICONS: Record<string, typeof Box> = {
  restaurant: UtensilsCrossed, hotel: BedDouble, agenda: Clock, custom: Box,
}
const NICHE_COLORS: Record<string, { border: string; bg: string; text: string; badge: string }> = {
  restaurant: { border: "border-orange-500", bg: "bg-orange-50", text: "text-orange-600", badge: "bg-orange-100 text-orange-700" },
  hotel: { border: "border-blue-500", bg: "bg-blue-50", text: "text-blue-600", badge: "bg-blue-100 text-blue-700" },
  agenda: { border: "border-violet-500", bg: "bg-violet-50", text: "text-violet-600", badge: "bg-violet-100 text-violet-700" },
  custom: { border: "border-gray-500", bg: "bg-gray-50", text: "text-gray-600", badge: "bg-gray-100 text-gray-700" },
}

// ── Componentes ──────────────────────────────────────────

function NodeCard({ node, expanded, onToggle, indent }: { node: FlowNode; expanded: boolean; onToggle: () => void; indent?: boolean }) {
  const Icon = node.icon
  return (
    <div
      className={`bg-white rounded-xl border-2 ${node.color} shadow-sm hover:shadow-md transition-all cursor-pointer ${indent ? "w-full" : "w-full max-w-lg"}`}
      onClick={onToggle}
    >
      <div className="p-4">
        <div className="flex items-center gap-3">
          <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${node.bgColor} ${node.color.replace("border-", "text-")}`}>
            <Icon className="w-4 h-4" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-sm">{node.label}</h3>
            <p className="text-xs text-gray-500 truncate">{node.description}</p>
          </div>
          {expanded ? <ChevronUp className="w-4 h-4 text-gray-400 shrink-0" /> : <ChevronDown className="w-4 h-4 text-gray-400 shrink-0" />}
        </div>
      </div>
      {expanded && (
        <div className="px-4 pb-4 border-t border-gray-50">
          <ul className="mt-3 space-y-1.5">
            {node.details.map((d, i) => (
              <li key={i} className="text-xs text-gray-600 flex items-start gap-2">
                <span className="text-gray-300 mt-0.5 shrink-0">&#9679;</span>
                <span>{d}</span>
              </li>
            ))}
          </ul>
          {node.branches && node.branches.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {node.branches.map((b, i) => (
                <span key={i} className={`text-[11px] px-2 py-0.5 rounded-full ${b.color}`}>{b.label}</span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function Connector({ label }: { label?: string }) {
  return (
    <div className="flex flex-col items-center py-0.5">
      <div className="w-0.5 h-5 bg-gray-200" />
      {label && <span className="text-[10px] text-gray-400 bg-gray-50 px-2 py-0.5 rounded-full -my-0.5 z-10">{label}</span>}
      <div className="w-0.5 h-5 bg-gray-200" />
      <ArrowDown className="w-3 h-3 text-gray-300 -mt-0.5" />
    </div>
  )
}

function BranchSplit({ labels }: { labels: string[] }) {
  return (
    <div className="flex flex-col items-center py-1">
      <div className="w-0.5 h-4 bg-gray-200" />
      <GitBranch className="w-4 h-4 text-gray-300 rotate-180" />
      <div className="flex gap-2 mt-1">
        {labels.map((l) => (
          <span key={l} className="text-[10px] text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">{l}</span>
        ))}
      </div>
    </div>
  )
}

// ── Flujo de un servicio ─────────────────────────────────

function ServiceFlow({ service, resources, expandedNode, setExpandedNode }: {
  service: ServiceData
  resources: ResourceData[]
  expandedNode: string | null
  setExpandedNode: (id: string | null) => void
}) {
  const colors = NICHE_COLORS[service.niche] || NICHE_COLORS.custom
  const Icon = NICHE_ICONS[service.niche] || Box
  const svcResources = resources.filter((r) => r.service_id === service.id)

  const nicheLabels: Record<string, { intent: string; ask: string; confirm: string; resource: string }> = {
    restaurant: { intent: "Quiero reservar mesa", ask: "Fecha, hora, personas, nombre", confirm: "Mesa confirmada", resource: "mesas" },
    hotel: { intent: "Quiero reservar habitacion", ask: "Fechas check-in/out, tipo, nombre", confirm: "Habitacion reservada", resource: "habitaciones" },
    agenda: { intent: "Quiero agendar cita", ask: "Fecha, hora preferida, nombre", confirm: "Cita agendada", resource: "horarios" },
    custom: { intent: "Quiero reservar", ask: "Fecha, hora, nombre", confirm: "Reserva confirmada", resource: "recursos" },
  }
  const labels = nicheLabels[service.niche] || nicheLabels.custom

  const nodes: FlowNode[] = [
    {
      id: `${service.id}-intent`,
      label: `"${labels.intent}"`,
      icon: MessageSquare,
      color: colors.border,
      bgColor: colors.bg,
      description: "El cliente expresa intencion de reservar",
      details: [
        "La IA detecta la intencion de reserva en el mensaje",
        `Servicio identificado: ${service.name}`,
      ],
    },
    {
      id: `${service.id}-check`,
      label: "Consultar disponibilidad",
      icon: Search,
      color: colors.border,
      bgColor: colors.bg,
      description: `Tool call: consultar_disponibilidad`,
      details: [
        `Busca ${labels.resource} disponibles para la fecha solicitada`,
        `${svcResources.length} ${labels.resource}: ${svcResources.map((r) => `${r.name} (${r.capacity} pers.)`).join(", ")}`,
        "Verifica conflictos de horario con reservas existentes",
      ],
      branches: [
        { label: "Disponible", color: "bg-green-100 text-green-700" },
        { label: "Sin disponibilidad", color: "bg-red-100 text-red-700" },
      ],
    },
    {
      id: `${service.id}-ask`,
      label: "Pedir datos",
      icon: ClipboardList,
      color: colors.border,
      bgColor: colors.bg,
      description: labels.ask,
      details: [
        "Presenta las opciones disponibles al cliente",
        "Pide los datos faltantes para confirmar",
        "Si no hay disponibilidad, sugiere alternativas",
      ],
    },
    {
      id: `${service.id}-confirm`,
      label: "Confirmar reserva",
      icon: CheckCircle,
      color: "border-green-500",
      bgColor: "bg-green-50",
      description: `Tool call: crear_reserva`,
      details: [
        labels.confirm,
        "Se guarda en la base de datos con estado 'confirmada'",
        "Se puede cancelar con cancelar_reserva",
        "Visible en el dashboard de Reservas",
      ],
    },
  ]

  return (
    <div className="bg-gray-50/50 rounded-xl border border-gray-100 p-5">
      <div className="flex items-center gap-2 mb-4">
        <div className={`w-7 h-7 rounded-lg flex items-center justify-center ${colors.bg} ${colors.text}`}>
          <Icon className="w-4 h-4" />
        </div>
        <h3 className="font-semibold text-sm">{service.name}</h3>
        <span className={`text-[10px] px-2 py-0.5 rounded-full ${colors.badge}`}>{service.niche}</span>
        <span className="text-[10px] text-gray-400">{svcResources.length} {labels.resource}</span>
      </div>
      <div className="flex flex-col items-center">
        {nodes.map((node, i) => (
          <div key={node.id} className="flex flex-col items-center w-full">
            {i > 0 && <Connector label={i === 3 ? "datos completos" : undefined} />}
            <NodeCard
              node={node} indent
              expanded={expandedNode === node.id}
              onToggle={() => setExpandedNode(expandedNode === node.id ? null : node.id)}
            />
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Pagina principal ─────────────────────────────────────

export default function FlowPage() {
  const [config, setConfig] = useState<AgentConfig | null>(null)
  const [services, setServices] = useState<ServiceData[]>([])
  const [resources, setResources] = useState<ResourceData[]>([])
  const [expandedNode, setExpandedNode] = useState<string | null>("welcome")
  const [detecting, setDetecting] = useState(false)
  const [detected, setDetected] = useState<DetectedService[] | null>(null)
  const [applying, setApplying] = useState(false)

  const token = getToken() || ""

  useEffect(() => {
    if (!token) return
    getConfig(token).then(setConfig).catch(console.error)
    getServices(token).then(setServices).catch(console.error)
    getResources(token).then(setResources).catch(console.error)
  }, [token])

  const hasOnboarding = config?.onboarding_questions && config.onboarding_questions.length > 0
  const hasServices = services.length > 0

  async function handleDetect() {
    setDetecting(true)
    try {
      const result = await detectServices(token)
      setDetected(result.services)
    } catch (e: any) { alert(e.message) }
    finally { setDetecting(false) }
  }

  async function handleApply() {
    if (!detected) return
    setApplying(true)
    try {
      const result = await applyServices(token, detected)
      alert(`${result.count} recursos creados`)
      setDetected(null)
      getServices(token).then(setServices)
      getResources(token).then(setResources)
    } catch (e: any) { alert(e.message) }
    finally { setApplying(false) }
  }

  // Nodos principales del flujo
  const mainNodes: FlowNode[] = [
    {
      id: "welcome",
      label: "Mensaje entrante",
      icon: MessageSquare,
      color: "border-blue-500",
      bgColor: "bg-blue-50",
      description: "Un cliente escribe al WhatsApp",
      details: [
        "Webhook recibe el mensaje del proveedor (Whapi/Meta/Twilio)",
        "Identifica el tenant y obtiene la conversacion",
        "Verifica que la IA este activa",
      ],
    },
  ]

  if (hasOnboarding) {
    mainNodes.push({
      id: "onboarding",
      label: "Onboarding",
      icon: ClipboardList,
      color: "border-purple-500",
      bgColor: "bg-purple-50",
      description: `${config!.onboarding_questions!.length} preguntas al contacto nuevo`,
      details: config!.onboarding_questions!.map((q: string, i: number) => `${i + 1}. ${q}`),
    })
  }

  mainNodes.push({
    id: "ai",
    label: "Agente IA",
    icon: Bot,
    color: "border-green-500",
    bgColor: "bg-green-50",
    description: `${config?.agent_name || "Agente"} analiza el mensaje con GPT-4o mini`,
    details: [
      "Carga system prompt + ultimos 20 mensajes + contexto del contacto",
      "Decide si es pregunta general, reserva o algo que no sabe",
    ],
    branches: [
      { label: "Pregunta general", color: "bg-green-100 text-green-700" },
      ...services.map((s) => ({
        label: `Reservar ${s.name}`,
        color: (NICHE_COLORS[s.niche] || NICHE_COLORS.custom).badge,
      })),
      { label: "No sabe", color: "bg-red-100 text-red-700" },
    ],
  })

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Flujo del agente</h1>
          <p className="text-sm text-gray-500">Visualiza como tu agente procesa cada mensaje</p>
        </div>
        <button onClick={handleDetect} disabled={detecting}
          className="flex items-center gap-2 bg-brand-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-brand-700 transition disabled:opacity-50">
          {detecting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
          {detecting ? "Analizando..." : "Detectar servicios"}
        </button>
      </div>

      {/* Panel detectar servicios */}
      {detected && detected.length > 0 && (
        <div className="bg-purple-50 border border-purple-200 rounded-xl p-5 mb-6">
          <h3 className="font-semibold text-purple-800 mb-3 flex items-center gap-2">
            <Sparkles className="w-4 h-4" /> Servicios detectados
          </h3>
          <div className="space-y-3">
            {detected.map((s, i) => (
              <div key={i} className="bg-white rounded-lg p-4 border border-purple-100">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full">{s.niche}</span>
                  <span className="font-medium text-sm">{s.label}</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {s.resources.map((r, j) => (
                    <span key={j} className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">{r.name} ({r.capacity} pers.)</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <div className="flex gap-2 mt-4">
            <button onClick={handleApply} disabled={applying}
              className="flex items-center gap-2 bg-purple-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-purple-700 disabled:opacity-50">
              {applying ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
              {applying ? "Creando..." : "Crear servicios y recursos"}
            </button>
            <button onClick={() => setDetected(null)} className="text-gray-500 px-4 py-2 text-sm">Cancelar</button>
          </div>
        </div>
      )}

      {detected && detected.length === 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 mb-6 text-sm text-yellow-700">
          No se detectaron servicios reservables en tu system prompt.
        </div>
      )}

      {/* ── Flujo principal ── */}
      <div className="flex flex-col items-center py-4 max-w-lg mx-auto">
        {mainNodes.map((node, i) => (
          <div key={node.id} className="flex flex-col items-center w-full">
            {i > 0 && <Connector label={node.id === "onboarding" ? "contacto nuevo" : node.id === "ai" ? (hasOnboarding ? "onboarding completo" : undefined) : undefined} />}
            <NodeCard node={node} expanded={expandedNode === node.id} onToggle={() => setExpandedNode(expandedNode === node.id ? null : node.id)} />
          </div>
        ))}
      </div>

      {/* ── Ramas por servicio ── */}
      {hasServices && (
        <>
          <BranchSplit labels={[...services.map((s) => s.name), "General", "Fallback"]} />
          <div className={`grid gap-4 mt-4 ${services.length >= 3 ? "md:grid-cols-3" : services.length === 2 ? "md:grid-cols-2" : "max-w-lg mx-auto"}`}>
            {services.map((svc) => (
              <ServiceFlow key={svc.id} service={svc} resources={resources} expandedNode={expandedNode} setExpandedNode={setExpandedNode} />
            ))}
          </div>

          {/* Merge final */}
          <div className="flex flex-col items-center mt-4 max-w-lg mx-auto">
            <Connector label="respuesta lista" />
            <NodeCard
              node={{
                id: "response",
                label: "Enviar respuesta",
                icon: Zap,
                color: "border-emerald-500",
                bgColor: "bg-emerald-50",
                description: "Se envia por WhatsApp y se guarda en DB",
                details: [
                  "Guarda mensaje user + assistant en la base de datos",
                  "Actualiza tracking de uso (tokens, mensajes)",
                  "Envia via proveedor de WhatsApp",
                ],
              }}
              expanded={expandedNode === "response"}
              onToggle={() => setExpandedNode(expandedNode === "response" ? null : "response")}
            />
          </div>
        </>
      )}

      {/* Sin servicios */}
      {!hasServices && (
        <div className="flex flex-col items-center max-w-lg mx-auto">
          <Connector label="respuesta lista" />
          <NodeCard
            node={{
              id: "response",
              label: "Enviar respuesta",
              icon: Zap,
              color: "border-emerald-500",
              bgColor: "bg-emerald-50",
              description: "Se envia por WhatsApp y se guarda en DB",
              details: [
                "Guarda mensajes en la base de datos",
                "Actualiza tracking de uso",
                "Envia via proveedor de WhatsApp",
                "Sin servicios configurados: solo respuestas generales",
              ],
            }}
            expanded={expandedNode === "response"}
            onToggle={() => setExpandedNode(expandedNode === "response" ? null : "response")}
          />
        </div>
      )}

      {/* Resumen */}
      <div className="mt-8 bg-gray-50 rounded-xl p-5 max-w-lg mx-auto">
        <h3 className="font-semibold text-sm mb-3 flex items-center gap-2">
          <Settings className="w-4 h-4 text-gray-400" /> Resumen
        </h3>
        <div className="grid grid-cols-2 gap-x-8 gap-y-2 text-xs text-gray-600">
          <div className="flex justify-between"><span>Agente</span><span className="font-medium">{config?.agent_name || "—"}</span></div>
          <div className="flex justify-between"><span>Tono</span><span className="font-medium">{config?.agent_tone || "—"}</span></div>
          <div className="flex justify-between"><span>Servicios</span><span className="font-medium">{services.length}</span></div>
          <div className="flex justify-between"><span>Recursos</span><span className="font-medium">{resources.length}</span></div>
          <div className="flex justify-between"><span>Onboarding</span><span className="font-medium">{config?.onboarding_questions?.length || 0} preguntas</span></div>
          <div className="flex justify-between"><span>WhatsApp</span><span className="font-medium">{config?.whatsapp_provider || "—"}</span></div>
        </div>
      </div>
    </div>
  )
}
