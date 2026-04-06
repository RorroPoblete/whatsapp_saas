"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { getToken } from "@/lib/auth"
import { getAnalytics, getConfig, type AnalyticsSummary, type AgentConfig } from "@/lib/api"
import { MessageSquare, Users, Zap, ArrowRight } from "lucide-react"

export default function DashboardPage() {
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null)
  const [config, setConfig] = useState<AgentConfig | null>(null)

  useEffect(() => {
    const token = getToken()
    if (!token) return
    getAnalytics(token, 7).then(setAnalytics).catch(console.error)
    getConfig(token).then(setConfig).catch(console.error)
  }, [])

  if (!config) {
    return <div className="animate-pulse text-gray-400">Cargando dashboard...</div>
  }

  // Si no ha completado el setup, mostrar CTA
  if (!config.is_setup_complete) {
    return (
      <div className="text-center py-20">
        <div className="text-6xl mb-4">&#129302;</div>
        <h1 className="text-2xl font-bold mb-2">Configura tu agente</h1>
        <p className="text-gray-600 mb-8 max-w-md mx-auto">
          Completa la configuracion de tu negocio para activar tu agente de WhatsApp con IA.
        </p>
        <Link
          href="/setup"
          className="inline-flex items-center gap-2 bg-brand-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-brand-700 transition"
        >
          Configurar agente <ArrowRight className="w-5 h-5" />
        </Link>
      </div>
    )
  }

  const cards = [
    {
      label: "Mensajes hoy",
      value: analytics?.total_messages_today ?? 0,
      icon: MessageSquare,
    },
    {
      label: "Mensajes esta semana",
      value: analytics?.total_messages_week ?? 0,
      icon: Zap,
    },
    {
      label: "Conversaciones activas",
      value: analytics?.active_conversations ?? 0,
      icon: Users,
    },
    {
      label: "Total conversaciones",
      value: analytics?.total_conversations ?? 0,
      icon: Users,
    },
  ]

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-gray-600">Agente: {config.agent_name} &mdash; {config.business_name}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {cards.map((card) => (
          <div key={card.label} className="bg-white p-6 rounded-xl border border-gray-100">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-500">{card.label}</span>
              <card.icon className="w-5 h-5 text-gray-400" />
            </div>
            <div className="text-3xl font-bold">{card.value}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Link
          href="/conversations"
          className="bg-white p-6 rounded-xl border border-gray-100 hover:border-brand-200 transition group"
        >
          <h3 className="font-semibold mb-1 group-hover:text-brand-600">Ver conversaciones</h3>
          <p className="text-sm text-gray-500">Revisa los chats de tus clientes en tiempo real</p>
        </Link>

        <Link
          href="/settings"
          className="bg-white p-6 rounded-xl border border-gray-100 hover:border-brand-200 transition group"
        >
          <h3 className="font-semibold mb-1 group-hover:text-brand-600">Configuracion</h3>
          <p className="text-sm text-gray-500">Ajusta el prompt, tono y herramientas de tu agente</p>
        </Link>
      </div>
    </div>
  )
}
