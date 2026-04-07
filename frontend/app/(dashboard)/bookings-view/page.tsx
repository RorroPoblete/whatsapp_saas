"use client"

import { useEffect, useState } from "react"
import { getToken } from "@/lib/auth"
import { getBookings, cancelBooking, type BookingData } from "@/lib/api"
import { CalendarDays, X, User, Clock } from "lucide-react"

function formatPhone(phone: string): string {
  const clean = phone.replace(/[^0-9+]/g, "")
  if (clean.startsWith("+56") && clean.length === 12) {
    return `+56 ${clean[3]} ${clean.slice(4, 8)} ${clean.slice(8)}`
  }
  return clean || phone
}

const STATUS_COLORS: Record<string, string> = {
  confirmed: "bg-green-100 text-green-700",
  pending: "bg-yellow-100 text-yellow-700",
  cancelled: "bg-red-100 text-red-700",
  completed: "bg-gray-100 text-gray-600",
}

const STATUS_LABELS: Record<string, string> = {
  confirmed: "Confirmada",
  pending: "Pendiente",
  cancelled: "Cancelada",
  completed: "Completada",
}

export default function BookingsPage() {
  const [bookings, setBookings] = useState<BookingData[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<"all" | "confirmed" | "cancelled">("all")

  const token = getToken() || ""

  async function loadBookings() {
    try {
      const params: Record<string, string> = {}
      if (filter !== "all") params.status = filter
      const data = await getBookings(token, params)
      setBookings(data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (token) loadBookings()
  }, [token, filter])

  async function handleCancel(id: string) {
    if (!confirm("Cancelar esta reserva?")) return
    try {
      await cancelBooking(token, id)
      loadBookings()
    } catch (e: any) {
      alert(e.message)
    }
  }

  if (loading) return <div className="animate-pulse text-gray-400">Cargando...</div>

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Reservas</h1>
          <p className="text-sm text-gray-500">Reservas creadas por el agente de WhatsApp</p>
        </div>
        <div className="flex gap-2">
          {(["all", "confirmed", "cancelled"] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                filter === f ? "bg-brand-600 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {f === "all" ? "Todas" : STATUS_LABELS[f]}
            </button>
          ))}
        </div>
      </div>

      {bookings.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-100 p-12 text-center">
          <CalendarDays className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500 mb-1">No hay reservas</p>
          <p className="text-sm text-gray-400">Las reservas apareceran aqui cuando tus clientes reserven por WhatsApp</p>
        </div>
      ) : (
        <div className="space-y-3">
          {bookings.map((b) => (
            <div key={b.id} className="bg-white p-5 rounded-xl border border-gray-100 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="text-center min-w-[60px]">
                  <div className="text-lg font-bold text-brand-600">
                    {new Date(b.date + "T12:00:00").toLocaleDateString("es-CL", { day: "numeric" })}
                  </div>
                  <div className="text-xs text-gray-500 uppercase">
                    {new Date(b.date + "T12:00:00").toLocaleDateString("es-CL", { month: "short" })}
                  </div>
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-sm">{b.service_name} &middot; {b.resource_name}</span>
                    <span className={`text-xs px-2 py-0.5 rounded ${STATUS_COLORS[b.status]}`}>
                      {STATUS_LABELS[b.status] || b.status}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-gray-500 mt-1">
                    <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {b.time_start} - {b.time_end}</span>
                    <span className="flex items-center gap-1"><User className="w-3 h-3" /> {b.contact_name || formatPhone(b.contact_phone)} ({b.guests} pers.)</span>
                  </div>
                  {b.notes && <p className="text-xs text-gray-400 mt-1">{b.notes}</p>}
                </div>
              </div>
              {(b.status === "confirmed" || b.status === "pending") && (
                <button
                  onClick={() => handleCancel(b.id)}
                  className="text-gray-300 hover:text-red-500 transition"
                  title="Cancelar reserva"
                >
                  <X className="w-5 h-5" />
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
