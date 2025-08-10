# OpsBrain Production Readiness Guide

## Overview

This document outlines the architecture and deployment process for running OpsBrain AI Assistant in a production environment on Render.com, ensuring data persistence and scalability.

## Production Architecture

### Core Components
- **Web Service**: Runs the FastAPI application using Gunicorn and Uvicorn workers
- **PostgreSQL Database**: Managed database service on Render.com for data persistence
- **Docker Container**: Application packaged in a secure, non-root container
- **Render Environment**: Production environment with managed scaling and backups

### Data Persistence
- **Problem**: SQLite database is lost on every deployment due to ephemeral file systems
- **Solution**: PostgreSQL database managed by Render.com ensures data is persistent across deployments
- **Benefits**:
  - ✅ Data survives application restarts and deployments
  - ✅ Managed backups and recovery
  - ✅ Scalability and performance
  - ✅ Secure connection with SSL

## Production Files

1.  **`src/postgres_database.py`**: PostgreSQL database adapter for production
2.  **`render.yaml`**: Render.com deployment configuration with database service
3.  **`migrate_to_production.py`**: Production migration script (SQLite to PostgreSQL)
4.  **`Dockerfile`**: Updated Dockerfile for production builds
5.  **`requirements.txt`**: Added `psycopg2-binary` for PostgreSQL support

## Deployment Process

### 1. Create PostgreSQL Database on Render.com
- Go to Render.com dashboard and create a new PostgreSQL database
- Name it `opsbrain-db` (matches `render.yaml`)
- Render will provide a `DATABASE_URL` environment variable

### 2. Configure `render.yaml`
The `render.yaml` file has been updated to:
- ✅ Create a `web` service and a `database` service
- ✅ Link the web service to the PostgreSQL database
- ✅ Automatically inject `DATABASE_URL` into the environment

```yaml
services:
  - type: web
    name: decouple-dev-ai-assistant
    env: python
    startCommand: "gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --timeout 120"
    buildCommand: "pip install -r requirements.txt && python migrate_to_production.py"
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: opsbrain-db
          property: connectionString

databases:
  - name: opsbrain-db
    databaseName: opsbrain
    user: opsbrain
```

### 3. Build and Deploy
On every push to the main branch, Render will automatically:
1. ✅ **Install dependencies** from `requirements.txt`
2. ✅ **Run production migration** using `python migrate_to_production.py`
3. ✅ **Start the application** with `gunicorn`

The migration script will:
- 🔗 Connect to the PostgreSQL database
- 📝 Create the schema if it doesn't exist
- 🔄 Migrate data from SQLite on first deployment
- 🧹 Clean up the local SQLite file

## Database Management

### Development vs Production
- **Development**: Uses local `opsbrain.db` SQLite file for ease of use
- **Production**: Uses PostgreSQL database for persistence and reliability
- The application **automatically detects** the environment and chooses the right database manager:

```python
# src/postgres_database.py

def create_database_manager():
    """Create appropriate database manager based on environment.""" 
    if os.getenv('DATABASE_URL'):
        # Production: Use PostgreSQL
        return PostgresDatabaseManager()
    else:
        # Development: Use SQLite
        return DatabaseManager()
```

### How Data is Preserved
- **PostgreSQL Database**: Lives independently of the application container
- **`DATABASE_URL`**: Connects the container to the database
- **Migration Script**: Ensures schema is always up-to-date
- **Data Migration**: Transfers local SQLite data to production on first deploy

## Security Considerations

- ✅ **SSL Connection**: PostgreSQL connection requires SSL by default
- ✅ **Managed Backups**: Render.com automatically backs up the database
- ✅ **Secure Credentials**: `DATABASE_URL` is securely injected by Render
- ✅ **Non-root Container**: Application runs as a non-root user

## Troubleshooting

### Deployment Failures
- Check Render.com build logs for migration script errors
- Ensure `DATABASE_URL` is correctly configured
- Verify all environment variables are set in Render dashboard

### Database Connection Issues
- Check database status on Render.com dashboard
- Ensure `psycopg2-binary` is installed correctly

## Summary

This production-ready architecture ensures that your database is:
- **Persistent**: Survives deployments and restarts
- **Secure**: Managed by Render with secure connections
- **Scalable**: Can handle production workloads
- **Maintainable**: Automated migrations and backups

Your application is now configured for robust, production-grade data management, solving the ephemeral file system problem entirely.
