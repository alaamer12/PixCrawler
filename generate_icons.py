import os
from PIL import Image, ImageOps

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_PUBLIC = os.path.join(BASE_DIR, 'frontend', 'public')
FRONTEND_APP = os.path.join(BASE_DIR, 'frontend', 'app')

LOGO_PATH = os.path.join(FRONTEND_PUBLIC, 'logo.png')

def generate_icons():
    if not os.path.exists(LOGO_PATH):
        print(f"Error: Logo not found at {LOGO_PATH}")
        return

    print(f"Opening logo from {LOGO_PATH}")
    img = Image.open(LOGO_PATH)

    # Ensure image is RGBA
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    # 1. Generate favicon.ico (16, 32, 48)
    print("Generating favicon.ico...")
    favicon_sizes = [(16, 16), (32, 32), (48, 48)]
    img.save(os.path.join(FRONTEND_PUBLIC, 'favicon.ico'), format='ICO', sizes=favicon_sizes)
    img.save(os.path.join(FRONTEND_APP, 'favicon.ico'), format='ICO', sizes=favicon_sizes)

    # 2. Generate apple-touch-icon.png (180x180)
    print("Generating apple-touch-icon.png...")
    apple_icon = img.resize((180, 180), Image.Resampling.LANCZOS)
    apple_icon.save(os.path.join(FRONTEND_PUBLIC, 'apple-touch-icon.png'))

    # 3. Generate android/manifest icons (192, 512)
    print("Generating manifest icons...")
    icon_192 = img.resize((192, 192), Image.Resampling.LANCZOS)
    icon_192.save(os.path.join(FRONTEND_PUBLIC, 'icon-192.png'))
    icon_192.save(os.path.join(FRONTEND_PUBLIC, 'android-chrome-192x192.png'))
    
    icon_512 = img.resize((512, 512), Image.Resampling.LANCZOS)
    icon_512.save(os.path.join(FRONTEND_PUBLIC, 'icon-512.png'))
    icon_512.save(os.path.join(FRONTEND_PUBLIC, 'android-chrome-512x512.png'))

    # 4. Generate OG Image (1200x630)
    # Create a background (dark theme)
    print("Generating OG images...")
    og_size = (1200, 630)
    bg_color = (9, 9, 11, 255) # #09090b
    og_img = Image.new('RGBA', og_size, bg_color)
    
    # Resize logo to fit in OG image (e.g. 400px height or width, keep aspect ratio)
    # Let's make it 50% of height or width
    logo_ratio = img.width / img.height
    target_height = 400
    target_width = int(target_height * logo_ratio)
    
    if target_width > 1000:
        target_width = 1000
        target_height = int(target_width / logo_ratio)
        
    resized_logo = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
    
    # Center the logo
    x = (og_size[0] - target_width) // 2
    y = (og_size[1] - target_height) // 2
    
    og_img.paste(resized_logo, (x, y), resized_logo)
    
    og_img.save(os.path.join(FRONTEND_PUBLIC, 'og-image.png'))
    og_img.save(os.path.join(FRONTEND_PUBLIC, 'twitter-card.png'))

    print("Done!")

if __name__ == "__main__":
    generate_icons()
