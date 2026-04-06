"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { login } from "@/lib/api"
import { setToken } from "@/lib/auth"

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError("")
    setLoading(true)

    try {
      const res = await login({ email, password })
      setToken(res.access_token)
      router.push("/dashboard")
    } catch (err: any) {
      setError(err.message || "Error al iniciar sesion")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link href="/" className="text-2xl font-bold text-brand-600">AgentKit</Link>
          <p className="text-gray-600 mt-2">Inicia sesion en tu cuenta</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-white p-8 rounded-xl shadow-sm border border-gray-100 space-y-4">
          {error && (
            <div className="bg-red-50 text-red-600 text-sm p-3 rounded-lg">{error}</div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none"
              placeholder="tu@email.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Contrasena</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none"
              placeholder="******"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-brand-600 text-white py-2.5 rounded-lg font-medium hover:bg-brand-700 transition disabled:opacity-50"
          >
            {loading ? "Entrando..." : "Iniciar sesion"}
          </button>

          <p className="text-center text-sm text-gray-600">
            No tienes cuenta?{" "}
            <Link href="/register" className="text-brand-600 hover:underline">
              Registrate
            </Link>
          </p>
        </form>
      </div>
    </div>
  )
}
