ALWAYS USE .venv, ie. `.venv\scripts\python <command>`


# PixCrawler Product Overview

PixCrawler is an automated image dataset builder SaaS platform designed for machine learning, research, and data science projects. The platform transforms keywords into organized, validated, and ready-to-use image collections.

## Core Value Proposition
- **Automated Dataset Creation**: Convert keywords into structured image datasets with AI-powered keyword expansion
- **Multi-Source Collection**: Intelligent crawling from multiple search engines (Google, Bing, Baidu, DuckDuckGo)
- **Quality Assurance**: Built-in validation, deduplication (perceptual & content hashing), and integrity checking
- **ML-Ready Output**: Generates datasets with proper labeling and metadata in multiple formats (JSON, CSV, YAML, TXT)
- **Enterprise-Grade Infrastructure**: Distributed task processing with Celery, Redis caching, and Azure storage

## Key Features

### Dataset Generation
- **AI-Powered Keyword Generation**: Automatic keyword expansion using GPT4Free when keywords aren't provided
- **Multi-Engine Crawling**: Parallel image discovery from Google, Bing, Baidu, and DuckDuckGo
- **Configurable Limits**: Control max images per category/keyword
- **Progress Tracking**: Real-time progress updates with caching for resume capability
- **Chunk-Based Processing**: Distributed processing with chunk tracking (total, active, completed, failed)

### Quality & Validation
- **Image Integrity Checks**: Automated validation of downloaded images
- **Duplicate Detection**: Advanced deduplication using perceptual hashing (imagehash) and content hashing
- **Format Validation**: Support for JPG, PNG, WebP with configurable quality filters
- **Resolution Filtering**: Minimum resolution requirements (e.g., 224x224 for ML)
- **Validation Levels**: Configurable integrity checking (basic, standard, strict)

### Organization & Export
- **Structured Directories**: Hierarchical organization by category and keyword
- **Multi-Format Labels**: Automatic label generation in TXT, JSON, CSV, and YAML formats
- **Metadata Generation**: Comprehensive metadata for each image (dimensions, format, hash, labels)
- **Compression Options**: ZIP for hot storage, 7z for warm storage (ultra-compressed)
- **Export Formats**: Multiple dataset export formats for different ML frameworks

### Storage & Delivery
- **Hot Storage**: Immediate access ZIP archives (available in minutes)
- **Warm Storage**: Cost-optimized 7z archives (available within hours)
- **Azure Integration**: Azure Blob Storage and Data Lake Gen2 support
- **Secure Downloads**: Time-limited secure download links
- **Local Development**: Filesystem-based storage for development

### User Management
- **Supabase Authentication**: Secure SSR authentication with email/password and OAuth
  - **No Custom JWT**: Uses Supabase Auth tokens exclusively
  - Frontend: Anon key + Row Level Security (RLS)
  - Backend: Service role key for admin operations
  - Token verification via `backend/services/supabase_auth.py`
- **User Profiles**: Extended profiles with onboarding, avatars, and role management
  - Automatically created via Supabase Auth trigger
  - Stored in `profiles` table (extends auth.users)
- **Project Organization**: Group crawl jobs into projects for better organization
- **API Keys**: Programmatic access with rate limiting and usage tracking
  - Hashed keys with prefix for security
  - Per-key rate limits and usage counters
- **Activity Logging**: Comprehensive audit trail of user actions
  - Tracks all CRUD operations on resources

### Billing & Credits
- **Credit System**: Pay-per-use credit-based billing
- **Usage Tracking**: Daily metrics for images processed, storage, API calls, bandwidth
- **Auto-Refill**: Automatic credit refill when balance drops below threshold
- **Monthly Limits**: Configurable monthly usage limits
- **Transaction History**: Complete billing history with detailed breakdowns

### Notifications
- **Multi-Channel**: Email, push, and SMS notification support
- **Customizable Preferences**: Granular control over notification types
- **Quiet Hours**: Configure do-not-disturb periods
- **Digest Options**: Daily, weekly, or real-time notification digests
- **Event Types**: Job completion, dataset ready, billing alerts, security notifications

### API & Integration
- **RESTful API**: Comprehensive REST API with OpenAPI documentation
- **Rate Limiting**: FastAPI-Limiter with Redis for API rate limiting
- **Pagination**: FastAPI-Pagination for efficient data retrieval
- **Webhooks**: Event-driven notifications for job status changes
- **Postman Collections**: Complete API testing collections with environments

## Target Users

### Researchers & Academia
- Custom datasets for computer vision research
- Balanced training sets for academic projects
- Benchmark datasets for model evaluation
- Reproducible research with versioned datasets

### Enterprise & Startups
- Rapid ML prototyping with custom data
- Product image datasets for e-commerce applications
- Visual content analysis for business intelligence
- Automated dataset generation for CI/CD pipelines

### Individual Developers
- Personal ML projects and experimentation
- Learning and educational purposes
- Portfolio and demonstration projects
- Hackathons and competitions

## Architecture

### Multi-Phase Processing Pipeline
1. **Discovery Phase** 📡
   - Multi-source image discovery from search engines
   - AI-powered keyword expansion and generation
   - URL validation and filtering
   - Duplicate URL detection

2. **Processing Phase** ⚙️
   - Distributed concurrent downloads via Celery workers
   - Real-time integrity checks with Pillow
   - Chunk-based processing for scalability
   - Progress tracking and caching

3. **Validation Phase** ✅
   - Image format and resolution validation
   - Perceptual hash-based duplicate detection
   - Content hash verification
   - Quality scoring and filtering

4. **Organization Phase** 📚
   - Structured directory creation (category/keyword hierarchy)
   - Metadata generation (JSON, CSV, YAML)
   - Label file creation in multiple formats
   - Dataset statistics and reporting

5. **Compression Phase** 📦
   - Hot storage: Fast ZIP compression for immediate access
   - Warm storage: Ultra-compressed 7z for cost optimization
   - Parallel compression with progress tracking
   - Checksum generation for integrity

6. **Delivery Phase** 🚚
   - Azure Blob Storage upload (hot tier)
   - Azure Data Lake archival (warm tier)
   - Secure time-limited download links
   - Notification delivery (email, push, SMS)

### Technology Stack
- **Backend**: FastAPI + Uvicorn for high-performance API
- **Frontend**: Next.js 15 + React 19 for modern web experience
  - **Package Manager**: Bun (primary) / npm (fallback only)
  - Centralized API client with error handling
  - Zod-based environment validation
- **Database**: **Shared Supabase PostgreSQL**
  - Single database for frontend + backend
  - Frontend: Drizzle ORM for type-safe queries
  - Backend: SQLAlchemy ORM synchronized with Drizzle schema
  - 10 tables managed by Drizzle migrations
- **Task Queue**: Celery + Redis for distributed processing
- **Storage**: Azure Blob Storage + Data Lake Gen2
- **Auth**: **Supabase Auth ONLY** (no custom JWT)
  - Frontend: Anon key + RLS policies
  - Backend: Service role key
- **Monitoring**: Comprehensive logging with Loguru
  - Azure Monitor integration for production
  - Structured logging across all packages

## Key Benefits

### Speed & Efficiency
- Process thousands of images in minutes with parallel processing
- Distributed architecture with Celery workers
- Optimized network utilization with concurrent downloads
- Resume capability for interrupted jobs

### Quality Assurance
- Automated validation pipelines with configurable levels
- Comprehensive error handling and retry logic
- Duplicate detection and removal (perceptual + content hashing)
- Integrity verification for all downloaded images

### Cost Effective
- Pay-per-use credit-based pricing model
- Optimized storage tiers (hot/warm) for cost savings
- No infrastructure overhead or maintenance
- Auto-refill with configurable thresholds

### Secure & Reliable
- Enterprise-grade security with Supabase Auth (no custom JWT)
- 99.9% uptime SLA with Azure infrastructure
- Data privacy compliance (GDPR, CCPA)
- Comprehensive audit logging
- Row Level Security (RLS) policies for data isolation

### Developer Friendly
- RESTful API with OpenAPI documentation
  - Custom Swagger UI at `/docs`
  - ReDoc alternative at `/redoc`
- Postman collections for easy testing (in `postman/` directory)
- SDK support (planned)
- Webhook integration for automation (planned)
- Comprehensive error messages and debugging
- Type-safe API client with interceptors (frontend)
- Centralized error handling with ApiError class

## Pricing Tiers (Planned)
- **Free Tier**: 1,000 images/month, 10GB storage, basic support
- **Pro Tier**: 50,000 images/month, 500GB storage, priority support
- **Enterprise**: Unlimited images, custom storage, dedicated support, SLA

## Roadmap
- **Phase 1** (Current): Core crawling, validation, and storage
  - ✅ Multi-engine crawling (Google, Bing, Baidu, DuckDuckGo)
  - ✅ AI-powered keyword generation (GPT4Free)
  - ✅ Duplicate detection (perceptual + content hashing)
  - ✅ Chunk-based distributed processing
  - ✅ Azure Blob Storage integration
  - ✅ Supabase Auth integration
  - ✅ Shared database architecture (Drizzle + SQLAlchemy)
- **Phase 2**: Advanced AI features (object detection, scene classification)
- **Phase 3**: SDK releases (Python, JavaScript, Go)
- **Phase 4**: Marketplace for pre-built datasets
- **Phase 5**: Collaborative features (team workspaces, sharing)
