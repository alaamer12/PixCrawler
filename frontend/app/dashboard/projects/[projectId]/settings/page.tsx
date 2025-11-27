'use client'

import {useEffect, useState} from 'react'
import {useRouter, useParams} from 'next/navigation'
import {Card, CardContent, CardDescription, CardHeader, CardTitle} from '@/components/ui/card'
import {Button} from '@/components/ui/button'
import {Badge} from '@/components/ui/badge'
import {Input} from '@/components/ui/input'
import {Label} from '@/components/ui/label'
import {Switch} from '@/components/ui/switch'
import {Textarea} from '@/components/ui/textarea'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {Checkbox} from '@/components/ui/checkbox'
import {Slider} from '@/components/ui/slider'
import {useToast} from '@/components/ui/use-toast'
import {cn} from '@/lib/utils'
import {
  ArrowLeft,
  Settings,
  Save,
  Trash2,
  Archive,
  Copy,
  RefreshCw,
  AlertCircle,
  Sparkles,
  Download,
  Database,
  Zap,
  Info,
  FileCheck
} from 'lucide-react'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import Link from 'next/link'

// Types
interface ProjectSettings {
  name: string
  description: string
  safeMode: boolean
  aiKeywordExpansion: boolean
  engines: { google: boolean; bing: boolean; pixabay: boolean; ddg: boolean }
  dedupLevel: 'none' | 'fast' | 'medium' | 'aggressive'
  validationProfile: 'fast' | 'balanced' | 'strict'
  minResolution: [number, number]
  formats: { jpg: boolean; png: boolean; webp: boolean }
  maxConcurrency: number
  chunkSize: number
  retryCount: number
  respectRobots: boolean
  storageTier: 'hot' | 'warm'
  exportFormat: 'zip' | '7z'
  labelFormats: { json: boolean; csv: boolean; txt: boolean }
}

const DEFAULT_SETTINGS: ProjectSettings = {
  name: 'Wildlife Conservation Dataset',
  description: 'African wildlife images for conservation AI and research purposes',
  safeMode: true,
  aiKeywordExpansion: true,
  engines: { google: true, bing: true, pixabay: true, ddg: false },
  dedupLevel: 'medium',
  validationProfile: 'balanced',
  minResolution: [512, 512],
  formats: { jpg: true, png: true, webp: true },
  maxConcurrency: 6,
  chunkSize: 100,
  retryCount: 3,
  respectRobots: true,
  storageTier: 'hot',
  exportFormat: 'zip',
  labelFormats: { json: true, csv: false, txt: false}
}

// Focused Components
const SettingsSection = ({ 
  id, 
  icon: Icon, 
  title, 
  description, 
  children,
  variant = 'default'
}: { 
  id: string
  icon: any
  title: string
  description: string
  children: React.ReactNode
  variant?: 'default' | 'danger'
}) => (
  <Card 
    id={`section-${id}`} 
    className={cn(
      "transition-all duration-200 hover:shadow-lg",
      variant === 'danger' && "border-destructive/40 bg-destructive/5"
    )}
  >
    <CardHeader>
      <CardTitle className={cn(
        "flex items-center gap-2.5 text-lg",
        variant === 'danger' && "text-destructive"
      )}>
        <div className={cn(
          "p-1.5 rounded-md",
          variant === 'danger' ? "bg-destructive/10" : "bg-primary/10"
        )}>
          <Icon className="w-4 h-4" />
        </div>
        {title}
      </CardTitle>
      <CardDescription>{description}</CardDescription>
    </CardHeader>
    <CardContent className="space-y-5">
      {children}
    </CardContent>
  </Card>
)

const SettingRow = ({ 
  label, 
  description, 
  tooltip,
  children 
}: { 
  label: string
  description?: string
  tooltip?: string
  children: React.ReactNode 
}) => (
  <div className="flex items-start justify-between gap-4 py-1">
    <div className="space-y-0.5 flex-1">
      <div className="flex items-center gap-2">
        <Label className="text-sm font-medium leading-none">{label}</Label>
        {tooltip && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Info className="w-3.5 h-3.5 text-muted-foreground cursor-help" />
              </TooltipTrigger>
              <TooltipContent className="max-w-xs">
                <p className="text-xs">{tooltip}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
      </div>
      {description && (
        <p className="text-xs text-muted-foreground leading-snug">{description}</p>
      )}
    </div>
    <div className="flex-shrink-0">
      {children}
    </div>
  </div>
)

const SliderSetting = ({
  label,
  description,
  value,
  min,
  max,
  step,
  unit,
  onChange
}: {
  label: string
  description?: string
  value: number
  min: number
  max: number
  step: number
  unit: string
  onChange: (value: number) => void
}) => (
  <div className="space-y-3">
    <div className="flex items-center justify-between">
      <Label className="text-sm font-medium">{label}</Label>
      <Badge variant="secondary" className="font-mono text-xs">
        {value} {unit}
      </Badge>
    </div>
    {description && (
      <p className="text-xs text-muted-foreground">{description}</p>
    )}
    <Slider 
      value={[value]} 
      min={min} 
      max={max} 
      step={step} 
      onValueChange={(v) => onChange(v[0])}
      className="py-1"
    />
  </div>
)

const SectionNav = ({ 
  sections, 
  activeSection, 
  onNavigate 
}: { 
  sections: Array<{id: string; label: string; icon: any}>
  activeSection: string
  onNavigate: (id: string) => void 
}) => (
  <div className="sticky top-4 space-y-1">
    {sections.map(({id, label, icon: Icon}) => (
      <button
        key={id}
        onClick={() => onNavigate(id)}
        className={cn(
          "w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-all",
          "hover:bg-accent hover:text-accent-foreground",
          activeSection === id 
            ? "bg-primary text-primary-foreground shadow-sm" 
            : "text-muted-foreground"
        )}
      >
        <Icon className="w-4 h-4 flex-shrink-0" />
        <span>{label}</span>
      </button>
    ))}
  </div>
)

export default function ProjectSettingsPage() {
  const router = useRouter()
  const params = useParams()
  const projectId = params.projectId as string
  const {toast} = useToast()

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [hasChanges, setHasChanges] = useState(false)
  const [settings, setSettings] = useState<ProjectSettings>(DEFAULT_SETTINGS)
  const [activeSection, setActiveSection] = useState('general')

  const sections = [
    { id: 'general', label: 'General', icon: Settings },
    { id: 'search', label: 'Search & AI', icon: Sparkles },
    { id: 'validation', label: 'Validation', icon: FileCheck },
    { id: 'download', label: 'Download', icon: Download },
    { id: 'storage', label: 'Storage', icon: Database },
    { id: 'danger', label: 'Danger Zone', icon: AlertCircle }
  ]

  const updateSetting = <K extends keyof ProjectSettings>(
    key: K, 
    value: ProjectSettings[K]
  ) => {
    setSettings(prev => ({ ...prev, [key]: value }))
    setHasChanges(true)
  }

  const scrollTo = (id: string) => {
    const el = document.getElementById(`section-${id}`)
    if (el) {
      const offset = 80
      const top = el.getBoundingClientRect().top + window.scrollY - offset
      window.scrollTo({ top, behavior: 'smooth' })
    }
  }

  const handleSave = async () => {
    setSaving(true)
    await new Promise(resolve => setTimeout(resolve, 800))
    setSaving(false)
    setHasChanges(false)
    toast({ 
      title: 'Settings saved',
      description: 'Your project configuration has been updated successfully'
    })
  }

  const resetToDefaults = () => {
    setSettings(DEFAULT_SETTINGS)
    setHasChanges(true)
    toast({ 
      title: 'Defaults restored',
      description: 'All settings have been reset to recommended defaults'
    })
  }

  const exportSettings = () => {
    const dataStr = 'data:application/json;charset=utf-8,' + 
      encodeURIComponent(JSON.stringify(settings, null, 2))
    const link = document.createElement('a')
    link.setAttribute('href', dataStr)
    link.setAttribute('download', `project_${projectId}_settings.json`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    toast({ 
      title: 'Settings exported',
      description: 'Configuration downloaded as JSON file'
    })
  }

  useEffect(() => {
    setTimeout(() => setLoading(false), 500)
  }, [projectId])

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter(e => e.isIntersecting)
          .sort((a,b) => a.boundingClientRect.top - b.boundingClientRect.top)[0]
        if (visible?.target?.id) {
          setActiveSection(visible.target.id.replace('section-',''))
        }
      },
      { rootMargin: '-20% 0px -60% 0px', threshold: 0.1 }
    )
    
    sections.forEach(({id}) => {
      const el = document.getElementById(`section-${id}`)
      if (el) observer.observe(el)
    })
    
    return () => observer.disconnect()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center space-y-4">
          <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-sm text-muted-foreground">Loading project settings...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
      {/* Header */}
      <div className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
        <div className="container max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between gap-6">
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="sm" asChild>
                <Link href={`/dashboard/projects/${projectId}`}>
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back
                </Link>
              </Button>
              <div className="h-6 w-px bg-border" />
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-xl font-semibold tracking-tight">Project Settings</h1>
                  <Badge variant="outline" className="bg-primary/10 text-primary border-primary/30">
                    {settings.name}
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Configure defaults and behavior for this project
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              {hasChanges && (
                <Badge variant="secondary" className="animate-pulse">
                  Unsaved changes
                </Badge>
              )}
              <Button
                variant="outline"
                size="sm"
                onClick={exportSettings}
              >
                <Copy className="w-4 h-4 mr-2" />
                Export
              </Button>
              <Button
                size="sm"
                onClick={handleSave}
                disabled={!hasChanges || saving}
              >
                {saving ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4 mr-2" />
                    Save Changes
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container max-w-7xl mx-auto px-6 py-8">
        <div className="grid lg:grid-cols-[240px_1fr] gap-8">
          {/* Sidebar Navigation */}
          <aside className="hidden lg:block">
            <SectionNav 
              sections={sections}
              activeSection={activeSection}
              onNavigate={scrollTo}
            />
          </aside>

          {/* Settings Sections */}
          <div className="space-y-6">
            {/* General */}
            <SettingsSection
              id="general"
              icon={Settings}
              title="General Information"
              description="Basic project details and identification"
            >
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="project-name">Project Name</Label>
                  <Input 
                    id="project-name" 
                    value={settings.name}
                    onChange={(e) => updateSetting('name', e.target.value)}
                    className="font-medium"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="project-description">Description</Label>
                  <Textarea 
                    id="project-description" 
                    value={settings.description}
                    onChange={(e) => updateSetting('description', e.target.value)}
                    rows={3}
                    className="resize-none"
                  />
                  <p className="text-xs text-muted-foreground">
                    Provide context about the purpose and scope of this project
                  </p>
                </div>
              </div>
            </SettingsSection>

            {/* Search & AI */}
            <SettingsSection
              id="search"
              icon={Sparkles}
              title="Search & AI Processing"
              description="Configure search behavior and AI-powered features"
            >
              <SettingRow
                label="Safe Search"
                description="Filter adult and explicit content from results"
                tooltip="Recommended for production datasets and compliance requirements"
              >
                <Switch 
                  checked={settings.safeMode}
                  onCheckedChange={(v) => updateSetting('safeMode', v)}
                />
              </SettingRow>

              <SettingRow
                label="AI Keyword Expansion"
                description="Automatically expand search terms using AI"
                tooltip="Uses semantic understanding to find related terms and improve coverage"
              >
                <Switch 
                  checked={settings.aiKeywordExpansion}
                  onCheckedChange={(v) => updateSetting('aiKeywordExpansion', v)}
                />
              </SettingRow>

              <div className="space-y-3 pt-2">
                <Label className="text-sm font-medium">Search Engines</Label>
                <div className="grid grid-cols-2 gap-3">
                  {Object.entries(settings.engines).map(([engine, enabled]) => (
                    <div key={engine} className="flex items-center gap-2">
                      <Checkbox 
                        id={`engine-${engine}`}
                        checked={enabled}
                        onCheckedChange={(v) => updateSetting('engines', {
                          ...settings.engines,
                          [engine]: !!v
                        })}
                      />
                      <Label 
                        htmlFor={`engine-${engine}`}
                        className="text-sm capitalize cursor-pointer"
                      >
                        {engine === 'ddg' ? 'DuckDuckGo' : engine}
                      </Label>
                    </div>
                  ))}
                </div>
              </div>

              <div className="space-y-2 pt-2">
                <Label htmlFor="dedup-level">Deduplication Level</Label>
                <Select 
                  value={settings.dedupLevel}
                  onValueChange={(v) => updateSetting('dedupLevel', v as any)}
                >
                  <SelectTrigger id="dedup-level">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">None - Keep all images</SelectItem>
                    <SelectItem value="fast">Fast - Basic duplicate detection</SelectItem>
                    <SelectItem value="medium">Medium - Balanced accuracy</SelectItem>
                    <SelectItem value="aggressive">Aggressive - Maximum removal</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </SettingsSection>

            {/* Validation */}
            <SettingsSection
              id="validation"
              icon={FileCheck}
              title="Validation & Quality"
              description="Set quality standards and format requirements"
            >
              <div className="space-y-2">
                <Label htmlFor="validation-profile">Validation Profile</Label>
                <Select 
                  value={settings.validationProfile}
                  onValueChange={(v) => updateSetting('validationProfile', v as any)}
                >
                  <SelectTrigger id="validation-profile">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="fast">Fast - Minimal checks</SelectItem>
                    <SelectItem value="balanced">Balanced - Standard validation</SelectItem>
                    <SelectItem value="strict">Strict - Comprehensive checks</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <SliderSetting
                label="Minimum Resolution"
                description="Reject images below this resolution threshold"
                value={settings.minResolution[0]}
                min={128}
                max={2048}
                step={64}
                unit="px"
                onChange={(v) => updateSetting('minResolution', [v, v])}
              />

              <div className="space-y-3 pt-2">
                <Label className="text-sm font-medium">Allowed Formats</Label>
                <div className="flex items-center gap-6">
                  {Object.entries(settings.formats).map(([format, enabled]) => (
                    <div key={format} className="flex items-center gap-2">
                      <Checkbox 
                        id={`format-${format}`}
                        checked={enabled}
                        onCheckedChange={(v) => updateSetting('formats', {
                          ...settings.formats,
                          [format]: !!v
                        })}
                      />
                      <Label 
                        htmlFor={`format-${format}`}
                        className="text-sm uppercase cursor-pointer font-mono"
                      >
                        {format}
                      </Label>
                    </div>
                  ))}
                </div>
              </div>
            </SettingsSection>

            {/* Download */}
            <SettingsSection
              id="download"
              icon={Download}
              title="Download & Performance"
              description="Configure download behavior and reliability"
            >
              <SliderSetting
                label="Max Concurrency"
                description="Number of parallel download workers"
                value={settings.maxConcurrency}
                min={1}
                max={16}
                step={1}
                unit="workers"
                onChange={(v) => updateSetting('maxConcurrency', v)}
              />

              <SliderSetting
                label="Chunk Size"
                description="Items processed per batch"
                value={settings.chunkSize}
                min={25}
                max={500}
                step={25}
                unit="items"
                onChange={(v) => updateSetting('chunkSize', v)}
              />

              <div className="space-y-2">
                <Label htmlFor="retry-count">Retry Attempts</Label>
                <Input 
                  id="retry-count"
                  type="number"
                  min={0}
                  max={10}
                  value={settings.retryCount}
                  onChange={(e) => updateSetting('retryCount', parseInt(e.target.value) || 0)}
                  className="w-32"
                />
                <p className="text-xs text-muted-foreground">
                  Number of retry attempts for failed downloads
                </p>
              </div>

              <SettingRow
                label="Respect robots.txt"
                description="Honor website crawling restrictions"
                tooltip="Recommended for ethical web scraping practices"
              >
                <Switch 
                  checked={settings.respectRobots}
                  onCheckedChange={(v) => updateSetting('respectRobots', v)}
                />
              </SettingRow>
            </SettingsSection>

            {/* Storage */}
            <SettingsSection
              id="storage"
              icon={Database}
              title="Storage & Export"
              description="Configure storage tiers and export formats"
            >
              <div className="space-y-2">
                <Label htmlFor="storage-tier">Storage Tier</Label>
                <Select 
                  value={settings.storageTier}
                  onValueChange={(v) => updateSetting('storageTier', v as any)}
                >
                  <SelectTrigger id="storage-tier">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="hot">
                      <div className="flex items-center gap-2">
                        <Zap className="w-4 h-4" />
                        <div>
                          <div className="font-medium">Hot Storage</div>
                          <div className="text-xs text-muted-foreground">Fastest access, higher cost</div>
                        </div>
                      </div>
                    </SelectItem>
                    <SelectItem value="warm">
                      <div className="flex items-center gap-2">
                        <Archive className="w-4 h-4" />
                        <div>
                          <div className="font-medium">Warm Storage</div>
                          <div className="text-xs text-muted-foreground">Balanced performance</div>
                        </div>
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="export-format">Compression Format</Label>
                <Select 
                  value={settings.exportFormat}
                  onValueChange={(v) => updateSetting('exportFormat', v as any)}
                >
                  <SelectTrigger id="export-format">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="zip">ZIP - Universal compatibility</SelectItem>
                    <SelectItem value="7z">7z - Higher compression ratio</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-3 pt-2">
                <Label className="text-sm font-medium">Label Export Formats</Label>
                <div className="grid grid-cols-2 gap-3">
                  {Object.entries(settings.labelFormats).map(([format, enabled]) => (
                    <div key={format} className="flex items-center gap-2">
                      <Checkbox 
                        id={`label-${format}`}
                        checked={enabled}
                        onCheckedChange={(v) => updateSetting('labelFormats', {
                          ...settings.labelFormats,
                          [format]: !!v
                        })}
                      />
                      <Label 
                        htmlFor={`label-${format}`}
                        className="text-sm uppercase cursor-pointer font-mono"
                      >
                        {format}
                      </Label>
                    </div>
                  ))}
                </div>
              </div>
            </SettingsSection>

            {/* Danger Zone */}
            <SettingsSection
              id="danger"
              icon={AlertCircle}
              title="Danger Zone"
              description="Irreversible actions - proceed with extreme caution"
              variant="danger"
            >
              <div className="grid gap-3 sm:grid-cols-2">
                <Button 
                  variant="outline" 
                  onClick={resetToDefaults}
                  className="justify-start"
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Reset to Defaults
                </Button>

                <Button 
                  variant="outline"
                  onClick={exportSettings}
                  className="justify-start"
                >
                  <Copy className="w-4 h-4 mr-2" />
                  Export Configuration
                </Button>

                <Button 
                  variant="outline"
                  onClick={() => {
                    toast({ 
                      title: 'Project archived',
                      description: 'Project moved to archive section'
                    })
                    setTimeout(() => router.push('/dashboard/projects'), 1000)
                  }}
                  className="justify-start"
                >
                  <Archive className="w-4 h-4 mr-2" />
                  Archive Project
                </Button>

                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button variant="destructive" className="justify-start">
                      <Trash2 className="w-4 h-4 mr-2" />
                      Delete Project
                    </Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle className="flex items-center gap-2">
                        <AlertCircle className="w-5 h-5 text-destructive" />
                        Delete "{settings.name}"?
                      </AlertDialogTitle>
                      <AlertDialogDescription className="space-y-2">
                        <p>This action cannot be undone. This will permanently delete:</p>
                        <ul className="list-disc list-inside space-y-1 text-sm">
                          <li>All datasets under this project</li>
                          <li>All processing jobs and results</li>
                          <li>All project settings and configurations</li>
                          <li>All associated metadata and labels</li>
                        </ul>
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>Cancel</AlertDialogCancel>
                      <AlertDialogAction 
                        onClick={() => {
                          toast({ 
                            title: 'Project deleted',
                            description: `"${settings.name}" has been permanently removed`
                          })
                          setTimeout(() => router.push('/dashboard/projects'), 1000)
                        }}
                        className="bg-destructive hover:bg-destructive/90"
                      >
                        Delete Project
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              </div>
            </SettingsSection>
          </div>
        </div>
      </div>
    </div>
  )
}