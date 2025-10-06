'use client'

import {useState} from 'react'
import {Button, GradientButton, IconButton, LoadingButton} from '@/components/ui/button'
import {AlertTriangle, ArrowRight, Check, Download, Heart, Info, Plus, Settings, Star, Trash2} from 'lucide-react'

export default function ButtonDemoPage() {
  const [loading, setLoading] = useState(false)

  const handleAsyncAction = async () => {
    setLoading(true)
    await new Promise(resolve => setTimeout(resolve, 2000))
    setLoading(false)
  }

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-4xl mx-auto space-y-12">
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold">Enhanced Button Component</h1>
          <p className="text-lg text-muted-foreground">
            Showcasing the advanced button system with color-awareness, loading states, and brand variants
          </p>
        </div>

        {/* Variants */}
        <section className="space-y-6">
          <h2 className="text-2xl font-semibold">Button Variants</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Button variant="default">Default</Button>
            <Button variant="secondary">Secondary</Button>
            <Button variant="outline">Outline</Button>
            <Button variant="ghost">Ghost</Button>
            <Button variant="link">Link</Button>
            <Button variant="destructive">Destructive</Button>
            <Button variant="success">Success</Button>
            <Button variant="warning">Warning</Button>
          </div>
        </section>

        {/* Brand Variant with Shimmer */}
        <section className="space-y-6">
          <h2 className="text-2xl font-semibold">Brand Variant (with Shimmer Effect)</h2>
          <div className="flex flex-wrap gap-4">
            <GradientButton size="sm">Small Brand</GradientButton>
            <GradientButton>Default Brand</GradientButton>
            <GradientButton size="lg">Large Brand</GradientButton>
            <GradientButton size="xl">Extra Large Brand</GradientButton>
          </div>
        </section>

        {/* Sizes */}
        <section className="space-y-6">
          <h2 className="text-2xl font-semibold">Button Sizes</h2>
          <div className="flex flex-wrap items-center gap-4">
            <Button size="sm">Small</Button>
            <Button size="default">Default</Button>
            <Button size="lg">Large</Button>
            <Button size="xl">Extra Large</Button>
          </div>
        </section>

        {/* Loading States */}
        <section className="space-y-6">
          <h2 className="text-2xl font-semibold">Loading States</h2>
          <div className="flex flex-wrap gap-4">
            <LoadingButton isLoading={loading} onClick={handleAsyncAction}>
              {loading ? 'Processing...' : 'Start Process'}
            </LoadingButton>
            <Button loading={true} loadingText="Saving...">Save</Button>
            <Button loading={true} variant="outline">Loading Outline</Button>
            <Button loading={true} variant="destructive">Deleting...</Button>
          </div>
        </section>

        {/* With Icons */}
        <section className="space-y-6">
          <h2 className="text-2xl font-semibold">Buttons with Icons</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <Button leftIcon={<Download className="w-4 h-4"/>}>
              Download
            </Button>
            <Button rightIcon={<ArrowRight className="w-4 h-4"/>}>
              Continue
            </Button>
            <Button
              leftIcon={<Plus className="w-4 h-4"/>}
              rightIcon={<ArrowRight className="w-4 h-4"/>}
            >
              Add & Continue
            </Button>
            <Button variant="outline" leftIcon={<Settings className="w-4 h-4"/>}>
              Settings
            </Button>
            <Button variant="destructive" leftIcon={<Trash2 className="w-4 h-4"/>}>
              Delete
            </Button>
            <Button variant="success" leftIcon={<Check className="w-4 h-4"/>}>
              Confirm
            </Button>
          </div>
        </section>

        {/* Icon Buttons */}
        <section className="space-y-6">
          <h2 className="text-2xl font-semibold">Icon Buttons</h2>
          <div className="flex flex-wrap gap-4">
            <IconButton icon={<Heart className="w-4 h-4"/>}/>
            <IconButton icon={<Star className="w-4 h-4"/>} variant="outline"/>
            <IconButton icon={<Settings className="w-4 h-4"/>} variant="secondary"/>
            <IconButton icon={<Trash2 className="w-4 h-4"/>} variant="destructive"/>
            <IconButton icon={<Plus className="w-4 h-4"/>} size="icon-sm"/>
            <IconButton icon={<Download className="w-4 h-4"/>} size="icon-lg"/>
          </div>
        </section>

        {/* Interactive States */}
        <section className="space-y-6">
          <h2 className="text-2xl font-semibold">Interactive States</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Button>Normal</Button>
            <Button className="hover:scale-105">Hover (scale)</Button>
            <Button disabled>Disabled</Button>
            <Button loading={true}>Loading</Button>
          </div>
        </section>

        {/* Contextual Usage */}
        <section className="space-y-6">
          <h2 className="text-2xl font-semibold">Contextual Usage Examples</h2>

          {/* Alert Actions */}
          <div className="bg-card border border-border rounded-lg p-6 space-y-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-warning"/>
              <h3 className="font-semibold">Confirm Deletion</h3>
            </div>
            <p className="text-muted-foreground">
              This action cannot be undone. Are you sure you want to delete this item?
            </p>
            <div className="flex gap-3">
              <Button variant="outline">Cancel</Button>
              <Button variant="destructive" leftIcon={<Trash2 className="w-4 h-4"/>}>
                Delete Permanently
              </Button>
            </div>
          </div>

          {/* Success Actions */}
          <div className="bg-card border border-border rounded-lg p-6 space-y-4">
            <div className="flex items-center gap-2">
              <Check className="w-5 h-5 text-success"/>
              <h3 className="font-semibold">Task Completed</h3>
            </div>
            <p className="text-muted-foreground">
              Your dataset has been successfully created and is ready for download.
            </p>
            <div className="flex gap-3">
              <Button variant="success" leftIcon={<Download className="w-4 h-4"/>}>
                Download Dataset
              </Button>
              <Button variant="outline">View Details</Button>
            </div>
          </div>

          {/* Info Actions */}
          <div className="bg-card border border-border rounded-lg p-6 space-y-4">
            <div className="flex items-center gap-2">
              <Info className="w-5 h-5 text-primary"/>
              <h3 className="font-semibold">Welcome to PixCrawler</h3>
            </div>
            <p className="text-muted-foreground">
              Get started by creating your first image dataset. It only takes a few minutes!
            </p>
            <div className="flex gap-3">
              <GradientButton
                leftIcon={<Plus className="w-4 h-4"/>}
                rightIcon={<ArrowRight className="w-4 h-4"/>}
              >
                Create First Dataset
              </GradientButton>
              <Button variant="ghost">Learn More</Button>
            </div>
          </div>
        </section>

        {/* Color Awareness Demo */}
        <section className="space-y-6">
          <h2 className="text-2xl font-semibold">Color Awareness & Accessibility</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Light Background */}
            <div className="bg-white p-6 rounded-lg border">
              <h3 className="font-semibold mb-4 text-black">Light Background</h3>
              <div className="space-y-3">
                <Button className="w-full">Primary Action</Button>
                <Button variant="outline" className="w-full">Secondary Action</Button>
                <Button variant="ghost" className="w-full">Tertiary Action</Button>
              </div>
            </div>

            {/* Dark Background */}
            <div className="bg-gray-900 p-6 rounded-lg border">
              <h3 className="font-semibold mb-4 text-white">Dark Background</h3>
              <div className="space-y-3">
                <Button className="w-full">Primary Action</Button>
                <Button variant="outline" className="w-full">Secondary Action</Button>
                <Button variant="ghost" className="w-full">Tertiary Action</Button>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}
