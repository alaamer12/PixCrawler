import {boolean, integer, jsonb, pgTable, serial, text, timestamp, uuid, varchar,} from 'drizzle-orm/pg-core';
import {relations} from 'drizzle-orm';

// User profiles table (extends Supabase auth.users)
export const profiles = pgTable('profiles', {
  id: uuid('id').primaryKey(), // References auth.users.id
  email: varchar('email', {length: 255}).notNull().unique(),
  fullName: varchar('full_name', {length: 100}),
  avatarUrl: text('avatar_url'),
  role: varchar('role', {length: 20}).notNull().default('user'),
  onboardingCompleted: boolean('onboarding_completed').notNull().default(false),
  onboardingCompletedAt: timestamp('onboarding_completed_at'),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  updatedAt: timestamp('updated_at').notNull().defaultNow(),
});

// Projects table for organizing image crawling tasks
export const projects = pgTable('projects', {
  id: serial('id').primaryKey(),
  name: varchar('name', {length: 100}).notNull(),
  description: text('description'),
  userId: uuid('user_id')
    .notNull()
    .references(() => profiles.id),
  status: varchar('status', {length: 20}).notNull().default('active'),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  updatedAt: timestamp('updated_at').notNull().defaultNow(),
});

// Crawl jobs table for tracking image crawling tasks
export const crawlJobs = pgTable('crawl_jobs', {
  id: serial('id').primaryKey(),
  projectId: integer('project_id')
    .notNull()
    .references(() => projects.id),
  name: varchar('name', {length: 100}).notNull(),
  keywords: jsonb('keywords').notNull(), // Array of search keywords
  maxImages: integer('max_images').notNull().default(100),
  searchEngine: varchar('search_engine', {length: 50}).notNull().default('duckduckgo'),
  status: varchar('status', {length: 20}).notNull().default('pending'),
  progress: integer('progress').notNull().default(0),
  totalImages: integer('total_images').notNull().default(0),
  downloadedImages: integer('downloaded_images').notNull().default(0),
  validImages: integer('valid_images').notNull().default(0),
  config: jsonb('config'), // Additional configuration options
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
  filename: varchar('filename', {length: 255}).notNull(),
  storageUrl: text('storage_url'), // Supabase Storage URL
  width: integer('width'),
  height: integer('height'),
  fileSize: integer('file_size'),
  format: varchar('format', {length: 10}),
  hash: varchar('hash', {length: 64}), // For duplicate detection
  isValid: boolean('is_valid').notNull().default(true),
  isDuplicate: boolean('is_duplicate').notNull().default(false),
  labels: jsonb('labels'), // AI-generated labels
  metadata: jsonb('metadata'), // Additional image metadata
  downloadedAt: timestamp('downloaded_at').notNull().defaultNow(),
  createdAt: timestamp('created_at').notNull().defaultNow(),
});

// Activity logs for tracking user actions
export const activityLogs = pgTable('activity_logs', {
  id: serial('id').primaryKey(),
  userId: uuid('user_id').references(() => profiles.id),
  action: text('action').notNull(),
  resourceType: varchar('resource_type', {length: 50}),
  resourceId: varchar('resource_id', {length: 50}),
  metadata: jsonb('metadata'),
  timestamp: timestamp('timestamp').notNull().defaultNow(),
  ipAddress: varchar('ip_address', {length: 45}),
});

// Notifications table for user notifications
export const notifications = pgTable('notifications', {
  id: serial('id').primaryKey(),
  userId: uuid('user_id')
    .notNull()
    .references(() => profiles.id),
  type: varchar('type', {length: 50}).notNull(), // 'crawl_job', 'billing', 'security', 'dataset'
  title: varchar('title', {length: 255}).notNull(),
  message: text('message').notNull(),
  icon: varchar('icon', {length: 50}), // Icon name for UI
  iconColor: varchar('icon_color', {length: 50}), // Color class for icon
  actionUrl: text('action_url'), // Optional URL to navigate to
  metadata: jsonb('metadata'), // Additional data
  isRead: boolean('is_read').notNull().default(false),
  readAt: timestamp('read_at'),
  createdAt: timestamp('created_at').notNull().defaultNow(),
});

// Relations
export const profilesRelations = relations(profiles, ({many}) => ({
  projects: many(projects),
  activityLogs: many(activityLogs),
  notifications: many(notifications),
}));

export const projectsRelations = relations(projects, ({one, many}) => ({
  user: one(profiles, {
    fields: [projects.userId],
    references: [profiles.id],
  }),
  crawlJobs: many(crawlJobs),
}));

export const crawlJobsRelations = relations(crawlJobs, ({one, many}) => ({
  project: one(projects, {
    fields: [crawlJobs.projectId],
    references: [projects.id],
  }),
  images: many(images),
}));

export const imagesRelations = relations(images, ({one}) => ({
  crawlJob: one(crawlJobs, {
    fields: [images.crawlJobId],
    references: [crawlJobs.id],
  }),
}));

export const activityLogsRelations = relations(activityLogs, ({one}) => ({
  user: one(profiles, {
    fields: [activityLogs.userId],
    references: [profiles.id],
  }),
}));

export const notificationsRelations = relations(notifications, ({one}) => ({
  user: one(profiles, {
    fields: [notifications.userId],
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
