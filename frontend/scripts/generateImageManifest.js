/**
 * Script to generate a manifest of all images in the public/images directory
 * Run this script to create imageManifest.json
 */

const fs = require('fs')
const path = require('path')

const imagesDir = path.join(__dirname, '..', 'public', 'images')
const outputPath = path.join(__dirname, '..', 'public', 'imageManifest.json')

function scanImagesDirectory() {
  const manifest = {}

  try {
    const categories = fs.readdirSync(imagesDir, { withFileTypes: true })
      .filter(d => d.isDirectory())
      .map(d => d.name)

    categories.forEach(category => {
      const categoryPath = path.join(imagesDir, category)
      const images = []

      const subcategories = fs.readdirSync(categoryPath, { withFileTypes: true })
        .filter(d => d.isDirectory())

      subcategories.forEach(subcat => {
        const subcatPath = path.join(categoryPath, subcat.name)
        const files = fs.readdirSync(subcatPath)
          .filter(f => f.endsWith('.webp'))
          .sort()

        files.forEach(file => {
          images.push(`/images/${category}/${subcat.name}/${file}`)
        })
      })

      manifest[category] = {
        count: images.length,
        images: images
      }
    })

    fs.writeFileSync(outputPath, JSON.stringify(manifest, null, 2))
    console.log('✅ Image manifest generated successfully!')
    console.log(`📊 Categories found: ${Object.keys(manifest).length}`)
    Object.entries(manifest).forEach(([cat, data]) => {
      console.log(`   - ${cat}: ${data.count} images`)
    })
  } catch (error) {
    console.error('❌ Error generating manifest:', error)
    process.exit(1)
  }
}

scanImagesDirectory()
