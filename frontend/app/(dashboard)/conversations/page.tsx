"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { getToken } from "@/lib/auth"
import { getConversations, type ConversationSummary } from "@/lib/api"
import { MessageSquare, Search } from "lucide-react"

function formatPhone(phone: string): string {
  // "+56971374935" → "+56 9 7137 4935"
  const clean = phone.replace(/[^0-9+]/g, "")
  if (clean.startsWith("+56") && clean.length === 12) {
    return `+56 ${clean[3]} ${clean.slice(4, 8)} ${clean.slice(8)}`
  }
  return clean || phone
}

export default function ConversationsPage() {
  const [conversations, setConversations] = useState<ConversationSummary[]>([])
  const [search, setSearch] = useState("")
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = getToken()
    if (!token) return
    getConversations(token)
      .then(setConversations)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const filtered = conversations.filter(
    (c) =>
      c.phone_number.includes(search) ||
      (c.contact_name || "").toLowerCase().includes(search.toLowerCase()),
  )

  if (loading) return <div className="animate-pulse text-gray-400">Cargando conversaciones...</div>

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Conversaciones</h1>
        <div className="relative">
          <Search className="w-4 h-4 text-gray-400 absolute left-3 top-2.5" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar por telefono..."
            className="pl-9 pr-4 py-2 border border-gray-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-brand-500 w-64"
          />
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="text-center py-20 text-gray-400">
          <MessageSquare className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>No hay conversaciones aun</p>
          <p className="text-sm">Apareceran aqui cuando tus clientes escriban por WhatsApp</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-100 divide-y divide-gray-50">
          {filtered.map((conv) => (
            <Link
              key={conv.id}
              href={`/conversations/${conv.id}`}
              className="flex items-center gap-4 p-4 hover:bg-gray-50 transition"
            >
              <div className="w-10 h-10 bg-brand-100 text-brand-600 rounded-full flex items-center justify-center text-sm font-bold">
                {(conv.contact_name || conv.phone_number).charAt(0).toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-sm">
                    {conv.contact_name || formatPhone(conv.phone_number)}
                  </span>
                  <span className="text-xs text-gray-400">
                    {conv.last_message_at
                      ? new Date(conv.last_message_at).toLocaleDateString("es-CL", {
                          day: "numeric",
                          month: "short",
                          hour: "2-digit",
                          minute: "2-digit",
                        })
                      : ""}
                  </span>
                </div>
                <p className="text-sm text-gray-500 truncate">{conv.last_message || "Sin mensajes"}</p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-400">{conv.message_count} msgs</span>
                {!conv.is_ai_active && (
                  <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded">Manual</span>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
