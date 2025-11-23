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
import {ArrowLeft, Settings, Save, Database, Trash2, Archive, Copy, RefreshCw, AlertCircle} from 'lucide-react'
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
import Link from 'next/link'

export default function ProjectSettingsPage() {
  const router = useRouter()
  const params = useParams()
  const projectId = params.projectId as string
  const {toast} = useToast()

  const [loading, setLoading] = useState(true)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [safeMode, setSafeMode] = useState(true)
  const [aiKeywordExpansion, setAiKeywordExpansion] = useState(true)
  const [engines, setEngines] = useState<{ google: boolean; bing: boolean; pixabay: boolean; ddg: boolean }>({ google: true, bing: true, pixabay: true, ddg: false })
  const [dedupLevel, setDedupLevel] = useState<'none' | 'fast' | 'medium' | 'aggressive'>('medium')
  const [validationProfile, setValidationProfile] = useState<'fast' | 'balanced' | 'strict'>('balanced')
  const [minResolution, setMinResolution] = useState<[number, number]>([512, 512])
  const [formats, setFormats] = useState<{ jpg: boolean; png: boolean; webp: boolean }>({ jpg: true, png: true, webp: true })
  const [maxConcurrency, setMaxConcurrency] = useState(6)
  const [chunkSize, setChunkSize] = useState(100)
  const [retryCount, setRetryCount] = useState(3)
  const [respectRobots, setRespectRobots] = useState(true)
  const [storageTier, setStorageTier] = useState<'hot' | 'warm'>('hot')
  const [exportFormat, setExportFormat] = useState<'zip' | '7z'>('zip')
  const [labelFormats, setLabelFormats] = useState<{ json: boolean; csv: boolean; yolo: boolean; coco: boolean }>({ json: true, csv: false, yolo: true, coco: false })
  const sections = ['general','processing','download','validation','storage','danger']
  const [activeSection, setActiveSection] = useState<string>('general')

  const scrollTo = (id: string) => {
    const el = document.getElementById(`section-${id}`)
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  const resetToDefaults = () => {
    setSafeMode(true)
    setAiKeywordExpansion(true)
    setEngines({ google: true, bing: true, pixabay: true, ddg: false })
    setDedupLevel('medium')
    setValidationProfile('balanced')
    setMinResolution([512, 512])
    setFormats({ jpg: true, png: true, webp: true })
    setMaxConcurrency(6)
    setChunkSize(100)
    setRetryCount(3)
    setRespectRobots(true)
    setStorageTier('hot')
    setExportFormat('zip')
    setLabelFormats({ json: true, csv: false, yolo: true, coco: false })
    toast({ title: 'Defaults restored', description: 'Project settings reset to recommended defaults' })
  }

  const exportSettings = () => {
    const payload = {
      name,
      description,
      safeMode,
      aiKeywordExpansion,
      engines,
      dedupLevel,
      validationProfile,
      minResolution,
      formats,
      maxConcurrency,
      chunkSize,
      retryCount,
      respectRobots,
      storageTier,
      exportFormat,
      labelFormats,
    }
    const dataStr = 'data:application/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(payload, null, 2))
    const link = document.createElement('a')
    link.setAttribute('href', dataStr)
    link.setAttribute('download', `project_${projectId}_settings.json`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    toast({ title: 'Settings exported', description: 'Project settings downloaded as JSON' })
  }

  useEffect(() => {
    setTimeout(() => {
      setName('Wildlife Conservation Dataset')
      setDescription('African wildlife images for conservation AI and research purposes')
      setLoading(false)
    }, 500)
  }, [projectId])

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries.filter(e => e.isIntersecting).sort((a,b) => a.boundingClientRect.top - b.boundingClientRect.top)[0]
        if (visible?.target?.id) setActiveSection(visible.target.id.replace('section-',''))
      },
      { rootMargin: '-35% 0px -55% 0px', threshold: 0.2 }
    )
    sections.forEach(id => {
      const el = document.getElementById(`section-${id}`)
      if (el) observer.observe(el)
    })
    return () => observer.disconnect()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[300px]">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Loading settings...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8 mx-6 py-10">
      <div className="flex items-start justify-between gap-6">
        <div className="space-y-1 flex-1">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" asChild>
              <Link href={`/dashboard/projects/${projectId}`}>
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Project
              </Link>
            </Button>
            <Badge variant="outline" className="ml-2 my-1 bg-primary/10 text-primary border-primary/30">Settings</Badge>
          </div>
          <h1 className="text-3xl font-bold tracking-tight">Project Settings</h1>
          <p className="text-sm text-muted-foreground">Manage project-level configuration and defaults</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" leftIcon={<Database className="w-4 h-4" />} onClick={() => router.push(`/dashboard/projects/${projectId}`)}>
            View Project
          </Button>
          <Button
            leftIcon={<Save className="w-4 h-4" />}
            onClick={() => {
              toast({ title: 'Settings saved', description: 'Project defaults updated successfully' })
            }}
          >
            Save Changes
          </Button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Sections</CardTitle>
            <CardDescription>Quick navigation</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {sections.map(id => (
                <Button
                  key={id}
                  size="sm"
                  variant={activeSection === id ? 'default' : 'outline'}
                  onClick={() => scrollTo(id)}
                  className={cn('rounded-full')}
                >
                  {id === 'general' && 'General'}
                  {id === 'processing' && 'Processing'}
                  {id === 'download' && 'Download'}
                  {id === 'validation' && 'Validation'}
                  {id === 'storage' && 'Storage'}
                  {id === 'danger' && 'Danger Zone'}
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>
        <Card id="section-general" className="bg-card/80 backdrop-blur-md">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="w-5 h-5" />
              General
            </CardTitle>
            <CardDescription>Basic information about this project</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="project-name">Project Name</Label>
              <Input id="project-name" value={name} onChange={(e) => setName(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="project-description">Description</Label>
              <Textarea id="project-description" value={description} onChange={(e) => setDescription(e.target.value)} />
            </div>
          </CardContent>
        </Card>

        <Card id="section-processing" className="bg-card/80 backdrop-blur-md">
          <CardHeader>
            <CardTitle>Processing Defaults</CardTitle>
            <CardDescription>Apply defaults to datasets created under this project</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-sm">Safe Search</p>
                <p className="text-xs text-muted-foreground">Filter adult or explicit content</p>
              </div>
              <Switch checked={safeMode} onCheckedChange={setSafeMode} />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-sm">AI Keyword Expansion</p>
                <p className="text-xs text-muted-foreground">Automatically expand search terms</p>
              </div>
              <Switch checked={aiKeywordExpansion} onCheckedChange={setAiKeywordExpansion} />
            </div>
            <div className="space-y-2">
              <p className="font-medium text-sm">Validation Profile</p>
              <Select value={validationProfile} onValueChange={(v) => setValidationProfile(v as any)}>
                <SelectTrigger className="w-full"><SelectValue placeholder="Select" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="fast">Fast</SelectItem>
                  <SelectItem value="balanced">Balanced</SelectItem>
                  <SelectItem value="strict">Strict</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <p className="font-medium text-sm">Deduplication Level</p>
              <Select value={dedupLevel} onValueChange={(v) => setDedupLevel(v as any)}>
                <SelectTrigger className="w-full"><SelectValue placeholder="Select" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">None</SelectItem>
                  <SelectItem value="fast">Fast</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="aggressive">Aggressive</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        

        <Card id="section-download" className="bg-card/80 backdrop-blur-md">
          <CardHeader>
            <CardTitle>Download & Chunking</CardTitle>
            <CardDescription>Performance and reliability</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <p className="text-sm font-medium">Max Concurrency</p>
              <Slider value={[maxConcurrency]} min={1} max={16} step={1} onValueChange={(v) => setMaxConcurrency(v[0])} />
              <p className="text-xs text-muted-foreground">{maxConcurrency} workers</p>
            </div>
            <div className="space-y-2">
              <p className="text-sm font-medium">Chunk Size</p>
              <Slider value={[chunkSize]} min={25} max={500} step={25} onValueChange={(v) => setChunkSize(v[0])} />
              <p className="text-xs text-muted-foreground">{chunkSize} items</p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="retry-count">Retry Count</Label>
              <Input id="retry-count" type="number" value={retryCount} onChange={(e) => setRetryCount(parseInt(e.target.value || '0'))} />
            </div>
          </CardContent>
        </Card>

        <Card id="section-validation" className="bg-card/80 backdrop-blur-md">
          <CardHeader>
            <CardTitle>Validation & Formats</CardTitle>
            <CardDescription>Quality and accepted formats</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <p className="text-sm font-medium">Minimum Resolution</p>
              <Slider value={minResolution} min={128} max={2048} step={64} onValueChange={(v) => setMinResolution([v[0], v[1] || v[0]])} />
              <p className="text-xs text-muted-foreground">{minResolution[0]} × {minResolution[1]} px</p>
            </div>
            <div className="space-y-2">
              <p className="text-sm font-medium">Allowed Formats</p>
              <div className="flex items-center gap-6">
                <div className="flex items-center gap-2"><Checkbox checked={formats.jpg} onCheckedChange={(v) => setFormats(s => ({...s, jpg: !!v}))} /><span className="text-sm">JPG</span></div>
                <div className="flex items-center gap-2"><Checkbox checked={formats.png} onCheckedChange={(v) => setFormats(s => ({...s, png: !!v}))} /><span className="text-sm">PNG</span></div>
                <div className="flex items-center gap-2"><Checkbox checked={formats.webp} onCheckedChange={(v) => setFormats(s => ({...s, webp: !!v}))} /><span className="text-sm">WEBP</span></div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card id="section-storage" className="bg-card/80 backdrop-blur-md">
          <CardHeader>
            <CardTitle>Storage & Export</CardTitle>
            <CardDescription>Delivery options</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <p className="text-sm font-medium">Storage Tier</p>
              <Select value={storageTier} onValueChange={(v) => setStorageTier(v as any)}>
                <SelectTrigger className="w-full"><SelectValue placeholder="Select" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="hot">Hot</SelectItem>
                  <SelectItem value="warm">Warm</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <p className="text-sm font-medium">Compression</p>
              <Select value={exportFormat} onValueChange={(v) => setExportFormat(v as any)}>
                <SelectTrigger className="w-full"><SelectValue placeholder="Select" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="zip">ZIP</SelectItem>
                  <SelectItem value="7z">7z</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <p className="text-sm font-medium">Label Formats</p>
              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-center gap-2"><Checkbox checked={labelFormats.json} onCheckedChange={(v) => setLabelFormats(s => ({...s, json: !!v}))} /><span className="text-sm">JSON</span></div>
                <div className="flex items-center gap-2"><Checkbox checked={labelFormats.csv} onCheckedChange={(v) => setLabelFormats(s => ({...s, csv: !!v}))} /><span className="text-sm">CSV</span></div>
                <div className="flex items-center gap-2"><Checkbox checked={labelFormats.yolo} onCheckedChange={(v) => setLabelFormats(s => ({...s, yolo: !!v}))} /><span className="text-sm">YOLO</span></div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card id="section-danger" className="bg-card/80 backdrop-blur-md border-destructive/40">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-destructive">
              <AlertCircle className="w-5 h-5" />
              Danger Zone
            </CardTitle>
            <CardDescription>Irreversible actions. Proceed with caution.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid gap-3 sm:grid-cols-2">
              <Button variant="outline" leftIcon={<RefreshCw className="w-4 h-4" />} onClick={resetToDefaults}>
                Reset to Defaults
              </Button>
              <Button variant="outline" leftIcon={<Copy className="w-4 h-4" />} onClick={exportSettings}>
                Export Settings
              </Button>
              <Button variant="outline" leftIcon={<Archive className="w-4 h-4" />} onClick={() => toast({ title: 'Project archived', description: 'Project moved to archive' })}>
                Archive Project
              </Button>
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button variant="destructive" leftIcon={<Trash2 className="w-4 h-4" />}>
                    Delete Project
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Delete this project?</AlertDialogTitle>
                    <AlertDialogDescription>
                      This action cannot be undone. All datasets, jobs, and settings under this project will be permanently removed.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction onClick={() => {
                      toast({ title: 'Project deleted', description: `Project ${projectId} has been removed` })
                      router.push('/dashboard/projects')
                    }}>Delete</AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
