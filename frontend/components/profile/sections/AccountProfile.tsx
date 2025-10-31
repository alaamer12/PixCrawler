'use client'

import React, {useState} from 'react'
import {Button} from '@/components/ui/button'
import {Input} from '@/components/ui/input'
import {Label} from '@/components/ui/label'
import {Textarea} from '@/components/ui/textarea'
import {Avatar, AvatarFallback, AvatarImage} from '@/components/ui/avatar'
import {Card, CardContent, CardDescription, CardHeader, CardTitle} from '@/components/ui/card'
import {Badge} from '@/components/ui/badge'
import {Separator} from '@/components/ui/separator'
import {Switch} from '@/components/ui/switch'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
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
import {useToast} from '@/components/ui/use-toast'
import {
  Camera,
  Mail,
  Phone,
  MapPin,
  Globe,
  Linkedin,
  Github,
  Twitter,
  Save,
  X,
  Check,
  AlertCircle,
  Shield,
  Trash2,
  Download,
  Upload,
  User,
  Building,
  Calendar,
  Clock,
  Edit2,
} from 'lucide-react'
import {useAuth} from '@/lib/auth/hooks'

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

export function AccountProfile() {
  const {toast} = useToast()
  const {user, signOut} = useAuth()
  const [isEditing, setIsEditing] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [deleteConfirmation, setDeleteConfirmation] = useState('')
  const [isDeleting, setIsDeleting] = useState(false)
  const [avatarUrl, setAvatarUrl] = useState(user?.profile?.avatarUrl || '')

  const [profileData, setProfileData] = useState<ProfileData>({
    firstName: user?.profile?.fullName?.split(' ')[0] || '',
    lastName: user?.profile?.fullName?.split(' ')[1] || '',
    email: user?.email || '',
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
  })

  const [editedData, setEditedData] = useState<ProfileData>(profileData)

  const handleSave = async () => {
    setIsSaving(true)
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1500))

    setProfileData(editedData)
    setIsEditing(false)
    setIsSaving(false)

    toast({
      title: 'Profile updated',
      description: 'Your profile information has been successfully saved.',
    })
  }

  const handleCancel = () => {
    setEditedData(profileData)
    setIsEditing(false)
  }

  const handleAvatarUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onloadend = () => {
        setAvatarUrl(reader.result as string)
        toast({
          title: 'Avatar uploaded',
          description: 'Your profile picture has been updated.',
        })
      }
      reader.readAsDataURL(file)
    }
  }

  const handleExportData = () => {
    const dataStr = JSON.stringify({profile: profileData, settings: {}}, null, 2)
    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr)

    const exportFileDefaultName = 'pixcrawler-profile-export.json'

    const linkElement = document.createElement('a')
    linkElement.setAttribute('href', dataUri)
    linkElement.setAttribute('download', exportFileDefaultName)
    linkElement.click()

    toast({
      title: 'Data exported',
      description: 'Your profile data has been downloaded.',
    })
  }

  const handleDeleteAccount = async () => {
    if (deleteConfirmation !== 'DELETE MY ACCOUNT') {
      toast({
        title: 'Invalid confirmation',
        description: 'Please type "DELETE MY ACCOUNT" to confirm.',
        variant: 'destructive',
      })
      return
    }

    setIsDeleting(true)

    try {
      // Call delete account API
      const response = await fetch('/api/account/delete', {
        method: 'DELETE',
      })

      if (!response.ok) {
        throw new Error('Failed to delete account')
      }

      toast({
        title: 'Account deleted',
        description: 'Your account has been permanently deleted.',
      })

      // Wait 1 second then redirect to landing page
      setTimeout(async () => {
        await signOut()
        window.location.href = '/'
      }, 1000)
    } catch (error) {
      console.error('Error deleting account:', error)
      toast({
        title: 'Error',
        description: 'Failed to delete account. Please try again.',
        variant: 'destructive',
      })
      setIsDeleting(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Account Profile</h1>
          <p className="text-muted-foreground">
            Manage your personal information and account settings
          </p>
        </div>
        <div className="flex items-center gap-2">
          {!isEditing ? (
            <Button onClick={() => setIsEditing(true)} variant="default">
              <Edit2 className="h-4 w-4 mr-2"/>
              Edit Profile
            </Button>
          ) : (
            <>
              <Button
                variant="outline"
                onClick={handleCancel}
                disabled={isSaving}
              >
                <X className="h-4 w-4 mr-2"/>
                Cancel
              </Button>
              <Button
                onClick={handleSave}
                disabled={isSaving}
              >
                {isSaving ? (
                  <>
                    <div
                      className="h-4 w-4 mr-2 animate-spin rounded-full border-2 border-current border-t-transparent"/>
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2"/>
                    Save Changes
                  </>
                )}
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Profile Picture Section */}
      <Card>
        <CardHeader>
          <CardTitle>Profile Picture</CardTitle>
          <CardDescription>
            Your profile picture is visible to other users when you share projects
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-6">
            <div className="relative">
              <Avatar className="h-24 w-24">
                <AvatarImage src={avatarUrl}/>
                <AvatarFallback>
                  <User className="h-12 w-12"/>
                </AvatarFallback>
              </Avatar>
              {isEditing && (
                <label
                  htmlFor="avatar-upload"
                  className="absolute bottom-0 right-0 p-1.5 bg-primary text-primary-foreground rounded-full cursor-pointer hover:bg-primary/90 transition-colors"
                >
                  <Camera className="h-4 w-4"/>
                  <input
                    id="avatar-upload"
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={handleAvatarUpload}
                  />
                </label>
              )}
            </div>
            <div className="space-y-2">
              <div className="text-sm text-muted-foreground">
                Recommended: Square image, at least 400x400px
              </div>
              {isEditing && (
                <div className="flex gap-2">
                  <Button variant="outline" size="sm">
                    <Upload className="h-4 w-4 mr-2"/>
                    Upload
                  </Button>
                  <Button variant="outline" size="sm">
                    Remove
                  </Button>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Personal Information */}
      <Card>
        <CardHeader>
          <CardTitle>Personal Information</CardTitle>
          <CardDescription>
            Update your personal details and contact information
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="firstName">First Name</Label>
              <Input
                id="firstName"
                value={isEditing ? editedData.firstName : profileData.firstName}
                onChange={(e) => setEditedData({...editedData, firstName: e.target.value})}
                disabled={!isEditing}
                placeholder="John"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="lastName">Last Name</Label>
              <Input
                id="lastName"
                value={isEditing ? editedData.lastName : profileData.lastName}
                onChange={(e) => setEditedData({...editedData, lastName: e.target.value})}
                disabled={!isEditing}
                placeholder="Doe"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="email">Email Address</Label>
            <div className="flex gap-2">
              <Input
                id="email"
                type="email"
                value={isEditing ? editedData.email : profileData.email}
                onChange={(e) => setEditedData({...editedData, email: e.target.value})}
                disabled={!isEditing}
                className="flex-1"
                placeholder="john@example.com"
              />
              {!isEditing && (
                <Badge variant="secondary" className="self-center">
                  <Check className="h-3 w-3 mr-1"/>
                  Verified
                </Badge>
              )}
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="phone">Phone Number</Label>
            <Input
              id="phone"
              type="tel"
              value={isEditing ? editedData.phone : profileData.phone}
              onChange={(e) => setEditedData({...editedData, phone: e.target.value})}
              disabled={!isEditing}
              placeholder="+1 (555) 123-4567"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="bio">Bio</Label>
            <Textarea
              id="bio"
              value={isEditing ? editedData.bio : profileData.bio}
              onChange={(e) => setEditedData({...editedData, bio: e.target.value})}
              disabled={!isEditing}
              placeholder="Tell us about yourself..."
              rows={4}
            />
            <p className="text-xs text-muted-foreground">
              {(isEditing ? editedData.bio : profileData.bio).length}/500 characters
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Professional Information */}
      <Card>
        <CardHeader>
          <CardTitle>Professional Information</CardTitle>
          <CardDescription>
            Add details about your work and professional background
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="company">Company</Label>
              <div className="relative">
                <Building className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground"/>
                <Input
                  id="company"
                  value={isEditing ? editedData.company : profileData.company}
                  onChange={(e) => setEditedData({...editedData, company: e.target.value})}
                  disabled={!isEditing}
                  className="pl-10"
                  placeholder="PixCrawler Inc."
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="jobTitle">Job Title</Label>
              <Input
                id="jobTitle"
                value={isEditing ? editedData.jobTitle : profileData.jobTitle}
                onChange={(e) => setEditedData({...editedData, jobTitle: e.target.value})}
                disabled={!isEditing}
                placeholder="ML Engineer"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="location">Location</Label>
              <div className="relative">
                <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground"/>
                <Input
                  id="location"
                  value={isEditing ? editedData.location : profileData.location}
                  onChange={(e) => setEditedData({...editedData, location: e.target.value})}
                  disabled={!isEditing}
                  className="pl-10"
                  placeholder="San Francisco, CA"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="website">Website</Label>
              <div className="relative">
                <Globe className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground"/>
                <Input
                  id="website"
                  type="url"
                  value={isEditing ? editedData.website : profileData.website}
                  onChange={(e) => setEditedData({...editedData, website: e.target.value})}
                  disabled={!isEditing}
                  className="pl-10"
                  placeholder="https://example.com"
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Social Profiles */}
      <Card>
        <CardHeader>
          <CardTitle>Social Profiles</CardTitle>
          <CardDescription>
            Connect your social media accounts
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <Linkedin className="h-5 w-5 text-[#0077B5]"/>
              <Input
                value={isEditing ? editedData.linkedin : profileData.linkedin}
                onChange={(e) => setEditedData({...editedData, linkedin: e.target.value})}
                disabled={!isEditing}
                placeholder="linkedin.com/in/username"
                className="flex-1"
              />
            </div>
            <div className="flex items-center gap-4">
              <Github className="h-5 w-5"/>
              <Input
                value={isEditing ? editedData.github : profileData.github}
                onChange={(e) => setEditedData({...editedData, github: e.target.value})}
                disabled={!isEditing}
                placeholder="github.com/username"
                className="flex-1"
              />
            </div>
            <div className="flex items-center gap-4">
              <Twitter className="h-5 w-5 text-[#1DA1F2]"/>
              <Input
                value={isEditing ? editedData.twitter : profileData.twitter}
                onChange={(e) => setEditedData({...editedData, twitter: e.target.value})}
                disabled={!isEditing}
                placeholder="@username"
                className="flex-1"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Privacy & Data */}
      <Card>
        <CardHeader>
          <CardTitle>Privacy & Data Management</CardTitle>
          <CardDescription>
            Control your privacy settings and manage your data
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Public Profile</Label>
                <p className="text-sm text-muted-foreground">
                  Make your profile visible to other users
                </p>
              </div>
              <Switch
                checked={isEditing ? editedData.publicProfile : profileData.publicProfile}
                onCheckedChange={(checked) => setEditedData({...editedData, publicProfile: checked})}
                disabled={!isEditing}
              />
            </div>

            <Separator/>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Email Notifications</Label>
                <p className="text-sm text-muted-foreground">
                  Receive important updates via email
                </p>
              </div>
              <Switch
                checked={isEditing ? editedData.emailNotifications : profileData.emailNotifications}
                onCheckedChange={(checked) => setEditedData({...editedData, emailNotifications: checked})}
                disabled={!isEditing}
              />
            </div>

            <Separator/>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Marketing Emails</Label>
                <p className="text-sm text-muted-foreground">
                  Receive news and special offers
                </p>
              </div>
              <Switch
                checked={isEditing ? editedData.marketingEmails : profileData.marketingEmails}
                onCheckedChange={(checked) => setEditedData({...editedData, marketingEmails: checked})}
                disabled={!isEditing}
              />
            </div>
          </div>

          <Separator/>

          <div className="space-y-4">
            <h4 className="text-sm font-medium">Data Management</h4>
            <div className="flex flex-wrap gap-2">
              <Button variant="outline" size="sm" onClick={handleExportData}>
                <Download className="h-4 w-4 mr-2"/>
                Export Data
              </Button>
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button
                    variant="destructive"
                    size="sm"
                    className="bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 shadow-lg shadow-red-500/20 transition-all duration-200"
                  >
                    <Trash2 className="h-4 w-4 mr-2"/>
                    Delete Account
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent className="max-w-md">
                  <AlertDialogHeader>
                    <AlertDialogTitle className="text-2xl">Delete Account</AlertDialogTitle>
                    <AlertDialogDescription className="text-base">
                      This action cannot be undone. This will permanently delete your
                      account and remove all your data from our servers.
                    </AlertDialogDescription>
                  </AlertDialogHeader>

                  <div className="space-y-4 py-4">
                    <div className="space-y-2">
                      <Label htmlFor="delete-confirmation" className="text-sm font-medium">
                        Type <span className="font-mono font-bold text-destructive">DELETE MY ACCOUNT</span> to confirm
                      </Label>
                      <Input
                        id="delete-confirmation"
                        type="text"
                        placeholder="DELETE MY ACCOUNT"
                        value={deleteConfirmation}
                        onChange={(e) => setDeleteConfirmation(e.target.value)}
                        className="font-mono"
                        disabled={isDeleting}
                      />
                    </div>

                    <div
                      className="flex items-start gap-2 p-3 bg-destructive/10 border border-destructive/20 rounded-lg">
                      <AlertCircle className="h-4 w-4 text-destructive mt-0.5 flex-shrink-0"/>
                      <p className="text-xs text-destructive">
                        All your projects, datasets, and crawl jobs will be permanently deleted.
                      </p>
                    </div>
                  </div>

                  <AlertDialogFooter>
                    <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
                    <Button
                      variant="destructive"
                      onClick={handleDeleteAccount}
                      disabled={deleteConfirmation !== 'DELETE MY ACCOUNT' || isDeleting}
                      className="bg-destructive hover:bg-destructive/90"
                    >
                      {isDeleting ? 'Deleting...' : 'Delete Account'}
                    </Button>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Account Security */}
      <Card>
        <CardHeader>
          <CardTitle>Account Security</CardTitle>
          <CardDescription>
            Manage your security settings and authentication methods
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Account Created</Label>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Calendar className="h-4 w-4"/>
              <span>January 15, 2024</span>
            </div>
          </div>

          <div className="space-y-2">
            <Label>Last Login</Label>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Clock className="h-4 w-4"/>
              <span>Today at 10:30 AM</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
