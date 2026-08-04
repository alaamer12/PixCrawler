

# PixCrawler

> ***Constructor Automatizado de Conjuntos de Datos de Imágenes para ML e Investigación***
> 

## 📋 Descripción General

PixCrawler es una plataforma SaaS potente y escalable que automatiza la creación de conjuntos de datos de imágenes de alta calidad para proyectos de aprendizaje automático, investigación y ciencia de datos. Transforma palabras clave en colecciones de imágenes organizadas, validadas y listas para usar con solo unos pocos clics.

### ✨ Características Principales

- 🤖 **Rastreo Inteligente** - Múltiples métodos de descubrimiento para una recopilación integral de imágenes
- 🔍 **Validación Inteligente** - Verificación automatizada de calidad e integridad
- 🗂️ **Organización Automática** - Jerarquías de carpetas estructuradas y generación de metadatos
- 🚀 **Procesamiento Paralelo** - Descargas y procesamiento concurrentes de alta velocidad
- 🔄 **Detección de Duplicados** - Deduplicación avanzada mediante hash perceptual y de contenido
- 📦 **Salida Multiformato** - Soporte para varios formatos de etiquetas (JSON, CSV, YAML, TXT)
- ⚡ **Almacenamiento Activo y en Caliente** - Niveles de almacenamiento optimizados para diferentes patrones de acceso
- 🎯 **Palabras Clave Impulsadas por IA** - Expansión y generación inteligente de términos de búsqueda

---

## 🎯 Casos de Uso

### 🔬 **Investigación y Academia**

- Crear conjuntos de datos personalizados para investigación en visión por computadora
- Generar conjuntos de entrenamiento equilibrados para proyectos académicos
- Producir conjuntos de datos de referencia para evaluación de modelos

### 🏢 **Empresas y Startups**

- Prototipado rápido de modelos de ML con datos personalizados
- Conjuntos de datos de imágenes de productos para aplicaciones de comercio electrónico
- Análisis de contenido visual para inteligencia empresarial

### 👨‍💻 **Desarrolladores Independientes**

- Proyectos personales de ML y experimentación
- Fines de aprendizaje y educación
- Proyectos de portafolio y demostración

---

## 🚀 Inicio Rápido - Sistema de Flujo Simple

```bash
# 1. Install
uv sync --all-extras
uv add --group dev poethepoet

# 2. Start Redis server (required)
redis-server

# 3. Start backend + worker
poe dev

# 4. Test
poe test-flow
```

Las imágenes se guardan en el directorio `datasets/`. API en http://127.0.0.1:8000/docs

### Prerrequisitos

- **Python**: 3.11 o superior
- **Redis**: Para la cola de tareas
- **Bun**: Última versión (administrador de paquetes principal para el frontend)
- **Redis**: 5.0 o superior
- **PostgreSQL**: 14 o superior (vía Supabase)

### Configuración del Entorno

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/yourusername/pixcrawler.git
   cd pixcrawler
   ```

2. **Configurar variables de entorno**
   
   Copie los archivos de entorno de ejemplo y configúrelos:
   ```bash
   # Root level (global settings)
   cp .env.example .env
   
   # Backend configuration
   cp backend/.env.example backend/.env
   
   # Frontend configuration
   cp frontend/.env.example frontend/.env
   ```
   
   Consulte [CONFIGURATION.md](./CONFIGURATION.md) para obtener una guía detallada de configuración.

3. **Instalar dependencias**
   
   ```bash
   # Backend (Python with UV)
   uv sync
   
   # Frontend (Bun)
   cd frontend
   bun install
   ```

4. **Configurar la base de datos**
   
   ```bash
   cd frontend
   bun run db:setup    # Create RLS policies
   bun run db:migrate  # Run migrations
   ```

5. **Iniciar el entorno de desarrollo**
   
   Utilice el script de inicio unificado para su plataforma:
   
   ```bash
   # Unix/Linux/Mac
   ./scripts/start-dev.sh
   
   # Windows PowerShell
   .\scripts\start-dev.ps1
   
   # Windows Command Prompt
   .\scripts\start-dev.cmd
   ```
   
   O inicie los servicios individualmente:
   
   ```bash
   # Terminal 1: Backend
   cd backend
   uv run uvicorn backend.main:app --reload
   
   # Terminal 2: Frontend
   cd frontend
   bun dev
   
   # Terminal 3: Redis
   redis-server
   
   # Terminal 4: Celery Worker
   celery -A celery_core.app worker --loglevel=info
   ```

6. **Acceder a la aplicación**
   - Frontend: http://localhost:3000
   - API de Backend: http://localhost:8000
   - Documentación de la API: http://localhost:8000/docs

### 1️⃣ **Configuración**

Cree la configuración de su conjunto de datos utilizando nuestra interfaz web intuitiva o el esquema JSON:

```json
{
  "name": "my_dataset",
  "categories": ["cats", "dogs", "birds"],
  "max_images_per_category": 1000,
  "engines": ["primary", "secondary", "tertiary"],
  "quality_filters": {
    "min_resolution": [224, 224],
    "formats": ["jpg", "png", "webp"]
  }
}

```

### 2️⃣ **Procesamiento**

Envíe su tarea a través de nuestro panel de control

### 3️⃣ **Descarga**

Obtenga su conjunto de datos procesado en formatos optimizados:

- **Versión Activa (Hot)**: ZIP de acceso rápido (disponible en minutos)
- **Versión en Caliente (Warm)**: 7z ultra comprimido (disponible en horas)

---

## 🏗️ Arquitectura

### 📊 **Pipeline de Procesamiento**

```mermaid
graph LR
    A[🔍 Discovery] --> B[📥 Download]
    B --> C[✅ Validation]
    C --> D[🔍 Deduplication]
    D --> E[📁 Organization]
    E --> F[📦 Compression]
    F --> G[☁️ Storage]

```

### 🔄 **Resumen del Flujo de Trabajo**

1. **Fase de Descubrimiento** 📡
    - Descubrimiento de imágenes en múltiples fuentes
    - Expansión inteligente de palabras clave
    - Validación y filtrado de URLs
2. **Fase de Procesamiento** ⚙️
    - Descargas concurrentes de imágenes
    - Verificaciones de integridad en tiempo real
    - Algoritmos avanzados de deduplicación
3. **Fase de Organización** 📚
    - Creación de directorios estructurados
    - Generación de metadatos
    - Creación de archivos de etiquetas
4. **Fase de Entrega** 🚚
    - Almacenamiento activo (acceso inmediato)
    - Almacenamiento en caliente (optimizado para costos)
    - Enlaces de descarga seguros

---

## 📚 Documentación

### 🔗 **Enlaces Rápidos**

- 📖 [Guía de Configuración](./CONFIGURATION.md) - Referencia completa de variables de entorno
- 🚀 [Guía de Despliegue](./DEPLOYMENT.md) - Instrucciones de despliegue en producción
- 🔧 [Documentación de la API](http://localhost:8000/docs) - Referencia interactiva de la API
- 🏗️ [Guía de Arquitectura](./backend/ARCHITECTURE.md) - Descripción general de la arquitectura del sistema
- 📊 [Informes de Cumplimiento](./docs/compilance/) - Documentación de cumplimiento de arquitectura

### 🛠️ **Recursos para Desarrolladores**

- 📊 Ejemplos de Jupyter
- 🔄 [Arquitectura de Reintento](./docs/RETRY_ARCHITECTURE.md) - Guía de estrategias de reintento
- 📝 [Guía de Registro](./docs/LOGGING_GUIDE.md) - Sistema de registro centralizado
- 🔀 [Guía de Flujos de Trabajo](./docs/WORKFLOWS_GUIDE.md) - Patrones de flujo de trabajo de Celery
- 📦 [Orquestación de Bloques](./docs/CHUNK_ORCHESTRATION_GUIDE.md) - Guía de procesamiento distribuido

---

## ⚙️ Guía de Configuración

PixCrawler utiliza un sistema de configuración de tres niveles:

1. **Nivel Raíz** (`.env`) - Configuración global del proyecto
   - Credenciales de Supabase (URL, clave de rol de servicio, clave anónima)
   - Cadenas de conexión de almacenamiento de Azure
   - Configuración global del entorno

2. **Nivel de Backend** (`backend/.env`) - Configuración específica del backend
   - Configuración del servidor (host, puerto, modo de depuración)
   - Conexión a la base de datos (PostgreSQL vía Supabase)
   - Configuración de caché Redis y limitador de velocidad
   - Configuración de la cola de tareas Celery
   - Configuración del proveedor de almacenamiento
   - Configuración de CORS

3. **Nivel de Frontend** (`frontend/.env`) - Configuración específica del frontend
   - Configuración del cliente de Supabase (URL, clave anónima)
   - URLs de puntos finales de la API
   - Integración de Lemon Squeezy (opcional)
   - Servicio de correo electrónico de Resend (opcional)
   - URLs de la aplicación

Para obtener opciones de configuración detalladas, consulte [CONFIGURATION.md](./CONFIGURATION.md).

---

## 🔧 Flujo de Trabajo de Desarrollo

### Ejecutar Pruebas

```bash
# Backend tests
cd backend
uv run pytest
uv run pytest --cov=backend --cov-report=html

# Frontend tests (when available)
cd frontend
bun test
```

### Calidad del Código

```bash
# Backend linting and formatting
cd backend
uv run ruff check .
uv run ruff format .

# Type checking
uv run mypy .

# Frontend linting
cd frontend
bun run lint
```

### Migraciones de Base de Datos

```bash
cd frontend

# Generate new migration
bun run db:generate

# Apply migrations
bun run db:migrate

# Open Drizzle Studio
bun run db:studio
```

### Desarrollo de API

- La documentación de la API se genera automáticamente en `/docs` (Swagger UI)
- Documentación alternativa en `/redoc`
- Colecciones de Postman disponibles en el directorio `postman/`

---

## 🚀 Despliegue en Producción

### Despliegue de Backend (Azure App Service)

1. **Establecer variables de entorno** en Azure Portal
   - Copie todas las variables de `backend/.env.example`
   - Establezca `PIXCRAWLER_ENVIRONMENT=production`
   - Configure las credenciales de Supabase
   - Configure las cadenas de conexión de almacenamiento de Azure

2. **Desplegar usando Azure CLI**
   ```bash
   az webapp up --name pixcrawler-backend --resource-group pixcrawler-rg
   ```

3. **Verificar el despliegue**
   - Compruebe el punto final de salud: `https://your-app.azurewebsites.net/health`
   - Revise los registros en Azure Monitor

### Despliegue de Frontend (Vercel)

1. **Conectar el repositorio** a Vercel
2. **Configurar variables de entorno** en el Panel de Vercel
   - Use los valores de `frontend/.env.example.production`
   - Establezca la URL y la clave anónima de Supabase
   - Configure la URL de la API para que apunte al backend
   - Agregue las claves de Lemon Squeezy (si usa pagos)
   - Agregue la clave API de Resend (si usa correo electrónico)

3. **Desplegar**
   ```bash
   cd frontend
   bun run build
   vercel --prod
   ```

### Alternativa: Azure Static Web Apps

1. **Crear Static Web App** en Azure Portal
2. **Configurar la compilación**
   - Comando de compilación: `bun run build`
   - Directorio de salida: `.next`
   - Ubicación de la app: `frontend`

3. **Establecer variables de entorno** en Azure Portal
4. **Desplegar a través de GitHub Actions** (configuración automática)

Para instrucciones detalladas de despliegue, consulte [DEPLOYMENT.md](./DEPLOYMENT.md).

---

## 🔍 Solución de Problemas

### Problemas Comunes

#### Error de Conexión a Redis

**Problema**: El backend no arranca con "Redis connection refused"

**Solución**:
```bash
# Check if Redis is running
redis-cli ping

# Start Redis if not running
redis-server

# For development, Redis failures are logged as warnings
# For production, ensure Redis is properly configured
```

#### Problemas de Conexión a la Base de Datos

**Problema**: "Could not connect to database"

**Solución**:
1. Verifique las credenciales de Supabase en los archivos `.env`
2. Compruebe el formato de la URL de la base de datos: `postgresql+asyncpg://user:pass@host:5432/db`
3. Asegúrese de que la configuración del grupo de conexiones sea adecuada para Supabase (5-10 conexiones)
4. Consulte el panel de Supabase para verificar los límites de conexión

#### Faltan Variables de Entorno del Frontend

**Problema**: "Missing required environment variable"

**Solución**:
1. Asegúrese de que todas las variables requeridas de `frontend/.env.example` estén configuradas
2. Reinicie el servidor de desarrollo de Next.js después de modificar los archivos `.env`
3. Consulte `frontend/lib/env.ts` para verificar errores de validación

#### El Trabajador de Celery No Procesa Tareas

**Problema**: Las tareas se quedan en estado pendiente

**Solución**:
```bash
# Check if Celery worker is running
celery -A celery_core.app inspect active

# Restart worker
celery -A celery_core.app worker --loglevel=info

# Check Redis connection
redis-cli ping
```

#### Puerto Ya en Uso

**Problema**: Error "Address already in use"

**Solución**:
```bash
# Find process using port 8000 (backend)
lsof -i :8000  # Unix/Mac
netstat -ano | findstr :8000  # Windows

# Kill the process or use a different port
uvicorn backend.main:app --reload --port 8001
```

### Obtener Ayuda

- Consulte [DEPLOYMENT.md](./DEPLOYMENT.md) para problemas específicos de despliegue
- Revise [CONFIGURATION.md](./CONFIGURATION.md) para problemas de configuración
- Abra un issue en GitHub para errores
- Contacte al soporte para problemas de producción

---

## 🌟 Beneficios Clave

### ⚡ **Velocidad y Eficiencia**

- Procese miles de imágenes en minutos
- Arquitectura de procesamiento paralelo
- Utilización optimizada de la red

### 🎯 **Garantía de Calidad**

- Pipelines de validación automatizados
- Manejo integral de errores
- Detección y eliminación de duplicados

### 💰 **Eficiencia en Costos**

- Modelo de precios por uso
- Niveles de almacenamiento optimizados
- Sin sobrecarga de infraestructura

### 🔒 **Seguro y Confiable**

- Seguridad de nivel empresarial
- SLA de disponibilidad del 99.9%
- Cumplimiento de privacidad de datos

---

## 🤝 Soporte y Comunidad

### 📞 **Obtener Ayuda**

- 📧 Soporte por correo electrónico
- 🐛 Informes de errores

### 🔄 **Mantente Actualizado**

- 📈 Registro de cambios

---

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia MIT - consulte el archivo LICENSE para más detalles.

---
