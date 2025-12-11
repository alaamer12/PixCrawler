CREATE TABLE "datasets" (
	"id" serial PRIMARY KEY NOT NULL,
	"user_id" uuid NOT NULL,
	"project_id" integer,
	"name" varchar(100) NOT NULL,
	"description" text,
	"keywords" jsonb NOT NULL,
	"max_images" integer DEFAULT 100 NOT NULL,
	"search_engines" jsonb DEFAULT '[]'::jsonb NOT NULL,
	"status" varchar(20) DEFAULT 'pending' NOT NULL,
	"progress" numeric(5, 2) DEFAULT '0.00' NOT NULL,
	"images_collected" integer DEFAULT 0 NOT NULL,
	"crawl_job_id" integer,
	"download_url" text,
	"error_message" text,
	"storage_tier" varchar(20) DEFAULT 'hot' NOT NULL,
	"archived_at" timestamp,
	"last_accessed_at" timestamp DEFAULT now() NOT NULL,
	"created_at" timestamp DEFAULT now() NOT NULL,
	"updated_at" timestamp DEFAULT now() NOT NULL
);
--> statement-breakpoint
ALTER TABLE "datasets" ADD CONSTRAINT "datasets_user_id_profiles_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."profiles"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "datasets" ADD CONSTRAINT "datasets_project_id_projects_id_fk" FOREIGN KEY ("project_id") REFERENCES "public"."projects"("id") ON DELETE set null ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "datasets" ADD CONSTRAINT "datasets_crawl_job_id_crawl_jobs_id_fk" FOREIGN KEY ("crawl_job_id") REFERENCES "public"."crawl_jobs"("id") ON DELETE set null ON UPDATE no action;