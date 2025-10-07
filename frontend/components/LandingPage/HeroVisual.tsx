'use client'

import React, {memo, useCallback, useEffect, useState} from 'react'
import {Check, CheckCircle2, Database, Loader2, Search} from 'lucide-react'
import {AnimatePresence, motion} from 'framer-motion'
import {NextImage, ImageModal} from '@/components/Image'

// Types
interface Step {
  label: string
  icon: typeof Search
  status: 'pending' | 'active' | 'complete'
}

interface LoadedImage {
  id: number
  url: string
  loaded: boolean
}

interface GalleryImage {
  src: string
  alt: string
  title?: string
}

interface Category {
  name: string
  id: number
}

interface BuildStats {
  sources: number
  quality: number
  time: number
}

// Constants
const CATEGORIES: Category[] = [
  {name: 'nature', id: 1},
  {name: 'architecture', id: 2},
  {name: 'technology', id: 3},
  {name: 'animals', id: 4},
  {name: 'food', id: 5},
  {name: 'travel', id: 6},
  {name: 'abstract', id: 7},
  {name: 'business', id: 8}
]

const TOTAL_IMAGES = 24
const PRIORITY_THUMBNAIL_COUNT = 6

const STEP_CONFIGS: Omit<Step, 'status'>[] = [
  {label: 'Define Query', icon: Search},
  {label: 'Build Dataset', icon: Database},
  {label: 'Complete', icon: CheckCircle2}
]

const TIMING = {
  STEP_1_DURATION: 1200,
  STEP_TRANSITION: 400,
  STEP_3_COMPLETE: 800,
  FINAL_PAUSE: 1200,
  RESET_FADE: 600,
  RESET_DELAY: 400,
  INITIAL_DELAY: 1000,
  RESTART_DELAY: 800,
  IMAGE_DELAY_MIN: 100,
  IMAGE_DELAY_MAX: 150,
  STATS_INTERVAL: 200
} as const

const QUALITY_RANGE = {MIN: 90, MAX: 98} as const

// Utility Functions
const getRandomCategory = (): Category =>
  CATEGORIES[Math.floor(Math.random() * CATEGORIES.length)]

const getRandomQuality = (): number =>
  Math.floor(Math.random() * (QUALITY_RANGE.MAX - QUALITY_RANGE.MIN + 1)) + QUALITY_RANGE.MIN

const createImageUrl = (category: string, timestamp: number, index: number): string =>
  `https://picsum.photos/seed/${category}-${timestamp}-${index}/200/200`

const createGalleryImage = (url: string, category: string, index: number): GalleryImage => ({
  src: url,
  alt: `${category} dataset image ${index + 1}`,
  title: `${category} #${index + 1}`
})

const createEmptyImages = (count: number): LoadedImage[] =>
  Array.from({length: count}, (_, i) => ({
    id: i,
    url: '',
    loaded: false
  }))

const createSteps = (statuses: Step['status'][]): Step[] =>
  STEP_CONFIGS.map((config, i) => ({...config, status: statuses[i]}))

// Sub-components
const WindowControls = memo(() => (
  <div className="flex items-center gap-2">
    <div className="w-3 h-3 rounded-full bg-red-500/80"/>
    <div className="w-3 h-3 rounded-full bg-yellow-500/80"/>
    <div className="w-3 h-3 rounded-full bg-green-500/80"/>
  </div>
))
WindowControls.displayName = 'WindowControls'

const AddressBar = memo(() => (
  <div className="text-xs text-muted-foreground font-mono">
    pixcrawler.io/build
  </div>
))
AddressBar.displayName = 'AddressBar'

const LoadingState = memo(() => (
  <div className="relative w-full max-w-5xl mx-auto">
    <div className="bg-card border border-border rounded-xl shadow-lg overflow-hidden">
      <div className="border-b border-border p-4 bg-muted/30">
        <div className="flex items-center justify-between">
          <WindowControls/>
          <AddressBar/>
        </div>
      </div>
      <div className="p-6 md:p-8 flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 text-muted-foreground animate-spin"/>
      </div>
    </div>
  </div>
))
LoadingState.displayName = 'LoadingState'

const QueryInput = memo(({
                           category,
                           isResetting,
                           isBuilding,
                           onTestModal,
                           showTestButton
                         }: {
  category: string
  isResetting: boolean
  isBuilding: boolean
  onTestModal: () => void
  showTestButton: boolean
}) => (
  <div className="space-y-3">
    <div className="relative">
      <motion.input
        type="text"
        value={category}
        readOnly
        className="w-full px-4 py-3 bg-background border border-border rounded-lg text-sm focus:outline-none capitalize"
        animate={{opacity: isResetting ? 0.5 : 1}}
        transition={{duration: 0.3}}
      />
      <div className="absolute right-2 top-1/2 -translate-y-1/2 flex gap-2">
        {showTestButton && (
          <button
            onClick={onTestModal}
            className="px-2 py-1 bg-secondary text-secondary-foreground text-xs rounded"
          >
            Test Modal
          </button>
        )}
        <div
          className="px-4 py-1.5 bg-primary text-primary-foreground text-sm font-medium rounded-md flex items-center gap-2">
          {isBuilding && <Loader2 className="w-3 h-3 animate-spin"/>}
          {isBuilding ? 'Building...' : 'Build'}
        </div>
      </div>
    </div>
  </div>
))
QueryInput.displayName = 'QueryInput'

const ProgressBar = memo(({progress}: { progress: number }) => (
  <div className="space-y-2 animate-in fade-in slide-in-from-top-2 duration-300">
    <div className="flex justify-between text-xs">
      <span className="text-muted-foreground">Processing images...</span>
      <span className="font-mono font-medium">{progress}%</span>
    </div>
    <div className="h-1.5 bg-muted rounded-full overflow-hidden">
      <div
        className="h-full bg-primary transition-all duration-500 ease-out"
        style={{width: `${progress}%`}}
      />
    </div>
  </div>
))
ProgressBar.displayName = 'ProgressBar'

const StepIcon = memo(({step}: { step: Step }) => (
  <motion.div
    className={`w-12 h-12 rounded-full flex items-center justify-center relative ${
      step.status === 'complete'
        ? 'bg-primary border-2 border-primary'
        : step.status === 'active'
          ? 'bg-primary border-2 border-primary'
          : 'bg-muted border-2 border-border'
    }`}
    animate={{
      scale: step.status === 'complete' ? 1.1 : 1,
      boxShadow: step.status === 'active'
        ? '0 10px 25px -5px rgba(var(--primary), 0.5)'
        : step.status === 'complete'
          ? '0 10px 25px -5px rgba(var(--primary), 0.3)'
          : 'none'
    }}
    transition={{duration: 0.4, ease: "easeOut"}}
  >
    <AnimatePresence mode="wait">
      {step.status === 'complete' ? (
        <motion.div
          key="check"
          initial={{scale: 0, rotate: -180}}
          animate={{scale: 1, rotate: 0}}
          exit={{scale: 0, rotate: 180}}
          transition={{duration: 0.4, ease: "backOut"}}
        >
          <Check className="w-6 h-6 text-primary-foreground" strokeWidth={3}/>
        </motion.div>
      ) : (
        <motion.div
          key="icon"
          initial={{scale: 0}}
          animate={{scale: 1}}
          exit={{scale: 0}}
          transition={{duration: 0.3}}
        >
          <step.icon
            className={`w-6 h-6 transition-all duration-300 ${
              step.status === 'active'
                ? 'text-primary-foreground'
                : 'text-muted-foreground'
            }`}
            strokeWidth={2}
          />
        </motion.div>
      )}
    </AnimatePresence>
    <AnimatePresence>
      {step.status === 'active' && (
        <motion.div
          className="absolute inset-0 rounded-full border-2 border-primary"
          initial={{scale: 1, opacity: 0.75}}
          animate={{scale: 1.5, opacity: 0}}
          exit={{scale: 1, opacity: 0}}
          transition={{duration: 1, repeat: Infinity, ease: "easeOut"}}
        />
      )}
    </AnimatePresence>
  </motion.div>
))
StepIcon.displayName = 'StepIcon'

const StepConnector = memo(({isActive}: { isActive: boolean }) => (
  <div className="flex-1 h-1 mx-6 bg-muted rounded-full relative overflow-hidden">
    <motion.div
      className="absolute inset-0 bg-primary rounded-full"
      initial={{scaleX: 0}}
      animate={{scaleX: isActive ? 1 : 0}}
      transition={{duration: 0.7, ease: "easeOut"}}
      style={{transformOrigin: 'left'}}
    >
      {isActive && (
        <div
          className="absolute inset-0 bg-gradient-to-r from-transparent via-white/50 to-transparent animate-shimmer"/>
      )}
    </motion.div>
  </div>
))
StepConnector.displayName = 'StepConnector'

const ProcessFlow = memo(({steps, isResetting}: { steps: Step[]; isResetting: boolean }) => (
  <div
    className="flex items-center py-4 relative transition-opacity duration-400"
    style={{opacity: isResetting ? 0.3 : 1}}
  >
    {steps.map((step, i) => (
      <React.Fragment key={step.label}>
        <div className="flex flex-col items-center gap-2 relative z-10">
          <StepIcon step={step}/>
          <motion.span
            className={`text-xs font-medium text-center whitespace-nowrap ${
              step.status === 'pending' ? 'text-muted-foreground' : 'text-foreground'
            }`}
            animate={{
              fontWeight: step.status === 'pending' ? 500 : 600,
              scale: step.status === 'active' ? 1.05 : 1
            }}
            transition={{duration: 0.3}}
          >
            {step.label}
          </motion.span>
        </div>
        {i < steps.length - 1 && (
          <StepConnector
            isActive={steps[i + 1].status === 'complete' || steps[i + 1].status === 'active'}
          />
        )}
      </React.Fragment>
    ))}
  </div>
))
ProcessFlow.displayName = 'ProcessFlow'

const ImageThumbnail = memo(({
                               image,
                               onClick
                             }: {
  image: LoadedImage
  onClick?: () => void
}) => {
  if (!image.loaded) {
    return (
      <div
        className="aspect-square bg-muted rounded-lg border border-border relative overflow-hidden group transition-opacity duration-300 animate-in fade-in">
        <div className="absolute inset-0 flex items-center justify-center">
          <Loader2 className="w-4 h-4 text-muted-foreground animate-spin"/>
        </div>
      </div>
    )
  }

  return (
    <div
      className="aspect-square bg-muted rounded-lg border border-border relative overflow-hidden group transition-opacity duration-300 animate-in fade-in">
      <NextImage
        src={image.url}
        alt={`Dataset image ${image.id + 1}`}
        className="w-full h-full object-cover transition-all duration-500"
        onClick={onClick}
        priority={image.id < PRIORITY_THUMBNAIL_COUNT}
      />
      <div
        className="absolute inset-0 bg-gradient-to-br from-primary/20 to-secondary/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"/>
    </div>
  )
})
ImageThumbnail.displayName = 'ImageThumbnail'

const DatasetGrid = memo(({
                            images,
                            galleryImages,
                            loadedCount,
                            isResetting,
                            onImageClick
                          }: {
  images: LoadedImage[]
  galleryImages: GalleryImage[]
  loadedCount: number
  isResetting: boolean
  onImageClick: (index: number) => void
}) => (
  <div className="space-y-3 transition-opacity duration-400" style={{opacity: isResetting ? 0 : 1}}>
    <div className="flex items-center justify-between">
      <h3 className="text-sm font-medium">Generated Dataset</h3>
      <span
        className="text-xs text-muted-foreground font-mono transition-opacity duration-300"
        style={{opacity: loadedCount > 0 ? 1 : 0.5}}
      >
        {loadedCount}/{TOTAL_IMAGES} images
      </span>
    </div>
    <div className="grid grid-cols-6 md:grid-cols-8 gap-2 transition-all duration-300">
      {images.map((image, index) => (
        <ImageThumbnail
          key={image.id}
          image={image}
          onClick={() => {
            if (image.loaded && galleryImages[index]) {
              onImageClick(index)
            }
          }}
        />
      ))}
    </div>
  </div>
))
DatasetGrid.displayName = 'DatasetGrid'

const StatsBar = memo(({stats, isResetting}: { stats: BuildStats; isResetting: boolean }) => (
  <div
    className="flex items-center justify-between pt-4 border-t border-border text-xs text-muted-foreground transition-opacity duration-400"
    style={{opacity: isResetting ? 0.3 : 1}}
  >
    <span
      className="font-mono transition-opacity duration-300"
      style={{opacity: stats.sources > 0 ? 1 : 0.5}}
    >
      Sources: {stats.sources}/3 engines
    </span>
    <span
      className="font-mono transition-opacity duration-300"
      style={{opacity: stats.quality > 0 ? 1 : 0.5}}
    >
      Quality: {Math.round(stats.quality)}%
    </span>
    <span
      className="font-mono transition-opacity duration-300"
      style={{opacity: stats.time > 0 ? 1 : 0.5}}
    >
      Time: {stats.time.toFixed(1)}s
    </span>
  </div>
))
StatsBar.displayName = 'StatsBar'

const DecorativeBlobs = memo(() => (
  <>
    <motion.div
      className="absolute -top-8 -left-8 w-32 h-32 bg-primary/5 rounded-full blur-2xl -z-10"
      animate={{
        scale: [1, 1.2, 1],
        opacity: [0.5, 0.8, 0.5]
      }}
      transition={{
        duration: 4,
        repeat: Infinity,
        ease: "easeInOut"
      }}
    />
    <motion.div
      className="absolute -bottom-8 -right-8 w-32 h-32 bg-secondary/5 rounded-full blur-2xl -z-10"
      animate={{
        scale: [1, 1.3, 1],
        opacity: [0.5, 0.7, 0.5]
      }}
      transition={{
        duration: 5,
        repeat: Infinity,
        ease: "easeInOut",
        delay: 1
      }}
    />
  </>
))
DecorativeBlobs.displayName = 'DecorativeBlobs'

const DebugInfo = memo(({
                          modalOpen,
                          galleryImagesLength,
                          currentIndex
                        }: {
  modalOpen: boolean
  galleryImagesLength: number
  currentIndex: number
}) => {
  if (process.env.NODE_ENV !== 'development') return null

  return (
    <div className="fixed bottom-4 left-4 bg-black/80 text-white p-2 rounded text-xs z-50">
      Modal: {modalOpen ? 'Open' : 'Closed'} | Images: {galleryImagesLength} | Index: {currentIndex}
    </div>
  )
})
DebugInfo.displayName = 'DebugInfo'

// Custom Hooks
const useShimmerAnimation = () => {
  useEffect(() => {
    const style = document.createElement('style')
    style.textContent = `
      @keyframes shimmer {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
      }
      .animate-shimmer {
        animation: shimmer 1.5s infinite;
      }
    `
    document.head.appendChild(style)
    return () => {
      document.head.removeChild(style)
    }
  }, [])
}

const useStatsSimulation = (
  isBuilding: boolean,
  onUpdate: (stats: BuildStats) => void
) => {
  useEffect(() => {
    if (!isBuilding) return

    let currentTime = 0
    let currentQuality = 0
    let currentSources = 0
    let statsActive = true
    const targetQuality = getRandomQuality()

    const statsInterval = setInterval(() => {
      if (!statsActive) return

      currentTime += 0.1
      currentQuality = Math.min(currentQuality + (Math.random() * 5 + 2), targetQuality)

      if (currentSources < 3 && Math.random() > 0.6) {
        currentSources++
      }

      onUpdate({
        sources: currentSources,
        quality: Math.round(currentQuality),
        time: currentTime
      })
    }, TIMING.STATS_INTERVAL)

    return () => {
      statsActive = false
      clearInterval(statsInterval)
    }
  }, [isBuilding, onUpdate])
}

// Main Component
export const HeroVisual = memo(() => {
  const [mounted, setMounted] = useState(false)
  const [currentCategory, setCurrentCategory] = useState(CATEGORIES[0])
  const [images, setImages] = useState<LoadedImage[]>([])
  const [galleryImages, setGalleryImages] = useState<GalleryImage[]>([])
  const [progress, setProgress] = useState(0)
  const [isBuilding, setIsBuilding] = useState(false)
  const [loadedCount, setLoadedCount] = useState(0)
  const [modalOpen, setModalOpen] = useState(false)
  const [currentImageIndex, setCurrentImageIndex] = useState(0)
  const [steps, setSteps] = useState<Step[]>(createSteps(['pending', 'pending', 'pending']))
  const [stats, setStats] = useState<BuildStats>({sources: 0, quality: 0, time: 0})
  const [isResetting, setIsResetting] = useState(false)

  useShimmerAnimation()

  useEffect(() => {
    setMounted(true)
  }, [])

  const resetState = useCallback(() => {
    setImages([])
    setGalleryImages([])
    setProgress(0)
    setLoadedCount(0)
    setStats({sources: 0, quality: 0, time: 0})
  }, [])

  const buildDataset = useCallback(async () => {
    if (isBuilding || !mounted) return

    setIsBuilding(true)
    resetState()

    const randomCategory = getRandomCategory()
    setCurrentCategory(randomCategory)

    // Step 1: Define Query
    setSteps(createSteps(['active', 'pending', 'pending']))
    await new Promise(resolve => setTimeout(resolve, TIMING.STEP_1_DURATION))

    setSteps(createSteps(['complete', 'pending', 'pending']))
    await new Promise(resolve => setTimeout(resolve, TIMING.STEP_TRANSITION))

    // Step 2: Build Dataset
    setSteps(createSteps(['complete', 'active', 'pending']))
    setImages(createEmptyImages(TOTAL_IMAGES))

    // Load images progressively
    const timestamp = Date.now()
    for (let i = 0; i < TOTAL_IMAGES; i++) {
      const delay = Math.random() * (TIMING.IMAGE_DELAY_MAX - TIMING.IMAGE_DELAY_MIN) + TIMING.IMAGE_DELAY_MIN
      await new Promise(resolve => setTimeout(resolve, delay))

      const imageUrl = createImageUrl(randomCategory.name, timestamp, i)

      setImages(prev => {
        const updated = [...prev]
        updated[i] = {id: i, url: imageUrl, loaded: true}
        return updated
      })

      setGalleryImages(prev => [...prev, createGalleryImage(imageUrl, randomCategory.name, i)])
      setLoadedCount(i + 1)
      setProgress(Math.round(((i + 1) / TOTAL_IMAGES) * 100))
    }

    // Step 3: Complete
    setSteps(createSteps(['complete', 'complete', 'pending']))
    await new Promise(resolve => setTimeout(resolve, TIMING.STEP_TRANSITION))

    setSteps(createSteps(['complete', 'complete', 'active']))

    const finalQuality = getRandomQuality()
    setStats(prev => ({sources: 3, quality: finalQuality, time: prev.time}))

    await new Promise(resolve => setTimeout(resolve, TIMING.STEP_3_COMPLETE))

    setSteps(createSteps(['complete', 'complete', 'complete']))
    await new Promise(resolve => setTimeout(resolve, TIMING.FINAL_PAUSE))

    // Reset
    setIsResetting(true)
    await new Promise(resolve => setTimeout(resolve, TIMING.RESET_FADE))

    resetState()
    await new Promise(resolve => setTimeout(resolve, TIMING.RESET_DELAY))

    setSteps(createSteps(['pending', 'pending', 'pending']))
    setIsResetting(false)
    setIsBuilding(false)

    await new Promise(resolve => setTimeout(resolve, TIMING.RESTART_DELAY))
    buildDataset()
  }, [isBuilding, mounted, resetState])

  useStatsSimulation(isBuilding, setStats)

  useEffect(() => {
    if (!mounted) return

    const timer = setTimeout(() => {
      buildDataset()
    }, TIMING.INITIAL_DELAY)

    return () => clearTimeout(timer)
  }, [mounted, buildDataset])

  const handleImageClick = useCallback((index: number) => {
    setCurrentImageIndex(index)
    setModalOpen(true)
  }, [])

  const handleTestModal = useCallback(() => {
    if (galleryImages.length > 0) {
      setCurrentImageIndex(0)
      setModalOpen(true)
    }
  }, [galleryImages.length])

  if (!mounted) {
    return <LoadingState/>
  }

  return (
    <div className="relative w-full max-w-5xl mx-auto h-[800px] md:h-[850px]">
      <div className="hero-visual-bg border border-border rounded-xl shadow-lg overflow-hidden h-full flex flex-col">
        <div className="border-b border-border p-4 bg-muted/30 flex-shrink-0">
          <div className="flex items-center justify-between">
            <WindowControls/>
            <AddressBar/>
          </div>
        </div>

        <div className="p-6 md:p-8 space-y-6 flex-1 overflow-hidden">
          <QueryInput
            category={currentCategory.name}
            isResetting={isResetting}
            isBuilding={isBuilding}
            onTestModal={handleTestModal}
            showTestButton={process.env.NODE_ENV === 'development' && galleryImages.length > 0}
          />

          {isBuilding && progress > 0 && <ProgressBar progress={progress}/>}

          <ProcessFlow steps={steps} isResetting={isResetting}/>

          <DatasetGrid
            images={images}
            galleryImages={galleryImages}
            loadedCount={loadedCount}
            isResetting={isResetting}
            onImageClick={handleImageClick}
          />

          <StatsBar stats={stats} isResetting={isResetting}/>
        </div>
      </div>

      <ImageModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        images={galleryImages}
        currentIndex={currentImageIndex}
        onIndexChange={setCurrentImageIndex}
      />

      <DebugInfo
        modalOpen={modalOpen}
        galleryImagesLength={galleryImages.length}
        currentIndex={currentImageIndex}
      />

      <DecorativeBlobs/>
    </div>
  )
})
HeroVisual.displayName = 'HeroVisual'
