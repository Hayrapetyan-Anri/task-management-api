-- Initialize the database
-- This file will be executed when the PostgreSQL container starts

-- Create the database if it doesn't exist (though it should be created by the environment variable)
-- CREATE DATABASE IF NOT EXISTS task_management;

-- Set timezone
SET timezone = 'UTC';

-- Enable UUID extension (useful for future enhancements)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";