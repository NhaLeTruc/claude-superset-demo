# Setup Guide

This guide will help you set up the GoodNote Analytics Platform from scratch on your local machine or server.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (5 Minutes)](#quick-start)
3. [Detailed Setup](#detailed-setup)
4. [Verification](#verification)
5. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

**Minimum:**
- CPU: 4 cores
- RAM: 16 GB
- Storage: 100 GB free space
- OS: Linux, macOS, or Windows (with WSL2)

**Recommended:**
- CPU: 8+ cores
- RAM: 32 GB
- Storage: 500 GB SSD
- OS: Linux or macOS

### Software Dependencies

1. **Docker** (24.x or higher)
   ```bash
   # Verify installation
   docker --version
   # Expected output: Docker version 24.x.x
   ```

2. **Docker Compose** (2.x or higher)
   ```bash
   # Verify installation
   docker compose version
   # Expected output: Docker Compose version 2.x.x
   ```

3. **Python** (3.9 or higher)
   ```bash
   # Verify installation
   python3 --version
   # Expected output: Python 3.9.x or higher
   ```

4. **Git** (2.x or higher)
   ```bash
   # Verify installation
   git --version
   # Expected output: git version 2.x.x
   ```

### Installing Prerequisites

#### Ubuntu/Debian
```bash
# Update package index
sudo apt update

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose Plugin
sudo apt install docker-compose-plugin

# Install Python 3.9+
sudo apt install python3.9 python3-pip python3-venv

# Install Git
sudo apt install git

# Restart terminal or logout/login for docker group to take effect
```

#### macOS
```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Docker Desktop
brew install --cask docker

# Install Python 3.9+
brew install python@3.9

# Install Git
brew install git
```

#### Windows (WSL2)
```powershell
# Install WSL2 (PowerShell as Administrator)
wsl --install

# Restart computer, then continue in WSL2 terminal

# Follow Ubuntu/Debian instructions above
```

---

## Quick Start

For those who want to get up and running immediately:

```bash
# 1. Clone repository
git clone <repository-url>
cd insight-engineer-challenge

# 2. Start all services
docker compose up -d

# 3. Wait for services to be ready (2-3 minutes)
docker compose ps

# 4. Generate sample data
docker exec goodnote-spark-master python /opt/spark-apps/scripts/generate_data.py --interactions 100000 --metadata 10000

# 5. Run Spark jobs
docker exec goodnote-spark-master ./scripts/run_all_jobs.sh

# 6. Access services
# Spark UI: http://localhost:8080
# Superset: http://localhost:8088 (admin/admin)
# Jupyter: http://localhost:8888
```

**That's it!** You now have a fully functional analytics platform.

---

## Detailed Setup

### Step 1: Clone Repository

```bash
# Clone the repository
git clone <repository-url>
cd insight-engineer-challenge

# Verify directory structure
ls -la
# You should see: src/, docker/, data/, scripts/, etc.
```

### Step 2: Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env  # or use your preferred editor
```

**Key Environment Variables:**

```bash
# .env file

# PostgreSQL Configuration
POSTGRES_USER=analytics_user
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=analytics
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Spark Configuration
SPARK_MASTER_URL=spark://spark-master:7077
SPARK_WORKER_MEMORY=16g
SPARK_WORKER_CORES=8
SPARK_EXECUTOR_MEMORY=16g
SPARK_DRIVER_MEMORY=8g

# Superset Configuration
SUPERSET_SECRET_KEY=your_secret_key_here_change_in_production
SUPERSET_ADMIN_USERNAME=admin
SUPERSET_ADMIN_PASSWORD=admin
SUPERSET_ADMIN_EMAIL=admin@example.com

# Data Configuration
DATA_RAW_PATH=/opt/spark-data/raw
DATA_PROCESSED_PATH=/opt/spark-data/processed
```

**Important:** Change default passwords in production!

### Step 3: Build Docker Images

```bash
# Navigate to docker directory
cd docker

# Build all images
docker compose build

# Expected output:
# Successfully built spark-master
# Successfully built spark-worker
# Successfully tagged goodnote-analytics:latest
```

This step may take 10-15 minutes depending on your internet speed.

### Step 4: Start Services

```bash
# Start all services in detached mode
docker compose up -d

# Verify all containers are running
docker compose ps

# Expected output:
# NAME                  STATUS    PORTS
# goodnote-spark-master  Up       0.0.0.0:8080->8080/tcp, 0.0.0.0:7077->7077/tcp
# goodnote-spark-worker  Up
# goodnote-postgres      Up       0.0.0.0:5432->5432/tcp
# goodnote-superset      Up       0.0.0.0:8088->8088/tcp
# goodnote-redis         Up       0.0.0.0:6379->6379/tcp
# goodnote-jupyter       Up       0.0.0.0:8888->8888/tcp
```

**Wait for services to be healthy:**
```bash
# Check PostgreSQL is ready
docker exec goodnote-postgres pg_isready -U analytics_user
# Expected output: postgres:5432 - accepting connections

# Check Spark Master is ready
curl http://localhost:8080
# Should return HTML (Spark UI)

# Check Superset is ready
curl http://localhost:8088/health
# Expected output: {"status": "ok"}
```

### Step 5: Initialize PostgreSQL Database

```bash
# Run database initialization script
docker exec goodnote-postgres psql -U analytics_user -d analytics -f /docker-entrypoint-initdb.d/schema.sql

# Verify tables were created
docker exec goodnote-postgres psql -U analytics_user -d analytics -c "\dt goodnote_analytics.*"

# Expected output:
# List of relations
# Schema              | Name                     | Type  | Owner
# goodnote_analytics  | daily_active_users       | table | analytics_user
# goodnote_analytics  | monthly_active_users     | table | analytics_user
# ...
```

### Step 6: Initialize Apache Superset

```bash
# Initialize Superset database
docker exec goodnote-superset superset db upgrade

# Create admin user
docker exec goodnote-superset superset fab create-admin \
    --username admin \
    --firstname Admin \
    --lastname User \
    --email admin@example.com \
    --password admin

# Initialize Superset
docker exec goodnote-superset superset init

# Add PostgreSQL database connection
docker exec goodnote-superset superset set_database_uri \
    --database_name "GoodNote Analytics" \
    --uri "postgresql://analytics_user:your_password@postgres:5432/analytics"

# Expected output: Database connection added successfully
```

### Step 7: Generate Sample Data

For development and testing, we'll generate a smaller dataset:

```bash
# Generate 1M interactions and 100K users (smaller dataset for testing)
docker exec goodnote-spark-master python /opt/spark-apps/scripts/generate_data.py \
    --interactions 1000000 \
    --metadata 100000 \
    --output-dir /opt/spark-data/raw

# Expected output:
# Generating 1,000,000 user interactions...
# Progress: 100% |████████████████████| 1000000/1000000
# Interactions saved to: /opt/spark-data/raw/interactions/
#
# Generating 100,000 user metadata records...
# Progress: 100% |████████████████████| 100000/100000
# Metadata saved to: /opt/spark-data/raw/metadata/
#
# Sample data generated successfully!
# Total size: 2.5 GB
```

**For full-scale testing (1TB dataset):**
```bash
# This will take several hours and require 1+ TB storage
docker exec goodnote-spark-master python /opt/spark-apps/scripts/generate_data.py \
    --interactions 10000000000 \
    --metadata 10000000 \
    --output-dir /opt/spark-data/raw
```

### Step 8: Run Spark ETL Jobs

#### Option A: Run All Jobs Sequentially

```bash
# Run all jobs at once
docker exec goodnote-spark-master /opt/spark-apps/scripts/run_all_jobs.sh

# Expected output:
# =========================================
# GoodNote Analytics - Running All Jobs
# =========================================
# [1/4] Running Data Processing Job...
# Job 1 completed in 12 minutes
# [2/4] Running User Engagement Job...
# Job 2 completed in 8 minutes
# [3/4] Running Performance Metrics Job...
# Job 3 completed in 6 minutes
# [4/4] Running Session Analysis Job...
# Job 4 completed in 10 minutes
# =========================================
# All jobs completed successfully!
# =========================================
```

#### Option B: Run Jobs Individually

```bash
# Job 1: Data Processing
docker exec goodnote-spark-master spark-submit \
    --master spark://spark-master:7077 \
    --conf spark.sql.adaptive.enabled=true \
    /opt/spark-apps/src/jobs/01_data_processing.py \
    --input-interactions /opt/spark-data/raw/interactions \
    --input-metadata /opt/spark-data/raw/metadata \
    --output /opt/spark-data/processed/interactions_enriched

# Job 2: User Engagement
docker exec goodnote-spark-master spark-submit \
    --master spark://spark-master:7077 \
    /opt/spark-apps/src/jobs/02_user_engagement.py \
    --input /opt/spark-data/processed/interactions_enriched

# Job 3: Performance Metrics
docker exec goodnote-spark-master spark-submit \
    --master spark://spark-master:7077 \
    /opt/spark-apps/src/jobs/03_performance_metrics.py \
    --input /opt/spark-data/processed/interactions_enriched

# Job 4: Session Analysis
docker exec goodnote-spark-master spark-submit \
    --master spark://spark-master:7077 \
    /opt/spark-apps/src/jobs/04_session_analysis.py \
    --input /opt/spark-data/processed/interactions_enriched
```

### Step 9: Import Superset Dashboards

```bash
# Import pre-configured dashboards
docker exec goodnote-superset superset import-dashboards \
    -p /app/superset_home/dashboards/01_executive_overview.json

docker exec goodnote-superset superset import-dashboards \
    -p /app/superset_home/dashboards/02_user_engagement.json

docker exec goodnote-superset superset import-dashboards \
    -p /app/superset_home/dashboards/03_performance_monitoring.json

docker exec goodnote-superset superset import-dashboards \
    -p /app/superset_home/dashboards/04_session_analytics.json

# Expected output: Dashboards imported successfully
```

### Step 10: Verify Setup

```bash
# Check data in PostgreSQL
docker exec goodnote-postgres psql -U analytics_user -d analytics -c \
    "SELECT COUNT(*) FROM goodnote_analytics.daily_active_users;"

# Expected output:
#  count
# -------
#    365
# (1 row)

# Check Spark job history
curl http://localhost:18080/api/v1/applications
# Should return JSON with completed applications

# Check Superset dashboards
curl http://localhost:8088/api/v1/dashboard/
# Should return JSON with dashboard list
```

---

## Verification

### Access Web Interfaces

#### 1. Spark Master UI
- **URL:** http://localhost:8080
- **Purpose:** Monitor Spark cluster status
- **What to check:**
  - Workers: 2 workers running
  - Status: ALIVE
  - Memory: 32 GB total (2 × 16 GB)
  - Cores: 16 cores total (2 × 8)

#### 2. Spark Application UI
- **URL:** http://localhost:4040 (when job is running)
- **Purpose:** Monitor active Spark job execution
- **What to check:**
  - Jobs: List of completed/running jobs
  - Stages: Stage progress and metrics
  - Storage: Cached RDDs/DataFrames
  - Executors: Executor resource usage

#### 3. Spark History Server
- **URL:** http://localhost:18080
- **Purpose:** Review completed Spark jobs
- **What to check:**
  - Application list
  - Job timelines
  - Stage details
  - Task metrics

#### 4. Apache Superset
- **URL:** http://localhost:8088
- **Credentials:** admin / admin
- **Purpose:** Interactive dashboards
- **What to check:**
  - Dashboards: 4 dashboards visible
  - Datasets: Connected to PostgreSQL
  - Charts: Rendering correctly
  - SQL Lab: Can query data

#### 5. Jupyter Notebook
- **URL:** http://localhost:8888
- **Token:** Check logs with `docker logs goodnote-jupyter`
- **Purpose:** Interactive development
- **What to check:**
  - Can create new notebook
  - PySpark available
  - Can read sample data

#### 6. PostgreSQL (via psql)
```bash
# Connect to PostgreSQL
docker exec -it goodnote-postgres psql -U analytics_user -d analytics

# Run sample query
SELECT date, dau FROM goodnote_analytics.daily_active_users ORDER BY date DESC LIMIT 10;

# Exit
\q
```

### Run Tests

```bash
# Run unit tests
docker exec goodnote-spark-master pytest /opt/spark-apps/tests/unit -v

# Run integration tests
docker exec goodnote-spark-master pytest /opt/spark-apps/tests/integration -v

# Expected output:
# tests/unit/test_data_processing.py::test_broadcast_join PASSED
# tests/unit/test_user_engagement.py::test_dau_calculation PASSED
# ...
# ========================= 15 passed in 30.5s =========================
```

---

## Troubleshooting

### Common Issues

#### Issue 1: Docker Containers Won't Start

**Symptoms:**
```bash
docker-compose ps
# Shows containers as "Restarting" or "Exited"
```

**Solutions:**
```bash
# Check logs for specific container
docker logs goodnote-spark-master

# Common causes:
# - Insufficient memory: Increase Docker memory limit (Docker Desktop → Settings → Resources)
# - Port conflicts: Check if ports 8080, 5432, 8088 are already in use
# - Permission issues: Ensure user is in docker group (sudo usermod -aG docker $USER)

# Restart all services
docker compose down
docker compose up -d
```

#### Issue 2: Spark Job Fails with OOM Error

**Symptoms:**
```
ERROR Executor: Exception in task 1.0 in stage 3.0
java.lang.OutOfMemoryError: Java heap space
```

**Solutions:**
```bash
# Increase executor memory
docker compose down
# Edit compose.yml:
# SPARK_WORKER_MEMORY=24G  # Increase from 16G
# SPARK_EXECUTOR_MEMORY=24g
docker compose up -d

# Or reduce dataset size for testing
docker exec goodnote-spark-master python /opt/spark-apps/scripts/generate_data.py \
    --interactions 100000 \  # Smaller dataset
    --metadata 10000
```

#### Issue 3: PostgreSQL Connection Refused

**Symptoms:**
```
psycopg2.OperationalError: could not connect to server: Connection refused
```

**Solutions:**
```bash
# Check PostgreSQL is running
docker exec goodnote-postgres pg_isready -U analytics_user

# If not ready, check logs
docker logs goodnote-postgres

# Restart PostgreSQL
docker compose restart postgres

# Wait 30 seconds and retry
```

#### Issue 4: Superset Dashboard Shows No Data

**Symptoms:**
- Charts show "No data"
- SQL Lab queries return empty results

**Solutions:**
```bash
# Verify data exists in PostgreSQL
docker exec goodnote-postgres psql -U analytics_user -d analytics -c \
    "SELECT COUNT(*) FROM goodnote_analytics.daily_active_users;"

# If count is 0, re-run Spark jobs
docker exec goodnote-spark-master /opt/spark-apps/scripts/run_all_jobs.sh

# Clear Superset cache
docker exec goodnote-superset superset cache-clear

# Refresh browser and retry
```

#### Issue 5: Spark UI Not Accessible

**Symptoms:**
- Browser shows "Connection refused" at http://localhost:8080

**Solutions:**
```bash
# Check Spark Master is running
docker ps | grep spark-master

# Check port mapping
docker port goodnote-spark-master
# Should show: 8080/tcp -> 0.0.0.0:8080

# If not mapped correctly, restart
docker compose down
docker compose up -d

# Check firewall (Linux)
sudo ufw allow 8080/tcp
```

### Getting Help

If you're still experiencing issues:

1. **Check logs:**
   ```bash
   docker compose logs --tail=100 <service-name>
   ```

2. **Review documentation:**
   - [TROUBLESHOOTING.md](./docs/TROUBLESHOOTING.md)
   - [GitHub Issues](https://github.com/your-repo/issues)

3. **Community support:**
   - Stack Overflow (tag: apache-spark, superset)
   - Apache Spark mailing list
   - Superset Slack community

---

## Next Steps

After successful setup:

1. **Explore Dashboards:**
   - Navigate to http://localhost:8088
   - Review the 4 pre-built dashboards
   - Experiment with filters and drill-downs

2. **Run Spark UI Analysis:**
   - Review [OPTIMIZATION_REPORT.md](./docs/OPTIMIZATION_REPORT.md)
   - Take screenshots of Spark UI
   - Identify optimization opportunities

3. **Develop Custom Queries:**
   - Use SQL Lab in Superset
   - Create new charts and dashboards
   - Export results to CSV

4. **Read Full Documentation:**
   - [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md)
   - [ARCHITECTURE.md](./ARCHITECTURE.md)
   - [SUPERSET_GUIDE.md](./docs/SUPERSET_GUIDE.md)

---

## Cleanup

### Stop Services

```bash
# Stop all containers
docker compose down

# Stop and remove volumes (deletes all data!)
docker compose down -v
```

### Remove Generated Data

```bash
# Remove all generated data
rm -rf data/raw/*
rm -rf data/processed/*
rm -rf logs/*

# Warning: This will delete all your data!
```

### Complete Cleanup

```bash
# Remove everything (containers, images, volumes, networks)
docker compose down -v --rmi all

# Remove data directory
rm -rf data/

# This will require rebuilding everything from scratch
```

---

## Production Deployment

For production deployment, refer to:
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Deployment strategies
- [PRODUCTION_GUIDE.md](./docs/PRODUCTION_GUIDE.md) - Production checklist
- [SECURITY.md](./docs/SECURITY.md) - Security best practices

---

**Document Version:** 1.0
**Last Updated:** 2025-11-13
**Estimated Setup Time:** 30-60 minutes
