import { toast as sonnerToast } from 'sonner'

interface ToastOptions {
  title?: string
  description?: string
  variant?: 'default' | 'destructive'
  action?: {
    label: string
    onClick: () => void
  }
}

export function useToast() {
  const toast = ({ title, description, variant, action }: ToastOptions) => {
    const message = title || description || ''
    const descriptionText = title && description ? description : undefined

    if (variant === 'destructive') {
      return sonnerToast.error(message, {
        description: descriptionText,
        action: action ? {
          label: action.label,
          onClick: action.onClick,
        } : undefined,
      })
    }

    return sonnerToast.success(message, {
      description: descriptionText,
      action: action ? {
        label: action.label,
        onClick: action.onClick,
      } : undefined,
    })
  }

  return {
    toast,
    dismiss: (toastId?: string | number) => sonnerToast.dismiss(toastId),
  }
}

export { sonnerToast as toast }
