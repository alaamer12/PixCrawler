'use client'

import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Switch } from '@/components/ui/switch'
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
import { useToast } from '@/components/ui/use-toast'
import {
  Camera,
  Globe,
  Linkedin,
  Github,
  Twitter,
  Save,
  X,
  Check,
  AlertCircle,
  Trash2,
  Download,
  Upload,
  User,
  Building,
  MapPin,
  Calendar,
  Clock,
  Edit2,
  Shield,
  Mail,
  Briefcase,
  UserCircle,
  Bell,
  Lock,
  ExternalLink,
  Info,
  Eye,
  EyeOff
} from 'lucide-react'
import { useAuth } from '@/lib/auth/hooks'
import { cn } from '@/lib/utils'
import { z } from 'zod'

// Validation Schema
const profileSchema = z.object({
  firstName: z.string().min(1, "First name is required"),
  lastName: z.string().min(1, "Last name is required"),
  email: z.string().email("Invalid email address"),
  phone: z.string().optional(),
  bio: z.string().max(500, "Bio must be less than 500 characters").optional(),
  company: z.string().optional(),
  jobTitle: z.string().optional(),
  location: z.string().optional(),
  website: z.string().url("Invalid URL").optional().or(z.literal('')),
  linkedin: z.string().optional(),
  github: z.string().optional(),
  twitter: z.string().optional(),
  publicProfile: z.boolean(),
  emailNotifications: z.boolean(),
  marketingEmails: z.boolean(),
})

// Types
interface ProfileData {
  firstName: string
  lastName: string
  email: string
  phone: string
  bio: string
  location: string
  website: string
  company: string
  jobTitle: string
  timezone: string
  language: string
  linkedin: string
  github: string
  twitter: string
  publicProfile: boolean
  emailNotifications: boolean
  marketingEmails: boolean
}

const DEFAULT_PROFILE: ProfileData = {
  firstName: '',
  lastName: '',
  email: '',
  phone: '+1 (555) 123-4567',
  bio: 'Machine learning engineer passionate about computer vision and dataset creation. Building the future of AI-powered image analysis.',
  location: 'San Francisco, CA',
  website: 'https://pixcrawler.io',
  company: 'PixCrawler Inc.',
  jobTitle: 'ML Engineer',
  timezone: 'America/Los_Angeles',
  language: 'en',
  linkedin: 'johndoe',
  github: 'johndoe',
  twitter: '@johndoe',
  publicProfile: true,
  emailNotifications: true,
  marketingEmails: false,
}

// Focused Components
const ProfileSection = ({
  icon: Icon,
  title,
  description,
  children,
  action
}: {
  icon: any
  title: string
  description: string
  children: React.ReactNode
  action?: React.ReactNode
}) => (
  <Card className="transition-all duration-200 hover:shadow-md">
    <CardHeader>
      <div className="flex items-start justify-between">
        <div className="space-y-1.5">
          <CardTitle className="flex items-center gap-2.5 text-lg">
            <div className="p-1.5 rounded-md bg-primary/10">
              <Icon className="w-4 h-4" />
            </div>
            {title}
          </CardTitle>
          <CardDescription>{description}</CardDescription>
        </div>
        {action}
      </div>
    </CardHeader>
    <CardContent className="space-y-5">
      {children}
    </CardContent>
  </Card>
)

const FormField = ({
  label,
  icon: Icon,
  tooltip,
  required,
  error,
  children
}: {
  label: string
  icon?: any
  tooltip?: string
  required?: boolean
  error?: string
  children: React.ReactNode
}) => (
  <div className="space-y-2">
    <div className="flex items-center gap-2">
      <Label className="text-sm font-medium flex items-center gap-1.5">
        {Icon && <Icon className="w-3.5 h-3.5 text-muted-foreground" />}
        {label}
        {required && <span className="text-destructive">*</span>}
      </Label>
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
    {children}
    {error && <p className="text-xs text-destructive font-medium">{error}</p>}
  </div>
)

const SocialLink = ({
  icon: Icon,
  platform,
  value,
  onChange,
  color
}: {
  icon: any
  platform: string
  value: string
  onChange: (value: string) => void
  color?: string
}) => (
  <div className="flex items-center gap-3">
    <div className={cn(
      "p-2 rounded-lg",
      color ? `bg-[${color}]/10` : "bg-muted"
    )}>
      <Icon className={cn("w-5 h-5", color && `text-[${color}]`)} />
    </div>
    <Input
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={`${platform} username`}
      className="flex-1"
    />
  </div>
)

const PrivacyToggle = ({
  icon: Icon,
  label,
  description,
  checked,
  onCheckedChange,
}: {
  icon: any
  label: string
  description: string
  checked: boolean
  onCheckedChange: (checked: boolean) => void
}) => (
  <div className="flex items-start justify-between gap-4 py-2">
    <div className="flex gap-3 flex-1">
      <div className="p-2 rounded-lg bg-muted/50 h-fit">
        <Icon className="w-4 h-4 text-muted-foreground" />
      </div>
      <div className="space-y-0.5">
        <Label className="text-sm font-medium">{label}</Label>
        <p className="text-xs text-muted-foreground leading-relaxed">
          {description}
        </p>
      </div>
    </div>
    <Switch
      checked={checked}
      onCheckedChange={onCheckedChange}
    />
  </div>
)

const InfoItem = ({
  icon: Icon,
  label,
  value
}: {
  icon: any
  label: string
  value: string
}) => (
  <div className="flex items-center justify-between py-2">
    <div className="flex items-center gap-2 text-sm text-muted-foreground">
      <Icon className="w-4 h-4" />
      <span>{label}</span>
    </div>
    <span className="text-sm font-medium">{value}</span>
  </div>
)

export function AccountProfile() {
  const { toast } = useToast()
  const { user, signOut, updateUser } = useAuth()
  const [isSaving, setIsSaving] = useState(false)
  const [deleteConfirmation, setDeleteConfirmation] = useState('')
  const [isDeleting, setIsDeleting] = useState(false)
  const [avatarUrl, setAvatarUrl] = useState(user?.profile?.avatarUrl || '')
  const [hasChanges, setHasChanges] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})

  const [profileData, setProfileData] = useState<ProfileData>({
    ...DEFAULT_PROFILE,
    firstName: user?.profile?.fullName?.split(' ')[0] || '',
    lastName: user?.profile?.fullName?.split(' ')[1] || '',
    email: user?.email || '',
  })

  const [editedData, setEditedData] = useState<ProfileData>(profileData)

  const validateField = (key: keyof ProfileData, value: any) => {
    try {
      (profileSchema.shape as any)[key].parse(value)
      setErrors(prev => {
        const newErrors = { ...prev }
        delete newErrors[key]
        return newErrors
      })
      return true
    } catch (error) {
      if (error instanceof z.ZodError) {
        setErrors(prev => ({ ...prev, [key]: error.errors[0].message }))
      }
      return false
    }
  }

  const updateField = <K extends keyof ProfileData>(
    key: K,
    value: ProfileData[K]
  ) => {
    setEditedData(prev => ({ ...prev, [key]: value }))
    setHasChanges(true)
    validateField(key, value)
  }

  const handleSave = async () => {
    // Validate all fields before saving
    const result = profileSchema.safeParse(editedData)
    if (!result.success) {
      const newErrors: Record<string, string> = {}
      result.error.errors.forEach(err => {
        if (err.path[0]) {
          newErrors[err.path[0] as string] = err.message
        }
      })
      setErrors(newErrors)
      toast({
        title: 'Validation Error',
        description: 'Please fix the errors in the form',
        variant: 'destructive',
      })
      return
    }

    setIsSaving(true)
    await new Promise(resolve => setTimeout(resolve, 1200))

    // Update global user state
    updateUser({
      email: editedData.email,
      profile: {
        ...user?.profile!,
        fullName: `${editedData.firstName} ${editedData.lastName}`.trim(),
        avatarUrl: avatarUrl,
        email: editedData.email
      }
    })

    setProfileData(editedData)
    setIsSaving(false)
    setHasChanges(false)

    toast({
      title: 'Profile updated',
      description: 'Your changes have been saved successfully',
    })
  }

  const handleAvatarUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        toast({
          title: 'File too large',
          description: 'Please select an image under 5MB',
          variant: 'destructive'
        })
        return
      }

      const reader = new FileReader()
      reader.onloadend = () => {
        setAvatarUrl(reader.result as string)
        setHasChanges(true)
        toast({
          title: 'Avatar updated',
          description: 'Your profile picture has been changed',
        })
      }
      reader.readAsDataURL(file)
    }
  }

  const handleRemoveAvatar = () => {
    setAvatarUrl('')
    setHasChanges(true)
    toast({
      title: 'Avatar removed',
      description: 'Your profile picture has been removed',
    })
  }

  const handleExportData = () => {
    const dataStr = JSON.stringify({
      profile: profileData,
      settings: {},
      exportDate: new Date().toISOString()
    }, null, 2)
    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr)

    const link = document.createElement('a')
    link.setAttribute('href', dataUri)
    link.setAttribute('download', `pixcrawler-profile-${Date.now()}.json`)
    link.click()

    toast({
      title: 'Data exported',
      description: 'Your profile data has been downloaded as JSON',
    })
  }

  const handleDeleteAccount = async () => {
    if (deleteConfirmation !== 'DELETE MY ACCOUNT') {
      toast({
        title: 'Invalid confirmation',
        description: 'Please type exactly "DELETE MY ACCOUNT" to confirm',
        variant: 'destructive',
      })
      return
    }

    setIsDeleting(true)

    try {
      const response = await fetch('/api/account/delete', {
        method: 'DELETE',
      })

      if (!response.ok) throw new Error('Failed to delete account')

      toast({
        title: 'Account deleted',
        description: 'Your account has been permanently deleted',
      })

      setTimeout(async () => {
        await signOut()
        window.location.href = '/'
      }, 1000)
    } catch (error) {
      console.error('Error deleting account:', error)
      toast({
        title: 'Error',
        description: 'Failed to delete account. Please try again',
        variant: 'destructive',
      })
      setIsDeleting(false)
    }
  }

  const displayData = editedData // Always show edited data since we are always editing

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
      {/* Sticky Header */}
      <div className="hidden md:block border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
        <div className="container max-w-5xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between gap-6">
            <div>
              <h1 className="text-2xl font-semibold tracking-tight">Account Profile</h1>
              <p className="text-sm text-muted-foreground mt-0.5">
                Manage your personal information and preferences
              </p>
            </div>

            <div className="flex items-center gap-2">
              {hasChanges && (
                <Badge variant="secondary" className="animate-pulse">
                  Unsaved changes
                </Badge>
              )}
              <Button
                size="sm"
                onClick={handleSave}
                disabled={isSaving || !hasChanges || Object.keys(errors).length > 0}
              >
                {isSaving ? (
                  <>
                    <div className="h-4 w-4 mr-2 animate-spin rounded-full border-2 border-white border-t-transparent" />
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
        </div>
      </div>

      {/* Main Content */}
      <div className="container max-w-5xl mx-auto px-6 py-8 space-y-6">
        {/* Profile Picture */}
        <ProfileSection
          icon={UserCircle}
          title="Profile Picture"
          description="Upload a profile photo to personalize your account"
        >
          <div className="flex items-start gap-6">
            <div className="relative group">
              <Avatar className="h-28 w-28 border-4 border-background shadow-lg">
                <AvatarImage src={avatarUrl} />
                <AvatarFallback className="bg-gradient-to-br from-primary/20 to-primary/10">
                  <User className="h-14 w-14 text-muted-foreground" />
                </AvatarFallback>
              </Avatar>
              <label
                htmlFor="avatar-upload"
                className="absolute inset-0 flex items-center justify-center bg-black/60 rounded-full cursor-pointer opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <Camera className="h-6 w-6 text-white" />
                <input
                  id="avatar-upload"
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  className="hidden"
                  onChange={handleAvatarUpload}
                />
              </label>
            </div>
            <div className="flex-1 space-y-3">
              <div>
                <p className="text-sm font-medium">
                  {displayData.firstName} {displayData.lastName}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  Recommended: Square image, at least 400×400px (max 5MB)
                </p>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" asChild>
                  <label htmlFor="avatar-upload" className="cursor-pointer">
                    <Upload className="h-4 w-4 mr-2" />
                    Upload New
                    <input
                      id="avatar-upload"
                      type="file"
                      accept="image/*"
                      className="hidden"
                      onChange={handleAvatarUpload}
                    />
                  </label>
                </Button>
                {avatarUrl && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleRemoveAvatar}
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    Remove
                  </Button>
                )}
              </div>
            </div>
          </div>
        </ProfileSection>

        {/* Personal Information */}
        <ProfileSection
          icon={User}
          title="Personal Information"
          description="Your basic contact details and bio"
        >
          <div className="grid gap-5">
            <div className="grid md:grid-cols-2 gap-4">
              <FormField label="First Name" required error={errors.firstName}>
                <Input
                  value={displayData.firstName}
                  onChange={(e) => updateField('firstName', e.target.value)}
                  placeholder="John"
                />
              </FormField>
              <FormField label="Last Name" required error={errors.lastName}>
                <Input
                  value={displayData.lastName}
                  onChange={(e) => updateField('lastName', e.target.value)}
                  placeholder="Doe"
                />
              </FormField>
            </div>

            <FormField
              label="Email Address"
              icon={Mail}
              required
              tooltip="Your primary email for account notifications"
              error={errors.email}
            >
              <div className="flex gap-2">
                <Input
                  type="email"
                  value={displayData.email}
                  onChange={(e) => updateField('email', e.target.value)}
                  placeholder="john@example.com"
                  className="flex-1"
                />
                <Badge variant="secondary" className="self-center px-3">
                  <Check className="h-3 w-3 mr-1" />
                  Verified
                </Badge>
              </div>
            </FormField>

            <FormField label="Phone Number" error={errors.phone}>
              <Input
                type="tel"
                value={displayData.phone}
                onChange={(e) => updateField('phone', e.target.value)}
                placeholder="+1 (555) 123-4567"
              />
            </FormField>

            <FormField
              label="Bio"
              tooltip="Tell others about yourself and your work"
              error={errors.bio}
            >
              <Textarea
                value={displayData.bio || ''}
                onChange={(e) => updateField('bio', e.target.value)}
                placeholder="Tell us about yourself..."
                rows={4}
                maxLength={500}
                className="resize-none"
              />
              <p className="text-xs text-muted-foreground text-right">
                {(displayData.bio || '').length}/500
              </p>
            </FormField>
          </div>
        </ProfileSection>

        {/* Professional Information */}
        <ProfileSection
          icon={Briefcase}
          title="Professional Information"
          description="Your work details and professional background"
        >
          <div className="grid gap-5">
            <div className="grid md:grid-cols-2 gap-4">
              <FormField label="Company" icon={Building} error={errors.company}>
                <Input
                  value={displayData.company}
                  onChange={(e) => updateField('company', e.target.value)}
                  placeholder="Company name"
                />
              </FormField>
              <FormField label="Job Title" error={errors.jobTitle}>
                <Input
                  value={displayData.jobTitle}
                  onChange={(e) => updateField('jobTitle', e.target.value)}
                  placeholder="Your role"
                />
              </FormField>
            </div>

            <div className="grid md:grid-cols-2 gap-4">
              <FormField label="Location" icon={MapPin} error={errors.location}>
                <Input
                  value={displayData.location}
                  onChange={(e) => updateField('location', e.target.value)}
                  placeholder="City, Country"
                />
              </FormField>
              <FormField label="Website" icon={Globe} error={errors.website}>
                <div className="relative">
                  <Input
                    type="url"
                    value={displayData.website}
                    onChange={(e) => updateField('website', e.target.value)}
                    placeholder="https://example.com"
                  />
                  {displayData.website && (
                    <a
                      href={displayData.website}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                    >
                      <ExternalLink className="h-4 w-4" />
                    </a>
                  )}
                </div>
              </FormField>
            </div>
          </div>
        </ProfileSection>

        {/* Social Profiles */}
        <ProfileSection
          icon={Globe}
          title="Social Profiles"
          description="Connect your professional social media accounts"
        >
          <div className="space-y-4">
            <SocialLink
              icon={Linkedin}
              platform="LinkedIn"
              value={displayData.linkedin}
              onChange={(v) => updateField('linkedin', v)}
              color="#0077B5"
            />
            <SocialLink
              icon={Github}
              platform="GitHub"
              value={displayData.github}
              onChange={(v) => updateField('github', v)}
            />
            <SocialLink
              icon={Twitter}
              platform="Twitter"
              value={displayData.twitter}
              onChange={(v) => updateField('twitter', v)}
              color="#1DA1F2"
            />
          </div>
        </ProfileSection>

        {/* Privacy Settings */}
        <ProfileSection
          icon={Shield}
          title="Privacy & Notifications"
          description="Control your visibility and communication preferences"
        >
          <div className="space-y-1">
            <PrivacyToggle
              icon={Eye}
              label="Public Profile"
              description="Allow other users to view your profile information"
              checked={displayData.publicProfile}
              onCheckedChange={(v) => updateField('publicProfile', v)}
            />
            <Separator />
            <PrivacyToggle
              icon={Bell}
              label="Email Notifications"
              description="Receive important updates and alerts via email"
              checked={displayData.emailNotifications}
              onCheckedChange={(v) => updateField('emailNotifications', v)}
            />
            <Separator />
            <PrivacyToggle
              icon={Mail}
              label="Marketing Emails"
              description="Get news, tips, and special offers from PixCrawler"
              checked={displayData.marketingEmails}
              onCheckedChange={(v) => updateField('marketingEmails', v)}
            />
          </div>
        </ProfileSection>

        {/* Account Security */}
        <ProfileSection
          icon={Lock}
          title="Account Security"
          description="Monitor your account activity and security status"
        >
          <div className="space-y-3">
            <InfoItem
              icon={Calendar}
              label="Account Created"
              value="January 15, 2024"
            />
            <Separator />
            <InfoItem
              icon={Clock}
              label="Last Login"
              value="Today at 10:30 AM"
            />
            <Separator />
            <InfoItem
              icon={Shield}
              label="Security Status"
              value="Strong"
            />
          </div>
        </ProfileSection>

        {/* Data Management */}
        <Card className="border-destructive/40 bg-destructive/5">
          <CardHeader>
            <CardTitle className="flex items-center gap-2.5 text-lg text-destructive">
              <div className="p-1.5 rounded-md bg-destructive/10">
                <AlertCircle className="w-4 h-4" />
              </div>
              Danger Zone
            </CardTitle>
            <CardDescription>
              Irreversible actions that affect your account permanently
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleExportData}
              >
                <Download className="h-4 w-4 mr-2" />
                Export My Data
              </Button>

              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button variant="destructive" size="sm">
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete Account
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent className="max-w-md">
                  <AlertDialogHeader>
                    <AlertDialogTitle className="flex items-center gap-2 text-xl">
                      <AlertCircle className="h-5 w-5 text-destructive" />
                      Delete Your Account?
                    </AlertDialogTitle>
                    <AlertDialogDescription className="text-base space-y-3">
                      <p>This action cannot be undone. This will permanently delete:</p>
                      <ul className="space-y-1.5 text-sm">
                        <li className="flex items-start gap-2">
                          <span className="text-destructive mt-0.5">•</span>
                          <span>All your projects and datasets</span>
                        </li>
                        <li className="flex items-start gap-2">
                          <span className="text-destructive mt-0.5">•</span>
                          <span>All processing jobs and results</span>
                        </li>
                        <li className="flex items-start gap-2">
                          <span className="text-destructive mt-0.5">•</span>
                          <span>Your profile and settings</span>
                        </li>
                        <li className="flex items-start gap-2">
                          <span className="text-destructive mt-0.5">•</span>
                          <span>All associated data and metadata</span>
                        </li>
                      </ul>
                    </AlertDialogDescription>
                  </AlertDialogHeader>

                  <div className="space-y-4 py-2">
                    <FormField
                      label="Type DELETE MY ACCOUNT to confirm"
                      required
                    >
                      <Input
                        type="text"
                        placeholder="DELETE MY ACCOUNT"
                        value={deleteConfirmation}
                        onChange={(e) => setDeleteConfirmation(e.target.value)}
                        className="font-mono"
                        disabled={isDeleting}
                      />
                    </FormField>

                    <div className="flex items-start gap-2 p-3 bg-destructive/10 border border-destructive/20 rounded-lg">
                      <AlertCircle className="h-4 w-4 text-destructive mt-0.5 flex-shrink-0" />
                      <p className="text-xs text-destructive leading-relaxed">
                        This action is immediate and cannot be reversed. All your data will be permanently erased from our servers.
                      </p>
                    </div>
                  </div>

                  <AlertDialogFooter>
                    <AlertDialogCancel disabled={isDeleting}>
                      Cancel
                    </AlertDialogCancel>
                    <Button
                      variant="destructive"
                      onClick={handleDeleteAccount}
                      disabled={deleteConfirmation !== 'DELETE MY ACCOUNT' || isDeleting}
                    >
                      {isDeleting ? (
                        <>
                          <div className="h-4 w-4 mr-2 animate-spin rounded-full border-2 border-white border-t-transparent" />
                          Deleting...
                        </>
                      ) : (
                        'Delete My Account'
                      )}
                    </Button>
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