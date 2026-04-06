"use client"

import Link from "next/link"
import { MessageSquare, Zap, BarChart3, Shield, ArrowRight } from "lucide-react"

const features = [
  {
    icon: MessageSquare,
    title: "Agente WhatsApp con IA",
    description: "Tu agente responde mensajes 24/7 con inteligencia artificial entrenada para tu negocio.",
  },
  {
    icon: Zap,
    title: "Listo en 10 minutos",
    description: "Configura tu negocio, conecta WhatsApp y tu agente empieza a funcionar. Sin programar.",
  },
  {
    icon: BarChart3,
    title: "Dashboard en tiempo real",
    description: "Ve las conversaciones de tus clientes, estadisticas y toma el control cuando lo necesites.",
  },
  {
    icon: Shield,
    title: "Multi-proveedor",
    description: "Funciona con Whapi.cloud, Meta Cloud API o Twilio. Tu eliges el que mejor te convenga.",
  },
]

const plans = [
  {
    name: "Free",
    price: "Gratis",
    features: ["500 mensajes/mes", "1 agente", "Historial 7 dias", "Soporte email"],
    cta: "Comenzar gratis",
    highlighted: false,
  },
  {
    name: "Pro",
    price: "$29/mes",
    features: ["5,000 mensajes/mes", "1 agente", "Historial 90 dias", "Analytics completo", "Soporte prioritario"],
    cta: "Comenzar prueba",
    highlighted: true,
  },
  {
    name: "Enterprise",
    price: "$99/mes",
    features: ["50,000 mensajes/mes", "Agentes ilimitados", "Historial ilimitado", "Integraciones API", "Soporte dedicado"],
    cta: "Contactar ventas",
    highlighted: false,
  },
]

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      {/* Navbar */}
      <nav className="border-b border-gray-100 bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <span className="text-xl font-bold text-brand-600">AgentKit</span>
          <div className="flex items-center gap-4">
            <Link href="/login" className="text-sm text-gray-600 hover:text-gray-900">
              Iniciar sesion
            </Link>
            <Link
              href="/register"
              className="text-sm bg-brand-600 text-white px-4 py-2 rounded-lg hover:bg-brand-700 transition"
            >
              Crear cuenta
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-6xl mx-auto px-6 pt-20 pb-16 text-center">
        <div className="inline-block bg-brand-50 text-brand-700 text-sm font-medium px-3 py-1 rounded-full mb-6">
          Plataforma de agentes WhatsApp con IA
        </div>
        <h1 className="text-5xl md:text-6xl font-bold tracking-tight mb-6">
          Tu negocio en WhatsApp
          <br />
          <span className="text-brand-600">con inteligencia artificial</span>
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto mb-10">
          Crea un agente de WhatsApp personalizado para tu negocio que responde
          preguntas, agenda citas y atiende clientes. Sin programar, listo en minutos.
        </p>
        <div className="flex items-center justify-center gap-4">
          <Link
            href="/register"
            className="bg-brand-600 text-white px-8 py-3 rounded-lg text-lg font-medium hover:bg-brand-700 transition flex items-center gap-2"
          >
            Crear mi agente <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="max-w-6xl mx-auto px-6 py-20">
        <h2 className="text-3xl font-bold text-center mb-12">Todo lo que necesitas</h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map((f) => (
            <div key={f.title} className="p-6 rounded-xl border border-gray-100 hover:border-brand-200 transition">
              <f.icon className="w-10 h-10 text-brand-600 mb-4" />
              <h3 className="font-semibold text-lg mb-2">{f.title}</h3>
              <p className="text-gray-600 text-sm">{f.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Pricing */}
      <section className="max-w-6xl mx-auto px-6 py-20">
        <h2 className="text-3xl font-bold text-center mb-4">Planes</h2>
        <p className="text-gray-600 text-center mb-12">Empieza gratis, escala cuando crezcas</p>
        <div className="grid md:grid-cols-3 gap-8">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`p-8 rounded-xl border-2 ${
                plan.highlighted
                  ? "border-brand-600 shadow-lg shadow-brand-100"
                  : "border-gray-100"
              }`}
            >
              <h3 className="text-xl font-bold mb-2">{plan.name}</h3>
              <p className="text-3xl font-bold mb-6">{plan.price}</p>
              <ul className="space-y-3 mb-8">
                {plan.features.map((f) => (
                  <li key={f} className="text-sm text-gray-600 flex items-center gap-2">
                    <span className="text-brand-600">&#10003;</span> {f}
                  </li>
                ))}
              </ul>
              <Link
                href="/register"
                className={`block text-center py-2.5 rounded-lg font-medium transition ${
                  plan.highlighted
                    ? "bg-brand-600 text-white hover:bg-brand-700"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                {plan.cta}
              </Link>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-100 py-8 mt-12">
        <div className="max-w-6xl mx-auto px-6 text-center text-sm text-gray-500">
          AgentKit &mdash; Plataforma de agentes WhatsApp con IA
        </div>
      </footer>
    </div>
  )
}
