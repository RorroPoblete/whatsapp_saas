"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { getToken } from "@/lib/auth"
import {
  getConfig,
  autoSetup,
  applySetup,
  completeSetup,
  type AutoSetupResult,
} from "@/lib/api"
import {
  Loader2,
  Sparkles,
  Globe,
  Bot,
  CalendarDays,
  ChevronDown,
  ChevronUp,
  Pencil,
  Check,
  X,
  UtensilsCrossed,
  BedDouble,
  Clock,
  Box,
  Zap,
  ArrowDown,
  Phone,
} from "lucide-react"

const NICHE_ICONS: Record<string, typeof Box> = { restaurant: UtensilsCrossed, hotel: BedDouble, agenda: Clock, custom: Box }
const NICHE_COLORS: Record<string, string> = { restaurant: "bg-orange-100 text-orange-700", hotel: "bg-blue-100 text-blue-700", agenda: "bg-violet-100 text-violet-700", custom: "bg-gray-100 text-gray-700" }

const STEPS = ["Describe tu negocio", "Revisa y ajusta", "Activar"]

export default function SetupPage() {
  const router = useRouter()
  const [step, setStep] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  // Step 0
  const [description, setDescription] = useState("")
  const [url, setUrl] = useState("")

  // Step 1
  const [setup, setSetup] = useState<AutoSetupResult | null>(null)
  const [editingPrompt, setEditingPrompt] = useState(false)
  const [expandedService, setExpandedService] = useState<number | null>(null)

  // Step 2
  const [assignedPhone, setAssignedPhone] = useState<string | null>(null)

  const token = getToken() || ""

  useEffect(() => {
    if (!token) return
    getConfig(token).then((c) => {
      if (c.is_setup_complete) router.push("/dashboard")
    }).catch(console.error)
  }, [token])

  async function handleGenerate() {
    if (!description.trim()) { setError("Describe tu negocio primero"); return }
    setError("")
    setLoading(true)
    try {
      const result = await autoSetup(token, { description, url: url || undefined })
      setSetup(result)
      setStep(1)
    } catch (e: any) { setError(e.message) }
    finally { setLoading(false) }
  }

  async function handleActivate() {
    if (!setup) return
    setError("")
    setLoading(true)
    try {
      // 1. Aplicar config + crear servicios
      await applySetup(token, setup)
      // 2. Completar setup + asignar numero
      const result = await completeSetup(token, setup.system_prompt)
      setAssignedPhone(result.phone_number || null)
      setStep(2)
    } catch (e: any) { setError(e.message) }
    finally { setLoading(false) }
  }

  return (
    <div className="max-w-3xl mx-auto">
      {/* Progress */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold mb-2">Configurar agente</h1>
        <p className="text-gray-500 text-sm">Paso {step + 1} de {STEPS.length} — {STEPS[step]}</p>
        <div className="mt-3 h-2 bg-gray-100 rounded-full overflow-hidden">
          <div className="h-full bg-brand-500 transition-all duration-300" style={{ width: `${((step + 1) / STEPS.length) * 100}%` }} />
        </div>
      </div>

      {error && <div className="bg-red-50 text-red-600 text-sm p-3 rounded-lg mb-4">{error}</div>}

      {/* ── PASO 0: Describe tu negocio ── */}
      {step === 0 && (
        <div className="bg-white p-8 rounded-xl border border-gray-100 space-y-6">
          <div>
            <label className="block text-sm font-medium mb-1">Cuentame sobre tu negocio</label>
            <p className="text-xs text-gray-500 mb-3">Describe que haces, servicios, precios, horarios, ubicacion... todo lo que tu agente deba saber.</p>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={6}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg outline-none focus:ring-2 focus:ring-brand-500 text-sm"
              placeholder="Somos un restaurante italiano en Santiago, tenemos 6 mesas, menu de pastas y pizzas, abrimos de 12 a 23 hrs..."
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">URL de tu sitio web (opcional)</label>
            <p className="text-xs text-gray-500 mb-3">Si tienes pagina web, la escaneamos para completar la informacion.</p>
            <div className="flex gap-2">
              <Globe className="w-5 h-5 text-gray-400 mt-2" />
              <input
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="flex-1 px-3 py-2 border border-gray-200 rounded-lg outline-none focus:ring-2 focus:ring-brand-500 text-sm"
                placeholder="https://minegocio.cl"
              />
            </div>
          </div>
          <button
            onClick={handleGenerate}
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 bg-brand-600 text-white py-3 rounded-lg font-medium hover:bg-brand-700 transition disabled:opacity-50"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            {loading ? "Analizando tu negocio..." : "Generar mi agente"}
          </button>
        </div>
      )}

      {/* ── PASO 1: Revisa y ajusta ── */}
      {step === 1 && setup && (
        <div className="space-y-4">
          {/* System prompt */}
          <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
            <div className="p-5 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-green-50 text-green-600 flex items-center justify-center">
                  <Bot className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="font-semibold text-sm">{setup.agent_name}</h3>
                  <p className="text-xs text-gray-500">Tono {setup.agent_tone} &middot; {setup.business_name}</p>
                </div>
              </div>
              <button onClick={() => setEditingPrompt(!editingPrompt)} className="text-xs text-brand-600 hover:text-brand-700 flex items-center gap-1">
                {editingPrompt ? <Check className="w-3 h-3" /> : <Pencil className="w-3 h-3" />}
                {editingPrompt ? "Listo" : "Editar prompt"}
              </button>
            </div>
            {editingPrompt ? (
              <div className="px-5 pb-5">
                <textarea value={setup.system_prompt} onChange={(e) => setSetup({ ...setup, system_prompt: e.target.value })} rows={12} className="w-full px-3 py-2 border border-gray-200 rounded-lg text-xs font-mono outline-none focus:ring-2 focus:ring-brand-500" />
              </div>
            ) : (
              <div className="px-5 pb-5">
                <p className="text-xs text-gray-500 bg-gray-50 p-3 rounded-lg max-h-32 overflow-y-auto font-mono whitespace-pre-wrap">{setup.system_prompt.slice(0, 300)}...</p>
              </div>
            )}
          </div>

          {/* Info del negocio */}
          <div className="bg-white rounded-xl border border-gray-100 p-5">
            <h3 className="font-semibold text-sm mb-3">Informacion detectada</h3>
            <div className="grid grid-cols-2 gap-3 text-xs">
              {[["Negocio", setup.business_name], ["Telefono", setup.business_phone || "—"], ["Direccion", setup.business_address || "—"], ["Web", setup.business_website || "—"]].map(([label, value]) => (
                <div key={label} className="flex justify-between border-b border-gray-50 pb-2">
                  <span className="text-gray-500">{label}</span>
                  <span className="font-medium text-right max-w-[200px] truncate">{value}</span>
                </div>
              ))}
            </div>
            {setup.business_hours && Object.keys(setup.business_hours).length > 0 && (
              <div className="mt-3">
                <span className="text-xs text-gray-500">Horario:</span>
                <div className="flex flex-wrap gap-2 mt-1">
                  {Object.entries(setup.business_hours).map(([dia, hora]) => (
                    <span key={dia} className="text-[11px] bg-gray-100 text-gray-600 px-2 py-0.5 rounded">{dia}: {hora}</span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Servicios */}
          {setup.services.length > 0 && (
            <div className="space-y-3">
              <h3 className="font-semibold text-sm flex items-center gap-2">
                <CalendarDays className="w-4 h-4 text-gray-400" /> Servicios detectados ({setup.services.length})
              </h3>
              {setup.services.map((svc, si) => {
                const Icon = NICHE_ICONS[svc.niche] || Box
                const isExpanded = expandedService === si
                return (
                  <div key={si} className="bg-white rounded-xl border border-gray-100 overflow-hidden">
                    <div className="p-4 flex items-center justify-between cursor-pointer hover:bg-gray-50" onClick={() => setExpandedService(isExpanded ? null : si)}>
                      <div className="flex items-center gap-3">
                        <Icon className="w-4 h-4 text-gray-400" />
                        <span className="font-medium text-sm">{svc.name}</span>
                        <span className={`text-[10px] px-2 py-0.5 rounded-full ${NICHE_COLORS[svc.niche] || NICHE_COLORS.custom}`}>{svc.niche}</span>
                        <span className="text-xs text-gray-400">{svc.resources.length} recursos</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <button onClick={(e) => { e.stopPropagation(); setSetup({ ...setup, services: setup.services.filter((_, i) => i !== si) }) }} className="text-gray-300 hover:text-red-500 p-1"><X className="w-3.5 h-3.5" /></button>
                        {isExpanded ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
                      </div>
                    </div>
                    {isExpanded && (
                      <div className="px-4 pb-4 border-t border-gray-50">
                        <div className="grid md:grid-cols-2 gap-2 mt-3">
                          {svc.resources.map((r, ri) => (
                            <div key={ri} className="flex items-center justify-between bg-gray-50 p-3 rounded-lg text-xs">
                              <div>
                                <span className="font-medium">{r.name}</span>
                                <span className="text-gray-500 ml-2">{r.capacity} pers. &middot; {r.duration_minutes} min</span>
                              </div>
                              <button onClick={() => { const res = svc.resources.filter((_, i) => i !== ri); const svcs = [...setup.services]; svcs[si] = { ...svc, resources: res }; setSetup({ ...setup, services: svcs }) }} className="text-gray-300 hover:text-red-500"><X className="w-3 h-3" /></button>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}

          <div className="flex justify-between pt-2">
            <button onClick={() => setStep(0)} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900">Volver</button>
            <button onClick={handleActivate} disabled={loading} className="flex items-center gap-2 bg-brand-600 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-brand-700 transition disabled:opacity-50 text-sm">
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
              {loading ? "Activando..." : "Activar agente"}
            </button>
          </div>
        </div>
      )}

      {/* ── PASO 2: Listo ── */}
      {step === 2 && setup && (
        <div className="bg-white p-8 rounded-xl border border-gray-100 text-center space-y-6">
          <div className="text-5xl">&#127881;</div>
          <h2 className="text-xl font-bold">Tu agente esta activo!</h2>
          <p className="text-gray-600">{setup.agent_name} ya esta respondiendo por WhatsApp para {setup.business_name}.</p>

          {assignedPhone && (
            <div className="bg-green-50 p-4 rounded-lg text-sm flex items-center justify-center gap-3">
              <Phone className="w-5 h-5 text-green-600" />
              <div className="text-left">
                <p className="font-medium text-green-800">Numero asignado: {assignedPhone}</p>
                <p className="text-xs text-green-600">Tu agente ya esta escuchando en este numero</p>
              </div>
            </div>
          )}

          {!assignedPhone && (
            <div className="bg-yellow-50 p-4 rounded-lg text-sm text-yellow-700">
              No hay numeros disponibles en este momento. Contactanos para activar tu numero.
            </div>
          )}

          <div className="text-left bg-gray-50 p-4 rounded-lg text-sm space-y-1">
            <p><strong>Agente:</strong> {setup.agent_name}</p>
            <p><strong>Negocio:</strong> {setup.business_name}</p>
            <p><strong>Servicios:</strong> {setup.services.map((s) => s.name).join(", ") || "Sin reservas"}</p>
          </div>

          <button onClick={() => router.push("/dashboard")} className="w-full bg-brand-600 text-white py-3 rounded-lg font-medium hover:bg-brand-700 transition">
            Ir al dashboard
          </button>
        </div>
      )}
    </div>
  )
}
