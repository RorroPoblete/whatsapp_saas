"use client"

import { useEffect, useState } from "react"
import { clsx } from "clsx"
import { X, CheckCircle, AlertCircle } from "lucide-react"

type ToastType = "success" | "error"

interface Toast {
  id: number
  type: ToastType
  message: string
}

let addToast: (type: ToastType, message: string) => void = () => {}

export function toast(type: ToastType, message: string) {
  addToast(type, message)
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  useEffect(() => {
    addToast = (type, message) => {
      const id = Date.now()
      setToasts((prev) => [...prev, { id, type, message }])
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id))
      }, 4000)
    }
  }, [])

  return (
    <>
      {children}
      <div className="fixed bottom-4 right-4 z-50 space-y-2">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={clsx(
              "flex items-center gap-2 px-4 py-3 rounded-lg shadow-lg text-sm animate-in slide-in-from-bottom",
              t.type === "success" ? "bg-green-600 text-white" : "bg-red-600 text-white",
            )}
          >
            {t.type === "success" ? (
              <CheckCircle className="w-4 h-4" />
            ) : (
              <AlertCircle className="w-4 h-4" />
            )}
            {t.message}
            <button
              onClick={() => setToasts((prev) => prev.filter((x) => x.id !== t.id))}
              className="ml-2 opacity-70 hover:opacity-100"
            >
              <X className="w-3 h-3" />
            </button>
          </div>
        ))}
      </div>
    </>
  )
}
