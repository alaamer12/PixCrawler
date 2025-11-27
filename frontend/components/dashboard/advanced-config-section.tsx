'use client'

import React, { memo, useCallback, useMemo } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Slider } from '@/components/ui/slider'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { 
  Settings2, 
  Shield, 
  Zap, 
  Brain, 
  Server, 
  Lock,
  Info,
  AlertCircle,
  CheckCircle2,
  Sparkles,
  Database,
  Cloud,
  Cpu,
  HardDrive,
  Activity,
  Globe,
  FileText,
  Package
} from 'lucide-react'
import { cn } from '@/lib/utils'

export interface ConfigOption {
  id: string
  label: string
  value: any
  type: 'switch' | 'slider' | 'select' | 'input' | 'multi-select'
  description?: string
  icon?: React.ElementType
  options?: { value: string; label: string; description?: string }[]
  min?: number
  max?: number
  step?: number
  unit?: string
  validation?: (value: any) => { valid: boolean; message?: string }
  premium?: boolean
  experimental?: boolean
  impact?: 'low' | 'medium' | 'high'
}

export interface ConfigSection {
  id: string
  title: string
  description?: string
  icon: React.ElementType
  options: ConfigOption[]
  collapsed?: boolean
  premium?: boolean
}

interface AdvancedConfigSectionProps {
  sections: ConfigSection[]
  values: Record<string, any>
  onChange: (id: string, value: any) => void
  className?: string
  showImpactIndicators?: boolean
  showValidation?: boolean
}

// Memoized config item component for performance
const ConfigItem = memo(({ 
  option, 
  value, 
  onChange,
  showImpact,
  showValidation 
}: {
  option: ConfigOption
  value: any
  onChange: (value: any) => void
  showImpact?: boolean
  showValidation?: boolean
}) => {
  const validation = useMemo(() => {
    if (!showValidation || !option.validation) return null
    return option.validation(value)
  }, [option, value, showValidation])

  const Icon = option.icon

  const renderControl = useCallback(() => {
    switch (option.type) {
      case 'switch':
        return (
          <Switch
            checked={value}
            onCheckedChange={onChange}
            className="data-[state=checked]:bg-primary"
          />
        )
      
      case 'slider':
        return (
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">
                {value}{option.unit}
              </span>
              {showImpact && option.impact && (
                <Badge 
                  variant="outline" 
                  className={cn(
                    "text-xs",
                    option.impact === 'high' && "border-red-500/50 text-red-500",
                    option.impact === 'medium' && "border-yellow-500/50 text-yellow-500",
                    option.impact === 'low' && "border-green-500/50 text-green-500"
                  )}
                >
                  {option.impact} impact
                </Badge>
              )}
            </div>
            <Slider
              value={[value]}
              onValueChange={([v]) => onChange(v)}
              min={option.min}
              max={option.max}
              step={option.step}
              className="py-4"
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>{option.min}{option.unit}</span>
              <span>{option.max}{option.unit}</span>
            </div>
          </div>
        )
      
      case 'select':
        return (
          <Select value={value} onValueChange={onChange}>
            <SelectTrigger className="bg-gradient-to-br from-background/60 to-background/30 border border-border/60 hover:border-primary/40 hover:from-background/70 rounded-xl shadow-sm px-3 py-2">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="rounded-xl border-border/50 bg-background/90 backdrop-blur-md shadow-lg">
              {option.options?.map(opt => (
                <SelectItem key={opt.value} value={opt.value} className="gap-2 py-2">
                  <div className="flex flex-col">
                    <span>{opt.label}</span>
                    {opt.description && (
                      <span className="text-xs text-muted-foreground">
                        {opt.description}
                      </span>
                    )}
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )
      
      case 'input':
        return (
          <Input
            value={value}
            onChange={(e) => onChange(e.target.value)}
            className="bg-background/50"
            placeholder={option.description}
          />
        )
      
      case 'multi-select':
        return (
          <div className="grid grid-cols-2 gap-2">
            {option.options?.map(opt => {
              const isSelected = value?.includes(opt.value)
              return (
                <button
                  key={opt.value}
                  onClick={() => {
                    const newValue = isSelected
                      ? value.filter((v: string) => v !== opt.value)
                      : [...(value || []), opt.value]
                    onChange(newValue)
                  }}
                  className={cn(
                    "flex items-center justify-center p-2 rounded-md border transition-all",
                    isSelected
                      ? "bg-primary/10 border-primary text-primary"
                      : "bg-background/50 border-border hover:bg-accent"
                  )}
                >
                  <span className="text-sm font-medium">{opt.label}</span>
                </button>
              )
            })}
          </div>
        )
      
      default:
        return null
    }
  }, [option, value, onChange, showImpact])

  return (
    <div className="space-y-3 p-4 rounded-lg bg-background/30 border border-border/50">
      <div className="flex items-start justify-between">
        <div className="flex-1 space-y-1">
          <div className="flex items-center gap-2">
            {Icon && <Icon className="w-4 h-4 text-muted-foreground" />}
            <Label className="text-sm font-medium flex items-center gap-2">
              {option.label}
              {option.premium && (
                <Badge variant="default" className="text-xs">PRO</Badge>
              )}
              {option.experimental && (
                <Badge variant="outline" className="text-xs border-yellow-500/50 text-yellow-500">
                  BETA
                </Badge>
              )}
            </Label>
            {option.description && (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger>
                    <Info className="w-3 h-3 text-muted-foreground" />
                  </TooltipTrigger>
                  <TooltipContent>
                    <p className="max-w-xs text-xs">{option.description}</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            )}
          </div>
          {validation && !validation.valid && (
            <p className="text-xs text-destructive flex items-center gap-1">
              <AlertCircle className="w-3 h-3" />
              {validation.message}
            </p>
          )}
          {validation && validation.valid && showValidation && (
            <p className="text-xs text-green-500 flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3" />
              Valid configuration
            </p>
          )}
        </div>
      </div>
      <div className="mt-3">
        {renderControl()}
      </div>
    </div>
  )
})

ConfigItem.displayName = 'ConfigItem'

// Main component with performance optimizations
export const AdvancedConfigSection = memo(({
  sections,
  values,
  onChange,
  className,
  showImpactIndicators = true,
  showValidation = true
}: AdvancedConfigSectionProps) => {
  const [expandedSections, setExpandedSections] = React.useState<Set<string>>(
    new Set(sections.filter(s => !s.collapsed).map(s => s.id))
  )

  const toggleSection = useCallback((sectionId: string) => {
    setExpandedSections(prev => {
      const next = new Set(prev)
      if (next.has(sectionId)) {
        next.delete(sectionId)
      } else {
        next.add(sectionId)
      }
      return next
    })
  }, [])

  return (
    <div className={cn("space-y-4", className)}>
      {sections.map(section => {
        const Icon = section.icon
        const isExpanded = expandedSections.has(section.id)
        
        return (
          <Card 
            key={section.id} 
            className="bg-card/80 backdrop-blur-md border-border/50 overflow-hidden"
          >
            <CardHeader 
              className="cursor-pointer select-none hover:bg-accent/5 transition-colors"
              onClick={() => toggleSection(section.id)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-primary/10">
                    <Icon className="w-5 h-5 text-primary" />
                  </div>
                  <div>
                    <CardTitle className="text-lg flex items-center gap-2">
                      {section.title}
                      {section.premium && (
                        <Badge variant="default" className="text-xs">PRO</Badge>
                      )}
                    </CardTitle>
                    {section.description && (
                      <CardDescription className="text-xs mt-1">
                        {section.description}
                      </CardDescription>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="text-xs">
                    {section.options.length} settings
                  </Badge>
                  <div className={cn(
                    "transition-transform duration-200",
                    isExpanded ? "rotate-180" : ""
                  )}>
                    <svg
                      className="w-4 h-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M19 9l-7 7-7-7"
                      />
                    </svg>
                  </div>
                </div>
              </div>
            </CardHeader>
            {isExpanded && (
              <CardContent className="space-y-3 animate-in slide-in-from-top-2 duration-200">
                {section.options.map(option => (
                  <ConfigItem
                    key={option.id}
                    option={option}
                    value={values[option.id]}
                    onChange={(value) => onChange(option.id, value)}
                    showImpact={showImpactIndicators}
                    showValidation={showValidation}
                  />
                ))}
              </CardContent>
            )}
          </Card>
        )
      })}
    </div>
  )
})

AdvancedConfigSection.displayName = 'AdvancedConfigSection'
