'use client'

import {useEffect, useState, useDeferredValue} from 'react'
import {Button} from '@/components/ui/button'
import {Slider} from '@/components/ui/slider'
import {CodePreview} from './code-preview'
import {Sparkles, FolderOpen, Tag, Images} from 'lucide-react'
import type {DatasetConfig} from '@/app/welcome/welcome-flow'

interface ConfigureStepProps {
  userName: string
  config: DatasetConfig
  onConfigChange: (config: DatasetConfig) => void
  onNext: () => void
}

export function ConfigureStep({
                                userName,
                                config,
                                onConfigChange,
                                onNext,
                              }: ConfigureStepProps) {
  const [localConfig, setLocalConfig] = useState(config)
  const [categoriesInput, setCategoriesInput] = useState(config.categories.join(', '))
  const [isValidatingName, setIsValidatingName] = useState(false)
  const [isValidatingCategories, setIsValidatingCategories] = useState(false)

  useEffect(() => {
    onConfigChange(localConfig)
  }, [localConfig, onConfigChange])

  // Validate and debounce name
  useEffect(() => {
    if (!localConfig.name) return

    setIsValidatingName(true)
    const timer = setTimeout(() => {
      setIsValidatingName(false)
    }, 300)

    return () => clearTimeout(timer)
  }, [localConfig.name])

  // Debounce category parsing
  useEffect(() => {
    setIsValidatingCategories(true)
    const timer = setTimeout(() => {
      const categories = categoriesInput
        .split(',')
        .map(cat => cat.trim())
        .filter(cat => cat.length > 0)
      setLocalConfig(prev => ({...prev, categories}))
      setIsValidatingCategories(false)
    }, 150)

    return () => clearTimeout(timer)
  }, [categoriesInput])

  const handleNameChange = (name: string) => {
    setLocalConfig(prev => ({...prev, name}))
  }

  const handleCategoriesInputChange = (input: string) => {
    setCategoriesInput(input)
  }

  const handleImagesChange = (imagesPerCategory: number) => {
    setLocalConfig(prev => ({...prev, imagesPerCategory}))
  }

  const isNameValid = localConfig.name.length >= 2
  const areCategoriesValid = localConfig.categories.length > 0

  // Defer expensive renders for better performance
  const deferredCategories = useDeferredValue(localConfig.categories)
  const deferredConfig = useDeferredValue(localConfig)

  return (
    <div className="space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-700">
      {/* Welcome Message */}
      <div className="text-center space-y-4 relative">
        {/* Subtle background glow */}
        <div
          className="absolute inset-0 -z-10 bg-gradient-to-b from-primary/5 via-transparent to-transparent blur-3xl"/>

        <div
          className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-primary/10 to-purple-500/10 border border-primary/20 text-primary text-sm font-semibold mb-2 shadow-lg shadow-primary/10 hover:shadow-primary/20 transition-all duration-300 hover:scale-105">
          <Sparkles className="size-4 animate-pulse"/>
          Let's get started
        </div>
        <h1
          className="text-4xl md:text-6xl font-bold tracking-tight bg-gradient-to-br from-foreground via-foreground to-foreground/60 bg-clip-text text-transparent animate-in slide-in-from-top-4 duration-1000">
          Welcome, {userName}!
        </h1>
        <p
          className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto animate-in slide-in-from-top-6 duration-1000 delay-100">
          Build your first <span className="font-semibold text-foreground">AI-ready</span> image dataset in minutes
        </p>
      </div>

      {/* Configuration Form */}
      <div className="bg-card/50 backdrop-blur-sm border border-border/50 rounded-2xl shadow-xl p-6 md:p-8 space-y-6">
        <div className="space-y-6">
          {/* Dataset Name */}
          <div className="space-y-3 group/field">
            <div className="flex items-center gap-2">
              <div
                className="p-2 rounded-lg bg-primary/10 text-primary group-hover/field:bg-primary/15 transition-colors duration-300 group-hover/field:scale-110 transition-transform">
                <FolderOpen className="size-4"/>
              </div>
              <label htmlFor="dataset-name"
                     className="text-sm font-semibold group-hover/field:text-foreground transition-colors">
                Dataset Name
              </label>
            </div>
            <div className="relative">
              <input
                id="dataset-name"
                type="text"
                value={localConfig.name}
                onChange={(e) => handleNameChange(e.target.value)}
                className={`w-full px-4 py-3.5 pr-10 bg-background/80 border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary focus:shadow-lg focus:shadow-primary/10 transition-all placeholder:text-muted-foreground/60 hover:border-border/80 ${
                  localConfig.name && !isNameValid ? 'border-red-500' : 'border-border'
                }`}
                placeholder="my_first_dataset"
              />
              <div className="absolute right-3 top-1/2 -translate-y-1/2">
                {isValidatingName ? (
                  <div className="size-5 border-2 border-primary border-t-transparent rounded-full animate-spin"/>
                ) : localConfig.name && isNameValid ? (
                  <div className="text-emerald-500">
                    <svg className="size-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7"/>
                    </svg>
                  </div>
                ) : localConfig.name && !isNameValid ? (
                  <div className="text-red-500">
                    <svg className="size-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12"/>
                    </svg>
                  </div>
                ) : null}
              </div>
            </div>
            {localConfig.name && !isNameValid && (
              <p className="text-xs text-red-500 flex items-center gap-1.5">
                <span className="inline-block size-1 rounded-full bg-red-500"/>
                Name must be at least 2 characters
              </p>
            )}
            <p
              className="text-xs text-muted-foreground flex items-center gap-1.5 opacity-70 group-hover/field:opacity-100 transition-opacity">
              <span className="inline-block size-1 rounded-full bg-muted-foreground/40"/>
              Use lowercase letters, numbers, and underscores
            </p>
          </div>

          {/* Categories */}
          <div className="space-y-3 group/field">
            <div className="flex items-center gap-2">
              <div
                className="p-2 rounded-lg bg-blue-500/10 text-blue-600 dark:text-blue-400 group-hover/field:bg-blue-500/15 transition-all duration-300 group-hover/field:scale-110">
                <Tag className="size-4"/>
              </div>
              <label htmlFor="categories"
                     className="text-sm font-semibold group-hover/field:text-foreground transition-colors">
                Categories
              </label>
            </div>
            <div className="relative">
              <input
                id="categories"
                type="text"
                value={categoriesInput}
                onChange={(e) => handleCategoriesInputChange(e.target.value)}
                className={`w-full px-4 py-3.5 pr-10 bg-background/80 border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary focus:shadow-lg focus:shadow-primary/10 transition-all placeholder:text-muted-foreground/60 hover:border-border/80 ${
                  categoriesInput && !areCategoriesValid ? 'border-red-500' : 'border-border'
                }`}
                placeholder="cats, dogs, birds"
              />
              <div className="absolute right-3 top-1/2 -translate-y-1/2">
                {isValidatingCategories ? (
                  <div
                    className="size-5 border-2 border-blue-600 dark:border-blue-400 border-t-transparent rounded-full animate-spin"/>
                ) : areCategoriesValid ? (
                  <div className="text-blue-600 dark:text-blue-400">
                    <svg className="size-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7"/>
                    </svg>
                  </div>
                ) : categoriesInput ? (
                  <div className="text-red-500">
                    <svg className="size-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12"/>
                    </svg>
                  </div>
                ) : null}
              </div>
            </div>
            {categoriesInput && !areCategoriesValid && (
              <p className="text-xs text-red-500 flex items-center gap-1.5">
                <span className="inline-block size-1 rounded-full bg-red-500"/>
                Please add at least one category
              </p>
            )}
            {deferredCategories.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {deferredCategories.map((category, i) => (
                  <kbd key={i} className="px-2 py-1 text-xs font-mono bg-muted border border-border rounded shadow-sm">
                    {category}
                  </kbd>
                ))}
              </div>
            )}
            <div
              className="flex items-center justify-between opacity-70 group-hover/field:opacity-100 transition-opacity">
              <p className="text-xs text-muted-foreground flex items-center gap-1.5">
                <span className="inline-block size-1 rounded-full bg-muted-foreground/40"/>
                Separate with commas
              </p>
              <div className="flex items-center gap-1.5">
                <span className="text-xs font-bold text-blue-600 dark:text-blue-400 tabular-nums">
                  {localConfig.categories.length}
                </span>
                <span className="text-xs text-muted-foreground">
                  {localConfig.categories.length === 1 ? 'category' : 'categories'}
                </span>
              </div>
            </div>
          </div>

          {/* Images Per Category */}
          <div className="space-y-3 group/field">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div
                  className="p-2 rounded-lg bg-purple-500/10 text-purple-600 dark:text-purple-400 group-hover/field:bg-purple-500/15 transition-all duration-300 group-hover/field:scale-110">
                  <Images className="size-4"/>
                </div>
                <label htmlFor="image-count"
                       className="text-sm font-semibold group-hover/field:text-foreground transition-colors">
                  Images Per Category
                </label>
              </div>
              <div className="flex items-center gap-2">
                <span
                  className="text-2xl font-bold bg-gradient-to-br from-primary to-purple-600 bg-clip-text text-transparent tabular-nums">
                  {localConfig.imagesPerCategory}
                </span>
                <span className="text-xs text-muted-foreground">images</span>
              </div>
            </div>
            <div className="relative pt-2">
              <Slider
                id="image-count"
                min={10}
                max={1000}
                step={10}
                value={[localConfig.imagesPerCategory]}
                onValueChange={(values) => handleImagesChange(values[0])}
                className="w-full"
              />
              {/* Slider glow */}
              <div
                className="absolute inset-0 -z-10 bg-gradient-to-r from-primary/10 to-purple-500/10 blur-xl opacity-30"/>
            </div>
            <div
              className="flex items-center justify-between px-1 opacity-70 group-hover/field:opacity-100 transition-opacity">
              <p className="text-xs text-muted-foreground flex items-center gap-1.5">
                <span className="inline-block size-1 rounded-full bg-muted-foreground/40"/>
                More images = better training
              </p>
              <div
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-gradient-to-r from-primary/5 to-purple-500/5 border border-primary/10">
                <span className="text-xs font-bold text-primary tabular-nums">
                  {localConfig.imagesPerCategory * localConfig.categories.length}
                </span>
                <span className="text-xs text-muted-foreground">total</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Code Preview */}
      <CodePreview config={deferredConfig}/>

      {/* Next Button */}
      <Button
        onClick={onNext}
        variant="brand"
        size="lg"
        className="w-full group relative overflow-hidden shadow-xl hover:shadow-2xl hover:shadow-primary/25 transition-all duration-500"
        rightIcon={
          <span className="group-hover:translate-x-1 transition-transform duration-300">→</span>
        }
      >
        <span className="relative z-10 font-semibold">Continue to Testing</span>
        {/* Shimmer effect */}
        <div
          className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000"/>
        {/* Pulse glow */}
        <div
          className="absolute inset-0 bg-gradient-to-r from-primary/50 to-purple-600/50 opacity-0 group-hover:opacity-20 blur-xl transition-opacity duration-500"/>
      </Button>
    </div>
  )
}
