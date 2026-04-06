"use client"

import { useEffect, useState } from "react"
import { getToken } from "@/lib/auth"
import { getConfig, updateConfig, getWebhookUrl, type AgentConfig } from "@/lib/api"

export default function SettingsPage() {
  const [config, setConfig] = useState<AgentConfig | null>(null)
  const [webhookUrl, setWebhookUrl] = useState("")
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    const token = getToken()
    if (!token) return
    getConfig(token).then(setConfig).catch(console.error)
    getWebhookUrl(token).then((r) => setWebhookUrl(r.webhook_url)).catch(() => {})
  }, [])

  async function handleSave() {
    const token = getToken()
    if (!token || !config) return
    setSaving(true)
    try {
      await updateConfig(token, {
        agent_name: config.agent_name,
        agent_tone: config.agent_tone,
        system_prompt: config.system_prompt,
        fallback_message: config.fallback_message,
        knowledge_base: config.knowledge_base,
      })
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (err) {
      console.error(err)
    } finally {
      setSaving(false)
    }
  }

  if (!config) return <div className="animate-pulse text-gray-400">Cargando configuracion...</div>

  return (
    <div className="max-w-3xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Configuracion del agente</h1>
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-4 py-2 bg-brand-600 text-white rounded-lg text-sm font-medium hover:bg-brand-700 transition disabled:opacity-50"
        >
          {saving ? "Guardando..." : saved ? "Guardado!" : "Guardar cambios"}
        </button>
      </div>

      <div className="space-y-6">
        {/* Agent info */}
        <div className="bg-white p-6 rounded-xl border border-gray-100 space-y-4">
          <h3 className="font-semibold">Agente</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-600 mb-1">Nombre</label>
              <input
                value={config.agent_name}
                onChange={(e) => setConfig({ ...config, agent_name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">Tono</label>
              <select
                value={config.agent_tone}
                onChange={(e) => setConfig({ ...config, agent_tone: e.target.value })}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-brand-500"
              >
                <option value="profesional">Profesional y formal</option>
                <option value="amigable">Amigable y casual</option>
                <option value="vendedor">Vendedor y persuasivo</option>
                <option value="empatico">Empatico y calido</option>
              </select>
            </div>
          </div>
        </div>

        {/* System prompt */}
        <div className="bg-white p-6 rounded-xl border border-gray-100 space-y-4">
          <h3 className="font-semibold">System Prompt</h3>
          <p className="text-xs text-gray-500">
            Este es el prompt que define la personalidad y conocimiento de tu agente.
          </p>
          <textarea
            value={config.system_prompt}
            onChange={(e) => setConfig({ ...config, system_prompt: e.target.value })}
            rows={12}
            className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm font-mono outline-none focus:ring-2 focus:ring-brand-500"
          />
        </div>

        {/* Knowledge base */}
        <div className="bg-white p-6 rounded-xl border border-gray-100 space-y-4">
          <h3 className="font-semibold">Base de conocimiento</h3>
          <textarea
            value={config.knowledge_base}
            onChange={(e) => setConfig({ ...config, knowledge_base: e.target.value })}
            rows={6}
            className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm font-mono outline-none focus:ring-2 focus:ring-brand-500"
            placeholder="Pega aqui informacion de tu negocio: menu, precios, FAQ..."
          />
        </div>

        {/* Fallback message */}
        <div className="bg-white p-6 rounded-xl border border-gray-100 space-y-4">
          <h3 className="font-semibold">Mensajes predeterminados</h3>
          <div>
            <label className="block text-sm text-gray-600 mb-1">Mensaje cuando no entiende</label>
            <input
              value={config.fallback_message}
              onChange={(e) => setConfig({ ...config, fallback_message: e.target.value })}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
        </div>

        {/* Webhook URL */}
        {webhookUrl && (
          <div className="bg-blue-50 p-4 rounded-xl text-sm">
            <p className="font-medium text-blue-800 mb-1">URL del Webhook</p>
            <code className="text-xs text-blue-700 break-all">{webhookUrl}</code>
          </div>
        )}

        {/* WhatsApp info */}
        <div className="bg-white p-6 rounded-xl border border-gray-100">
          <h3 className="font-semibold mb-2">WhatsApp</h3>
          <p className="text-sm text-gray-500">
            Proveedor: <span className="font-medium">{config.whatsapp_provider}</span>
            {" | "}
            IA: <span className="font-medium">{config.ai_model}</span>
          </p>
        </div>
      </div>
    </div>
  )
}
