'use client'

import React, {useState} from 'react'
import {Button} from '@/components/ui/button'
import {Card, CardContent, CardDescription, CardHeader, CardTitle} from '@/components/ui/card'
import {Badge} from '@/components/ui/badge'
import {Input} from '@/components/ui/input'
import {Label} from '@/components/ui/label'
import {Switch} from '@/components/ui/switch'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
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
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {useToast} from '@/components/ui/use-toast'
import {
  Key,
  Plus,
  Copy,
  Eye,
  EyeOff,
  MoreVertical,
  Shield,
  Clock,
  Activity,
  AlertCircle,
  CheckCircle,
  XCircle,
  Info,
  Calendar,
  Globe,
  Lock,
  Unlock,
  RefreshCw,
  Trash2,
  Edit,
  Download,
  Upload,
  Code,
  Terminal,
  Zap,
  Database,
} from 'lucide-react'
import {Progress} from '@/components/ui/progress'

interface ApiKey {
  id: string
  name: string
  key: string
  created: string
  lastUsed: string
  status: 'active' | 'inactive' | 'expired'
  permissions: string[]
  rateLimit: number
  usage: number
  expiresAt?: string
}

interface Permission {
  id: string
  name: string
  description: string
  category: string
}

export function ApiKeys() {
  const {toast} = useToast()
  const [showKey, setShowKey] = useState<string | null>(null)
  const [isCreating, setIsCreating] = useState(false)
  const [newKeyName, setNewKeyName] = useState('')
  const [newKeyExpiry, setNewKeyExpiry] = useState('never')
  const [selectedPermissions, setSelectedPermissions] = useState<string[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [editingKey, setEditingKey] = useState<ApiKey | null>(null)
  const [editPermissions, setEditPermissions] = useState<string[]>([])
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)

  const [apiKeys, setApiKeys] = useState<ApiKey[]>([
    {
      id: 'key_1',
      name: 'Production API',
      key: 'pk_live_51234567890abcdefghijklmnop',
      created: '2024-01-15',
      lastUsed: '2024-10-30',
      status: 'active',
      permissions: ['read:images', 'write:images', 'read:datasets', 'write:datasets'],
      rateLimit: 1000,
      usage: 523,
    },
    {
      id: 'key_2',
      name: 'Development API',
      key: 'pk_test_98765432109876543210987654',
      created: '2024-03-20',
      lastUsed: '2024-10-29',
      status: 'active',
      permissions: ['read:images', 'read:datasets'],
      rateLimit: 100,
      usage: 89,
    },
    {
      id: 'key_3',
      name: 'Mobile App',
      key: 'pk_mobile_abcdefghijklmnopqrstuvwx',
      created: '2024-06-10',
      lastUsed: '2024-09-15',
      status: 'inactive',
      permissions: ['read:images'],
      rateLimit: 500,
      usage: 0,
      expiresAt: '2024-12-31',
    },
  ])

  const permissions: Permission[] = [
    // Images
    {id: 'read:images', name: 'Read Images', description: 'View and download images', category: 'Images'},
    {id: 'write:images', name: 'Write Images', description: 'Upload and modify images', category: 'Images'},
    {id: 'delete:images', name: 'Delete Images', description: 'Remove images', category: 'Images'},

    // Datasets
    {id: 'read:datasets', name: 'Read Datasets', description: 'View dataset information', category: 'Datasets'},
    {id: 'write:datasets', name: 'Write Datasets', description: 'Create and modify datasets', category: 'Datasets'},
    {id: 'delete:datasets', name: 'Delete Datasets', description: 'Remove datasets', category: 'Datasets'},

    // Crawl Jobs
    {id: 'read:jobs', name: 'Read Jobs', description: 'View crawl job status', category: 'Crawl Jobs'},
    {id: 'write:jobs', name: 'Write Jobs', description: 'Create and manage crawl jobs', category: 'Crawl Jobs'},
    {id: 'delete:jobs', name: 'Delete Jobs', description: 'Cancel and remove jobs', category: 'Crawl Jobs'},

    // Analytics
    {id: 'read:analytics', name: 'Read Analytics', description: 'View usage analytics', category: 'Analytics'},

    // Admin
    {id: 'admin:all', name: 'Admin Access', description: 'Full administrative access', category: 'Admin'},
  ]

  const handleCreateKey = async () => {
    if (!newKeyName) {
      toast({
        title: 'Error',
        description: 'Please enter a name for the API key',
        variant: 'destructive',
      })
      return
    }

    setIsCreating(true)
    await new Promise(resolve => setTimeout(resolve, 1500))

    const newKey: ApiKey = {
      id: `key_${Date.now()}`,
      name: newKeyName,
      key: `pk_${Math.random().toString(36).substring(2, 15)}${Math.random().toString(36).substring(2, 15)}`,
      created: new Date().toISOString().split('T')[0],
      lastUsed: 'Never',
      status: 'active',
      permissions: selectedPermissions,
      rateLimit: 1000,
      usage: 0,
      expiresAt: newKeyExpiry !== 'never' ? new Date(Date.now() + parseInt(newKeyExpiry) * 24 * 60 * 60 * 1000).toISOString().split('T')[0] : undefined,
    }

    setApiKeys([...apiKeys, newKey])
    setIsCreating(false)
    setNewKeyName('')
    setSelectedPermissions([])
    setNewKeyExpiry('never')

    toast({
      title: 'API key created',
      description: 'Your new API key has been generated successfully.',
    })
  }

  const handleCopyKey = (key: string) => {
    navigator.clipboard.writeText(key)
    toast({
      title: 'Copied to clipboard',
      description: 'API key has been copied to your clipboard.',
    })
  }

  const handleToggleKey = (keyId: string) => {
    setApiKeys(prev =>
      prev.map(key =>
        key.id === keyId
          ? {...key, status: key.status === 'active' ? 'inactive' : 'active'}
          : key
      )
    )

    toast({
      title: 'API key updated',
      description: 'The API key status has been changed.',
    })
  }

  const handleDeleteKey = (keyId: string) => {
    setApiKeys(prev => prev.filter(key => key.id !== keyId))

    toast({
      title: 'API key deleted',
      description: 'The API key has been permanently removed.',
    })
  }

  const handleRegenerateKey = (keyId: string) => {
    setApiKeys(prev =>
      prev.map(key =>
        key.id === keyId
          ? {
            ...key,
            key: `pk_${Math.random().toString(36).substring(2, 15)}${Math.random().toString(36).substring(2, 15)}`
          }
          : key
      )
    )

    toast({
      title: 'API key regenerated',
      description: 'A new API key has been generated.',
    })
  }

  const handleOpenEditPermissions = (apiKey: ApiKey) => {
    setEditingKey(apiKey)
    setEditPermissions([...apiKey.permissions])
    setIsEditDialogOpen(true)
  }

  const handleSavePermissions = () => {
    if (!editingKey) return

    setApiKeys(prev =>
      prev.map(key =>
        key.id === editingKey.id
          ? {...key, permissions: editPermissions}
          : key
      )
    )

    toast({
      title: 'Permissions updated',
      description: `Permissions for "${editingKey.name}" have been updated.`,
    })

    setIsEditDialogOpen(false)
    setEditingKey(null)
    setEditPermissions([])
  }

  const toggleEditPermission = (permissionId: string) => {
    setEditPermissions(prev =>
      prev.includes(permissionId)
        ? prev.filter(p => p !== permissionId)
        : [...prev, permissionId]
    )
  }

  const filteredKeys = apiKeys.filter(key =>
    key.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const groupedPermissions = permissions.reduce((acc, perm) => {
    if (!acc[perm.category]) acc[perm.category] = []
    acc[perm.category].push(perm)
    return acc
  }, {} as Record<string, Permission[]>)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">API Keys</h1>
          <p className="text-muted-foreground">
            Manage API access tokens for your applications
          </p>
        </div>
        <Dialog>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2"/>
              Create API Key
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Create New API Key</DialogTitle>
              <DialogDescription>
                Generate a new API key with specific permissions
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="key-name">Key Name</Label>
                <Input
                  id="key-name"
                  placeholder="e.g., Production API"
                  value={newKeyName}
                  onChange={(e) => setNewKeyName(e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="expiry">Expiration</Label>
                <Select value={newKeyExpiry} onValueChange={setNewKeyExpiry}>
                  <SelectTrigger id="expiry">
                    <SelectValue/>
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="never">Never expires</SelectItem>
                    <SelectItem value="30">30 days</SelectItem>
                    <SelectItem value="60">60 days</SelectItem>
                    <SelectItem value="90">90 days</SelectItem>
                    <SelectItem value="365">1 year</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Permissions</Label>
                <div className="border rounded-lg p-4 space-y-4 max-h-[300px] overflow-y-auto">
                  {Object.entries(groupedPermissions).map(([category, perms]) => (
                    <div key={category} className="space-y-2">
                      <h4 className="text-sm font-medium text-muted-foreground">{category}</h4>
                      <div className="space-y-2">
                        {perms.map((perm) => (
                          <div key={perm.id} className="flex items-center space-x-2">
                            <input
                              type="checkbox"
                              id={perm.id}
                              checked={selectedPermissions.includes(perm.id)}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setSelectedPermissions([...selectedPermissions, perm.id])
                                } else {
                                  setSelectedPermissions(selectedPermissions.filter(p => p !== perm.id))
                                }
                              }}
                              className="rounded border-gray-300"
                            />
                            <Label htmlFor={perm.id} className="font-normal cursor-pointer">
                              <div>
                                <p className="font-medium">{perm.name}</p>
                                <p className="text-xs text-muted-foreground">{perm.description}</p>
                              </div>
                            </Label>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline">Cancel</Button>
              <Button onClick={handleCreateKey} disabled={isCreating}>
                {isCreating ? (
                  <>
                    <div
                      className="h-4 w-4 mr-2 animate-spin rounded-full border-2 border-current border-t-transparent"/>
                    Creating...
                  </>
                ) : (
                  'Create Key'
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* API Keys List */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Your API Keys</CardTitle>
              <CardDescription>
                {apiKeys.length} active API {apiKeys.length === 1 ? 'key' : 'keys'}
              </CardDescription>
            </div>
            <Input
              placeholder="Search keys..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-[200px]"
            />
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredKeys.map((apiKey) => (
              <div
                key={apiKey.id}
                className="flex items-center justify-between p-4 border rounded-lg"
              >
                <div className="flex items-center gap-4">
                  <div className={cn(
                    "p-2 rounded-lg",
                    apiKey.status === 'active' && "bg-green-100 dark:bg-green-900/20",
                    apiKey.status === 'inactive' && "bg-gray-100 dark:bg-gray-900/20",
                    apiKey.status === 'expired' && "bg-red-100 dark:bg-red-900/20"
                  )}>
                    <Key className={cn(
                      "h-5 w-5",
                      apiKey.status === 'active' && "text-green-600 dark:text-green-400",
                      apiKey.status === 'inactive' && "text-gray-600 dark:text-gray-400",
                      apiKey.status === 'expired' && "text-red-600 dark:text-red-400"
                    )}/>
                  </div>

                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <p className="font-medium">{apiKey.name}</p>
                      <Badge
                        variant={
                          apiKey.status === 'active' ? 'secondary' :
                            apiKey.status === 'inactive' ? 'outline' :
                              'destructive'
                        }
                      >
                        {apiKey.status}
                      </Badge>
                    </div>

                    <div className="flex items-center gap-2 font-mono text-sm">
                      <span className="text-muted-foreground">
                        {showKey === apiKey.id ? apiKey.key : `${apiKey.key.substring(0, 7)}...${apiKey.key.slice(-4)}`}
                      </span>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6"
                        onClick={() => setShowKey(showKey === apiKey.id ? null : apiKey.id)}
                      >
                        {showKey === apiKey.id ? (
                          <EyeOff className="h-3 w-3"/>
                        ) : (
                          <Eye className="h-3 w-3"/>
                        )}
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6"
                        onClick={() => handleCopyKey(apiKey.key)}
                      >
                        <Copy className="h-3 w-3"/>
                      </Button>
                    </div>

                    <div className="flex items-center gap-4 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Calendar className="h-3 w-3"/>
                        Created {new Date(apiKey.created).toLocaleDateString()}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3"/>
                        Last used {apiKey.lastUsed}
                      </span>
                      {apiKey.expiresAt && (
                        <span className="flex items-center gap-1 text-yellow-600 dark:text-yellow-400">
                          <AlertCircle className="h-3 w-3"/>
                          Expires {new Date(apiKey.expiresAt).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Switch
                    checked={apiKey.status === 'active'}
                    onCheckedChange={() => handleToggleKey(apiKey.id)}
                    disabled={apiKey.status === 'expired'}
                  />

                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon">
                        <MoreVertical className="h-4 w-4"/>
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuLabel>Actions</DropdownMenuLabel>
                      <DropdownMenuSeparator/>
                      <DropdownMenuItem onClick={() => handleCopyKey(apiKey.key)}>
                        <Copy className="h-4 w-4 mr-2"/>
                        Copy Key
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => handleOpenEditPermissions(apiKey)}>
                        <Edit className="h-4 w-4 mr-2"/>
                        Edit Permissions
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => handleRegenerateKey(apiKey.id)}>
                        <RefreshCw className="h-4 w-4 mr-2"/>
                        Regenerate Key
                      </DropdownMenuItem>
                      <DropdownMenuSeparator/>
                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <DropdownMenuItem
                            className="text-destructive"
                            onSelect={(e) => e.preventDefault()}
                          >
                            <Trash2 className="h-4 w-4 mr-2"/>
                            Delete Key
                          </DropdownMenuItem>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
                          <AlertDialogHeader>
                            <AlertDialogTitle>Delete API Key?</AlertDialogTitle>
                            <AlertDialogDescription>
                              This action cannot be undone. Any applications using this key will lose access.
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel>Cancel</AlertDialogCancel>
                            <AlertDialogAction
                              onClick={() => handleDeleteKey(apiKey.id)}
                              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                            >
                              Delete Key
                            </AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </div>
            ))}

            {filteredKeys.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                <Key className="h-12 w-12 mx-auto mb-4 opacity-50"/>
                <p>No API keys found</p>
                <p className="text-sm">Create your first API key to get started</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Usage Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">API Usage</CardTitle>
            <CardDescription>Last 30 days</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {apiKeys.filter(k => k.status === 'active').map((key) => (
                <div key={key.id} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">{key.name}</span>
                    <span className="text-sm text-muted-foreground">
                      {key.usage}/{key.rateLimit} requests
                    </span>
                  </div>
                  <Progress value={(key.usage / key.rateLimit) * 100} className="h-2"/>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Quick Start</CardTitle>
            <CardDescription>Get started with the API</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <Button variant="outline" className="w-full justify-start">
                <Code className="h-4 w-4 mr-2"/>
                View API Documentation
              </Button>
              <Button variant="outline" className="w-full justify-start">
                <Terminal className="h-4 w-4 mr-2"/>
                Download SDK
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Security Notice */}
      <Card className="bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800">
        <CardContent className="pt-6">
          <div className="flex gap-3">
            <Shield className="h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5"/>
            <div className="space-y-1">
              <p className="text-sm font-medium text-blue-900 dark:text-blue-100">
                Security best practices
              </p>
              <p className="text-sm text-blue-800 dark:text-blue-200">
                Never share your API keys publicly. Rotate keys regularly and use environment variables to store them
                securely.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Edit Permissions Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[85vh] p-0 gap-0">
          {/* Header with gradient background */}
          <div className="px-8 py-6 border-b bg-gradient-to-r from-primary/5 via-primary/10 to-primary/5">
            <DialogHeader>
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-lg bg-primary/10 border border-primary/20">
                  <Shield className="h-5 w-5 text-primary"/>
                </div>
                <div>
                  <DialogTitle className="text-xl">Edit API Key Permissions</DialogTitle>
                  <DialogDescription className="mt-1">
                    Configure access permissions for <span
                    className="font-semibold text-foreground">"{editingKey?.name}"</span>
                  </DialogDescription>
                </div>
              </div>
            </DialogHeader>
          </div>

          {/* Scrollable Content */}
          <div className="overflow-y-auto max-h-[calc(85vh-200px)] px-8 py-6">
            <div className="space-y-8">
              {/* Permission Summary Card */}
              <div
                className="flex items-center justify-between p-4 bg-gradient-to-br from-muted/50 to-muted rounded-xl border shadow-sm">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-primary/10">
                    <CheckCircle className="h-5 w-5 text-primary"/>
                  </div>
                  <div>
                    <p className="text-sm font-semibold">
                      {editPermissions.length} Permission{editPermissions.length !== 1 ? 's' : ''} Selected
                    </p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {editPermissions.length === 0
                        ? 'Select at least one permission to continue'
                        : `${Math.round((editPermissions.length / permissions.length) * 100)}% of available permissions`}
                    </p>
                  </div>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setEditPermissions([])}
                  disabled={editPermissions.length === 0}
                  className="hover:bg-destructive/10 hover:text-destructive hover:border-destructive/30"
                >
                  <XCircle className="h-4 w-4 mr-2"/>
                  Clear All
                </Button>
              </div>

              {/* Permissions by Category */}
              <div className="space-y-8">
                {Object.entries(groupedPermissions).map(([category, perms]) => {
                  const selectedCount = perms.filter(p => editPermissions.includes(p.id)).length
                  const allSelected = selectedCount === perms.length

                  return (
                    <div key={category} className="space-y-4">
                      {/* Category Header */}
                      <div
                        className="flex items-center justify-between sticky top-0 bg-background/95 backdrop-blur-sm py-2 z-10">
                        <div className="flex items-center gap-3">
                          <div className="h-px w-8 bg-gradient-to-r from-primary/50 to-transparent"/>
                          <h4 className="text-sm font-bold text-foreground uppercase tracking-wide">{category}</h4>
                          <Badge
                            variant={allSelected ? "default" : "outline"}
                            className="text-xs font-semibold"
                          >
                            {selectedCount}/{perms.length}
                          </Badge>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            if (allSelected) {
                              setEditPermissions(prev => prev.filter(p => !perms.map(perm => perm.id).includes(p)))
                            } else {
                              setEditPermissions(prev => [...new Set([...prev, ...perms.map(p => p.id)])])
                            }
                          }}
                          className="h-7 text-xs"
                        >
                          {allSelected ? 'Deselect All' : 'Select All'}
                        </Button>
                      </div>

                      {/* Permission Items */}
                      <div className="space-y-3">
                        {perms.map((permission) => {
                          const isSelected = editPermissions.includes(permission.id)

                          return (
                            <div
                              key={permission.id}
                              className={cn(
                                "group relative flex items-start justify-between p-4 rounded-xl border-2 transition-all duration-200 cursor-pointer",
                                isSelected
                                  ? "bg-primary/5 border-primary/30 shadow-sm hover:shadow-md hover:border-primary/50"
                                  : "bg-card border-border/50 hover:bg-accent/30 hover:border-border"
                              )}
                              onClick={() => toggleEditPermission(permission.id)}
                            >
                              <div className="flex items-start gap-4 flex-1 min-w-0">
                                {/* Custom Checkbox */}
                                <div className="pt-0.5">
                                  <div
                                    className={cn(
                                      "h-5 w-5 rounded-md border-2 flex items-center justify-center transition-all duration-200",
                                      isSelected
                                        ? "bg-primary border-primary scale-100"
                                        : "border-muted-foreground/40 group-hover:border-primary/50 scale-95"
                                    )}
                                  >
                                    {isSelected && (
                                      <CheckCircle className="h-3.5 w-3.5 text-primary-foreground"/>
                                    )}
                                  </div>
                                </div>

                                {/* Permission Details */}
                                <div className="flex-1 min-w-0">
                                  <p className={cn(
                                    "text-sm font-semibold transition-colors",
                                    isSelected ? "text-foreground" : "text-foreground/80"
                                  )}>
                                    {permission.name}
                                  </p>
                                  <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
                                    {permission.description}
                                  </p>
                                </div>
                              </div>

                              {/* Permission ID Badge */}
                              <Badge
                                variant={isSelected ? "default" : "outline"}
                                className={cn(
                                  "ml-3 text-xs font-mono shrink-0 transition-all",
                                  isSelected && "shadow-sm"
                                )}
                              >
                                {permission.id}
                              </Badge>
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  )
                })}
              </div>

              {/* Warning for Admin Permissions */}
              {editPermissions.includes('admin:all') && (
                <div
                  className="flex items-start gap-3 p-4 bg-gradient-to-r from-destructive/10 to-destructive/5 border-2 border-destructive/30 rounded-xl shadow-sm">
                  <div className="p-2 rounded-lg bg-destructive/10">
                    <AlertCircle className="h-5 w-5 text-destructive"/>
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-bold text-destructive">⚠️ Critical Warning: Admin Access</p>
                    <p className="text-xs text-destructive/90 mt-1.5 leading-relaxed">
                      This permission grants unrestricted administrative access to all resources and operations.
                      Only assign this to highly trusted applications with proper security measures in place.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Footer with Actions */}
          <div className="px-8 py-5 border-t bg-muted/30">
            <DialogFooter className="gap-2">
              <Button
                variant="outline"
                onClick={() => setIsEditDialogOpen(false)}
                className="min-w-[100px]"
              >
                Cancel
              </Button>
              <Button
                onClick={handleSavePermissions}
                disabled={editPermissions.length === 0}
                className="min-w-[140px] shadow-sm"
              >
                <CheckCircle className="h-4 w-4 mr-2"/>
                Save Permissions
              </Button>
            </DialogFooter>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}

function cn(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(' ')
}
