'use client'

import { useState, useEffect, useMemo, useCallback, memo } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { BrandIcon } from '@/components/icons/brands'
import { Slider } from '@/components/ui/slider'
import { Switch } from '@/components/ui/switch'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'
import {
  ArrowLeft,
  Database,
  Search,
  Image as ImageIcon,
  Sparkles,
  Settings,
  Zap,
  CheckCircle2,
  Info,
  TrendingUp,
  Clock,
  HardDrive,
  AlertCircle,
  Settings2
} from 'lucide-react'
import Link from 'next/link'
import { validateDatasetForm, type DatasetFormData, type ValidationResult } from '@/lib/validation'

interface ImageSource {
  id: string
  name: string
  icon: typeof Search
  enabled: boolean
}

// Memoized source button component for performance
const SourceButton = memo(({ 
  source, 
  onToggle 
}: { 
  source: ImageSource
  onToggle: (id: string) => void 
}) => {
  return (
    <button
      onClick={() => onToggle(source.id)}
      className={`flex items-center gap-4 p-5 rounded-xl border transition-all ${
        source.enabled
          ? 'bg-primary/10 border-primary shadow-md'
          : 'bg-background/50 hover:bg-accent border-border'
      }`}
    >
      <BrandIcon name={source.id} className={`size-5 ${source.enabled ? '' : 'opacity-70'}`} />
      <span
        className={`font-medium ${
          source.enabled ? 'text-primary' : ''
        }`}
      >
        {source.name}
      </span>
      {source.enabled && (
        <CheckCircle2 className="w-4 h-4 text-primary ml-auto" />
      )}
    </button>
  )
})

SourceButton.displayName = 'SourceButton'

export default function NewDatasetPage() {
  const router = useRouter()
  const params = useParams()
  const projectId = params.projectId as string

  const [projectName, setProjectName] = useState('Loading...')
  const [datasetName, setDatasetName] = useState('')
  const [keywords, setKeywords] = useState('')
  const [imageCount, setImageCount] = useState(100)
  const [isEditingImageCount, setIsEditingImageCount] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [validation, setValidation] = useState<ValidationResult>({ valid: true, errors: {} })
  const [touched, setTouched] = useState({ name: false, keywords: false, sources: false })

  // Image sources
  const [sources, setSources] = useState<ImageSource[]>([
    { id: 'google', name: 'Google Images', icon: Search, enabled: true },
    { id: 'bing', name: 'Bing Images', icon: Search, enabled: false },
    { id: 'duckduckgo', name: 'DuckDuckGo', icon: Search, enabled: false },
    { id: 'unsplash', name: 'Unsplash', icon: ImageIcon, enabled: false },
    { id: 'pixabay', name: 'Pixabay', icon: ImageIcon, enabled: false },
  ])

  // Advanced settings
  const [aiExpansion, setAiExpansion] = useState(true)
  const [deduplicationLevel, setDeduplicationLevel] = useState('medium')
  const [minImageSize, setMinImageSize] = useState(512)
  const [imageFormat, setImageFormat] = useState('any')
  const [safeSearch, setSafeSearch] = useState(true)

  useEffect(() => {
    // TODO: Fetch project details
    // Simulate API call
    setTimeout(() => {
      setProjectName('Wildlife Conservation Dataset')
    }, 500)
  }, [projectId])

  const toggleSource = useCallback((sourceId: string) => {
    setSources(prev =>
      prev.map(source =>
        source.id === sourceId
          ? { ...source, enabled: !source.enabled }
          : source
      )
    )
    if (touched.sources) {
      validateForm()
    }
  }, [touched.sources])

  const validateForm = useCallback(() => {
    const result = validateDatasetForm({
      name: datasetName,
      keywords,
      imageCount,
      sources: sources.filter(s => s.enabled).map(s => s.id),
      aiExpansion,
      deduplicationLevel,
      minImageSize,
      imageFormat,
      safeSearch
    })
    setValidation(result)
    return result
  }, [datasetName, keywords, imageCount, sources, aiExpansion, deduplicationLevel, minImageSize, imageFormat, safeSearch])

  const handleNameChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setDatasetName(e.target.value)
    if (touched.name) {
      validateForm()
    }
  }, [touched.name, validateForm])

  const handleKeywordsChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setKeywords(e.target.value)
    if (touched.keywords) {
      validateForm()
    }
  }, [touched.keywords, validateForm])

  const handleBlur = useCallback((field: 'name' | 'keywords' | 'sources') => {
    setTouched(prev => ({ ...prev, [field]: true }))
    validateForm()
  }, [validateForm])

  const handleCreateDataset = async () => {
    if (!datasetName.trim() || !keywords.trim()) return

    setIsCreating(true)

    try {
      // TODO: Implement actual dataset creation API call
      // const response = await fetch(`/api/projects/${projectId}/datasets`, {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({
      //     name: datasetName,
      //     keywords: keywords.split(',').map(k => k.trim()),
      //     sources: sources.filter(s => s.enabled).map(s => s.id),
      //     imagesPerKeyword: imageCount,
      //     config: {
      //       aiExpansion,
      //       deduplicationLevel,
      //       minImageSize,
      //       imageFormat,
      //       safeSearch
      //     }
      //   })
      // })

      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000))

      // Redirect to dataset view or project view
      router.push(`/dashboard/projects/${projectId}`)
    } catch (error) {
      console.error('Failed to create dataset:', error)
      // TODO: Show error toast
    } finally {
      setIsCreating(false)
    }
  }

  // Memoized calculations for performance
  const selectedSourcesCount = useMemo(() => sources.filter(s => s.enabled).length, [sources])
  const keywordCount = useMemo(() => keywords.split(',').filter(k => k.trim()).length, [keywords])
  const estimatedImages = useMemo(() => imageCount * keywordCount * selectedSourcesCount, [imageCount, keywordCount, selectedSourcesCount])

  const isFormValid = useMemo(() =>
    datasetName.trim().length > 0 &&
    keywords.trim().length > 0 &&
    selectedSourcesCount > 0,
    [datasetName, keywords, selectedSourcesCount]
  )

  const estimatedTime = useMemo(() => ({
    min: Math.ceil(estimatedImages / 100),
    max: Math.ceil(estimatedImages / 50)
  }), [estimatedImages])

  return (
    <div className="space-y-8 mx-6 py-10">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="sm" asChild>
              <Link href={`/dashboard/projects/${projectId}`}>
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Project
              </Link>
            </Button>
          </div>
          <h1 className="text-4xl font-bold mt-12 tracking-tight bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
            Create New Dataset
          </h1>
          <p className="text-base text-muted-foreground">
            Project: <span className="font-medium">{projectName}</span>
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-primary" />
          <span className="text-sm text-muted-foreground">AI-Powered</span>
        </div>
      </div>

      {/* Validation Warnings */}
      {validation.warnings?.general && (
        <div className="rounded-lg border border-yellow-500/20 bg-yellow-500/5 p-4">
          <div className="flex gap-3">
            <AlertCircle className="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" />
            <div className="space-y-1">
              <p className="text-sm font-medium text-yellow-600">Configuration Warning</p>
              <p className="text-xs text-muted-foreground">
                {validation.warnings.general}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Main Form */}
      <div className="grid gap-8 lg:grid-cols-3">
        {/* Left Column - Form */}
        <div className="lg:col-span-2 space-y-6">
          {/* Dataset Details */}
          <Card className="bg-card/80 backdrop-blur-md border-border/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="w-5 h-5" />
                Dataset Details
              </CardTitle>
              <CardDescription>
                Define your dataset name and search keywords for image collection
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="dataset-name">
                  Dataset Name <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="dataset-name"
                  type="text"
                  value={datasetName}
                  onChange={handleNameChange}
                  onBlur={() => handleBlur('name')}
                  placeholder="e.g., African Wildlife - Lions and Elephants"
                  className={`bg-background/50 ${validation.errors.name && touched.name ? 'border-destructive' : ''}`}
                  maxLength={100}
                />
                {validation.errors.name && touched.name && (
                  <p className="text-xs text-destructive flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" />
                    {validation.errors.name}
                  </p>
                )}
                {validation.warnings?.name && !validation.errors.name && touched.name && (
                  <p className="text-xs text-yellow-600 flex items-center gap-1">
                    <Info className="w-3 h-3" />
                    {validation.warnings.name}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="keywords">
                  Search Keywords <span className="text-destructive">*</span>
                </Label>
                <Textarea
                  id="keywords"
                  value={keywords}
                  onChange={handleKeywordsChange}
                  onBlur={() => handleBlur('keywords')}
                  placeholder="Enter keywords separated by commas (e.g., african lion, elephant herd, safari wildlife)"
                  rows={4}
                  className={`bg-background/50 resize-none ${validation.errors.keywords && touched.keywords ? 'border-destructive' : ''}`}
                />
                {validation.errors.keywords && touched.keywords && (
                  <p className="text-xs text-destructive flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" />
                    {validation.errors.keywords}
                  </p>
                )}
                {validation.warnings?.keywords && !validation.errors.keywords && touched.keywords && (
                  <p className="text-xs text-yellow-600 flex items-center gap-1">
                    <Info className="w-3 h-3" />
                    {validation.warnings.keywords}
                  </p>
                )}
                {!validation.errors.keywords && !validation.warnings?.keywords && (
                  <p className="text-xs text-muted-foreground">
                    {aiExpansion && '✨ AI will automatically expand and optimize your keywords'}
                    {!aiExpansion && `${keywordCount} keyword${keywordCount !== 1 ? 's' : ''} entered`}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <Label>Images per Keyword</Label>
                  {isEditingImageCount ? (
                    <div className="flex items-center gap-2">
                      <Input
                        type="number"
                        value={imageCount}
                        onChange={(e) => {
                          const v = parseInt(e.target.value || '0', 10)
                          const clamped = Math.min(500, Math.max(10, isNaN(v) ? 10 : v))
                          const normalized = Math.round(clamped / 10) * 10
                          setImageCount(normalized)
                        }}
                        onBlur={() => setIsEditingImageCount(false)}
                        onKeyDown={(e) => { if (e.key === 'Enter') setIsEditingImageCount(false) }}
                        className="w-24 h-8"
                      />
                      <span className="text-xs text-muted-foreground">Enter 10–500</span>
                    </div>
                  ) : (
                    <span
                      className="text-sm font-semibold text-primary cursor-pointer select-none"
                      onDoubleClick={() => setIsEditingImageCount(true)}
                      title="Double-click to type a value"
                    >
                      {imageCount} images
                    </span>
                  )}
                </div>
                <Slider
                  value={[imageCount]}
                  onValueChange={(value) => setImageCount(value[0])}
                  min={10}
                  max={500}
                  step={10}
                  className="py-4"
                />
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>10</span>
                  <span>500</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Image Sources section removed */}

          {/* Advanced Configuration */}
          <Card className="bg-card/80 backdrop-blur-md border-border/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings2 className="w-5 h-5" />
                Advanced Configuration
              </CardTitle>
              <CardDescription>
                Fine-tune your dataset creation settings for optimal results
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Accordion type="single" collapsible className="w-full">
                <AccordionItem value="ai-settings">
                  <AccordionTrigger>AI & Processing</AccordionTrigger>
                  <AccordionContent className="space-y-4 pt-4">
                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label>AI Keyword Expansion</Label>
                        <p className="text-xs text-muted-foreground">
                          Automatically generate related keywords
                        </p>
                      </div>
                      <Switch
                        checked={aiExpansion}
                        onCheckedChange={setAiExpansion}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label>Deduplication Level</Label>
                      <Select
                        value={deduplicationLevel}
                        onValueChange={setDeduplicationLevel}
                      >
                        <SelectTrigger className="bg-background/50">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="low">Low - Keep similar images</SelectItem>
                          <SelectItem value="medium">Medium - Balanced</SelectItem>
                          <SelectItem value="high">High - Strict filtering</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </AccordionContent>
                </AccordionItem>

                <AccordionItem value="quality-settings">
                  <AccordionTrigger>Quality Filters</AccordionTrigger>
                  <AccordionContent className="space-y-4 pt-4">
                    <div className="space-y-2">
                      <div className="flex justify-between items-center">
                        <Label>Minimum Image Size</Label>
                        <span className="text-sm font-medium">{minImageSize}px</span>
                      </div>
                      <Slider
                        value={[minImageSize]}
                        onValueChange={(value) => setMinImageSize(value[0])}
                        min={256}
                        max={2048}
                        step={128}
                        className="py-4"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label>Image Format</Label>
                      <Select value={imageFormat} onValueChange={setImageFormat}>
                        <SelectTrigger className="bg-background/50">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="any">Any Format</SelectItem>
                          <SelectItem value="jpg">JPEG Only</SelectItem>
                          <SelectItem value="png">PNG Only</SelectItem>
                          <SelectItem value="webp">WebP Only</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label>Safe Search</Label>
                        <p className="text-xs text-muted-foreground">
                          Filter inappropriate content
                        </p>
                      </div>
                      <Switch checked={safeSearch} onCheckedChange={setSafeSearch} />
                    </div>
                  </AccordionContent>
                </AccordionItem>
              </Accordion>
            </CardContent>
          </Card>
        </div>

        {/* Right Column - Summary & Actions */}
        <div className="space-y-6">
          {/* Configuration Summary */}
          <Card className="bg-card/80 backdrop-blur-md border-border/50">
            <CardHeader>
              <CardTitle className="text-lg">Configuration</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex justify-between items-center py-2 border-b border-border/50">
                <span className="text-sm text-muted-foreground">Dataset Name</span>
                <span className="text-sm font-medium text-right max-w-[150px] truncate">
                  {datasetName || <span className="text-muted-foreground">Not set</span>}
                </span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-border/50">
                <span className="text-sm text-muted-foreground">Keywords</span>
                <Badge variant="outline">{keywordCount} keywords</Badge>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-border/50">
                <span className="text-sm text-muted-foreground">Sources</span>
                <div className="flex items-center gap-2">
                  <TooltipProvider>
                    {sources.filter(s => s.enabled).map(s => (
                      <Tooltip key={s.id}>
                        <TooltipTrigger asChild>
                          <span className="inline-flex items-center justify-center rounded-md border px-2 py-1 bg-background/60">
                            <BrandIcon name={s.id} className="size-4" />
                          </span>
                        </TooltipTrigger>
                        <TooltipContent className="px-2 py-1 bg-card border border-border/50 text-foreground rounded-md shadow-md">
                          <p className="text-xs">{s.name}</p>
                        </TooltipContent>
                      </Tooltip>
                    ))}
                  </TooltipProvider>
                </div>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-border/50">
                <span className="text-sm text-muted-foreground">Per Keyword</span>
                <span className="text-sm font-medium">{imageCount} images</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-border/50">
                <span className="text-sm text-muted-foreground">Validation</span>
                {validation.valid ? (
                  <CheckCircle2 className="w-4 h-4 text-green-500" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-red-500" />
                )}
              </div>
              {/* Est. Total row removed */}
            </CardContent>
          </Card>

          {/* Features */}
          <Card className="bg-gradient-to-br from-primary/10 to-purple-500/10 border-primary/20 backdrop-blur-md">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-primary">
                <Zap className="w-5 h-5" />
                What You Get
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm">
                <li className="flex items-start gap-2">
                  <span className="text-primary mt-0.5">✓</span>
                  <span>AI-powered keyword expansion</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary mt-0.5">✓</span>
                  <span>Automatic deduplication</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary mt-0.5">✓</span>
                  <span>Quality validation & filtering</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary mt-0.5">✓</span>
                  <span>ML-ready label formats</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary mt-0.5">✓</span>
                  <span>Organized folder structure</span>
                </li>
              </ul>
            </CardContent>
          </Card>

          {/* Enhanced Info Cards */}
          <div className="space-y-3">
            {/* Processing Time card removed */}
            <div className="rounded-lg border border-green-500/20 bg-green-500/5 p-4">
              <div className="flex gap-3">
                <HardDrive className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <p className="text-sm font-medium text-green-500">Storage Impact</p>
                  <p className="text-xs text-muted-foreground">
                    ~{(estimatedImages * 0.5).toFixed(1)} MB estimated
                  </p>
                </div>
              </div>
            </div>

            <div className="rounded-lg border border-purple-500/20 bg-purple-500/5 p-4">
              <div className="flex gap-3">
                <TrendingUp className="w-5 h-5 text-purple-500 flex-shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <p className="text-sm font-medium text-purple-500">Quality Score</p>
                  <p className="text-xs text-muted-foreground">
                    {deduplicationLevel === 'high' ? 'Excellent' : deduplicationLevel === 'medium' ? 'Good' : 'Standard'} filtering applied
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="space-y-3">
            <Button
              onClick={handleCreateDataset}
              disabled={!isFormValid || isCreating}
              loading={isCreating}
              loadingText="Creating Dataset..."
              className="w-full"
              size="lg"
              leftIcon={<Database className="w-4 h-4" />}
            >
              Create Dataset
            </Button>
            <Button
              variant="outline"
              onClick={() => router.push(`/dashboard/projects/${projectId}`)}
              className="w-full"
              disabled={isCreating}
            >
              Cancel
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
