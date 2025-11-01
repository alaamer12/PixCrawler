# Custom API Documentation Styling

**Status:** ✅ Complete  
**Last Updated:** 2025-11-01

---

## Overview

The PixCrawler API documentation has been fully customized to match the frontend design system, providing a cohesive brand experience across the entire platform.

---

## 🎨 Design System Integration

### Color Palette

| Element | Light Mode | Dark Mode |
|---------|-----------|-----------|
| **Background** | `hsl(45, 20%, 88%)` | `hsl(210, 15%, 8%)` |
| **Foreground** | `hsl(210, 25%, 12%)` | `hsl(210, 10%, 90%)` |
| **Primary** | `hsl(210, 25%, 40%)` | `hsl(210, 20%, 50%)` |
| **Secondary** | `hsl(150, 20%, 45%)` | `hsl(150, 15%, 55%)` |
| **Card** | `hsl(50, 25%, 92%)` | `hsl(210, 15%, 12%)` |
| **Border** | `hsl(45, 15%, 78%)` | `hsl(210, 10%, 18%)` |

### Typography

- **Font Family**: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif
- **Code Font**: Monaco, Menlo, Consolas, monospace
- **Smoothing**: Antialiased for optimal readability

### Spacing & Borders

- **Border Radius**: `0.5rem` (consistent with frontend)
- **Container Padding**: `2rem`
- **Card Padding**: `1rem - 1.5rem`

---

## 📁 File Structure

```
backend/
├── static/
│   ├── swagger-ui-custom.css    # Custom Swagger UI theme
│   ├── swagger-ui.html           # Custom Swagger UI page
│   └── redoc.html                # Custom ReDoc page
└── main.py                       # FastAPI app with custom docs
```

---

## 🎯 Features Implemented

### 1. **Custom Swagger UI Theme**

**File:** `backend/static/swagger-ui-custom.css`

#### Key Features:
- ✅ HSL color variables matching frontend
- ✅ Dark mode support (auto-detects system preference)
- ✅ Custom scrollbar with gradient
- ✅ Branded text selection
- ✅ Smooth animations and transitions
- ✅ HTTP method color coding
- ✅ Enhanced buttons and inputs
- ✅ Custom code blocks
- ✅ Responsive design

#### HTTP Method Colors:
- **GET**: Primary blue (`hsl(210, 25%, 40%)`)
- **POST**: Success green (`hsl(150, 20%, 45%)`)
- **PUT**: Warning orange (`hsl(35, 60%, 60%)`)
- **DELETE**: Destructive red (`hsl(0, 50%, 55%)`)
- **PATCH**: Secondary teal (`hsl(150, 20%, 45%)`)

### 2. **Custom HTML Templates**

#### Swagger UI (`swagger-ui.html`)
- Custom header with gradient background
- PixCrawler branding and logo
- Version badge
- Loading screen with spinner
- Enhanced configuration:
  - Deep linking enabled
  - Request/response duration display
  - Operation ID display
  - Persistent authorization
  - Syntax highlighting (Monokai theme)

#### ReDoc (`redoc.html`)
- Minimal loading screen
- Clean, professional layout
- Automatic dark mode support
- Console branding

### 3. **FastAPI Configuration**

**File:** `backend/main.py`

#### Enhancements:
```python
FastAPI(
    title="PixCrawler API",
    description="🖼️ Automated Image Dataset Builder for ML/AI",
    version="1.0.0",
    contact={...},
    license_info={...},
    docs_url=None,        # Custom route
    redoc_url=None,       # Custom route
    openapi_url="/openapi.json",
)
```

#### Custom Routes:
- `/docs` - Custom Swagger UI
- `/redoc` - Custom ReDoc
- `/openapi.json` - OpenAPI schema
- `/static/*` - Static assets

---

## 🚀 Usage

### Accessing Documentation

1. **Swagger UI (Interactive)**
   ```
   http://localhost:8000/docs
   ```
   - Try out endpoints
   - Test authentication
   - View request/response examples

2. **ReDoc (Reference)**
   ```
   http://localhost:8000/redoc
   ```
   - Clean, readable format
   - Better for reference
   - Print-friendly

3. **OpenAPI JSON**
   ```
   http://localhost:8000/openapi.json
   ```
   - Raw OpenAPI specification
   - For client generation

### Development

Start the server:
```bash
cd backend
uv run uvicorn main:app --reload
```

The custom docs will be available immediately at `/docs` and `/redoc`.

---

## 🎨 Customization Guide

### Updating Colors

Edit `backend/static/swagger-ui-custom.css`:

```css
:root {
  --pc-primary: hsl(210, 25%, 40%);  /* Change primary color */
  --pc-secondary: hsl(150, 20%, 45%); /* Change secondary color */
  /* ... */
}
```

### Updating Header

Edit `backend/static/swagger-ui.html`:

```html
<div class="custom-header">
    <h1>🖼️ PixCrawler API</h1>
    <p>Your custom description</p>
    <span class="version-badge">v1.0.0</span>
</div>
```

### Adding Custom Branding

1. Add logo to `backend/static/`
2. Update HTML templates to reference logo
3. Adjust CSS for logo positioning

---

## 📊 Benefits

### For Developers
- **Consistent Experience**: Matches frontend design
- **Better UX**: Smooth animations, clear hierarchy
- **Dark Mode**: Automatic system preference detection
- **Readable**: Optimized typography and spacing

### For API Consumers
- **Professional**: Polished, branded documentation
- **Intuitive**: Clear HTTP method colors
- **Interactive**: Try endpoints directly
- **Comprehensive**: All endpoints documented

### For Branding
- **Cohesive**: Unified design across platform
- **Memorable**: Custom colors and gradients
- **Professional**: Production-ready appearance

---

## 🔧 Technical Details

### CSS Architecture

1. **Variables**: HSL color system for easy theming
2. **Selectors**: Specific Swagger UI class overrides
3. **Animations**: Smooth transitions and loading states
4. **Responsive**: Mobile-friendly breakpoints

### HTML Structure

1. **Loading Screen**: Prevents flash of unstyled content
2. **Custom Header**: Branded top section
3. **Swagger Container**: Standard Swagger UI integration
4. **Scripts**: Configuration and initialization

### FastAPI Integration

1. **Static Files**: Mounted at `/static`
2. **Custom Routes**: HTML responses for docs
3. **OpenAPI**: Standard JSON endpoint
4. **Middleware**: CORS and security headers

---

## 🐛 Troubleshooting

### Styles Not Loading

1. Check static files are mounted:
   ```python
   app.mount("/static", StaticFiles(directory="backend/static"), name="static")
   ```

2. Verify CSS file exists:
   ```
   backend/static/swagger-ui-custom.css
   ```

3. Clear browser cache (Ctrl+Shift+R)

### Dark Mode Not Working

1. Check system preferences
2. Verify CSS media query:
   ```css
   @media (prefers-color-scheme: dark) { ... }
   ```

### Custom HTML Not Showing

1. Verify file paths in `main.py`
2. Check file encoding (UTF-8)
3. Ensure routes are registered before `app.run()`

---

## 📚 Related Files

- `backend/api/v1/response_models.py` - Response schemas
- `backend/api/v1/router.py` - API router configuration
- `backend/api/v1/endpoints/*.py` - Individual endpoints
- `frontend/app/globals.css` - Frontend design system

---

## 🎯 Future Enhancements

### Potential Additions

1. **Custom Logo**
   - Add PixCrawler logo to header
   - Favicon customization

2. **Theme Switcher**
   - Manual dark/light mode toggle
   - Theme persistence

3. **Code Examples**
   - Multi-language code snippets
   - Copy-to-clipboard functionality

4. **API Playground**
   - Enhanced try-it-out features
   - Request history
   - Environment variables

5. **Analytics**
   - Track endpoint usage
   - Popular endpoints dashboard

---

**Status:** Production Ready ✅  
**Maintenance:** Update colors when frontend design system changes
