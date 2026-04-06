"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { getToken } from "@/lib/auth"
import {
  getConfig,
  updateConfig,
  updateWhatsApp,
  updateAI,
  generatePrompt,
  completeSetup,
  getWebhookUrl,
  type AgentConfig,
} from "@/lib/api"

const TONES = [
  { value: "profesional", label: "Profesional y formal", emoji: "&#128188;" },
  { value: "amigable", label: "Amigable y casual", emoji: "&#128075;" },
  { value: "vendedor", label: "Vendedor y persuasivo", emoji: "&#128640;" },
  { value: "empatico", label: "Empatico y calido", emoji: "&#128155;" },
]

const USE_CASES = [
  "Responder preguntas frecuentes",
  "Agendar citas o reservaciones",
  "Calificar y atender leads",
  "Tomar pedidos",
  "Soporte post-venta",
]

const PROVIDERS = [
  { value: "whapi", label: "Whapi.cloud", desc: "El mas facil. Sandbox gratis.", fields: ["token"] },
  { value: "meta", label: "Meta Cloud API", desc: "API oficial de WhatsApp.", fields: ["access_token", "phone_number_id", "verify_token"] },
  { value: "twilio", label: "Twilio", desc: "Muy confiable y robusto.", fields: ["account_sid", "auth_token", "phone_number"] },
]

const STEPS = [
  "Tu negocio",
  "Tu agente",
  "Horarios",
  "Conocimiento",
  "WhatsApp",
  "API Key IA",
  "Activar",
]

export default function SetupPage() {
  const router = useRouter()
  const [step, setStep] = useState(0)
  const [loading, setLoading] = useState(false)
  const [config, setConfig] = useState<Partial<AgentConfig>>({})
  const [whatsappCreds, setWhatsappCreds] = useState<Record<string, string>>({})
  const [aiKey, setAiKey] = useState("")
  const [generatedPrompt, setGeneratedPrompt] = useState("")
  const [webhookUrl, setWebhookUrl] = useState("")
  const [error, setError] = useState("")

  const token = getToken() || ""

  useEffect(() => {
    if (!token) return
    getConfig(token).then((c) => setConfig(c)).catch(console.error)
  }, [token])

  async function saveAndNext() {
    setError("")
    setLoading(true)
    try {
      if (step <= 3) {
        await updateConfig(token, config)
      }
      if (step === 4) {
        const provider = config.whatsapp_provider || "whapi"
        await updateWhatsApp(token, { provider, credentials: whatsappCreds })
        const wh = await getWebhookUrl(token)
        setWebhookUrl(wh.webhook_url)
      }
      if (step === 5) {
        await updateAI(token, { provider: "openai", api_key: aiKey, model: "gpt-4o-mini" })
      }
      if (step === 6) {
        const res = await generatePrompt(token)
        setGeneratedPrompt(res.system_prompt)
        await completeSetup(token, res.system_prompt)
        router.push("/dashboard")
        return
      }
      setStep((s) => s + 1)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  function updateField(field: string, value: any) {
    setConfig((prev) => ({ ...prev, [field]: value }))
  }

  const selectedProvider = PROVIDERS.find((p) => p.value === (config.whatsapp_provider || "whapi"))

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold mb-2">Configurar agente</h1>
        <p className="text-gray-500 text-sm">
          Paso {step + 1} de {STEPS.length} &mdash; {STEPS[step]}
        </p>
        {/* Progress bar */}
        <div className="mt-3 h-2 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-brand-500 transition-all duration-300"
            style={{ width: `${((step + 1) / STEPS.length) * 100}%` }}
          />
        </div>
      </div>

      {error && <div className="bg-red-50 text-red-600 text-sm p-3 rounded-lg mb-4">{error}</div>}

      <div className="bg-white p-8 rounded-xl border border-gray-100 space-y-6">
        {/* Step 0: Business info */}
        {step === 0 && (
          <>
            <div>
              <label className="block text-sm font-medium mb-1">Nombre del negocio</label>
              <input
                value={config.business_name || ""}
                onChange={(e) => updateField("business_name", e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Descripcion del negocio</label>
              <textarea
                value={config.business_description || ""}
                onChange={(e) => updateField("business_description", e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg outline-none focus:ring-2 focus:ring-brand-500"
                placeholder="Que vendes o que servicios ofreces, quienes son tus clientes..."
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Telefono</label>
                <input
                  value={config.business_phone || ""}
                  onChange={(e) => updateField("business_phone", e.target.value)}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Sitio web</label>
                <input
                  value={config.business_website || ""}
                  onChange={(e) => updateField("business_website", e.target.value)}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>
            </div>
          </>
        )}

        {/* Step 1: Agent config */}
        {step === 1 && (
          <>
            <div>
              <label className="block text-sm font-medium mb-1">Nombre del agente</label>
              <input
                value={config.agent_name || ""}
                onChange={(e) => updateField("agent_name", e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg outline-none focus:ring-2 focus:ring-brand-500"
                placeholder="ej: Ana, Sofia, Soporte MiEmpresa"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Tono del agente</label>
              <div className="grid grid-cols-2 gap-3">
                {TONES.map((t) => (
                  <button
                    key={t.value}
                    type="button"
                    onClick={() => updateField("agent_tone", t.value)}
                    className={`p-3 rounded-lg border text-left text-sm transition ${
                      config.agent_tone === t.value
                        ? "border-brand-500 bg-brand-50 text-brand-700"
                        : "border-gray-200 hover:border-gray-300"
                    }`}
                  >
                    <span dangerouslySetInnerHTML={{ __html: t.emoji }} /> {t.label}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Casos de uso</label>
              <div className="space-y-2">
                {USE_CASES.map((uc) => (
                  <label key={uc} className="flex items-center gap-2 text-sm cursor-pointer">
                    <input
                      type="checkbox"
                      checked={(config.use_cases || []).includes(uc)}
                      onChange={(e) => {
                        const current = config.use_cases || []
                        if (e.target.checked) {
                          updateField("use_cases", [...current, uc])
                        } else {
                          updateField("use_cases", current.filter((c: string) => c !== uc))
                        }
                      }}
                      className="rounded border-gray-300 text-brand-600 focus:ring-brand-500"
                    />
                    {uc}
                  </label>
                ))}
              </div>
            </div>
          </>
        )}

        {/* Step 2: Hours */}
        {step === 2 && (
          <div>
            <label className="block text-sm font-medium mb-2">Horario de atencion</label>
            {["Lunes a Viernes", "Sabado", "Domingo"].map((dia) => (
              <div key={dia} className="flex items-center gap-3 mb-3">
                <span className="text-sm w-36">{dia}</span>
                <input
                  value={(config.business_hours as any)?.[dia] || ""}
                  onChange={(e) =>
                    updateField("business_hours", {
                      ...(config.business_hours || {}),
                      [dia]: e.target.value,
                    })
                  }
                  placeholder="ej: 9:00 - 18:00 o Cerrado"
                  className="flex-1 px-3 py-2 border border-gray-200 rounded-lg outline-none focus:ring-2 focus:ring-brand-500 text-sm"
                />
              </div>
            ))}
          </div>
        )}

        {/* Step 3: Knowledge */}
        {step === 3 && (
          <div>
            <label className="block text-sm font-medium mb-1">Informacion de tu negocio</label>
            <p className="text-xs text-gray-500 mb-3">
              Pega aqui informacion relevante: menu, precios, FAQ, servicios, politicas, etc.
              El agente usara esta informacion para responder.
            </p>
            <textarea
              value={config.knowledge_base || ""}
              onChange={(e) => updateField("knowledge_base", e.target.value)}
              rows={10}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg outline-none focus:ring-2 focus:ring-brand-500 text-sm font-mono"
              placeholder={"Menu:\n- Pizza Margherita: $8.990\n- Pizza Pepperoni: $9.990\n\nHorario de delivery: 12:00 - 22:00\n..."}
            />
          </div>
        )}

        {/* Step 4: WhatsApp */}
        {step === 4 && (
          <>
            <div>
              <label className="block text-sm font-medium mb-2">Proveedor de WhatsApp</label>
              <div className="space-y-2">
                {PROVIDERS.map((p) => (
                  <button
                    key={p.value}
                    type="button"
                    onClick={() => updateField("whatsapp_provider", p.value)}
                    className={`w-full p-3 rounded-lg border text-left text-sm transition ${
                      (config.whatsapp_provider || "whapi") === p.value
                        ? "border-brand-500 bg-brand-50"
                        : "border-gray-200 hover:border-gray-300"
                    }`}
                  >
                    <span className="font-medium">{p.label}</span>
                    <span className="text-gray-500 ml-2">{p.desc}</span>
                  </button>
                ))}
              </div>
            </div>
            {selectedProvider && (
              <div className="space-y-3">
                <p className="text-sm text-gray-500">Credenciales de {selectedProvider.label}:</p>
                {selectedProvider.fields.map((field) => (
                  <div key={field}>
                    <label className="block text-xs font-medium text-gray-600 mb-1">{field}</label>
                    <input
                      value={whatsappCreds[field] || ""}
                      onChange={(e) => setWhatsappCreds((prev) => ({ ...prev, [field]: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg outline-none focus:ring-2 focus:ring-brand-500 text-sm font-mono"
                    />
                  </div>
                ))}
              </div>
            )}
            {webhookUrl && (
              <div className="bg-blue-50 p-3 rounded-lg text-sm">
                <p className="font-medium text-blue-800 mb-1">URL del Webhook:</p>
                <code className="text-xs text-blue-700 break-all">{webhookUrl}</code>
                <p className="text-xs text-blue-600 mt-1">Configura esta URL en tu proveedor de WhatsApp.</p>
              </div>
            )}
          </>
        )}

        {/* Step 5: AI Key */}
        {step === 5 && (
          <div>
            <label className="block text-sm font-medium mb-1">OpenAI API Key</label>
            <p className="text-xs text-gray-500 mb-3">
              Obtenla en platform.openai.com &rarr; API Keys. Empieza con &quot;sk-...&quot;
            </p>
            <input
              value={aiKey}
              onChange={(e) => setAiKey(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg outline-none focus:ring-2 focus:ring-brand-500 text-sm font-mono"
              placeholder="sk-..."
              type="password"
            />
          </div>
        )}

        {/* Step 6: Review & Activate */}
        {step === 6 && (
          <div className="text-center py-4">
            <div className="text-5xl mb-4">&#127881;</div>
            <h2 className="text-xl font-bold mb-2">Todo listo!</h2>
            <p className="text-gray-600 mb-4">
              Vamos a generar el prompt de tu agente y activarlo.
            </p>
            <div className="text-left bg-gray-50 p-4 rounded-lg text-sm">
              <p><strong>Negocio:</strong> {config.business_name}</p>
              <p><strong>Agente:</strong> {config.agent_name}</p>
              <p><strong>Tono:</strong> {config.agent_tone}</p>
              <p><strong>WhatsApp:</strong> {config.whatsapp_provider || "whapi"}</p>
              <p><strong>Casos de uso:</strong> {(config.use_cases || []).join(", ")}</p>
            </div>
          </div>
        )}
      </div>

      {/* Navigation buttons */}
      <div className="flex justify-between mt-6">
        <button
          onClick={() => setStep((s) => Math.max(0, s - 1))}
          disabled={step === 0}
          className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 disabled:opacity-30"
        >
          Anterior
        </button>
        <button
          onClick={saveAndNext}
          disabled={loading}
          className="px-6 py-2.5 bg-brand-600 text-white rounded-lg font-medium hover:bg-brand-700 transition disabled:opacity-50 text-sm"
        >
          {loading ? "Guardando..." : step === 6 ? "Activar agente" : "Siguiente"}
        </button>
      </div>
    </div>
  )
}
