'use client'

import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Separator } from '@/components/ui/separator'
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
  Globe,
  Grid,
  Shield,
  Key,
  Lock,
  Save,
  RotateCcw,
  Info,
} from 'lucide-react'


interface SettingsSelectProps {
  id: string
  label: string
  description?: string
  value: string
  onValueChange: (value: string) => void
  options: { value: string; label: string }[]
}

const SettingsSelect = ({ id, label, description, value, onValueChange, options }: SettingsSelectProps) => (
  <div className="flex items-center justify-between py-4 first:pt-0 last:pb-0">
    <div className="space-y-0.5">
      <Label htmlFor={id} className="text-base font-medium">{label}</Label>
      {description && <p className="text-sm text-muted-foreground">{description}</p>}
    </div>
    <Select value={value} onValueChange={onValueChange}>
      <SelectTrigger id={id} className="w-[200px]">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {options.map((option) => (
          <SelectItem key={option.value} value={option.value}>
            {option.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  </div>
)

interface SettingsSwitchProps {
  label: string
  description: string
  checked: boolean
  onCheckedChange: (checked: boolean) => void
}

const SettingsSwitch = ({ label, description, checked, onCheckedChange }: SettingsSwitchProps) => (
  <div className="flex items-center justify-between py-4 first:pt-0 last:pb-0">
    <div className="space-y-0.5">
      <Label className="text-base font-medium">{label}</Label>
      <p className="text-sm text-muted-foreground">{description}</p>
    </div>
    <Switch checked={checked} onCheckedChange={onCheckedChange} />
  </div>
)

// --- Section Components ---

interface LocalizationSettingsProps {
  language: string
  setLanguage: (v: string) => void
  timezone: string
  setTimezone: (v: string) => void
  dateFormat: string
  setDateFormat: (v: string) => void
  timeFormat: string
  setTimeFormat: (v: string) => void
  currency: string
  setCurrency: (v: string) => void
}

const LocalizationSettings = ({
  language,
  setLanguage,
  timezone,
  setTimezone,
  dateFormat,
  setDateFormat,
  timeFormat,
  setTimeFormat,
  currency,
  setCurrency,
}: LocalizationSettingsProps) => (
  <div className="divide-y">
    <SettingsSelect
      id="language"
      label="Language"
      description="Select your preferred language"
      value={language}
      onValueChange={setLanguage}
      options={[
        { value: 'en', label: 'English' },
        { value: 'es', label: 'Español' },
        { value: 'fr', label: 'Français' },
        { value: 'de', label: 'Deutsch' },
        { value: 'ja', label: '日本語' },
        { value: 'zh', label: '中文' },
      ]}
    />
    <SettingsSelect
      id="timezone"
      label="Timezone"
      description="Set your local timezone"
      value={timezone}
      onValueChange={setTimezone}
      options={[
        { value: 'America/Los_Angeles', label: 'Pacific Time (PT)' },
        { value: 'America/Denver', label: 'Mountain Time (MT)' },
        { value: 'America/Chicago', label: 'Central Time (CT)' },
        { value: 'America/New_York', label: 'Eastern Time (ET)' },
        { value: 'Europe/London', label: 'London (GMT)' },
        { value: 'Europe/Paris', label: 'Paris (CET)' },
        { value: 'Asia/Tokyo', label: 'Tokyo (JST)' },
      ]}
    />
    <SettingsSelect
      id="date-format"
      label="Date Format"
      description="Choose how dates are displayed"
      value={dateFormat}
      onValueChange={setDateFormat}
      options={[
        { value: 'MM/DD/YYYY', label: 'MM/DD/YYYY' },
        { value: 'DD/MM/YYYY', label: 'DD/MM/YYYY' },
        { value: 'YYYY-MM-DD', label: 'YYYY-MM-DD' },
      ]}
    />
    <SettingsSelect
      id="time-format"
      label="Time Format"
      description="Choose 12-hour or 24-hour format"
      value={timeFormat}
      onValueChange={setTimeFormat}
      options={[
        { value: '12h', label: '12-hour (AM/PM)' },
        { value: '24h', label: '24-hour' },
      ]}
    />
    <SettingsSelect
      id="currency"
      label="Currency"
      description="Select your preferred currency"
      value={currency}
      onValueChange={setCurrency}
      options={[
        { value: 'USD', label: 'USD ($)' },
        { value: 'EUR', label: 'EUR (€)' },
        { value: 'GBP', label: 'GBP (£)' },
        { value: 'JPY', label: 'JPY (¥)' },
        { value: 'CNY', label: 'CNY (¥)' },
      ]}
    />
  </div>
)

interface WorkspaceSettingsProps {
  itemsPerPage: number
  setItemsPerPage: (v: number) => void
  showThumbnails: boolean
  setShowThumbnails: (v: boolean) => void
  autoExpandFolders: boolean
  setAutoExpandFolders: (v: boolean) => void
  confirmDelete: boolean
  setConfirmDelete: (v: boolean) => void
}

const WorkspaceSettings = ({
  itemsPerPage,
  setItemsPerPage,
  showThumbnails,
  setShowThumbnails,
  autoExpandFolders,
  setAutoExpandFolders,
  confirmDelete,
  setConfirmDelete,
}: WorkspaceSettingsProps) => (
  <div className="divide-y">
    <div className="flex items-center justify-between py-4 first:pt-0 last:pb-0">
      <div className="space-y-0.5">
        <Label htmlFor="items-per-page" className="text-base font-medium">Items per page</Label>
        <p className="text-sm text-muted-foreground">Number of items to show in lists</p>
      </div>
      <div className="flex items-center gap-4 w-[200px]">
        <Slider
          id="items-per-page"
          min={10}
          max={100}
          step={10}
          value={[itemsPerPage]}
          onValueChange={(value) => setItemsPerPage(value[0])}
          className="flex-1"
        />
        <span className="text-sm font-medium w-8 text-right">{itemsPerPage}</span>
      </div>
    </div>

    <SettingsSwitch
      label="Show Thumbnails"
      description="Display image previews in lists"
      checked={showThumbnails}
      onCheckedChange={setShowThumbnails}
    />
    <SettingsSwitch
      label="Auto-expand Folders"
      description="Automatically open folders on click"
      checked={autoExpandFolders}
      onCheckedChange={setAutoExpandFolders}
    />
    <SettingsSwitch
      label="Confirm Delete"
      description="Ask for confirmation before deleting items"
      checked={confirmDelete}
      onCheckedChange={setConfirmDelete}
    />
  </div>
)

interface PrivacySecuritySettingsProps {
  telemetry: boolean
  setTelemetry: (v: boolean) => void
  crashReports: boolean
  setCrashReports: (v: boolean) => void
  analytics: boolean
  setAnalytics: (v: boolean) => void
  sessionRecording: boolean
  setSessionRecording: (v: boolean) => void
}

const PrivacySecuritySettings = ({
  telemetry,
  setTelemetry,
  crashReports,
  setCrashReports,
  analytics,
  setAnalytics,
  sessionRecording,
  setSessionRecording,
}: PrivacySecuritySettingsProps) => (
  <div className="space-y-6">
    <div className="divide-y">
      <SettingsSwitch
        label="Telemetry"
        description="Help improve the app with usage data"
        checked={telemetry}
        onCheckedChange={setTelemetry}
      />
      <SettingsSwitch
        label="Crash Reports"
        description="Send crash reports to help fix issues"
        checked={crashReports}
        onCheckedChange={setCrashReports}
      />
      <SettingsSwitch
        label="Analytics"
        description="Share anonymous usage statistics"
        checked={analytics}
        onCheckedChange={setAnalytics}
      />
      <SettingsSwitch
        label="Session Recording"
        description="Record sessions for support purposes"
        checked={sessionRecording}
        onCheckedChange={setSessionRecording}
      />
    </div>

    <Separator />

    <div className="space-y-4">
      <h4 className="text-sm font-medium">Security</h4>

      <div className="flex items-center justify-between p-4 border rounded-lg bg-muted/20">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary/10 rounded-full">
            <Key className="h-4 w-4 text-primary" />
          </div>
          <div>
            <p className="font-medium">Password</p>
            <p className="text-sm text-muted-foreground">Last changed 30 days ago</p>
          </div>
        </div>
        <Button variant="outline" size="sm">
          Change
        </Button>
      </div>

      <div className="flex items-center justify-between p-4 border rounded-lg bg-muted/20">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary/10 rounded-full">
            <Lock className="h-4 w-4 text-primary" />
          </div>
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
)

// --- Main Component ---

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
        <LocalizationSettings
          language={language}
          setLanguage={setLanguage}
          timezone={timezone}
          setTimezone={setTimezone}
          dateFormat={dateFormat}
          setDateFormat={setDateFormat}
          timeFormat={timeFormat}
          setTimeFormat={setTimeFormat}
          currency={currency}
          setCurrency={setCurrency}
        />
      ),
    },
    {
      title: 'Workspace',
      description: 'Configure your default workspace preferences',
      icon: Grid,
      content: (
        <WorkspaceSettings
          itemsPerPage={itemsPerPage}
          setItemsPerPage={setItemsPerPage}
          showThumbnails={showThumbnails}
          setShowThumbnails={setShowThumbnails}
          autoExpandFolders={autoExpandFolders}
          setAutoExpandFolders={setAutoExpandFolders}
          confirmDelete={confirmDelete}
          setConfirmDelete={setConfirmDelete}
        />
      ),
    },
    {
      title: 'Privacy & Security',
      description: 'Control data collection and security settings',
      icon: Shield,
      content: (
        <PrivacySecuritySettings
          telemetry={telemetry}
          setTelemetry={setTelemetry}
          crashReports={crashReports}
          setCrashReports={setCrashReports}
          analytics={analytics}
          setAnalytics={setAnalytics}
          sessionRecording={sessionRecording}
          setSessionRecording={setSessionRecording}
        />
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
