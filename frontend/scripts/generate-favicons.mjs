#!/usr/bin/env node

/**
 * Favicon Generator Script
 * Generates all necessary favicon formats from PNG logo files
 *
 * Usage: node scripts/generate-favicons.mjs
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// Get __dirname equivalent in ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Dynamic imports for the libraries
const sharp = (await import('sharp')).default;
const toIco = (await import('to-ico')).default;

const INPUT_LOGO_PNG = path.join(__dirname, '../public/logo.png');
const OUTPUT_DIR = path.join(__dirname, '../public');

// Favicon configurations
const FAVICON_CONFIGS = [
  // Standard favicons
  { name: 'favicon-16x16.png', size: 16 },
  { name: 'favicon-32x32.png', size: 32 },
  { name: 'favicon-48x48.png', size: 48 },

  // Apple Touch Icons
  { name: 'apple-touch-icon-57x57.png', size: 57 },
  { name: 'apple-touch-icon-60x60.png', size: 60 },
  { name: 'apple-touch-icon-72x72.png', size: 72 },
  { name: 'apple-touch-icon-76x76.png', size: 76 },
  { name: 'apple-touch-icon-114x114.png', size: 114 },
  { name: 'apple-touch-icon-120x120.png', size: 120 },
  { name: 'apple-touch-icon-144x144.png', size: 144 },
  { name: 'apple-touch-icon-152x152.png', size: 152 },
  { name: 'apple-touch-icon-180x180.png', size: 180 },
  { name: 'apple-touch-icon.png', size: 180 },

  // Android/Chrome icons
  { name: 'android-chrome-36x36.png', size: 36 },
  { name: 'android-chrome-48x48.png', size: 48 },
  { name: 'android-chrome-72x72.png', size: 72 },
  { name: 'android-chrome-96x96.png', size: 96 },
  { name: 'android-chrome-144x144.png', size: 144 },
  { name: 'android-chrome-192x192.png', size: 192 },
  { name: 'android-chrome-256x256.png', size: 256 },
  { name: 'android-chrome-384x384.png', size: 384 },
  { name: 'android-chrome-512x512.png', size: 512 },

  // Microsoft tiles
  { name: 'mstile-70x70.png', size: 70 },
  { name: 'mstile-144x144.png', size: 144 },
  { name: 'mstile-150x150.png', size: 150 },
  { name: 'mstile-310x150.png', size: 310, height: 150 },
  { name: 'mstile-310x310.png', size: 310 },

  // Open Graph and social media
  { name: 'og-image.png', size: 1200, height: 630 },
  { name: 'twitter-card.png', size: 1200, height: 600 },

  // Additional modern formats
  { name: 'icon-192.png', size: 192 },
  { name: 'icon-512.png', size: 512 },
  { name: 'maskable-icon-192.png', size: 192 },
  { name: 'maskable-icon-512.png', size: 512 },
];

async function generateFavicons() {
  console.log('🎨 Generating favicons from PNG logo...\n');

  // Check if PNG logo exists
  if (!fs.existsSync(INPUT_LOGO_PNG)) {
    console.error(`❌ PNG logo file not found: ${INPUT_LOGO_PNG}`);
    console.error('Please ensure logo.png exists in the public directory.');
    process.exit(1);
  }

  console.log(`📁 Using PNG source: ${path.basename(INPUT_LOGO_PNG)}`);

  // Create output directory if it doesn't exist
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }

  let successCount = 0;
  let errorCount = 0;

  // Generate each favicon size
  for (const config of FAVICON_CONFIGS) {
    try {
      const outputPath = path.join(OUTPUT_DIR, config.name);
      const width = config.size;
      const height = config.height || config.size;

      // Special handling for maskable icons (add padding)
      const isMaskable = config.name.includes('maskable');
      const padding = isMaskable ? Math.floor(width * 0.1) : 0;

      await sharp(INPUT_LOGO_PNG)
        .resize(width - (padding * 2), height - (padding * 2), {
          fit: 'contain',
          background: { r: 0, g: 0, b: 0, alpha: 0 }
        })
        .extend({
          top: padding,
          bottom: padding,
          left: padding,
          right: padding,
          background: { r: 0, g: 0, b: 0, alpha: 0 }
        })
        .png()
        .toFile(outputPath);

      const paddingInfo = isMaskable ? ' (maskable with padding)' : '';
      console.log(`✅ Generated ${config.name} (${width}x${height})${paddingInfo}`);
      successCount++;
    } catch (error) {
      console.error(`❌ Failed to generate ${config.name}:`, error.message);
      errorCount++;
    }
  }

  // Generate proper ICO file with multiple sizes
  try {
    console.log('🔄 Generating favicon.ico with multiple sizes...');
    const icoSizes = [16, 32, 48];
    const icoBuffers = [];

    // Generate PNG buffers for each size
    for (const size of icoSizes) {
      const buffer = await sharp(INPUT_LOGO_PNG)
        .resize(size, size, {
          fit: 'contain',
          background: { r: 0, g: 0, b: 0, alpha: 0 }
        })
        .png()
        .toBuffer();
      icoBuffers.push(buffer);
    }

    // Convert PNG buffers to ICO format_
    const icoBuffer = await toIco(icoBuffers);

    // Write ICO file
    const icoPath = path.join(OUTPUT_DIR, 'favicon.ico');
    fs.writeFileSync(icoPath, icoBuffer);

    console.log('✅ Generated favicon.ico (16x16, 32x32, 48x48)');
    successCount++;
  } catch (error) {
    console.error('❌ Failed to generate favicon.ico:', error.message);
    errorCount++;
  }

  // Generate web app manifest
  await generateWebAppManifest();

  // Generate browserconfig.xml for Microsoft
  await generateBrowserConfig();

  console.log(`\n🎉 Favicon generation complete!`);
  console.log(`✅ Successfully generated: ${successCount} files`);
  if (errorCount > 0) {
    console.log(`❌ Failed to generate: ${errorCount} files`);
  }
  console.log('\n📝 All favicons generated from PNG source!');
}

async function generateWebAppManifest() {
  const manifest = {
    name: "PixCrawler",
    short_name: "PixCrawler",
    description: "AI-Powered Image Dataset Builder",
    start_url: "/",
    display: "standalone",
    background_color: "#ffffff",
    theme_color: "#4d6b8a",
    orientation: "portrait-primary",
    categories: ["developer", "productivity", "utilities"],
    lang: "en",
    dir: "ltr",
    icons: [
      {
        src: "/icon-192.png",
        sizes: "192x192",
        type: "image/png",
        purpose: "any"
      },
      {
        src: "/icon-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "any"
      },
      {
        src: "/maskable-icon-192.png",
        sizes: "192x192",
        type: "image/png",
        purpose: "maskable"
      },
      {
        src: "/maskable-icon-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "maskable"
      }
    ]
  };

  const manifestPath = path.join(OUTPUT_DIR, 'site.webmanifest');
  fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
  console.log('✅ Generated site.webmanifest');
}

async function generateBrowserConfig() {
  const browserConfig = `<?xml version="1.0" encoding="utf-8"?>
<browserconfig>
    <msapplication>
        <tile>
            <square70x70logo src="/mstile-70x70.png"/>
            <square150x150logo src="/mstile-150x150.png"/>
            <square310x310logo src="/mstile-310x310.png"/>
            <wide310x150logo src="/mstile-310x150.png"/>
            <TileColor>#4d6b8a</TileColor>
        </tile>
    </msapplication>
</browserconfig>`;

  const configPath = path.join(OUTPUT_DIR, 'browserconfig.xml');
  fs.writeFileSync(configPath, browserConfig);
  console.log('✅ Generated browserconfig.xml');
}

// Run the generator
try {
  await generateFavicons();
} catch (error) {
  console.error('❌ Favicon generation failed:', error);
  process.exit(1);
}
