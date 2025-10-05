# Data Flow

## Overview

This document illustrates the complete data flow through the PixCrawler system, from user input to final dataset delivery. The flow encompasses multiple processing stages with validation, transformation, and storage operations.

## High-Level Data Flow

The high-level data flow diagram provides an overview of the end-to-end pipeline in PixCrawler, organized into logical subgraphs: User Interface (input collection), API Layer (request handling), Job Management (orchestration), Processing Pipeline (core transformations), Storage System (tiered persistence), and Data Persistence (metadata tracking). Arrows depict the sequential progression of data, from configuration to distribution, with branches for monitoring, logging, and storage decisions. This structure underscores the system's modularity, allowing for parallel processing and efficient resource management across stages.

```mermaid
flowchart TD
    subgraph "User Interface"
        UI[Web Dashboard]
        CONFIG[Dataset Configuration]
    end

    subgraph "API Layer"
        API[Backend API]
        AUTH[Authentication]
        VALIDATE[Request Validation]
    end

    subgraph "Job Management"
        QUEUE[Job Queue<br/>Redis/Celery]
        ORCHESTRATOR[Job Orchestrator]
        MONITOR[Progress Monitor]
    end

    subgraph "Processing Pipeline"
        KEYWORDS[Keyword Generation<br/>AI-Powered]
        DISCOVERY[URL Discovery<br/>Multi-Engine Search]
        DOWNLOAD[Image Download<br/>Parallel Processing]
        VALIDATION[Image Validation<br/>Multi-Tier Strategy]
        DEDUP[Deduplication<br/>Hash-Based]
        LABELING[Label Generation<br/>AI Classification]
        ORGANIZATION[Dataset Organization<br/>Folder Structure]
    end

    subgraph "Storage System"
        TEMP[Temp Storage<br/>Processing Workspace]
        HOT[Hot Storage<br/>Immediate Access]
        WARM[Warm Storage<br/>Compressed Archive]
        CDN[CDN Distribution<br/>Global Access]
    end

    subgraph "Data Persistence"
        DB[(PostgreSQL<br/>Metadata & Config)]
        CACHE[(Redis<br/>Session & Cache)]
        LOGS[(Log Storage<br/>Audit Trail)]
    end

    UI --> CONFIG
    CONFIG --> API
    API --> AUTH
    AUTH --> VALIDATE
    VALIDATE --> QUEUE

    QUEUE --> ORCHESTRATOR
    ORCHESTRATOR --> KEYWORDS
    KEYWORDS --> DISCOVERY
    DISCOVERY --> DOWNLOAD
    DOWNLOAD --> VALIDATION
    VALIDATION --> DEDUP
    DEDUP --> LABELING
    LABELING --> ORGANIZATION

    DOWNLOAD --> TEMP
    ORGANIZATION --> HOT
    HOT --> WARM
    WARM --> CDN

    ORCHESTRATOR --> DB
    MONITOR --> DB
    VALIDATION --> DB
    ORCHESTRATOR --> CACHE
    MONITOR --> LOGS

```

## Detailed Processing Pipeline

### Phase 1: Configuration & Job Creation

This sequence diagram details the initial phase where users configure and initiate a dataset job. It traces interactions from the user through the web interface to the backend API, database storage, and job queuing. Key steps include configuration validation, job record creation, and asynchronous queuing, ensuring immediate feedback to the user via job status responses. This phase sets the foundation for scalable, trackable processing.

```mermaid
sequenceDiagram
    participant U as User
    participant UI as Web Interface
    participant API as Backend API
    participant DB as Database
    participant Q as Job Queue

    U->>UI: Configure Dataset
    UI->>UI: Validate Configuration
    UI->>API: POST /api/v1/datasets/
    API->>DB: Store Dataset Config
    API->>DB: Create Job Record
    API->>Q: Queue Processing Job
    Q-->>API: Job ID
    API-->>UI: Job Created Response
    UI-->>U: Show Job Status

```

### Phase 2: Keyword Generation & URL Discovery

The flowchart for Phase 2 illustrates the expansion and search process for gathering image URLs. It begins with user-provided keywords, enhanced by AI generation and variations, then branches to multiple search engines for diverse results. Subsequent aggregation, filtering, and deduplication ensure a clean queue for downloads. This phase emphasizes redundancy across engines to maximize coverage and quality of discovered content.

```mermaid
flowchart LR
    subgraph "Input Processing"
        KEYWORDS[Base Keywords<br/>User Provided]
        AI_GEN[AI Keyword Generation<br/>GPT/Claude Expansion]
        VARIATIONS[Search Variations<br/>Template Application]
    end

    subgraph "Search Engines"
        DDG[DuckDuckGo<br/>Primary Engine]
        BING[Bing Images<br/>Secondary Engine]
        GOOGLE[Google Images<br/>Tertiary Engine]
    end

    subgraph "URL Processing"
        COLLECT[URL Collection<br/>Aggregate Results]
        FILTER[URL Filtering<br/>Format & Size Checks]
        DEDUPE[URL Deduplication<br/>Remove Duplicates]
    end

    KEYWORDS --> AI_GEN
    AI_GEN --> VARIATIONS
    VARIATIONS --> DDG
    VARIATIONS --> BING
    VARIATIONS --> GOOGLE

    DDG --> COLLECT
    BING --> COLLECT
    GOOGLE --> COLLECT

    COLLECT --> FILTER
    FILTER --> DEDUPE
    DEDUPE --> DOWNLOAD_QUEUE[Download Queue]

```

### Phase 3: Image Download & Validation

This flowchart outlines the download and multi-tier validation in Phase 3, showing parallel downloading into temporary storage followed by sequential validation gates (fast, medium, slow). Quality controls like hashing, metadata extraction, and scoring feed into decision diamonds for acceptance or rejection. Rejected items trigger cleanup, while valid ones proceed, highlighting the system's efficiency in handling high-volume, error-prone downloads.

```mermaid
flowchart TD
    subgraph "Download Process"
        QUEUE[Download Queue<br/>Prioritized URLs]
        PARALLEL[Parallel Downloaders<br/>Concurrent Workers]
        TEMP_STORE[Temporary Storage<br/>Processing Workspace]
    end

    subgraph "Validation Pipeline"
        FAST[Fast Validation<br/>File Integrity]
        MEDIUM[Medium Validation<br/>Content Analysis]
        SLOW[Slow Validation<br/>AI-Powered Quality]
    end

    subgraph "Quality Control"
        HASH[Hash Generation<br/>SHA-256 + pHash]
        METADATA[Metadata Extraction<br/>EXIF + Properties]
        QUALITY[Quality Scoring<br/>0.0 - 1.0 Scale]
    end

    subgraph "Storage Decision"
        VALID{Valid Image?}
        DUPLICATE{Duplicate?}
        KEEP[Keep Image]
        REJECT[Reject Image]
    end

    QUEUE --> PARALLEL
    PARALLEL --> TEMP_STORE
    TEMP_STORE --> FAST

    FAST --> MEDIUM
    MEDIUM --> SLOW

    SLOW --> HASH
    HASH --> METADATA
    METADATA --> QUALITY

    QUALITY --> VALID
    VALID -->|Yes| DUPLICATE
    VALID -->|No| REJECT
    DUPLICATE -->|No| KEEP
    DUPLICATE -->|Yes| REJECT

    KEEP --> PROCESSED[Processed Images]
    REJECT --> CLEANUP[Cleanup & Log]

```

### Phase 4: Dataset Organization & Labeling

The Phase 4 flowchart depicts the transformation of processed images into a structured dataset. It flows from categorization into hierarchical folders, through AI-driven labeling with confidence checks, to generating multiple format outputs and assembly artifacts like manifests and reports. This phase ensures the dataset is not only organized but also enriched with metadata for downstream usability in machine learning workflows.

```mermaid
flowchart LR
    subgraph "Organization Process"
        PROCESSED[Processed Images]
        CATEGORIZE[Categorization<br/>Keyword-Based Folders]
        STRUCTURE[Directory Structure<br/>Hierarchical Layout]
    end

    subgraph "Labeling System"
        AI_LABEL[AI Labeling<br/>Computer Vision]
        CONFIDENCE[Confidence Scoring<br/>Label Reliability]
        FORMATS[Multiple Formats<br/>JSON, CSV, YAML, TXT]
    end

    subgraph "Final Assembly"
        MANIFEST[Dataset Manifest<br/>Complete File List]
        METADATA_FILE[Metadata Files<br/>Statistics & Info]
        VALIDATION_REPORT[Validation Report<br/>Quality Analysis]
    end

    PROCESSED --> CATEGORIZE
    CATEGORIZE --> STRUCTURE
    STRUCTURE --> AI_LABEL

    AI_LABEL --> CONFIDENCE
    CONFIDENCE --> FORMATS

    FORMATS --> MANIFEST
    MANIFEST --> METADATA_FILE
    METADATA_FILE --> VALIDATION_REPORT

    VALIDATION_REPORT --> FINAL[Final Dataset]

```

### Phase 5: Storage & Distribution

This final flowchart illustrates the tiered storage progression and distribution mechanisms in Phase 5. From the assembled dataset, data moves through hot, warm, and archive tiers, with CDN integration for secure, resumable downloads. Parallel cleanup and metrics collection ensure resource efficiency and auditability, completing the pipeline with optimized accessibility and cost management.

```mermaid
flowchart TD
    subgraph "Storage Tiers"
        FINAL[Final Dataset]
        HOT[Hot Storage<br/>Immediate Access<br/>Uncompressed ZIP]
        WARM[Warm Storage<br/>Cost-Optimized<br/>7z Compression]
        ARCHIVE[Archive Storage<br/>Long-term<br/>Cold Storage]
    end

    subgraph "Distribution"
        CDN[CDN Distribution<br/>Global Edge Locations]
        SECURE[Secure URLs<br/>Time-Limited Access]
        DOWNLOAD[Download Manager<br/>Resume Support]
    end

    subgraph "Cleanup Process"
        TEMP_CLEANUP[Temp File Cleanup<br/>Processing Workspace]
        LOG_ARCHIVE[Log Archival<br/>Audit Trail]
        METRICS[Metrics Collection<br/>Performance Data]
    end

    FINAL --> HOT
    HOT --> WARM
    WARM --> ARCHIVE

    HOT --> CDN
    WARM --> CDN
    CDN --> SECURE
    SECURE --> DOWNLOAD

    FINAL --> TEMP_CLEANUP
    TEMP_CLEANUP --> LOG_ARCHIVE
    LOG_ARCHIVE --> METRICS

```