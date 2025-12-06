import { boolean, integer, jsonb, pgTable, serial, text, timestamp, uuid, varchar, numeric, time, check, index, unique } from 'drizzle-orm/pg-core';
import { relations } from 'drizzle-orm';

// User profiles table (extends Supabase auth.users)
export const profiles = pgTable('profiles', {
  id: uuid('id').primaryKey(), // References auth.users.id
  email: varchar('email', { length: 255 }).notNull().unique(),
  fullName: varchar('full_name', { length: 100 }),
  avatarUrl: text('avatar_url'),
  role: varchar('role', { length: 20 }).notNull().default('user'),
  onboardingCompleted: boolean('onboarding_completed').notNull().default(false),
  onboardingCompletedAt: timestamp('onboarding_completed_at'),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  updatedAt: timestamp('updated_at').notNull().defaultNow(),
});

// Projects table for organizing image crawling tasks
export const projects = pgTable('projects', {
  id: serial('id').primaryKey(),
  name: varchar('name', { length: 100 }).notNull(),
  description: text('description'),
  userId: uuid('user_id')
    .notNull()
    .references(() => profiles.id),
  status: varchar('status', { length: 20 }).notNull().default('active'),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  updatedAt: timestamp('updated_at').notNull().defaultNow(),
});

// Crawl jobs table for tracking image crawling tasks with chunk tracking
export const crawlJobs = pgTable('crawl_jobs', {
  id: serial('id').primaryKey(),
  projectId: integer('project_id')
    .notNull()
    .references(() => projects.id),
  name: varchar('name', { length: 100 }).notNull(),
  keywords: jsonb('keywords').notNull(), // Array of search keywords
  maxImages: integer('max_images').notNull().default(1000),
  status: varchar('status', { length: 20 }).notNull().default('pending'),
  progress: integer('progress').notNull().default(0),
  totalImages: integer('total_images').notNull().default(0),
  downloadedImages: integer('downloaded_images').notNull().default(0),
  validImages: integer('valid_images').notNull().default(0),
  // Chunk tracking fields
  totalChunks: integer('total_chunks').notNull().default(0),
  activeChunks: integer('active_chunks').notNull().default(0),
  completedChunks: integer('completed_chunks').notNull().default(0),
  failedChunks: integer('failed_chunks').notNull().default(0),
  taskIds: jsonb('task_ids').notNull().default([]),
  startedAt: timestamp('started_at'),
  completedAt: timestamp('completed_at'),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  updatedAt: timestamp('updated_at').notNull().defaultNow(),
});

// Images table for storing crawled image metadata
export const images = pgTable('images', {
  id: serial('id').primaryKey(),
  crawlJobId: integer('crawl_job_id')
    .notNull()
    .references(() => crawlJobs.id),
  originalUrl: text('original_url').notNull(),
  filename: varchar('filename', { length: 255 }).notNull(),
  storageUrl: text('storage_url'), // Supabase Storage URL
  width: integer('width'),
  height: integer('height'),
  fileSize: integer('file_size'),
  format: varchar('format', { length: 10 }),
  hash: varchar('hash', { length: 64 }), // For duplicate detection
  isValid: boolean('is_valid').notNull().default(true),
  isDuplicate: boolean('is_duplicate').notNull().default(false),
  labels: jsonb('labels'), // AI-generated labels
  metadata: jsonb('metadata'), // Additional image metadata
  downloadedAt: timestamp('downloaded_at').notNull().defaultNow(),
  createdAt: timestamp('created_at').notNull().defaultNow(),
});

// Datasets table (sync with backend models)
export const datasets = pgTable('datasets', {
  id: serial('id').primaryKey(),
  userId: uuid('user_id').notNull().references(() => profiles.id, { onDelete: 'cascade' }),
  crawlJobId: integer('crawl_job_id').references(() => crawlJobs.id, { onDelete: 'set null' }),
  name: varchar('name', { length: 100 }).notNull(),
  description: text('description'),
  keywords: jsonb('keywords').notNull(),
  searchEngines: jsonb('search_engines').notNull(),
  maxImages: integer('max_images').notNull().default(100),
  status: varchar('status', { length: 20 }).notNull().default('pending'),
  progress: integer('progress').notNull().default(0),
  imagesCollected: integer('images_collected').notNull().default(0),
  downloadUrl: text('download_url'),
  errorMessage: text('error_message'),
  storageTier: varchar('storage_tier', { length: 20 }).notNull().default('hot'),
  archivedAt: timestamp('archived_at', { withTimezone: true }),
  lastAccessedAt: timestamp('last_accessed_at', { withTimezone: true }).notNull().defaultNow(),
  createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(),
  updatedAt: timestamp('updated_at', { withTimezone: true }).notNull().defaultNow(),
});

// Dataset Versions table for history tracking
export const datasetVersions = pgTable('dataset_versions', {
  id: serial('id').primaryKey(),
  datasetId: integer('dataset_id').notNull().references(() => datasets.id, { onDelete: 'cascade' }),
  versionNumber: integer('version_number').notNull(),
  keywords: jsonb('keywords').notNull(),
  searchEngines: jsonb('search_engines').notNull(),
  maxImages: integer('max_images').notNull(),
  crawlJobId: integer('crawl_job_id').references(() => crawlJobs.id, { onDelete: 'set null' }),
  changeSummary: text('change_summary'),
  createdBy: uuid('created_by').references(() => profiles.id, { onDelete: 'set null' }),
  createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(),
}, (table) => {
  return {
    datasetVersionIdx: index('ix_dataset_versions_dataset_version').on(table.datasetId, table.versionNumber),
  };
});

// Activity logs for tracking user actions
export const activityLogs = pgTable('activity_logs', {
  id: serial('id').primaryKey(),
  userId: uuid('user_id').references(() => profiles.id),
  action: text('action').notNull(),
  resourceType: varchar('resource_type', { length: 50 }),
  resourceId: varchar('resource_id', { length: 50 }),
  metadata: jsonb('metadata'),
  timestamp: timestamp('timestamp').notNull().defaultNow(),
});

// API Keys table for programmatic access
export const apiKeys = pgTable('api_keys', {
  id: uuid('id').primaryKey().defaultRandom(),
  userId: uuid('user_id')
    .notNull()
    .references(() => profiles.id),
  name: varchar('name', { length: 200 }).notNull(),
  keyHash: varchar('key_hash', { length: 255 }).notNull().unique(),
  keyPrefix: varchar('key_prefix', { length: 20 }).notNull(),
  status: varchar('status', { length: 20 }).notNull().default('active'),
  permissions: jsonb('permissions').notNull().default([]),
  rateLimit: integer('rate_limit').notNull().default(1000),
  usageCount: integer('usage_count').notNull().default(0),
  lastUsedAt: timestamp('last_used_at'),
  lastUsedIp: varchar('last_used_ip', { length: 45 }),
  expiresAt: timestamp('expires_at'),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  updatedAt: timestamp('updated_at').notNull().defaultNow(),
});

// Credit Accounts table for user billing
export const creditAccounts = pgTable('credit_accounts', {
  id: uuid('id').primaryKey().defaultRandom(),
  userId: uuid('user_id')
    .notNull()
    .unique()
    .references(() => profiles.id),
  currentBalance: integer('current_balance').notNull().default(0),
  monthlyUsage: integer('monthly_usage').notNull().default(0),
  averageDailyUsage: numeric('average_daily_usage', { precision: 10, scale: 2 }).notNull().default('0.00'),
  autoRefillEnabled: boolean('auto_refill_enabled').notNull().default(false),
  refillThreshold: integer('refill_threshold').notNull().default(100),
  refillAmount: integer('refill_amount').notNull().default(500),
  monthlyLimit: integer('monthly_limit').notNull().default(2000),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  updatedAt: timestamp('updated_at').notNull().defaultNow(),
});

// Credit Transactions table for billing history
export const creditTransactions = pgTable('credit_transactions', {
  id: uuid('id').primaryKey().defaultRandom(),
  accountId: uuid('account_id')
    .notNull()
    .references(() => creditAccounts.id),
  userId: uuid('user_id')
    .notNull()
    .references(() => profiles.id),
  type: varchar('type', { length: 20 }).notNull(), // 'purchase', 'usage', 'refund', 'bonus'
  description: text('description').notNull(),
  amount: integer('amount').notNull(),
  balanceAfter: integer('balance_after').notNull(),
  status: varchar('status', { length: 20 }).notNull().default('completed'),
  metadata: jsonb('metadata'),
  createdAt: timestamp('created_at').notNull().defaultNow(),
});

// Notification Preferences table for user settings
export const notificationPreferences = pgTable('notification_preferences', {
  id: uuid('id').primaryKey().defaultRandom(),
  userId: uuid('user_id')
    .notNull()
    .unique()
    .references(() => profiles.id),
  emailEnabled: boolean('email_enabled').notNull().default(true),
  pushEnabled: boolean('push_enabled').notNull().default(false),
  smsEnabled: boolean('sms_enabled').notNull().default(false),
  crawlJobsEnabled: boolean('crawl_jobs_enabled').notNull().default(true),
  datasetsEnabled: boolean('datasets_enabled').notNull().default(true),
  billingEnabled: boolean('billing_enabled').notNull().default(true),
  securityEnabled: boolean('security_enabled').notNull().default(true),
  marketingEnabled: boolean('marketing_enabled').notNull().default(false),
  productUpdatesEnabled: boolean('product_updates_enabled').notNull().default(true),
  digestFrequency: varchar('digest_frequency', { length: 20 }).notNull().default('daily'),
  quietHoursStart: time('quiet_hours_start'),
  quietHoursEnd: time('quiet_hours_end'),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  updatedAt: timestamp('updated_at').notNull().defaultNow(),
});

// Usage Metrics table for tracking daily user activity
export const usageMetrics = pgTable('usage_metrics', {
  id: uuid('id').primaryKey().defaultRandom(),
  userId: uuid('user_id')
    .notNull()
    .references(() => profiles.id),
  metricDate: timestamp('metric_date', { mode: 'date' }).notNull(),
  imagesProcessed: integer('images_processed').notNull().default(0),
  imagesLimit: integer('images_limit').notNull().default(10000),
  storageUsedGb: numeric('storage_used_gb', { precision: 10, scale: 2 }).notNull().default('0.00'),
  storageLimitGb: numeric('storage_limit_gb', { precision: 10, scale: 2 }).notNull().default('100.00'),
  apiCalls: integer('api_calls').notNull().default(0),
  apiCallsLimit: integer('api_calls_limit').notNull().default(50000),
  bandwidthUsedGb: numeric('bandwidth_used_gb', { precision: 10, scale: 2 }).notNull().default('0.00'),
  bandwidthLimitGb: numeric('bandwidth_limit_gb', { precision: 10, scale: 2 }).notNull().default('500.00'),
  createdAt: timestamp('created_at').notNull().defaultNow(),
});

// Notifications table for user notifications
export const notifications = pgTable('notifications', {
  id: serial('id').primaryKey(),
  userId: uuid('user_id')
    .notNull()
    .references(() => profiles.id),
  type: varchar('type', { length: 50 }).notNull(), // 'success', 'info', 'warning', 'error'
  category: varchar('category', { length: 50 }), // 'crawl_job', 'payment', 'system', 'security', 'dataset', 'project'
  title: varchar('title', { length: 255 }).notNull(),
  message: text('message').notNull(),
  icon: varchar('icon', { length: 50 }), // Lucide icon name
  color: varchar('color', { length: 20 }), // Display color
  actionUrl: text('action_url'), // Optional URL to navigate to
  actionLabel: varchar('action_label', { length: 100 }), // Action button label
  metadata: jsonb('metadata'), // Additional data
  isRead: boolean('is_read').notNull().default(false),
  readAt: timestamp('read_at'),
  createdAt: timestamp('created_at').notNull().defaultNow(),
});

// Subscriptions table for Lemon Squeezy subscriptions
export const subscriptions = pgTable('subscriptions', {
  id: uuid('id').primaryKey().defaultRandom(),
  userId: uuid('user_id')
    .notNull()
    .references(() => profiles.id),
  lemonSqueezyCustomerId: varchar('lemonsqueezy_customer_id', { length: 255 }).notNull(),
  lemonSqueezySubscriptionId: varchar('lemonsqueezy_subscription_id', { length: 255 }).notNull().unique(),
  lemonSqueezyVariantId: varchar('lemonsqueezy_variant_id', { length: 255 }).notNull(),
  planId: varchar('plan_id', { length: 50 }).notNull(),
  status: varchar('status', { length: 20 }).notNull(), // 'active', 'cancelled', 'expired', 'on_trial', 'paused', 'past_due', 'unpaid'
  currentPeriodStart: timestamp('current_period_start').notNull(),
  currentPeriodEnd: timestamp('current_period_end').notNull(),
  cancelAtPeriodEnd: boolean('cancel_at_period_end').notNull().default(false),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  updatedAt: timestamp('updated_at').notNull().defaultNow(),
});

// Transactions table for payment transactions
export const transactions = pgTable('transactions', {
  id: uuid('id').primaryKey().defaultRandom(),
  userId: uuid('user_id')
    .notNull()
    .references(() => profiles.id),
  lemonSqueezyOrderId: varchar('lemonsqueezy_order_id', { length: 255 }).notNull().unique(),
  amount: numeric('amount', { precision: 10, scale: 2 }).notNull(),
  currency: varchar('currency', { length: 3 }).notNull().default('usd'),
  status: varchar('status', { length: 20 }).notNull(), // 'paid', 'pending', 'failed', 'refunded'
  planId: varchar('plan_id', { length: 50 }).notNull(),
  metadata: jsonb('metadata'),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  updatedAt: timestamp('updated_at').notNull().defaultNow(),
});

// Relations
export const profilesRelations = relations(profiles, ({ many, one }) => ({
  projects: many(projects),
  activityLogs: many(activityLogs),
  notifications: many(notifications),
  apiKeys: many(apiKeys),
  creditAccount: one(creditAccounts),
  notificationPreferences: one(notificationPreferences),
  usageMetrics: many(usageMetrics),
  subscriptions: many(subscriptions),
  transactions: many(transactions),
}));

export const projectsRelations = relations(projects, ({ one, many }) => ({
  user: one(profiles, {
    fields: [projects.userId],
    references: [profiles.id],
  }),
  crawlJobs: many(crawlJobs),
}));

export const crawlJobsRelations = relations(crawlJobs, ({ one, many }) => ({
  project: one(projects, {
    fields: [crawlJobs.projectId],
    references: [projects.id],
  }),
  images: many(images),
  dataset: one(datasets, {
    fields: [crawlJobs.id],
    references: [datasets.crawlJobId],
    relationName: 'crawlJobDataset'
  }),
}));

export const datasetsRelations = relations(datasets, ({ one, many }) => ({
  user: one(profiles, {
    fields: [datasets.userId],
    references: [profiles.id],
  }),
  crawlJob: one(crawlJobs, {
    fields: [datasets.crawlJobId],
    references: [crawlJobs.id],
    relationName: 'crawlJobDataset'
  }),
  versions: many(datasetVersions),
}));

export const datasetVersionsRelations = relations(datasetVersions, ({ one }) => ({
  dataset: one(datasets, {
    fields: [datasetVersions.datasetId],
    references: [datasets.id],
  }),
  crawlJob: one(crawlJobs, {
    fields: [datasetVersions.crawlJobId],
    references: [crawlJobs.id],
  }),
  creator: one(profiles, {
    fields: [datasetVersions.createdBy],
    references: [profiles.id],
  }),
}));

export const imagesRelations = relations(images, ({ one }) => ({
  crawlJob: one(crawlJobs, {
    fields: [images.crawlJobId],
    references: [crawlJobs.id],
  }),
}));

export const activityLogsRelations = relations(activityLogs, ({ one }) => ({
  user: one(profiles, {
    fields: [activityLogs.userId],
    references: [profiles.id],
  }),
}));

export const notificationsRelations = relations(notifications, ({ one }) => ({
  user: one(profiles, {
    fields: [notifications.userId],
    references: [profiles.id],
  }),
}));

export const apiKeysRelations = relations(apiKeys, ({ one }) => ({
  user: one(profiles, {
    fields: [apiKeys.userId],
    references: [profiles.id],
  }),
}));

export const creditAccountsRelations = relations(creditAccounts, ({ one, many }) => ({
  user: one(profiles, {
    fields: [creditAccounts.userId],
    references: [profiles.id],
  }),
  transactions: many(creditTransactions),
}));

export const creditTransactionsRelations = relations(creditTransactions, ({ one }) => ({
  account: one(creditAccounts, {
    fields: [creditTransactions.accountId],
    references: [creditAccounts.id],
  }),
  user: one(profiles, {
    fields: [creditTransactions.userId],
    references: [profiles.id],
  }),
}));

export const notificationPreferencesRelations = relations(notificationPreferences, ({ one }) => ({
  user: one(profiles, {
    fields: [notificationPreferences.userId],
    references: [profiles.id],
  }),
}));

export const usageMetricsRelations = relations(usageMetrics, ({ one }) => ({
  user: one(profiles, {
    fields: [usageMetrics.userId],
    references: [profiles.id],
  }),
}));

export const subscriptionsRelations = relations(subscriptions, ({ one }) => ({
  user: one(profiles, {
    fields: [subscriptions.userId],
    references: [profiles.id],
  }),
}));

export const transactionsRelations = relations(transactions, ({ one }) => ({
  user: one(profiles, {
    fields: [transactions.userId],
    references: [profiles.id],
  }),
}));

// Type exports
export type Profile = typeof profiles.$inferSelect;
export type NewProfile = typeof profiles.$inferInsert;
export type Project = typeof projects.$inferSelect;
export type NewProject = typeof projects.$inferInsert;
export type CrawlJob = typeof crawlJobs.$inferSelect;
export type NewCrawlJob = typeof crawlJobs.$inferInsert;
export type Image = typeof images.$inferSelect;
export type NewImage = typeof images.$inferInsert;
export type ActivityLog = typeof activityLogs.$inferSelect;
export type NewActivityLog = typeof activityLogs.$inferInsert;
export type Notification = typeof notifications.$inferSelect;
export type NewNotification = typeof notifications.$inferInsert;
export type APIKey = typeof apiKeys.$inferSelect;
export type NewAPIKey = typeof apiKeys.$inferInsert;
export type CreditAccount = typeof creditAccounts.$inferSelect;
export type NewCreditAccount = typeof creditAccounts.$inferInsert;
export type CreditTransaction = typeof creditTransactions.$inferSelect;
export type NewCreditTransaction = typeof creditTransactions.$inferInsert;
export type NotificationPreference = typeof notificationPreferences.$inferSelect;
export type NewNotificationPreference = typeof notificationPreferences.$inferInsert;
export type UsageMetric = typeof usageMetrics.$inferSelect;
export type NewUsageMetric = typeof usageMetrics.$inferInsert;
export type Subscription = typeof subscriptions.$inferSelect;
export type NewSubscription = typeof subscriptions.$inferInsert;
export type Transaction = typeof transactions.$inferSelect;
export type NewTransaction = typeof transactions.$inferInsert;

// Enums
export enum ProjectStatus {
  ACTIVE = 'active',
  ARCHIVED = 'archived',
  DELETED = 'deleted',
}

export enum CrawlJobStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
}

export enum ActivityType {
  SIGN_UP = 'SIGN_UP',
  SIGN_IN = 'SIGN_IN',
  SIGN_OUT = 'SIGN_OUT',
  CREATE_PROJECT = 'CREATE_PROJECT',
  UPDATE_PROJECT = 'UPDATE_PROJECT',
  DELETE_PROJECT = 'DELETE_PROJECT',
  START_CRAWL_JOB = 'START_CRAWL_JOB',
  COMPLETE_CRAWL_JOB = 'COMPLETE_CRAWL_JOB',
  DOWNLOAD_IMAGES = 'DOWNLOAD_IMAGES',
}
