'use client'

import {useEffect, useState} from 'react'
import {Button} from '@/components/ui/button'
import {CodePreview} from './code-preview'
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

  useEffect(() => {
    onConfigChange(localConfig)
  }, [localConfig, onConfigChange])

  const handleNameChange = (name: string) => {
    setLocalConfig(prev => ({...prev, name}))
  }

  const handleCategoriesChange = (categoriesStr: string) => {
    const categories = categoriesStr
      .split(',')
      .map(cat => cat.trim())
      .filter(cat => cat.length > 0)
    setLocalConfig(prev => ({...prev, categories}))
  }

  const handleImagesChange = (imagesPerCategory: number) => {
    setLocalConfig(prev => ({...prev, imagesPerCategory}))
  }

  const categoriesString = localConfig.categories.join(', ')

  return (
    <div className="space-y-8">
      {/* Welcome Message */}
      <div className="text-center space-y-3">
        <h1 className="text-4xl md:text-5xl font-bold tracking-tight">
          Welcome to PixCrawler, {userName}!
        </h1>
        <p className="text-lg text-muted-foreground">
          Create your first dataset in 3 simple steps
        </p>
      </div>

      {/* Configuration Form */}
      <div className="bg-card border border-border rounded-xl shadow-lg p-8 space-y-6">
        <div className="space-y-6">
          <div className="space-y-2">
            <label htmlFor="dataset-name" className="text-sm font-medium">
              Dataset Name
            </label>
            <input
              id="dataset-name"
              type="text"
              value={localConfig.name}
              onChange={(e) => handleNameChange(e.target.value)}
              className="w-full px-4 py-3 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
              placeholder="my_first_dataset"
            />
            <p className="text-xs text-muted-foreground">
              Use lowercase letters, numbers, and underscores
            </p>
          </div>

          <div className="space-y-2">
            <label htmlFor="categories" className="text-sm font-medium">
              Categories
            </label>
            <input
              id="categories"
              type="text"
              value={categoriesString}
              onChange={(e) => handleCategoriesChange(e.target.value)}
              className="w-full px-4 py-3 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
              placeholder="cats, dogs, birds"
            />
            <p className="text-xs text-muted-foreground">
              Separate multiple categories with commas
            </p>
          </div>

          <div className="space-y-3">
            <label htmlFor="image-count" className="text-sm font-medium">
              Images Per Category
            </label>
            <div className="space-y-3">
              <input
                id="image-count"
                type="range"
                min="10"
                max="1000"
                step="10"
                value={localConfig.imagesPerCategory}
                onChange={(e) => handleImagesChange(parseInt(e.target.value))}
                className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer slider"
              />
              <div className="text-center">
                <span className="text-2xl font-bold text-primary">
                  {localConfig.imagesPerCategory}
                </span>
                <span className="text-sm text-muted-foreground ml-1">images</span>
              </div>
            </div>
            <p className="text-xs text-muted-foreground">
              More images = better model training
            </p>
          </div>
        </div>
      </div>

      {/* Code Preview */}
      <CodePreview config={localConfig}/>

      {/* Next Button */}
      <Button
        onClick={onNext}
        variant="brand"
        size="lg"
        className="w-full"
        rightIcon={<span>→</span>}
      >
        Configure Dataset
      </Button>
    </div>
  )
}
