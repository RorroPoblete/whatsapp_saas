import { InputHTMLAttributes, forwardRef } from "react"
import { clsx } from "clsx"

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className, ...props }, ref) => {
    return (
      <div>
        {label && (
          <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
        )}
        <input
          ref={ref}
          className={clsx(
            "w-full px-3 py-2 border rounded-lg text-sm outline-none transition",
            "focus:ring-2 focus:ring-brand-500 focus:border-transparent",
            error ? "border-red-300 bg-red-50" : "border-gray-200",
            className,
          )}
          {...props}
        />
        {error && <p className="text-xs text-red-600 mt-1">{error}</p>}
      </div>
    )
  },
)

Input.displayName = "Input"
