# Environment Variables Documentation

This document provides detailed information about all environment variables used in the GoodNote Analytics Platform.

## Table of Contents

- [Quick Start](#quick-start)
- [PostgreSQL Configuration](#postgresql-configuration)
- [Apache Spark Configuration](#apache-spark-configuration)
- [Apache Superset Configuration](#apache-superset-configuration)
- [Redis Configuration](#redis-configuration)
- [Data Paths](#data-paths)
- [Job Configuration](#job-configuration)
- [Logging Configuration](#logging-configuration)
- [Testing Configuration](#testing-configuration)
- [Production Settings](#production-settings)
- [Docker Compose Settings](#docker-compose-settings)

---

## Quick Start

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Update the following critical variables in `.env`:
   - `POSTGRES_PASSWORD` - Change from default
   - `SUPERSET_ADMIN_PASSWORD` - Change from default
   - `SUPERSET_SECRET_KEY` - Generate with: `openssl rand -base64 42`

3. Start the services:
   ```bash
   docker-compose up -d
   ```

---

## PostgreSQL Configuration

PostgreSQL is used as the primary analytics database for storing aggregated metrics.

### Connection Settings

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `POSTGRES_HOST` | `postgres` | PostgreSQL hostname | Yes |
| `POSTGRES_PORT` | `5432` | PostgreSQL port | Yes |
| `POSTGRES_DB` | `analytics` | Database name | Yes |
| `POSTGRES_USER` | `analytics_user` | Database username | Yes |
| `POSTGRES_PASSWORD` | `change_this_password_in_production` | Database password | Yes |
| `POSTGRES_SCHEMA` | `public` | Schema name | Yes |

### Usage Examples

**In PySpark:**
```python
from src.config.database_config import get_postgres_connection_props

props = get_postgres_connection_props()
df.write.jdbc(url=props["url"], table="metrics", properties=props)
```

**Connection String:**
```
jdbc:postgresql://postgres:5432/analytics
```

### Security Notes

- **DO NOT** use default passwords in production
- Use strong passwords (minimum 16 characters, mixed case, numbers, symbols)
- Consider using PostgreSQL's `pg_hba.conf` for IP-based access control
- Enable SSL/TLS in production (set `POSTGRES_SSL_MODE=require`)

---

## Apache Spark Configuration

Apache Spark is the core distributed processing engine for all analytics jobs.

### Master Settings

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `SPARK_MASTER_HOST` | `spark-master` | Spark master hostname | Yes |
| `SPARK_MASTER_PORT` | `7077` | Spark master port | Yes |
| `SPARK_MASTER_WEBUI_PORT` | `8080` | Spark UI port | Yes |

### Worker Settings

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `SPARK_WORKER_CORES` | `2` | CPU cores per worker | Yes |
| `SPARK_WORKER_MEMORY` | `2g` | Memory per worker | Yes |
| `SPARK_WORKER_INSTANCES` | `2` | Number of worker instances | Yes |

**Sizing Guidelines:**
- **Development**: 2 workers × 2 cores × 2GB = 4 cores, 4GB total
- **Production**: Scale based on data volume
  - 10M rows: 4 workers × 4 cores × 8GB
  - 100M rows: 8 workers × 8 cores × 16GB
  - 1B rows: 16 workers × 16 cores × 32GB

### Application Settings

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `SPARK_DRIVER_MEMORY` | `1g` | Driver process memory | Yes |
| `SPARK_EXECUTOR_MEMORY` | `2g` | Executor process memory | Yes |
| `SPARK_EXECUTOR_CORES` | `2` | Cores per executor | Yes |

**Memory Tuning:**
```
Total Executor Memory = SPARK_EXECUTOR_MEMORY × Number of Executors
Recommended: 3-5× input data size for joins and aggregations
```

### Spark SQL Settings

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `SPARK_SQL_SHUFFLE_PARTITIONS` | `200` | Shuffle partition count | Yes |
| `SPARK_SQL_ADAPTIVE_ENABLED` | `true` | Enable Adaptive Query Execution | Yes |
| `SPARK_SQL_AUTOBROADCAST_JOIN_THRESHOLD` | `104857600` (100MB) | Auto broadcast threshold | Yes |

**Optimization Notes:**
- **Shuffle Partitions**: Set to 2-3× number of cores
  - Too low: Large partitions, OOM errors
  - Too high: Small partitions, overhead
- **AQE**: Dynamically optimizes query plans at runtime
- **Broadcast Threshold**: Smaller tables are broadcast to avoid shuffle

### Usage Examples

**Submit a Spark Job:**
```bash
spark-submit \
  --master spark://spark-master:7077 \
  --driver-memory $SPARK_DRIVER_MEMORY \
  --executor-memory $SPARK_EXECUTOR_MEMORY \
  --executor-cores $SPARK_EXECUTOR_CORES \
  src/jobs/01_data_processing.py
```

**Access Spark UI:**
```
http://localhost:8080
```

---

## Apache Superset Configuration

Apache Superset provides interactive dashboards for visualizing analytics metrics.

### Admin Credentials

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `SUPERSET_ADMIN_USERNAME` | `admin` | Admin username | Yes |
| `SUPERSET_ADMIN_PASSWORD` | `change_this_password_in_production` | Admin password | Yes |
| `SUPERSET_ADMIN_EMAIL` | `admin@example.com` | Admin email | Yes |
| `SUPERSET_ADMIN_FIRSTNAME` | `Admin` | Admin first name | Yes |
| `SUPERSET_ADMIN_LASTNAME` | `User` | Admin last name | Yes |

**Security Best Practices:**
- Use strong password (minimum 12 characters)
- Enable MFA in production
- Create role-based access control (RBAC) for team members
- Rotate passwords regularly (every 90 days)

### Application Settings

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `SUPERSET_SECRET_KEY` | `CHANGE_THIS...` | Flask secret key | Yes |
| `SUPERSET_DATABASE_URI` | `postgresql+psycopg2://...` | Metadata database | Yes |
| `SUPERSET_REDIS_HOST` | `redis` | Redis cache hostname | Yes |
| `SUPERSET_REDIS_PORT` | `6379` | Redis port | Yes |
| `SUPERSET_REDIS_DB` | `1` | Redis database number | Yes |
| `SUPERSET_WEBSERVER_PORT` | `8088` | Web server port | Yes |
| `SUPERSET_LOAD_EXAMPLES` | `no` | Load example datasets | No |

**Generate Secret Key:**
```bash
openssl rand -base64 42
```

**Access Superset:**
```
http://localhost:8088
Login: admin / (your SUPERSET_ADMIN_PASSWORD)
```

---

## Redis Configuration

Redis is used for Superset query result caching and session storage.

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `REDIS_HOST` | `redis` | Redis hostname | Yes |
| `REDIS_PORT` | `6379` | Redis port | Yes |
| `REDIS_PASSWORD` | `` (empty) | Redis password | No |

**Production Recommendations:**
- Set `REDIS_PASSWORD` for security
- Configure `maxmemory-policy` to `allkeys-lru`
- Set `maxmemory` to 25-50% of available RAM
- Enable Redis persistence (AOF or RDB)

---

## Data Paths

Configure paths for input data, processed data, and outputs.

### Input Paths

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `DATA_INPUT_INTERACTIONS` | `/app/data/raw/user_interactions.csv` | User interactions CSV | Yes |
| `DATA_INPUT_METADATA` | `/app/data/raw/user_metadata.csv` | User metadata CSV | Yes |

### Processed Paths

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `DATA_PROCESSED_ENRICHED` | `/app/data/processed/enriched_interactions.parquet` | Enriched Parquet data | Yes |

### Output Paths

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `DATA_OUTPUT_METRICS` | `/app/data/output/metrics` | Metrics output directory | Yes |

**Path Guidelines:**
- Use `/app` prefix for Docker container paths
- Mount host directories via `docker-compose.yml` volumes
- Ensure directories exist before running jobs
- Use Parquet format for processed data (columnar, compressed)

---

## Job Configuration

Configure behavior of Spark analytics jobs.

### ETL Settings

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `ETL_BATCH_SIZE` | `10000` | Database write batch size | Yes |
| `ETL_NUM_PARTITIONS` | `4` | Parallel write partitions | Yes |
| `ETL_WRITE_MODE` | `overwrite` | Write mode (overwrite/append) | Yes |

**Batch Size Tuning:**
- Small batch (1000): Slower, less memory
- Large batch (50000): Faster, more memory
- Recommended: 10000-20000 for most workloads

### Session Analysis

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `SESSION_TIMEOUT_SECONDS` | `1800` (30 min) | Session inactivity timeout | Yes |
| `SESSION_BOUNCE_THRESHOLD` | `1` | Actions before non-bounce | Yes |

**Session Timeout:**
- 1800s (30 min): Standard web analytics
- 3600s (1 hour): Mobile apps, longer sessions
- 600s (10 min): E-commerce, shorter sessions

### Cohort Analysis

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `COHORT_RETENTION_WEEKS` | `26` | Weeks to track retention | Yes |
| `COHORT_PERIOD` | `weekly` | Cohort period (weekly/monthly) | Yes |

**Retention Tracking:**
- 26 weeks: ~6 months, standard for SaaS
- 52 weeks: 1 year, for annual subscriptions
- 13 weeks: 3 months, for rapid iteration

### Performance Analysis

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `PERFORMANCE_PERCENTILES` | `0.5,0.95,0.99` | Percentiles to calculate | Yes |
| `PERFORMANCE_ANOMALY_THRESHOLD` | `3.0` | Z-score threshold | Yes |
| `PERFORMANCE_ANOMALY_SEVERITY_CRITICAL` | `4.0` | Critical severity Z-score | Yes |
| `PERFORMANCE_ANOMALY_SEVERITY_HIGH` | `3.5` | High severity Z-score | Yes |
| `PERFORMANCE_ANOMALY_SEVERITY_MEDIUM` | `3.0` | Medium severity Z-score | Yes |

**Anomaly Thresholds:**
- Z-score = 2.0: 95% confidence (more sensitive)
- Z-score = 3.0: 99.7% confidence (recommended)
- Z-score = 4.0: 99.99% confidence (very strict)

### Power Users

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `POWER_USER_PERCENTILE` | `0.99` (top 1%) | Power user threshold | Yes |

---

## Logging Configuration

Configure application logging behavior.

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `LOG_LEVEL` | `INFO` | Log level (DEBUG/INFO/WARN/ERROR) | Yes |
| `LOG_FORMAT` | `%(asctime)s...` | Python logging format | Yes |
| `LOG_FILE_PATH` | `/app/logs/spark-jobs.log` | Log file path | Yes |

**Log Levels:**
- `DEBUG`: Detailed information, debugging
- `INFO`: Informational messages (recommended)
- `WARN`: Warning messages
- `ERROR`: Error messages only

**Log Rotation:**
```python
# Recommended: Use RotatingFileHandler
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    LOG_FILE_PATH,
    maxBytes=100*1024*1024,  # 100MB
    backupCount=10
)
```

---

## Testing Configuration

Configure test execution behavior.

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `TEST_MODE` | `false` | Enable test mode | No |
| `TEST_SAMPLE_SIZE` | `1000` | Sample size for tests | No |
| `PYTEST_TIMEOUT` | `300` (5 min) | Test timeout seconds | No |

**Test Mode:**
- Set `TEST_MODE=true` to use sample data
- Reduces test execution time
- Useful for CI/CD pipelines

---

## Production Settings

Additional configuration for production deployments (commented out in `.env.example`).

### Security

```bash
SSL_ENABLED=true
SSL_CERT_PATH=/app/certs/server.crt
SSL_KEY_PATH=/app/certs/server.key
```

### Monitoring

```bash
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
SPARK_METRICS_NAMESPACE=goodnote_analytics
```

### Resource Limits

```bash
MAX_CONCURRENT_JOBS=5
JOB_TIMEOUT_SECONDS=7200  # 2 hours
```

### Backup

```bash
BACKUP_ENABLED=true
BACKUP_SCHEDULE="0 2 * * *"  # Daily at 2 AM
BACKUP_RETENTION_DAYS=30
```

### Alerts

```bash
ALERT_EMAIL=alerts@example.com
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
PAGERDUTY_API_KEY=your_pagerduty_api_key
```

---

## Docker Compose Settings

Configure Docker Compose project settings.

### Project

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `COMPOSE_PROJECT_NAME` | `goodnote-analytics` | Docker Compose project name | Yes |
| `COMPOSE_FILE` | `docker-compose.yml` | Compose file path | Yes |

### Container Names

| Variable | Default | Description |
|----------|---------|-------------|
| `CONTAINER_SPARK_MASTER` | `goodnote-spark-master` | Spark master container |
| `CONTAINER_SPARK_WORKER_1` | `goodnote-spark-worker-1` | Spark worker 1 container |
| `CONTAINER_SPARK_WORKER_2` | `goodnote-spark-worker-2` | Spark worker 2 container |
| `CONTAINER_POSTGRES` | `goodnote-postgres` | PostgreSQL container |
| `CONTAINER_SUPERSET` | `goodnote-superset` | Superset container |
| `CONTAINER_REDIS` | `goodnote-redis` | Redis container |

### Network

| Variable | Default | Description |
|----------|---------|-------------|
| `NETWORK_NAME` | `goodnote-network` | Docker network name |

### Volumes

| Variable | Default | Description |
|----------|---------|-------------|
| `VOLUME_POSTGRES_DATA` | `postgres_data` | PostgreSQL data volume |
| `VOLUME_SPARK_WORK` | `spark_work` | Spark work directory volume |
| `VOLUME_REDIS_DATA` | `redis_data` | Redis data volume |

---

## Environment Validation

Use this checklist to validate your environment configuration:

### Development Environment

- [ ] `.env` file created from `.env.example`
- [ ] `POSTGRES_PASSWORD` changed from default
- [ ] `SUPERSET_ADMIN_PASSWORD` changed from default
- [ ] `SUPERSET_SECRET_KEY` generated
- [ ] Docker containers start successfully
- [ ] PostgreSQL accessible on port 5432
- [ ] Spark UI accessible on port 8080
- [ ] Superset accessible on port 8088

### Production Environment

- [ ] All development checks passed
- [ ] SSL/TLS certificates configured
- [ ] Strong passwords (16+ characters)
- [ ] Backup strategy configured
- [ ] Monitoring tools configured (Prometheus/Grafana)
- [ ] Alert channels configured (Email/Slack/PagerDuty)
- [ ] Resource limits set appropriately
- [ ] Log rotation configured
- [ ] Network security groups configured
- [ ] Database connection pooling configured

---

## Troubleshooting

### Common Issues

**Issue: PostgreSQL connection refused**
```
Solution: Check POSTGRES_HOST and POSTGRES_PORT are correct.
Verify container is running: docker ps | grep postgres
```

**Issue: Spark out of memory errors**
```
Solution: Increase SPARK_EXECUTOR_MEMORY and SPARK_DRIVER_MEMORY
Check data volume and partition count
```

**Issue: Superset can't connect to database**
```
Solution: Verify SUPERSET_DATABASE_URI is correct
Check PostgreSQL is accessible from Superset container
Ensure superset database exists: CREATE DATABASE superset;
```

**Issue: Redis connection timeout**
```
Solution: Check REDIS_HOST and REDIS_PORT
Verify Redis container is running
Check network connectivity between containers
```

---

## Additional Resources

- [Apache Spark Configuration](https://spark.apache.org/docs/latest/configuration.html)
- [PostgreSQL Configuration](https://www.postgresql.org/docs/15/runtime-config.html)
- [Apache Superset Installation](https://superset.apache.org/docs/installation/installing-superset-using-docker-compose)
- [Redis Configuration](https://redis.io/docs/management/config/)
- [Docker Compose](https://docs.docker.com/compose/)

---

**Last Updated:** 2025-11-13
**Version:** 1.0
