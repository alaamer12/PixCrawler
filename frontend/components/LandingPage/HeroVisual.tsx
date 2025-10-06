'use client'

import React, {Fragment, memo, useCallback, useEffect, useState} from 'react'
import {Check, CheckCircle2, Database, Loader2, Search} from 'lucide-react'
import {AnimatePresence, motion} from 'framer-motion'
import { OptimizedNextImage } from '@/components/ui/OptimizedNextImage'
import { SimpleImageModal } from '@/components/ui/SimpleImageModal'

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

const categories = [
  {name: 'nature', id: 1},
  {name: 'architecture', id: 2},
  {name: 'technology', id: 3},
  {name: 'animals', id: 4},
  {name: 'food', id: 5},
  {name: 'travel', id: 6},
  {name: 'abstract', id: 7},
  {name: 'business', id: 8}
]

const ImageThumbnail = memo(({image, onClick}: { image: LoadedImage, onClick?: () => void }) => {
  const handleClick = () => {
    console.log('ImageThumbnail handleClick called for image:', image.id)
    onClick?.()
  }

  if (!image.loaded) {
    return (
      <div className="aspect-square bg-muted rounded-lg border border-border relative overflow-hidden group transition-opacity duration-300 animate-in fade-in">
        <div className="absolute inset-0 flex items-center justify-center">
          <Loader2 className="w-4 h-4 text-muted-foreground animate-spin"/>
        </div>
      </div>
    )
  }

  return (
    <div className="aspect-square bg-muted rounded-lg border border-border relative overflow-hidden group transition-opacity duration-300 animate-in fade-in">
      <OptimizedNextImage
        src={image.url}
        alt={`Dataset image ${image.id + 1}`}
        className="w-full h-full object-cover transition-all duration-500"
        onClick={handleClick}
        priority={image.id < 6}
      />
      <div className="absolute inset-0 bg-gradient-to-br from-primary/20 to-secondary/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"/>
    </div>
  )
})
ImageThumbnail.displayName = 'ImageThumbnail'

export const HeroVisual = memo(() => {
  const [mounted, setMounted] = useState(false)
  const [currentCategory, setCurrentCategory] = useState(categories[0])
  const [images, setImages] = useState<LoadedImage[]>([])
  const [galleryImages, setGalleryImages] = useState<GalleryImage[]>([])
  const [progress, setProgress] = useState(0)
  const [isBuilding, setIsBuilding] = useState(false)
  const [loadedCount, setLoadedCount] = useState(0)
  const [modalOpen, setModalOpen] = useState(false)
  const [currentImageIndex, setCurrentImageIndex] = useState(0)
  const [steps, setSteps] = useState<Step[]>([
    {label: 'Define Query', icon: Search, status: 'pending'},
    {label: 'Build Dataset', icon: Database, status: 'pending'},
    {label: 'Complete', icon: CheckCircle2, status: 'pending'}
  ])
  const [stats, setStats] = useState({sources: 0, quality: 0, time: 0})
  const [isResetting, setIsResetting] = useState(false)

  const totalImages = 24

  // Add shimmer animation
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

  // Prevent hydration mismatch
  useEffect(() => {
    setMounted(true)
  }, [])

  const buildDataset = useCallback(async () => {
    if (isBuilding || !mounted) return

    // Reset state
    setIsBuilding(true)
    setImages([])
    setGalleryImages([])
    setProgress(0)
    setLoadedCount(0)
    setStats({sources: 0, quality: 0, time: 0})

    // Random category
    const randomCategory = categories[Math.floor(Math.random() * categories.length)]
    setCurrentCategory(randomCategory)

    // Step 1: Define Query (active)
    setSteps([
      {label: 'Define Query', icon: Search, status: 'active'},
      {label: 'Build Dataset', icon: Database, status: 'pending'},
      {label: 'Complete', icon: CheckCircle2, status: 'pending'}
    ])
    await new Promise(resolve => setTimeout(resolve, 1200))

    // Step 1: Complete, Step 2: Active (with transition delay)
    setSteps([
      {label: 'Define Query', icon: Search, status: 'complete'},
      {label: 'Build Dataset', icon: Database, status: 'pending'},
      {label: 'Complete', icon: CheckCircle2, status: 'pending'}
    ])
    await new Promise(resolve => setTimeout(resolve, 400))

    setSteps([
      {label: 'Define Query', icon: Search, status: 'complete'},
      {label: 'Build Dataset', icon: Database, status: 'active'},
      {label: 'Complete', icon: CheckCircle2, status: 'pending'}
    ])

    // Initialize empty images
    const emptyImages: LoadedImage[] = Array.from({length: totalImages}, (_, i) => ({
      id: i,
      url: '',
      loaded: false
    }))
    setImages(emptyImages)

    let currentTime = 0
    let currentQuality = 0
    let currentSources = 0
    let statsActive = true
    // Target quality between 90-98
    const targetQuality = Math.floor(Math.random() * 9) + 90

    // Simulate stats building
    const statsInterval = setInterval(() => {
      if (!statsActive) return

      currentTime += 0.1
      currentQuality = Math.min(currentQuality + (Math.random() * 5 + 2), targetQuality)

      // Increment sources gradually
      if (currentSources < 3) {
        if (Math.random() > 0.6) {
          currentSources++
        }
      }

      setStats({
        sources: currentSources,
        quality: Math.round(currentQuality),
        time: currentTime
      })
    }, 200)

    // Load images progressively using Picsum
    const timestamp = Date.now()
    for (let i = 0; i < totalImages; i++) {
      const delay = Math.random() * 150 + 100
      await new Promise(resolve => setTimeout(resolve, delay))

      // Use Picsum with unique seed per image
      const seed = `${randomCategory.name}-${timestamp}-${i}`
      const imageUrl = `https://picsum.photos/seed/${seed}/200/200`

      setImages(prev => {
        const updated = [...prev]
        updated[i] = {id: i, url: imageUrl, loaded: true}
        return updated
      })

      // Update gallery images for NextImageGallery
      setGalleryImages(prev => [
        ...prev,
        {
          src: imageUrl,
          alt: `${randomCategory.name} dataset image ${i + 1}`,
          title: `${randomCategory.name} #${i + 1}`
        }
      ])

      setLoadedCount(i + 1)
      setProgress(Math.round(((i + 1) / totalImages) * 100))
    }

    statsActive = false
    clearInterval(statsInterval)

    // Step 2: Complete, Step 3: Active (with transition)
    setSteps([
      {label: 'Define Query', icon: Search, status: 'complete'},
      {label: 'Build Dataset', icon: Database, status: 'complete'},
      {label: 'Complete', icon: CheckCircle2, status: 'pending'}
    ])
    await new Promise(resolve => setTimeout(resolve, 400))

    setSteps([
      {label: 'Define Query', icon: Search, status: 'complete'},
      {label: 'Build Dataset', icon: Database, status: 'complete'},
      {label: 'Complete', icon: CheckCircle2, status: 'active'}
    ])

    // Random quality between 90-98
    const finalQuality = Math.floor(Math.random() * 9) + 90
    setStats({sources: 3, quality: finalQuality, time: currentTime})

    await new Promise(resolve => setTimeout(resolve, 800))

    // All complete
    setSteps([
      {label: 'Define Query', icon: Search, status: 'complete'},
      {label: 'Build Dataset', icon: Database, status: 'complete'},
      {label: 'Complete', icon: CheckCircle2, status: 'complete'}
    ])

    // Pause to show complete state
    await new Promise(resolve => setTimeout(resolve, 1200))

    // Start smooth reset
    setIsResetting(true)
    await new Promise(resolve => setTimeout(resolve, 600))

    // Clear data
    setProgress(0)
    setImages([])
    setGalleryImages([])
    setLoadedCount(0)
    setStats({sources: 0, quality: 0, time: 0})

    await new Promise(resolve => setTimeout(resolve, 400))

    // Reset steps
    setSteps([
      {label: 'Define Query', icon: Search, status: 'pending'},
      {label: 'Build Dataset', icon: Database, status: 'pending'},
      {label: 'Complete', icon: CheckCircle2, status: 'pending'}
    ])

    setIsResetting(false)
    setIsBuilding(false)

    await new Promise(resolve => setTimeout(resolve, 800))
    buildDataset()
  }, [isBuilding, mounted])

  useEffect(() => {
    if (!mounted) return

    const timer = setTimeout(() => {
      buildDataset()
    }, 1000)

    return () => {
      clearTimeout(timer)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mounted])

  // Show loading state during SSR
  if (!mounted) {
    return (
      <div className="relative w-full max-w-5xl mx-auto">
        <div className="bg-card border border-border rounded-xl shadow-lg overflow-hidden">
          <div className="border-b border-border p-4 bg-muted/30">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-red-500/80"/>
                <div className="w-3 h-3 rounded-full bg-yellow-500/80"/>
                <div className="w-3 h-3 rounded-full bg-green-500/80"/>
              </div>
              <div className="text-xs text-muted-foreground font-mono">pixcrawler.io/build</div>
            </div>
          </div>
          <div className="p-6 md:p-8 flex items-center justify-center h-96">
            <Loader2 className="w-8 h-8 text-muted-foreground animate-spin"/>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="relative w-full max-w-5xl mx-auto h-[800px] md:h-[850px]">
      <div className="hero-visual-bg border border-border rounded-xl shadow-lg overflow-hidden h-full flex flex-col">
        <div className="border-b border-border p-4 bg-muted/30 flex-shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500/80"/>
              <div className="w-3 h-3 rounded-full bg-yellow-500/80"/>
              <div className="w-3 h-3 rounded-full bg-green-500/80"/>
            </div>
            <div className="text-xs text-muted-foreground font-mono">pixcrawler.io/build</div>
          </div>
        </div>

        {/* Content area - Fixed height to prevent layout shift */}
        <div className="p-6  md:p-8 space-y-6 flex-1 overflow-hidden">
          {/* Query input simulation */}
          <div className="space-y-3">
            <div className="relative">
              <motion.input
                type="text"
                value={currentCategory.name}
                readOnly
                className="w-full px-4 py-3 bg-background border border-border rounded-lg text-sm focus:outline-none capitalize"
                animate={{opacity: isResetting ? 0.5 : 1}}
                transition={{duration: 0.3}}
              />
              <div className="absolute right-2 top-1/2 -translate-y-1/2 flex gap-2">
                {process.env.NODE_ENV === 'development' && galleryImages.length > 0 && (
                  <button
                    onClick={() => {
                      console.log('Test modal button clicked')
                      setCurrentImageIndex(0)
                      setModalOpen(true)
                    }}
                    className="px-2 py-1 bg-secondary text-secondary-foreground text-xs rounded"
                  >
                    Test Modal
                  </button>
                )}
                <div className="px-4 py-1.5 bg-primary text-primary-foreground text-sm font-medium rounded-md flex items-center gap-2">
                  {isBuilding && <Loader2 className="w-3 h-3 animate-spin"/>}
                  {isBuilding ? 'Building...' : 'Build'}
                </div>
              </div>
            </div>
          </div>

          {/* Progress bar */}
          {isBuilding && progress > 0 && (
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
          )}

          {/* Process flow */}
          <div className="flex items-center py-4 relative transition-opacity duration-400"
               style={{opacity: isResetting ? 0.3 : 1}}>
            {steps.map((step, i) => (
              <React.Fragment key={step.label}>
                <div className="flex flex-col items-center gap-2 relative z-10">
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
                  <div className="flex-1 h-1 mx-6 bg-muted rounded-full relative overflow-hidden">
                    <motion.div
                      className="absolute inset-0 bg-primary rounded-full"
                      initial={{scaleX: 0}}
                      animate={{
                        scaleX: steps[i + 1].status === 'complete' || steps[i + 1].status === 'active' ? 1 : 0
                      }}
                      transition={{duration: 0.7, ease: "easeOut"}}
                      style={{transformOrigin: 'left'}}
                    >
                      {steps[i + 1].status === 'active' && (
                        <div
                          className="absolute inset-0 bg-gradient-to-r from-transparent via-white/50 to-transparent animate-shimmer"/>
                      )}
                    </motion.div>
                  </div>
                )}
              </React.Fragment>
            ))}
          </div>

          {/* Results grid */}
          <div className="space-y-3 transition-opacity duration-400" style={{opacity: isResetting ? 0 : 1}}>
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-medium">Generated Dataset</h3>
              <span
                className="text-xs text-muted-foreground font-mono transition-opacity duration-300"
                style={{opacity: loadedCount > 0 ? 1 : 0.5}}
              >
								{loadedCount}/{totalImages} images
							</span>
            </div>
            <div className="grid grid-cols-6 md:grid-cols-8 gap-2 transition-all duration-300">
              {images.map((image, index) => (
                <ImageThumbnail 
                  key={image.id} 
                  image={image}
                  onClick={() => {
                    console.log('ImageThumbnail clicked:', {
                      imageId: image.id,
                      index,
                      loaded: image.loaded,
                      hasGalleryImage: !!galleryImages[index],
                      galleryImagesLength: galleryImages.length
                    })
                    if (image.loaded && galleryImages[index]) {
                      console.log('Opening modal for image:', index, galleryImages[index])
                      setCurrentImageIndex(index)
                      setModalOpen(true)
                    } else {
                      console.log('Cannot open modal - image not loaded or gallery image missing')
                    }
                  }}
                />
              ))}
            </div>
          </div>

          {/* Stats bar */}
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
        </div>
      </div>

      {/* Image Modal */}
      <SimpleImageModal
        isOpen={modalOpen}
        onClose={() => {
          console.log('Closing modal')
          setModalOpen(false)
        }}
        images={galleryImages}
        currentIndex={currentImageIndex}
        onIndexChange={setCurrentImageIndex}
      />
      
      {/* Debug info */}
      {process.env.NODE_ENV === 'development' && (
        <div className="fixed bottom-4 left-4 bg-black/80 text-white p-2 rounded text-xs z-50">
          Modal: {modalOpen ? 'Open' : 'Closed'} | Images: {galleryImages.length} | Index: {currentImageIndex}
        </div>
      )}

      {/* Subtle decorative elements */}
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
    </div>
  )
})
HeroVisual.displayName = 'HeroVisual'
