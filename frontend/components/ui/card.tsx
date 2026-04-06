import { HTMLAttributes } from "react"
import { clsx } from "clsx"

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  padding?: "sm" | "md" | "lg"
}

export function Card({ padding = "md", className, children, ...props }: CardProps) {
  const paddings = { sm: "p-4", md: "p-6", lg: "p-8" }
  return (
    <div
      className={clsx(
        "bg-white rounded-xl border border-gray-100",
        paddings[padding],
        className,
      )}
      {...props}
    >
      {children}
    </div>
  )
}

export function CardTitle({ children }: { children: React.ReactNode }) {
  return <h3 className="font-semibold text-lg mb-2">{children}</h3>
}

export function CardDescription({ children }: { children: React.ReactNode }) {
  return <p className="text-sm text-gray-500">{children}</p>
}
