-- Create job_chunks table for PixCrawler backend
-- This table tracks individual chunks of crawl jobs for parallel processing

CREATE TABLE IF NOT EXISTS job_chunks (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES crawl_jobs(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    priority INTEGER DEFAULT 0,
    image_range JSONB,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    task_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure unique chunk index per job
    UNIQUE(job_id, chunk_index)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_job_chunks_job_id ON job_chunks(job_id);
CREATE INDEX IF NOT EXISTS idx_job_chunks_status ON job_chunks(status);
CREATE INDEX IF NOT EXISTS idx_job_chunks_task_id ON job_chunks(task_id);

-- Add comment
COMMENT ON TABLE job_chunks IS 'Tracks individual processing chunks for crawl jobs to enable parallel execution';
