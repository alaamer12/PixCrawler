'use client'

import * as React from 'react'
import {Slot} from '@radix-ui/react-slot'
import {cva, type VariantProps} from 'class-variance-authority'
import {cn} from '@/lib/utils'
import {Loader2} from 'lucide-react'

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 active:scale-[0.98] select-none',
  {
    variants: {
      variant: {
        default:
          'bg-gradient-to-r from-primary to-secondary text-primary-foreground shadow-lg hover:shadow-xl hover:opacity-90 active:shadow-md',
        destructive:
          'bg-destructive text-destructive-foreground shadow-sm hover:bg-destructive/90 active:bg-destructive/80',
        outline:
          'border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground active:bg-accent/80',
        secondary:
          'bg-secondary text-secondary-foreground shadow-sm hover:bg-secondary/80 active:bg-secondary/70',
        ghost: 'hover:bg-accent hover:text-accent-foreground active:bg-accent/80',
        link: 'text-primary underline-offset-4 hover:underline active:text-primary/80',
        brand:
          'bg-primary text-primary-foreground shadow-lg hover:shadow-xl hover:scale-[1.02] active:scale-[0.98] relative overflow-hidden',
        success:
          'bg-success text-success-foreground shadow-sm hover:bg-success/90 active:bg-success/80',
        warning:
          'bg-warning text-warning-foreground shadow-sm hover:bg-warning/90 active:bg-warning/80',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-8 rounded-md px-3 text-xs',
        lg: 'h-12 rounded-lg px-8 text-base',
        xl: 'h-14 rounded-xl px-10 text-lg',
        icon: 'h-10 w-10',
        'icon-sm': 'h-8 w-8 rounded-md',
        'icon-lg': 'h-12 w-12 rounded-lg',
      },
      loading: {
        true: 'cursor-not-allowed',
        false: '',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
      loading: false,
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
  loading?: boolean
  loadingText?: string
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant,
      size,
      loading = false,
      loadingText,
      leftIcon,
      rightIcon,
      asChild = false,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    const Comp = asChild ? Slot : 'button'
    const isDisabled = disabled || loading

    // When using asChild, we can't add extra elements, so we just pass the children
    if (asChild) {
      return (
        <Comp
          className={cn(buttonVariants({variant, size, loading, className}))}
          ref={ref}
          disabled={isDisabled}
          {...props}
        >
          {children}
        </Comp>
      )
    }

    return (
      <Comp
        className={cn(buttonVariants({variant, size, loading, className}))}
        ref={ref}
        disabled={isDisabled}
        {...props}
      >
        {/* Brand variant shimmer effect */}
        {variant === 'brand' && (
          <div
            className="absolute inset-0 -top-[2px] -bottom-[2px] bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer"/>
        )}

        {/* Loading state */}
        {loading && (
          <Loader2 className="h-4 w-4 animate-spin"/>
        )}

        {/* Left icon */}
        {!loading && leftIcon && (
          <span className="flex-shrink-0">{leftIcon}</span>
        )}

        {/* Button content */}
        <span className={cn(loading && 'opacity-70')}>
          {loading && loadingText ? loadingText : children}
        </span>

        {/* Right icon */}
        {!loading && rightIcon && (
          <span className="flex-shrink-0">{rightIcon}</span>
        )}
      </Comp>
    )
  }
)
Button.displayName = 'Button'

// Enhanced button variants for specific use cases
const IconButton = React.forwardRef<
  HTMLButtonElement,
  Omit<ButtonProps, 'leftIcon' | 'rightIcon'> & { icon: React.ReactNode }
>(({icon, className, size = 'icon', ...props}, ref) => (
  <Button ref={ref} size={size} className={className} {...props}>
    {icon}
  </Button>
))
IconButton.displayName = 'IconButton'

const LoadingButton = React.forwardRef<
  HTMLButtonElement,
  ButtonProps & { isLoading?: boolean }
>(({isLoading, children, ...props}, ref) => (
  <Button ref={ref} loading={isLoading} {...props}>
    {children}
  </Button>
))
LoadingButton.displayName = 'LoadingButton'

const GradientButton = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({className, ...props}, ref) => (
    <Button
      ref={ref}
      variant="brand"
      className={cn(
        'bg-gradient-to-r from-primary via-accent to-secondary',
        'hover:from-primary/90 hover:via-accent/90 hover:to-secondary/90',
        'active:from-primary/80 active:via-accent/80 active:to-secondary/80',
        className
      )}
      {...props}
    />
  )
)
GradientButton.displayName = 'GradientButton'

export {Button, IconButton, LoadingButton, GradientButton, buttonVariants}
