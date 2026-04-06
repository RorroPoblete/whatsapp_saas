"use client"

import { useEffect, useState } from "react"
import { useRouter, usePathname } from "next/navigation"
import Link from "next/link"
import { getToken, removeToken } from "@/lib/auth"
import { getMe, type UserResponse } from "@/lib/api"
import {
  LayoutDashboard,
  MessageSquare,
  Settings,
  BarChart3,
  LogOut,
  Wand2,
} from "lucide-react"

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/conversations", label: "Conversaciones", icon: MessageSquare },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/settings", label: "Configuracion", icon: Settings },
]

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()
  const [user, setUser] = useState<UserResponse | null>(null)

  useEffect(() => {
    const token = getToken()
    if (!token) {
      router.push("/login")
      return
    }
    getMe(token)
      .then(setUser)
      .catch(() => {
        removeToken()
        router.push("/login")
      })
  }, [router])

  function handleLogout() {
    removeToken()
    router.push("/login")
  }

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-pulse text-gray-400">Cargando...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex bg-gray-50">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-100 flex flex-col">
        <div className="h-16 flex items-center px-6 border-b border-gray-100">
          <Link href="/dashboard" className="text-xl font-bold text-brand-600">
            AgentKit
          </Link>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => {
            const active = pathname === item.href || pathname.startsWith(item.href + "/")
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition ${
                  active
                    ? "bg-brand-50 text-brand-700 font-medium"
                    : "text-gray-600 hover:bg-gray-50"
                }`}
              >
                <item.icon className="w-5 h-5" />
                {item.label}
              </Link>
            )
          })}
        </nav>

        <div className="p-4 border-t border-gray-100">
          <div className="text-sm text-gray-500 mb-1 truncate">{user.tenant_name}</div>
          <div className="text-xs text-gray-400 mb-3 truncate">{user.email}</div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 text-sm text-gray-500 hover:text-red-500 transition"
          >
            <LogOut className="w-4 h-4" /> Cerrar sesion
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-6xl mx-auto p-8">{children}</div>
      </main>
    </div>
  )
}
