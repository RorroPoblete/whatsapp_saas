"use client"

import { useEffect, useState } from "react"
import { getToken } from "@/lib/auth"
import { getAnalytics, type AnalyticsSummary } from "@/lib/api"
import { BarChart3, MessageSquare, Users, TrendingUp } from "lucide-react"

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsSummary | null>(null)

  useEffect(() => {
    const token = getToken()
    if (!token) return
    getAnalytics(token, 30).then(setData).catch(console.error)
  }, [])

  if (!data) return <div className="animate-pulse text-gray-400">Cargando analytics...</div>

  const cards = [
    { label: "Mensajes hoy", value: data.total_messages_today, icon: MessageSquare },
    { label: "Mensajes semana", value: data.total_messages_week, icon: TrendingUp },
    { label: "Mensajes mes", value: data.total_messages_month, icon: BarChart3 },
    { label: "Conversaciones activas", value: data.active_conversations, icon: Users },
  ]

  // Calcular max para la barra del grafico
  const maxMessages = Math.max(
    ...data.daily_usage.map((d) => d.messages_received + d.messages_sent),
    1,
  )

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Analytics</h1>

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

      {/* Simple bar chart */}
      <div className="bg-white p-6 rounded-xl border border-gray-100">
        <h3 className="font-semibold mb-4">Actividad diaria (ultimos 30 dias)</h3>
        {data.daily_usage.length === 0 ? (
          <p className="text-gray-400 text-sm py-8 text-center">No hay datos aun</p>
        ) : (
          <div className="flex items-end gap-1 h-40">
            {data.daily_usage.map((day) => {
              const total = day.messages_received + day.messages_sent
              const height = (total / maxMessages) * 100
              return (
                <div key={day.date} className="flex-1 flex flex-col items-center group relative">
                  <div
                    className="w-full bg-brand-500 rounded-t hover:bg-brand-600 transition min-h-[2px]"
                    style={{ height: `${height}%` }}
                  />
                  <div className="hidden group-hover:block absolute -top-8 bg-gray-800 text-white text-xs px-2 py-1 rounded whitespace-nowrap">
                    {day.date}: {total} msgs
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
