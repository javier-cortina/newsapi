-- Initialize PostgreSQL database for News API Pipeline
-- This script creates the required schemas for the Dagster pipeline

-- Create schemas for data organization
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS processed;
CREATE SCHEMA IF NOT EXISTS final;

-- Grant permissions to dagster_user
GRANT ALL PRIVILEGES ON SCHEMA raw TO dagster_user;
GRANT ALL PRIVILEGES ON SCHEMA processed TO dagster_user;
GRANT ALL PRIVILEGES ON SCHEMA final TO dagster_user;

-- Grant usage on public schema (for Dagster metadata)
GRANT ALL PRIVILEGES ON SCHEMA public TO dagster_user;

-- Create extension for UUID support (useful for future enhancements)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'Database initialized successfully for News API Pipeline';
    RAISE NOTICE 'Schemas created: raw, processed, final';
END $$;
