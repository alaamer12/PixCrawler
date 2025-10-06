'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Separator } from '@/components/ui/separator'

interface Dataset {
  id: string
  name: string
  status: 'processing' | 'complete' | 'failed' | 'paused'
  totalImages: number
  categories: number
  qualityScore: number
  totalSize: string
}

interface DatasetSettingsProps {
  dataset: Dataset
}

export function DatasetSettings({ dataset }: DatasetSettingsProps) {
  const [settings, setSettings] = useState({
    name: dataset.name,
    description: '',
    storageTier: 'hot',
    autoArchiveDays: 30,
    exportFormat: 'zip',
    includeMetadata: true,
    enableNotifications: true,
    publicAccess: false,
    downloadExpiry: 7,
  })

  const handleSave = () => {
    // Handle save logic here
    console.log('Saving settings:', settings)
  }

  return (
    <div className="p-6 space-y-6 overflow-y-auto bg-muted/30">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Dataset Settings</h2>
        <Button onClick={handleSave}>Save Changes</Button>
      </div>

      {/* General Information */}
      <Card>
        <CardHeader>
          <CardTitle>General Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="dataset-name">Dataset Name</Label>
            <Input
              id="dataset-name"
              value={settings.name}
              onChange={(e) => setSettings({ ...settings, name: e.target.value })}
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="dataset-description">Description</Label>
            <Textarea
              id="dataset-description"
              placeholder="Add a description for this dataset..."
              value={settings.description}
              onChange={(e) => setSettings({ ...settings, description: e.target.value })}
              rows={3}
            />
          </div>
        </CardContent>
      </Card>

      {/* Storage Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Storage Settings</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="storage-tier">Storage Tier</Label>
            <Select
              value={settings.storageTier}
              onValueChange={(value) => setSettings({ ...settings, storageTier: value })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="hot">Hot Storage (Immediate Access)</SelectItem>
                <SelectItem value="warm">Warm Storage (Cost-Optimized)</SelectItem>
                <SelectItem value="cold">Cold Storage (Archive)</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-sm text-muted-foreground">
              Current tier affects access speed and cost
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="auto-archive">Auto-Archive After</Label>
            <div className="flex items-center gap-2">
              <Input
                id="auto-archive"
                type="number"
                value={settings.autoArchiveDays}
                onChange={(e) => setSettings({ ...settings, autoArchiveDays: parseInt(e.target.value) })}
                className="w-24"
              />
              <span className="text-sm text-muted-foreground">days</span>
            </div>
            <p className="text-sm text-muted-foreground">
              Automatically move to warm storage after specified days
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Export Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Export Settings</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="export-format">Default Export Format</Label>
            <Select
              value={settings.exportFormat}
              onValueChange={(value) => setSettings({ ...settings, exportFormat: value })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="zip">ZIP (Standard)</SelectItem>
                <SelectItem value="7z">7z (Ultra-Compressed)</SelectItem>
                <SelectItem value="tar">TAR.GZ (Unix)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Include Metadata Files</Label>
              <p className="text-sm text-muted-foreground">
                Include manifest.json, labels.txt, and metadata.csv in exports
              </p>
            </div>
            <Switch
              checked={settings.includeMetadata}
              onCheckedChange={(checked) => setSettings({ ...settings, includeMetadata: checked })}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="download-expiry">Download Link Expiry</Label>
            <div className="flex items-center gap-2">
              <Input
                id="download-expiry"
                type="number"
                value={settings.downloadExpiry}
                onChange={(e) => setSettings({ ...settings, downloadExpiry: parseInt(e.target.value) })}
                className="w-24"
              />
              <span className="text-sm text-muted-foreground">days</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Access & Sharing */}
      <Card>
        <CardHeader>
          <CardTitle>Access & Sharing</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Public Access</Label>
              <p className="text-sm text-muted-foreground">
                Allow anyone with the link to view and download this dataset
              </p>
            </div>
            <Switch
              checked={settings.publicAccess}
              onCheckedChange={(checked) => setSettings({ ...settings, publicAccess: checked })}
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Email Notifications</Label>
              <p className="text-sm text-muted-foreground">
                Receive notifications about dataset processing and updates
              </p>
            </div>
            <Switch
              checked={settings.enableNotifications}
              onCheckedChange={(checked) => setSettings({ ...settings, enableNotifications: checked })}
            />
          </div>
        </CardContent>
      </Card>

      {/* Danger Zone */}
      <Card className="border-destructive">
        <CardHeader>
          <CardTitle className="text-destructive">Danger Zone</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between p-4 border border-destructive/20 rounded-lg">
            <div>
              <h4 className="font-medium">Delete Dataset</h4>
              <p className="text-sm text-muted-foreground">
                Permanently delete this dataset and all associated files. This action cannot be undone.
              </p>
            </div>
            <Button variant="destructive">Delete Dataset</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}