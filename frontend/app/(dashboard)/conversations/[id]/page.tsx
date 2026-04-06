"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { getToken } from "@/lib/auth"
import { getConversation, toggleAI, type ConversationDetail } from "@/lib/api"
import { ArrowLeft, Bot, BotOff, User } from "lucide-react"

export default function ConversationDetailPage() {
  const params = useParams()
  const router = useRouter()
  const [conv, setConv] = useState<ConversationDetail | null>(null)
  const [loading, setLoading] = useState(true)

  const id = params.id as string

  useEffect(() => {
    const token = getToken()
    if (!token || !id) return
    getConversation(token, id)
      .then(setConv)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [id])

  async function handleToggleAI() {
    const token = getToken()
    if (!token || !conv) return
    const res = await toggleAI(token, conv.id)
    setConv((prev) => prev ? { ...prev, is_ai_active: res.is_ai_active } : null)
  }

  if (loading) return <div className="animate-pulse text-gray-400">Cargando conversacion...</div>
  if (!conv) return <div className="text-gray-400">Conversacion no encontrada</div>

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      {/* Header */}
      <div className="flex items-center gap-4 pb-4 border-b border-gray-100">
        <button onClick={() => router.push("/conversations")} className="text-gray-400 hover:text-gray-600">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="flex-1">
          <h2 className="font-semibold">{conv.contact_name || conv.phone_number}</h2>
          <p className="text-xs text-gray-500">{conv.phone_number}</p>
        </div>
        <button
          onClick={handleToggleAI}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition ${
            conv.is_ai_active
              ? "bg-brand-50 text-brand-700 hover:bg-brand-100"
              : "bg-yellow-50 text-yellow-700 hover:bg-yellow-100"
          }`}
        >
          {conv.is_ai_active ? (
            <>
              <Bot className="w-4 h-4" /> IA activa
            </>
          ) : (
            <>
              <BotOff className="w-4 h-4" /> IA pausada
            </>
          )}
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto py-4 space-y-3">
        {conv.messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === "assistant" ? "justify-start" : "justify-end"}`}
          >
            <div
              className={`max-w-[70%] p-3 rounded-2xl text-sm ${
                msg.role === "assistant"
                  ? "bg-white border border-gray-100 text-gray-800 rounded-bl-sm"
                  : "bg-brand-600 text-white rounded-br-sm"
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.content}</p>
              <p
                className={`text-[10px] mt-1 ${
                  msg.role === "assistant" ? "text-gray-400" : "text-brand-200"
                }`}
              >
                {new Date(msg.created_at).toLocaleTimeString("es-CL", {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
