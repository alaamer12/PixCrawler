CREATE TABLE "activity_logs" (
	"id" serial PRIMARY KEY NOT NULL,
	"user_id" uuid,
	"action" text NOT NULL,
	"resource_type" varchar(50),
	"resource_id" varchar(50),
	"metadata" jsonb,
	"timestamp" timestamp DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "api_keys" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"user_id" uuid NOT NULL,
	"name" varchar(200) NOT NULL,
	"key_hash" varchar(255) NOT NULL,
	"key_prefix" varchar(20) NOT NULL,
	"status" varchar(20) DEFAULT 'active' NOT NULL,
	"permissions" jsonb DEFAULT '[]'::jsonb NOT NULL,
	"rate_limit" integer DEFAULT 1000 NOT NULL,
	"usage_count" integer DEFAULT 0 NOT NULL,
	"last_used_at" timestamp,
	"last_used_ip" varchar(45),
	"expires_at" timestamp,
	"created_at" timestamp DEFAULT now() NOT NULL,
	"updated_at" timestamp DEFAULT now() NOT NULL,
	CONSTRAINT "api_keys_key_hash_unique" UNIQUE("key_hash")
);
--> statement-breakpoint
CREATE TABLE "crawl_jobs" (
	"id" serial PRIMARY KEY NOT NULL,
	"project_id" integer NOT NULL,
	"name" varchar(100) NOT NULL,
	"keywords" jsonb NOT NULL,
	"max_images" integer DEFAULT 1000 NOT NULL,
	"status" varchar(20) DEFAULT 'pending' NOT NULL,
	"progress" integer DEFAULT 0 NOT NULL,
	"total_images" integer DEFAULT 0 NOT NULL,
	"downloaded_images" integer DEFAULT 0 NOT NULL,
	"valid_images" integer DEFAULT 0 NOT NULL,
	"total_chunks" integer DEFAULT 0 NOT NULL,
	"active_chunks" integer DEFAULT 0 NOT NULL,
	"completed_chunks" integer DEFAULT 0 NOT NULL,
	"failed_chunks" integer DEFAULT 0 NOT NULL,
	"task_ids" jsonb DEFAULT '[]'::jsonb NOT NULL,
	"started_at" timestamp,
	"completed_at" timestamp,
	"created_at" timestamp DEFAULT now() NOT NULL,
	"updated_at" timestamp DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "credit_accounts" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"user_id" uuid NOT NULL,
	"current_balance" integer DEFAULT 0 NOT NULL,
	"monthly_usage" integer DEFAULT 0 NOT NULL,
	"average_daily_usage" numeric(10, 2) DEFAULT '0.00' NOT NULL,
	"auto_refill_enabled" boolean DEFAULT false NOT NULL,
	"refill_threshold" integer DEFAULT 100 NOT NULL,
	"refill_amount" integer DEFAULT 500 NOT NULL,
	"monthly_limit" integer DEFAULT 2000 NOT NULL,
	"created_at" timestamp DEFAULT now() NOT NULL,
	"updated_at" timestamp DEFAULT now() NOT NULL,
	CONSTRAINT "credit_accounts_user_id_unique" UNIQUE("user_id")
);
--> statement-breakpoint
CREATE TABLE "credit_transactions" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"account_id" uuid NOT NULL,
	"user_id" uuid NOT NULL,
	"type" varchar(20) NOT NULL,
	"description" text NOT NULL,
	"amount" integer NOT NULL,
	"balance_after" integer NOT NULL,
	"status" varchar(20) DEFAULT 'completed' NOT NULL,
	"metadata" jsonb,
	"created_at" timestamp DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "images" (
	"id" serial PRIMARY KEY NOT NULL,
	"crawl_job_id" integer NOT NULL,
	"original_url" text NOT NULL,
	"filename" varchar(255) NOT NULL,
	"storage_url" text,
	"width" integer,
	"height" integer,
	"file_size" integer,
	"format" varchar(10),
	"hash" varchar(64),
	"is_valid" boolean DEFAULT true NOT NULL,
	"is_duplicate" boolean DEFAULT false NOT NULL,
	"labels" jsonb,
	"metadata" jsonb,
	"downloaded_at" timestamp DEFAULT now() NOT NULL,
	"created_at" timestamp DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "notification_preferences" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"user_id" uuid NOT NULL,
	"email_enabled" boolean DEFAULT true NOT NULL,
	"push_enabled" boolean DEFAULT false NOT NULL,
	"sms_enabled" boolean DEFAULT false NOT NULL,
	"crawl_jobs_enabled" boolean DEFAULT true NOT NULL,
	"datasets_enabled" boolean DEFAULT true NOT NULL,
	"billing_enabled" boolean DEFAULT true NOT NULL,
	"security_enabled" boolean DEFAULT true NOT NULL,
	"marketing_enabled" boolean DEFAULT false NOT NULL,
	"product_updates_enabled" boolean DEFAULT true NOT NULL,
	"digest_frequency" varchar(20) DEFAULT 'daily' NOT NULL,
	"quiet_hours_start" time,
	"quiet_hours_end" time,
	"created_at" timestamp DEFAULT now() NOT NULL,
	"updated_at" timestamp DEFAULT now() NOT NULL,
	CONSTRAINT "notification_preferences_user_id_unique" UNIQUE("user_id")
);
--> statement-breakpoint
CREATE TABLE "notifications" (
	"id" serial PRIMARY KEY NOT NULL,
	"user_id" uuid NOT NULL,
	"type" varchar(50) NOT NULL,
	"category" varchar(50),
	"title" varchar(255) NOT NULL,
	"message" text NOT NULL,
	"icon" varchar(50),
	"color" varchar(20),
	"action_url" text,
	"action_label" varchar(100),
	"metadata" jsonb,
	"is_read" boolean DEFAULT false NOT NULL,
	"read_at" timestamp,
	"created_at" timestamp DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "profiles" (
	"id" uuid PRIMARY KEY NOT NULL,
	"email" varchar(255) NOT NULL,
	"full_name" varchar(100),
	"avatar_url" text,
	"role" varchar(20) DEFAULT 'user' NOT NULL,
	"onboarding_completed" boolean DEFAULT false NOT NULL,
	"onboarding_completed_at" timestamp,
	"created_at" timestamp DEFAULT now() NOT NULL,
	"updated_at" timestamp DEFAULT now() NOT NULL,
	CONSTRAINT "profiles_email_unique" UNIQUE("email")
);
--> statement-breakpoint
CREATE TABLE "projects" (
	"id" serial PRIMARY KEY NOT NULL,
	"name" varchar(100) NOT NULL,
	"description" text,
	"user_id" uuid NOT NULL,
	"status" varchar(20) DEFAULT 'active' NOT NULL,
	"created_at" timestamp DEFAULT now() NOT NULL,
	"updated_at" timestamp DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "usage_metrics" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"user_id" uuid NOT NULL,
	"metric_date" timestamp NOT NULL,
	"images_processed" integer DEFAULT 0 NOT NULL,
	"images_limit" integer DEFAULT 10000 NOT NULL,
	"storage_used_gb" numeric(10, 2) DEFAULT '0.00' NOT NULL,
	"storage_limit_gb" numeric(10, 2) DEFAULT '100.00' NOT NULL,
	"api_calls" integer DEFAULT 0 NOT NULL,
	"api_calls_limit" integer DEFAULT 50000 NOT NULL,
	"bandwidth_used_gb" numeric(10, 2) DEFAULT '0.00' NOT NULL,
	"bandwidth_limit_gb" numeric(10, 2) DEFAULT '500.00' NOT NULL,
	"created_at" timestamp DEFAULT now() NOT NULL
);
--> statement-breakpoint
ALTER TABLE "activity_logs" ADD CONSTRAINT "activity_logs_user_id_profiles_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."profiles"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "api_keys" ADD CONSTRAINT "api_keys_user_id_profiles_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."profiles"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "crawl_jobs" ADD CONSTRAINT "crawl_jobs_project_id_projects_id_fk" FOREIGN KEY ("project_id") REFERENCES "public"."projects"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "credit_accounts" ADD CONSTRAINT "credit_accounts_user_id_profiles_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."profiles"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "credit_transactions" ADD CONSTRAINT "credit_transactions_account_id_credit_accounts_id_fk" FOREIGN KEY ("account_id") REFERENCES "public"."credit_accounts"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "credit_transactions" ADD CONSTRAINT "credit_transactions_user_id_profiles_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."profiles"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "images" ADD CONSTRAINT "images_crawl_job_id_crawl_jobs_id_fk" FOREIGN KEY ("crawl_job_id") REFERENCES "public"."crawl_jobs"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "notification_preferences" ADD CONSTRAINT "notification_preferences_user_id_profiles_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."profiles"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "notifications" ADD CONSTRAINT "notifications_user_id_profiles_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."profiles"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "projects" ADD CONSTRAINT "projects_user_id_profiles_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."profiles"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "usage_metrics" ADD CONSTRAINT "usage_metrics_user_id_profiles_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."profiles"("id") ON DELETE no action ON UPDATE no action;