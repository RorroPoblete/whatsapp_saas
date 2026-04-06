"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { register } from "@/lib/api"
import { setToken } from "@/lib/auth"

export default function RegisterPage() {
  const router = useRouter()
  const [form, setForm] = useState({ name: "", email: "", password: "", business_name: "" })
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  function update(field: string, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError("")
    setLoading(true)

    try {
      const res = await register(form)
      setToken(res.access_token)
      router.push("/setup")
    } catch (err: any) {
      setError(err.message || "Error al registrarse")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link href="/" className="text-2xl font-bold text-brand-600">AgentKit</Link>
          <p className="text-gray-600 mt-2">Crea tu cuenta y configura tu agente</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-white p-8 rounded-xl shadow-sm border border-gray-100 space-y-4">
          {error && (
            <div className="bg-red-50 text-red-600 text-sm p-3 rounded-lg">{error}</div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Tu nombre</label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => update("name", e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none"
              placeholder="Juan Perez"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Nombre de tu negocio</label>
            <input
              type="text"
              value={form.business_name}
              onChange={(e) => update("business_name", e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none"
              placeholder="Mi Empresa"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input
              type="email"
              value={form.email}
              onChange={(e) => update("email", e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none"
              placeholder="tu@email.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Contrasena</label>
            <input
              type="password"
              value={form.password}
              onChange={(e) => update("password", e.target.value)}
              required
              minLength={6}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none"
              placeholder="Minimo 6 caracteres"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-brand-600 text-white py-2.5 rounded-lg font-medium hover:bg-brand-700 transition disabled:opacity-50"
          >
            {loading ? "Creando cuenta..." : "Crear cuenta"}
          </button>

          <p className="text-center text-sm text-gray-600">
            Ya tienes cuenta?{" "}
            <Link href="/login" className="text-brand-600 hover:underline">
              Inicia sesion
            </Link>
          </p>
        </form>
      </div>
    </div>
  )
}
