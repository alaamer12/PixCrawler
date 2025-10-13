# Validation Service API

A FastAPI-based REST API service for image validation with configurable validation levels.

## API Endpoints

### POST /api/v1/validation/analyze/
Analyze a single image for validation.

**Parameters:**
- `image` (file): Image file to validate
- `validation_level` (optional): Validation level (basic, standard, strict)

### POST /api/v1/validation/batch/
Batch validation of multiple images.

**Parameters:**
- `images` (files): Multiple image files to validate
- `validation_level` (optional): Validation level (basic, standard, strict)

### GET /api/v1/validation/results/{job_id}/
Get validation results for a batch job.

### GET /api/v1/validation/stats/{dataset_id}/
Get validation statistics for a dataset.

### PUT /api/v1/validation/level/
Change validation level for a dataset.

**Body:**
```json
{
  "dataset_id": "string",
  "validation_level": "basic|standard|strict"
}
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the service:
```bash
python app.py
```

The service will be available at `http://localhost:8000`

3. View interactive API documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Validation Levels

- **basic**: Minimal validation checks
- **standard**: Standard validation with moderate strictness
- **strict**: Comprehensive validation with high standards
