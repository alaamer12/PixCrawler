'use client'

import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Separator } from '@/components/ui/separator'
import { Input } from '@/components/ui/input'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Slider } from '@/components/ui/slider'
import { useToast } from '@/components/ui/use-toast'
import { useTheme } from 'next-themes'
import {
  Monitor,
  Moon,
  Sun,
  Globe,
  Clock,
  Palette,
  Type,
  Volume2,
  Keyboard,
  MousePointer,
  Zap,
  Eye,
  Download,
  Upload,
  HardDrive,
  Cpu,
  Wifi,
  Battery,
  Shield,
  Lock,
  Key,
  Fingerprint,
  Save,
  RotateCcw,
  Info,
  CheckCircle,
  AlertCircle,
  Terminal,
  Code,
  FileCode,
  Layers,
  Grid,
  List,
  LayoutGrid,
} from 'lucide-react'

interface SettingSection {
  title: string
  description: string
  icon: React.ElementType
  content: React.ReactNode
}

export function Settings() {
  const { theme, setTheme } = useTheme()
  const { toast } = useToast()
  const [isSaving, setIsSaving] = useState(false)

  // Localization
  const [language, setLanguage] = useState('en')
  const [timezone, setTimezone] = useState('America/Los_Angeles')
  const [dateFormat, setDateFormat] = useState('MM/DD/YYYY')
  const [timeFormat, setTimeFormat] = useState('12h')
  const [currency, setCurrency] = useState('USD')

  // Privacy & Security
  const [telemetry, setTelemetry] = useState(true)
  const [crashReports, setCrashReports] = useState(true)
  const [analytics, setAnalytics] = useState(true)
  const [sessionRecording, setSessionRecording] = useState(false)
  const [twoFactorAuth, setTwoFactorAuth] = useState(false)

  // Workspace
  const [defaultView, setDefaultView] = useState('grid')
  const [itemsPerPage, setItemsPerPage] = useState(20)
  const [showThumbnails, setShowThumbnails] = useState(true)
  const [autoExpandFolders, setAutoExpandFolders] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(true)

  const handleSave = async () => {
    setIsSaving(true)
    await new Promise(resolve => setTimeout(resolve, 1500))
    setIsSaving(false)
    
    toast({
      title: 'Settings saved',
      description: 'Your preferences have been updated successfully.',
    })
  }

  const handleReset = () => {
    toast({
      title: 'Settings reset',
      description: 'All settings have been restored to their default values.',
    })
  }

  const sections: SettingSection[] = [
    {
      title: 'Localization',
      description: 'Language, timezone, and regional preferences',
      icon: Globe,
      content: (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="language">Language</Label>
              <Select value={language} onValueChange={setLanguage}>
                <SelectTrigger id="language">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="en">English</SelectItem>
                  <SelectItem value="es">Español</SelectItem>
                  <SelectItem value="fr">Français</SelectItem>
                  <SelectItem value="de">Deutsch</SelectItem>
                  <SelectItem value="ja">日本語</SelectItem>
                  <SelectItem value="zh">中文</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="timezone">Timezone</Label>
              <Select value={timezone} onValueChange={setTimezone}>
                <SelectTrigger id="timezone">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="America/Los_Angeles">Pacific Time (PT)</SelectItem>
                  <SelectItem value="America/Denver">Mountain Time (MT)</SelectItem>
                  <SelectItem value="America/Chicago">Central Time (CT)</SelectItem>
                  <SelectItem value="America/New_York">Eastern Time (ET)</SelectItem>
                  <SelectItem value="Europe/London">London (GMT)</SelectItem>
                  <SelectItem value="Europe/Paris">Paris (CET)</SelectItem>
                  <SelectItem value="Asia/Tokyo">Tokyo (JST)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="date-format">Date Format</Label>
              <Select value={dateFormat} onValueChange={setDateFormat}>
                <SelectTrigger id="date-format">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="MM/DD/YYYY">MM/DD/YYYY</SelectItem>
                  <SelectItem value="DD/MM/YYYY">DD/MM/YYYY</SelectItem>
                  <SelectItem value="YYYY-MM-DD">YYYY-MM-DD</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="time-format">Time Format</Label>
              <Select value={timeFormat} onValueChange={setTimeFormat}>
                <SelectTrigger id="time-format">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="12h">12-hour (AM/PM)</SelectItem>
                  <SelectItem value="24h">24-hour</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="currency">Currency</Label>
              <Select value={currency} onValueChange={setCurrency}>
                <SelectTrigger id="currency">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="USD">USD ($)</SelectItem>
                  <SelectItem value="EUR">EUR (€)</SelectItem>
                  <SelectItem value="GBP">GBP (£)</SelectItem>
                  <SelectItem value="JPY">JPY (¥)</SelectItem>
                  <SelectItem value="CNY">CNY (¥)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>
      ),
    },
    {
      title: 'Workspace',
      description: 'Configure your default workspace preferences',
      icon: Grid,
      content: (
        <div className="space-y-6">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label htmlFor="items-per-page">Items per page</Label>
              <span className="text-sm text-muted-foreground">{itemsPerPage}</span>
            </div>
            <Slider
              id="items-per-page"
              min={10}
              max={100}
              step={10}
              value={[itemsPerPage]}
              onValueChange={(value) => setItemsPerPage(value[0])}
            />
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Show Thumbnails</Label>
                <p className="text-sm text-muted-foreground">Display image previews</p>
              </div>
              <Switch checked={showThumbnails} onCheckedChange={setShowThumbnails} />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Auto-expand Folders</Label>
                <p className="text-sm text-muted-foreground">Automatically open folders on click</p>
              </div>
              <Switch checked={autoExpandFolders} onCheckedChange={setAutoExpandFolders} />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Confirm Delete</Label>
                <p className="text-sm text-muted-foreground">Ask before deleting items</p>
              </div>
              <Switch checked={confirmDelete} onCheckedChange={setConfirmDelete} />
            </div>
          </div>
        </div>
      ),
    },
    {
      title: 'Privacy & Security',
      description: 'Control data collection and security settings',
      icon: Shield,
      content: (
        <div className="space-y-6">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Telemetry</Label>
                <p className="text-sm text-muted-foreground">Help improve the app with usage data</p>
              </div>
              <Switch checked={telemetry} onCheckedChange={setTelemetry} />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Crash Reports</Label>
                <p className="text-sm text-muted-foreground">Send crash reports to help fix issues</p>
              </div>
              <Switch checked={crashReports} onCheckedChange={setCrashReports} />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Analytics</Label>
                <p className="text-sm text-muted-foreground">Share anonymous usage statistics</p>
              </div>
              <Switch checked={analytics} onCheckedChange={setAnalytics} />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Session Recording</Label>
                <p className="text-sm text-muted-foreground">Record sessions for support purposes</p>
              </div>
              <Switch checked={sessionRecording} onCheckedChange={setSessionRecording} />
            </div>
          </div>

          <Separator />

          <div className="space-y-4">
            <h4 className="text-sm font-medium">Security</h4>
            
            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div className="flex items-center gap-3">
                <Key className="h-5 w-5 text-primary" />
                <div>
                  <p className="font-medium">Password</p>
                  <p className="text-sm text-muted-foreground">Last changed 30 days ago</p>
                </div>
              </div>
              <Button variant="outline" size="sm">
                Change
              </Button>
            </div>

            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div className="flex items-center gap-3">
                <Lock className="h-5 w-5 text-primary" />
                <div>
                  <p className="font-medium">Active Sessions</p>
                  <p className="text-sm text-muted-foreground">3 devices logged in</p>
                </div>
              </div>
              <Button variant="outline" size="sm">
                Manage
              </Button>
            </div>
          </div>
        </div>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
          <p className="text-muted-foreground">
            Manage your application preferences and configuration
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={handleReset}>
            <RotateCcw className="h-4 w-4 mr-2" />
            Reset to Defaults
          </Button>
          <Button onClick={handleSave} disabled={isSaving}>
            {isSaving ? (
              <>
                <div className="h-4 w-4 mr-2 animate-spin rounded-full border-2 border-current border-t-transparent" />
                Saving...
              </>
            ) : (
              <>
                <Save className="h-4 w-4 mr-2" />
                Save Changes
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Settings Sections */}
      {sections.map((section, index) => {
        const Icon = section.icon
        return (
          <Card key={index}>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="p-2 bg-primary/10 rounded-lg">
                  <Icon className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <CardTitle>{section.title}</CardTitle>
                  <CardDescription>{section.description}</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>{section.content}</CardContent>
          </Card>
        )
      })}

      {/* Info Banner */}
      <Card className="bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800">
        <CardContent className="pt-6">
          <div className="flex gap-3">
            <Info className="h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5" />
            <div className="space-y-1">
              <p className="text-sm font-medium text-blue-900 dark:text-blue-100">
                Settings are saved automatically
              </p>
              <p className="text-sm text-blue-800 dark:text-blue-200">
                Most changes take effect immediately. Some settings may require a page refresh.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
