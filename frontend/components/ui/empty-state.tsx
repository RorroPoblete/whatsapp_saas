import { LucideIcon } from "lucide-react"

interface EmptyStateProps {
  icon: LucideIcon
  title: string
  description: string
  action?: React.ReactNode
}

export function EmptyState({ icon: Icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="text-center py-16">
      <Icon className="w-12 h-12 mx-auto mb-3 text-gray-300" />
      <h3 className="font-medium text-gray-600 mb-1">{title}</h3>
      <p className="text-sm text-gray-400 mb-6 max-w-sm mx-auto">{description}</p>
      {action}
    </div>
  )
}
