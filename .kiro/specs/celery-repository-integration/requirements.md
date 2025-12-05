# Requirements Document

## Introduction

This document specifies the requirements for integrating Celery tasks from the builder and validator packages into the FastAPI backend API endpoints. The integration will follow the established Repository Pattern and ensure proper database session management for distributed workers. The system will enable asynchronous image crawling, validation, and dataset generation through RESTful API endpoints while maintaining data consistency and proper error handling.

## Glossary

- **Celery Task**: An asynchronous task executed by Celery workers in separate processes
- **Repository Pattern**: A data access pattern that abstracts database operations through repository classes
- **AsyncSession**: SQLAlchemy asynchronous database session for non-blocking database operations
- **Service Layer**: Business logic layer that orchestrates repository operations and task dispatch
- **Task ID**: Unique identifier assigned to a Celery task for tracking and management
- **Chunk**: A unit of work in a crawl job, typically representing one keyword-engine combination
- **RLS**: Row Level Security policies in PostgreSQL for multi-tenant data isolation
- **Supabase Auth**: Authentication service providing JWT tokens for API access
- **Service Role Key**: Privileged Supabase key that bypasses RLS policies for backend operations

## Requirements

### Requirement 1

**User Story:** As a backend developer, I want to dispatch Celery tasks from API endpoints, so that image crawling and validation can be triggered via REST API calls.

#### Acceptance Criteria

1. WHEN an authenticated user sends a POST request to `/api/v1/jobs/{job_id}/start`, THE system SHALL dispatch download tasks for each keyword-engine combination
2. WHEN dispatching tasks, THE system SHALL pass only serializable data types (strings, integers, dictionaries) to Celery tasks
3. WHEN tasks are dispatched, THE system SHALL store task IDs in the database for tracking
4. WHEN a job start request is received for a job that is not in pending status, THE system SHALL return a 400 Bad Request error
5. WHEN task dispatch completes, THE system SHALL update the job status to "running" and set the total_chunks count

### Requirement 2

**User Story:** As a backend developer, I want to manage database sessions properly in distributed workers, so that database connections are not leaked or shared across processes.

#### Acceptance Criteria

1. WHEN an API endpoint dispatches a Celery task, THE system SHALL NOT pass AsyncSession instances to the task
2. WHEN an API endpoint dispatches a Celery task, THE system SHALL NOT pass repository instances to the task
3. WHEN a Celery task requires database access, THE task SHALL create its own database session
4. WHEN a Celery task completes, THE task SHALL close its database session
5. WHEN multiple tasks execute concurrently, THE system SHALL maintain session isolation between tasks

### Requirement 3

**User Story:** As a backend developer, I want to track crawl job progress, so that users can monitor the status of their image downloads.

#### Acceptance Criteria

1. WHEN a download task completes, THE system SHALL update the job's completed_chunks count
2. WHEN a download task completes, THE system SHALL decrement the job's active_chunks count
3. WHEN chunk counts are updated, THE system SHALL calculate progress as (completed_chunks / total_chunks) * 100
4. WHEN all chunks complete, THE system SHALL update the job status to "completed"
5. WHEN a user requests job progress via GET `/api/v1/jobs/{job_id}/progress`, THE system SHALL return current progress percentage and chunk statistics

### Requirement 4

**User Story:** As a backend developer, I want to stop running crawl jobs, so that users can cancel jobs that are no longer needed.

#### Acceptance Criteria

1. WHEN an authenticated user sends a POST request to `/api/v1/jobs/{job_id}/stop`, THE system SHALL retrieve all active task IDs for the job
2. WHEN active task IDs are retrieved, THE system SHALL revoke each task using Celery's revoke mechanism
3. WHEN tasks are revoked, THE system SHALL update the job status to "cancelled"
4. WHEN a job is cancelled, THE system SHALL create a notification for the user
5. WHEN a stop request is received for a job that is not running, THE system SHALL return a 400 Bad Request error

### Requirement 5

**User Story:** As a backend developer, I want to validate downloaded images, so that invalid or duplicate images can be identified and marked.

#### Acceptance Criteria

1. WHEN an authenticated user sends a POST request to `/api/v1/validation/job/{job_id}`, THE system SHALL retrieve all images for the specified job
2. WHEN images are retrieved, THE system SHALL dispatch validation tasks based on the requested validation level (fast, medium, slow)
3. WHEN validation level is "fast", THE system SHALL use the validate_image_fast_task with 1000/m rate limit
4. WHEN validation level is "medium", THE system SHALL use the validate_image_medium_task with 500/m rate limit
5. WHEN validation level is "slow", THE system SHALL use the validate_image_slow_task with 100/m rate limit
6. WHEN validation tasks complete, THE system SHALL update image records with validation results

### Requirement 6

**User Story:** As a backend developer, I want to handle task completion callbacks, so that job progress and results are properly recorded in the database.

#### Acceptance Criteria

1. WHEN a download task completes successfully, THE system SHALL create image records in the database for downloaded images
2. WHEN a download task completes successfully, THE system SHALL update the job's downloaded_images count
3. WHEN a download task fails, THE system SHALL increment the job's failed_chunks count
4. WHEN a download task fails, THE system SHALL log the error with structured logging
5. WHEN all tasks for a job complete, THE system SHALL create a completion notification for the user

### Requirement 7

**User Story:** As a backend developer, I want to implement proper error handling, so that task failures and API errors are handled gracefully.

#### Acceptance Criteria

1. WHEN a task dispatch fails, THE system SHALL return a 500 Internal Server Error with error details
2. WHEN a job is not found, THE system SHALL return a 404 Not Found error
3. WHEN a user attempts to access a job they do not own, THE system SHALL return a 403 Forbidden error
4. WHEN a validation error occurs, THE system SHALL return a 422 Unprocessable Entity error with field-level details
5. WHEN any error occurs, THE system SHALL log the error with request context using structured logging

### Requirement 8

**User Story:** As a backend developer, I want to enforce authentication on all endpoints, so that only authorized users can access job and validation operations.

#### Acceptance Criteria

1. WHEN a request is received without an Authorization header, THE system SHALL return a 401 Unauthorized error
2. WHEN a request is received with an invalid JWT token, THE system SHALL return a 401 Unauthorized error
3. WHEN a valid JWT token is provided, THE system SHALL extract the user ID from the token
4. WHEN a user attempts to access a resource, THE system SHALL verify the resource belongs to the user
5. WHEN token verification fails, THE system SHALL log the failure with the request ID

### Requirement 9

**User Story:** As a backend developer, I want to add repository methods for task management, so that task-related database operations follow the repository pattern.

#### Acceptance Criteria

1. WHEN a task ID needs to be stored, THE CrawlJobRepository SHALL provide an add_task_id method
2. WHEN job progress needs to be updated, THE CrawlJobRepository SHALL provide an update_progress method
3. WHEN chunk status needs to be updated, THE CrawlJobRepository SHALL provide an update_chunk_status method
4. WHEN a job needs to be marked complete, THE CrawlJobRepository SHALL provide a mark_completed method
5. WHEN a job needs to be marked failed, THE CrawlJobRepository SHALL provide a mark_failed method
6. WHEN images need to be created from download results, THE ImageRepository SHALL provide a create_from_download method
7. WHEN validation results need to be stored, THE ImageRepository SHALL provide a mark_validated method

### Requirement 10

**User Story:** As a backend developer, I want to implement service layer orchestration, so that complex task workflows are properly coordinated.

#### Acceptance Criteria

1. WHEN a job start is requested, THE CrawlJobService SHALL validate job ownership and status before dispatching tasks
2. WHEN tasks are dispatched, THE CrawlJobService SHALL coordinate between job repository and task dispatch
3. WHEN a task completes, THE CrawlJobService SHALL handle the result and update related database records
4. WHEN validation is requested, THE ValidationService SHALL retrieve images and dispatch appropriate validation tasks
5. WHEN a job is stopped, THE CrawlJobService SHALL revoke tasks and update job status atomically

### Requirement 11

**User Story:** As a backend developer, I want to implement idempotent operations, so that duplicate requests do not cause inconsistent state.

#### Acceptance Criteria

1. WHEN a job start request is received for a job already running, THE system SHALL return the existing task IDs without dispatching new tasks
2. WHEN a job stop request is received for a job already stopped, THE system SHALL return success without attempting to revoke tasks
3. WHEN duplicate task results are received, THE system SHALL process only the first result
4. WHEN a retry is requested for a failed job, THE system SHALL reset chunk counters before dispatching new tasks
5. WHEN concurrent requests modify the same job, THE system SHALL use database transactions to prevent race conditions

### Requirement 12

**User Story:** As a backend developer, I want to implement rate limiting awareness, so that API endpoints respect Celery task rate limits.

#### Acceptance Criteria

1. WHEN dispatching download tasks, THE system SHALL respect the 10/m rate limit for each engine
2. WHEN dispatching validation tasks, THE system SHALL respect the rate limit for the selected validation level
3. WHEN rate limits are exceeded, THE system SHALL queue tasks for later execution
4. WHEN keyword generation is requested, THE system SHALL respect the 5/m rate limit
5. WHEN label generation is requested, THE system SHALL respect the time limit of 900 seconds
