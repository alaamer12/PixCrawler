# Dataset Dashboard Components

This directory contains the components for the dataset dashboard interface, implementing the design from the wireframes.

## Components

### DatasetDashboard

Main dashboard component that orchestrates all other components. Features:

- Collapsible sidebar navigation
- Tab-based content switching
- Responsive layout

### DatasetTopBar

Top navigation bar with:

- Dataset name and status
- Action buttons (Settings, Download, Re-run)
- Status badge with completion info

### DatasetFilesystem

File tree explorer showing:

- Hierarchical folder structure
- File counts and sizes
- Expandable/collapsible folders
- File type icons

### DatasetGallery

Image gallery with:

- Grid and list view modes
- Search functionality
- Image metadata display
- Responsive grid layout

### DatasetOverview

Statistics and overview panel with:

- Key metrics cards
- Processing summary
- Validation results
- Chart placeholders for future implementation

### DatasetSettings

Configuration panel with:

- General information settings
- Storage tier configuration
- Export format options
- Access and sharing controls
- Danger zone for dataset deletion

## Usage

```tsx
import { DatasetDashboard } from '@/components/dataset/dashboard'

export default function DatasetPage() {
  return <DatasetDashboard datasetId="your-dataset-id" />
}
```

## Design

The components follow a flat, professional design similar to modern SaaS platforms like Resend and Auth0, using:

- Clean typography
- Subtle borders and shadows
- Consistent spacing
- Professional color scheme
- Responsive layout patterns
