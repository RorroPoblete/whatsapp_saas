import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "AgentKit — WhatsApp AI Agent Platform",
  description: "Crea tu agente de WhatsApp con IA para tu negocio. Sin programar.",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body className="bg-white text-gray-900 antialiased">{children}</body>
    </html>
  )
}
