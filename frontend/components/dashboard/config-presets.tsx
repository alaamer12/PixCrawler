'use client'

import { ConfigSection } from './advanced-config-section'
import { 
  Cpu, 
  Brain, 
  HardDrive, 
  Shield, 
  Globe, 
  FileText,
  Package,
  Zap,
  Server,
  Cloud,
  Sparkles,
  Database,
  Lock,
  Activity
} from 'lucide-react'

// Export pre-configured sections for project configuration
export const projectConfigSections: ConfigSection[] = [
  {
    id: 'processing',
    title: 'Processing & Performance',
    description: 'Configure how your datasets are processed',
    icon: Cpu,
    options: [
      {
        id: 'parallel_processing',
        label: 'Parallel Processing',
        value: true,
        type: 'switch',
        description: 'Process multiple images simultaneously for faster completion',
        icon: Zap,
        impact: 'high'
      },
      {
        id: 'worker_threads',
        label: 'Worker Threads',
        value: 4,
        type: 'slider',
        min: 1,
        max: 16,
        step: 1,
        description: 'Number of concurrent processing threads',
        icon: Server,
        impact: 'high'
      },
      {
        id: 'batch_size',
        label: 'Batch Size',
        value: 50,
        type: 'slider',
        min: 10,
        max: 200,
        step: 10,
        unit: ' images',
        description: 'Images processed per batch',
        impact: 'medium'
      },
      {
        id: 'processing_priority',
        label: 'Processing Priority',
        value: 'balanced',
        type: 'select',
        options: [
          { value: 'speed', label: 'Speed Priority', description: 'Faster but uses more resources' },
          { value: 'balanced', label: 'Balanced', description: 'Optimal speed and resource usage' },
          { value: 'efficiency', label: 'Efficiency Priority', description: 'Lower resource usage' }
        ],
        impact: 'medium'
      },
      {
        id: 'retry_failed',
        label: 'Auto-Retry Failed Downloads',
        value: true,
        type: 'switch',
        description: 'Automatically retry failed image downloads',
        impact: 'low'
      },
      {
        id: 'max_retries',
        label: 'Maximum Retries',
        value: 3,
        type: 'slider',
        min: 1,
        max: 10,
        step: 1,
        description: 'Maximum retry attempts for failed downloads',
        impact: 'low'
      }
    ]
  },
  {
    id: 'ai_enhancement',
    title: 'AI Enhancement',
    description: 'Advanced AI-powered features',
    icon: Brain,
    options: [
      {
        id: 'smart_deduplication',
        label: 'Smart Deduplication',
        value: true,
        type: 'switch',
        description: 'AI-powered duplicate detection using perceptual hashing',
        icon: Sparkles,
        premium: true
      },
      {
        id: 'content_moderation',
        label: 'Content Moderation',
        value: 'strict',
        type: 'select',
        options: [
          { value: 'off', label: 'Disabled' },
          { value: 'moderate', label: 'Moderate' },
          { value: 'strict', label: 'Strict' }
        ],
        description: 'AI-based inappropriate content filtering',
        premium: true
      },
      {
        id: 'auto_tagging',
        label: 'Automatic Tagging',
        value: true,
        type: 'switch',
        description: 'Generate tags using computer vision',
        icon: Brain,
        experimental: true
      },
      {
        id: 'quality_scoring',
        label: 'Quality Scoring',
        value: true,
        type: 'switch',
        description: 'AI-based image quality assessment',
        experimental: true
      },
      {
        id: 'face_detection',
        label: 'Face Detection & Blurring',
        value: false,
        type: 'switch',
        description: 'Detect and optionally blur faces for privacy',
        premium: true
      },
      {
        id: 'object_detection',
        label: 'Object Detection',
        value: true,
        type: 'switch',
        description: 'Identify objects in images for better categorization',
        premium: true,
        experimental: true
      }
    ],
    collapsed: true
  },
  {
    id: 'storage',
    title: 'Storage & Delivery',
    description: 'Configure storage options and delivery methods',
    icon: HardDrive,
    options: [
      {
        id: 'storage_tier',
        label: 'Storage Tier',
        value: 'hot',
        type: 'select',
        options: [
          { value: 'hot', label: 'Hot Storage', description: 'Instant access, higher cost' },
          { value: 'warm', label: 'Warm Storage', description: 'Quick access, balanced cost' },
          { value: 'cold', label: 'Cold Storage', description: 'Slower access, lowest cost' }
        ],
        impact: 'low'
      },
      {
        id: 'compression',
        label: 'Compression Level',
        value: 85,
        type: 'slider',
        min: 60,
        max: 100,
        step: 5,
        unit: '%',
        description: 'Image compression quality',
        impact: 'medium'
      },
      {
        id: 'cdn_delivery',
        label: 'CDN Delivery',
        value: true,
        type: 'switch',
        description: 'Use global CDN for faster delivery',
        icon: Cloud,
        premium: true
      },
      {
        id: 'backup_enabled',
        label: 'Automatic Backups',
        value: true,
        type: 'switch',
        description: 'Enable automatic dataset backups',
        premium: true
      },
      {
        id: 'retention_days',
        label: 'Data Retention',
        value: 90,
        type: 'slider',
        min: 7,
        max: 365,
        step: 7,
        unit: ' days',
        description: 'How long to keep datasets',
        impact: 'low'
      }
    ],
    collapsed: true
  },
  {
    id: 'security',
    title: 'Security & Privacy',
    description: 'Security and privacy settings',
    icon: Shield,
    options: [
      {
        id: 'encryption_at_rest',
        label: 'Encryption at Rest',
        value: true,
        type: 'switch',
        description: 'Encrypt stored datasets',
        icon: Lock,
        premium: true
      },
      {
        id: 'private_datasets',
        label: 'Private Datasets',
        value: true,
        type: 'switch',
        description: 'Keep datasets private by default',
        impact: 'low'
      },
      {
        id: 'watermarking',
        label: 'Watermarking',
        value: false,
        type: 'switch',
        description: 'Add watermarks to downloaded images',
        premium: true
      },
      {
        id: 'access_logs',
        label: 'Access Logging',
        value: true,
        type: 'switch',
        description: 'Log all dataset access for audit',
        impact: 'low'
      },
      {
        id: 'ip_whitelist',
        label: 'IP Whitelisting',
        value: false,
        type: 'switch',
        description: 'Restrict access to specific IP addresses',
        premium: true
      }
    ],
    collapsed: true
  },
  {
    id: 'export',
    title: 'Export & Integration',
    description: 'Export formats and third-party integrations',
    icon: Package,
    options: [
      {
        id: 'export_formats',
        label: 'Export Formats',
        value: ['yolo', 'pascal'],
        type: 'multi-select',
        options: [
          { value: 'yolo', label: 'YOLO' },
          { value: 'pascal', label: 'Pascal VOC' },
          { value: 'csv', label: 'CSV' },
          { value: 'json', label: 'JSON' },
          { value: 'tfrecord', label: 'TFRecord' }
        ],
        description: 'Available export formats for datasets'
      },
      {
        id: 'auto_export',
        label: 'Auto-Export on Completion',
        value: false,
        type: 'switch',
        description: 'Automatically export when dataset is ready',
        impact: 'low'
      },
      {
        id: 'webhook_notifications',
        label: 'Webhook Notifications',
        value: true,
        type: 'switch',
        description: 'Send webhooks on dataset events',
        premium: true
      },
      {
        id: 'api_access',
        label: 'API Access',
        value: true,
        type: 'switch',
        description: 'Enable programmatic access via API',
        premium: true
      }
    ],
    collapsed: true
  },
  {
    id: 'monitoring',
    title: 'Monitoring & Alerts',
    description: 'Track performance and get notified',
    icon: Activity,
    options: [
      {
        id: 'email_notifications',
        label: 'Email Notifications',
        value: true,
        type: 'switch',
        description: 'Receive email updates on dataset progress'
      },
      {
        id: 'slack_integration',
        label: 'Slack Integration',
        value: false,
        type: 'switch',
        description: 'Send notifications to Slack',
        premium: true
      },
      {
        id: 'progress_webhooks',
        label: 'Progress Webhooks',
        value: false,
        type: 'switch',
        description: 'Send progress updates via webhooks',
        premium: true
      },
      {
        id: 'error_alerts',
        label: 'Error Alerts',
        value: true,
        type: 'switch',
        description: 'Get notified of processing errors'
      },
      {
        id: 'completion_alerts',
        label: 'Completion Alerts',
        value: true,
        type: 'switch',
        description: 'Get notified when datasets are ready'
      }
    ],
    collapsed: true
  }
]

// Default values for project configuration
export const defaultProjectConfigValues: Record<string, any> = {
  // Processing
  parallel_processing: true,
  worker_threads: 4,
  batch_size: 50,
  processing_priority: 'balanced',
  retry_failed: true,
  max_retries: 3,
  
  // AI Enhancement
  smart_deduplication: true,
  content_moderation: 'strict',
  auto_tagging: true,
  quality_scoring: true,
  face_detection: false,
  object_detection: true,
  
  // Storage
  storage_tier: 'hot',
  compression: 85,
  cdn_delivery: true,
  backup_enabled: true,
  retention_days: 90,
  
  // Security
  encryption_at_rest: true,
  private_datasets: true,
  watermarking: false,
  access_logs: true,
  ip_whitelist: false,
  
  // Export
  export_formats: ['coco', 'yolo', 'pascal'],
  auto_export: false,
  webhook_notifications: true,
  api_access: true,
  
  // Monitoring
  email_notifications: true,
  slack_integration: false,
  progress_webhooks: false,
  error_alerts: true,
  completion_alerts: true
}
