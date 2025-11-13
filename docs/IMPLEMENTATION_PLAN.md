# GoodNote Challenge - Implementation Plan

## Executive Summary

This document outlines a comprehensive implementation plan for the GoodNote Data Engineering Challenge. The solution leverages **Apache Spark 3.5**, **PostgreSQL**, and **Apache Superset** to process and analyze 1TB+ of user interaction data, providing actionable insights through interactive dashboards.

**Estimated Timeline:** 8-10 hours for complete implementation
**Technology Stack:** 100% open-source, runs locally via Docker

---

## Table of Contents

1. [Technology Stack](#technology-stack)
2. [Implementation Strategy](#implementation-strategy)
3. [Task-by-Task Approach](#task-by-task-approach)
4. [Optimization Techniques](#optimization-techniques)
5. [Development Phases](#development-phases)
6. [Success Metrics](#success-metrics)

---

## Technology Stack

### Core Processing Layer
- **Apache Spark 3.5.x (PySpark)** - Distributed data processing
- **Python 3.9+** - Primary programming language
- **Delta Lake** (optional) - ACID transactions and time travel

### Data Storage Layer
- **Parquet Format** - Columnar storage with snappy compression
- **PostgreSQL 15** - OLAP analytics database (indexed, optimized)
- **Local Filesystem** - Raw CSV and intermediate Parquet files

### Visualization & BI Layer
- **Apache Superset 3.x** - Interactive dashboards and SQL Lab
- **Redis 7** - Superset caching layer

### Development & Testing
- **Docker Compose** - Multi-container orchestration
- **Jupyter Notebooks** - Interactive development and exploration
- **pytest + chispa** - Unit testing framework for PySpark
- **pytest-spark** - Spark testing utilities

### Monitoring & Analysis
- **Spark UI** (ports 8080, 4040, 18080) - Job monitoring and optimization
- **Spark History Server** - Historical job analysis
- **PostgreSQL pgAdmin** (optional) - Database management

---

## Implementation Strategy

### Overall Approach

The implementation follows a **bottom-up, iterative approach**:

1. **Foundation First** - Setup infrastructure (Docker, Spark, PostgreSQL, Superset)
2. **Data Quality** - Generate realistic test datasets with known characteristics
3. **Incremental Development** - Build and test each Spark job independently
4. **Optimization Cycle** - Measure → Identify bottlenecks → Optimize → Validate
5. **Visualization Last** - Connect validated data to Superset dashboards

### Key Design Principles

1. **Scalability** - All solutions designed for TB-scale data
2. **Testability** - Unit tests for business logic, integration tests for pipelines
3. **Observability** - Comprehensive logging, metrics, and Spark UI analysis
4. **Production-Ready** - Error handling, data quality checks, idempotency
5. **Documentation** - Code comments, README files, architecture diagrams

---

## Task-by-Task Approach

### Task 1: Data Processing and Optimization

**Objective:** Efficiently join 1TB interactions with 100GB metadata, handling data skew.

#### 1.a Join Strategy with Skew Handling

**Problem Analysis:**
- Power users (top 1%) may have 100x-1000x more interactions
- Naive join causes executor OOM on skewed partitions
- Need to distribute hot keys across multiple partitions

**Solution: Multi-Pronged Approach**

```python
# Strategy A: Broadcast Join (for smaller table)
# - Metadata (100GB) can be broadcast if executors have 16GB+ memory
# - Avoids shuffle entirely for smaller table
# - Configuration:
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "10MB")  # Conservative
# Then manually broadcast if needed:
from pyspark.sql.functions import broadcast
result = interactions.join(broadcast(metadata), "user_id")

# Strategy B: Salting for Skewed Keys
# Step 1: Identify hot keys
hot_keys = interactions.groupBy("user_id") \
    .count() \
    .filter(col("count") > percentile_threshold) \
    .select("user_id")

# Step 2: Salt hot keys (add random suffix 0-N)
SALT_FACTOR = 10
interactions_salted = interactions.join(broadcast(hot_keys), "user_id", "left") \
    .withColumn("salt", when(col("user_id").isNotNull(),
                             (rand() * SALT_FACTOR).cast("int"))
                        .otherwise(lit(0))) \
    .withColumn("user_id_salted", concat(col("user_id"), lit("_"), col("salt")))

# Step 3: Explode metadata to match salt range
metadata_exploded = metadata.join(broadcast(hot_keys), "user_id", "left") \
    .withColumn("salt", when(col("user_id").isNotNull(),
                             explode(array([lit(i) for i in range(SALT_FACTOR)])))
                        .otherwise(lit(0))) \
    .withColumn("user_id_salted", concat(col("user_id"), lit("_"), col("salt")))

# Step 4: Join on salted key
joined = interactions_salted.join(metadata_exploded, "user_id_salted") \
    .drop("salt", "user_id_salted")

# Strategy C: Adaptive Query Execution (Spark 3.x)
# Let Spark automatically detect and handle skew
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.skewedPartitionFactor", "5")
spark.conf.set("spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes", "256MB")
```

**Join Strategy Decision Tree:**
- Metadata < 10GB → Use broadcast join
- Metadata 10-100GB + Executors have sufficient memory → Try broadcast with increased threshold
- Skew detected (max task time > 3x median) → Apply salting to hot keys
- No skew detected → Standard sort-merge join with AQE

#### 1.b Shuffle Optimization

**Techniques to Minimize Shuffle:**

1. **Predicate Pushdown** - Filter early
```python
# Bad: Filter after join (shuffles unnecessary data)
df = interactions.join(metadata, "user_id").filter(col("country") == "US")

# Good: Filter before join (reduces shuffle volume)
interactions_filtered = interactions.filter(col("timestamp") >= "2023-01-01")
metadata_us = metadata.filter(col("country") == "US")
df = interactions_filtered.join(metadata_us, "user_id")
```

2. **Column Pruning** - Select only needed columns
```python
# Bad: Select all columns
df = interactions.select("*").join(metadata.select("*"), "user_id")

# Good: Select only required columns
interactions_slim = interactions.select("user_id", "timestamp", "duration_ms")
metadata_slim = metadata.select("user_id", "country", "device_type")
df = interactions_slim.join(metadata_slim, "user_id")
```

3. **Optimal Shuffle Partitions**
```python
# Calculate optimal shuffle partitions
# Rule of thumb: 128MB - 200MB per partition
total_data_size_mb = 1_000_000  # 1TB in MB
partition_size_mb = 128
optimal_partitions = total_data_size_mb / partition_size_mb
spark.conf.set("spark.sql.shuffle.partitions", str(int(optimal_partitions)))

# For this dataset: 1,000,000 MB / 128 MB ≈ 7,800 partitions
# Start with 8,000 and adjust based on Spark UI
```

4. **Repartition by Join Key Before Join**
```python
# Repartition on join key to minimize shuffle
interactions_repart = interactions.repartition("user_id")
metadata_repart = metadata.repartition("user_id")
joined = interactions_repart.join(metadata_repart, "user_id")
```

5. **Coalesce for Reducing Partitions**
```python
# After filtering that reduces data size significantly
# Bad: repartition (full shuffle)
df_small = df_large.filter(col("country") == "US").repartition(100)

# Good: coalesce (no shuffle, just combines partitions)
df_small = df_large.filter(col("country") == "US").coalesce(100)
```

**Avoiding OOM Errors:**

1. **Increase Executor Memory**
```python
spark.conf.set("spark.executor.memory", "16g")
spark.conf.set("spark.executor.memoryOverhead", "2g")
spark.conf.set("spark.driver.memory", "8g")
```

2. **Tune Memory Fractions**
```python
# Increase storage memory for caching
spark.conf.set("spark.memory.fraction", "0.8")  # Up from 0.6
spark.conf.set("spark.memory.storageFraction", "0.3")  # 30% for cache
```

3. **Enable Off-Heap Memory**
```python
spark.conf.set("spark.memory.offHeap.enabled", "true")
spark.conf.set("spark.memory.offHeap.size", "4g")
```

4. **Monitor and Adjust**
- Watch Spark UI → Storage tab for cache usage
- Check GC time (should be < 10% of task time)
- Look for spilled memory/disk (indicates memory pressure)

#### 1.c Partitioning and Caching Strategies

**Input Data Partitioning:**

```python
# Read interactions partitioned by date (maintains source partitioning)
interactions = spark.read.parquet("data/raw/interactions/")
# Expected directory structure:
# interactions/
#   year=2023/
#     month=01/
#       day=01/
#         part-00000.parquet
#       day=02/
#         part-00000.parquet

# Read metadata partitioned by country
metadata = spark.read.parquet("data/raw/metadata/")
# Expected directory structure:
# metadata/
#   country=US/
#     part-00000.parquet
#   country=UK/
#     part-00000.parquet
```

**Output Data Partitioning:**

```python
# Partition by date and country for time-series + geographic queries
joined_df.write \
    .partitionBy("date", "country") \
    .parquet("data/processed/interactions_enriched/")

# For repeated user lookups, consider bucketing
metadata.write \
    .bucketBy(100, "user_id") \
    .sortBy("user_id") \
    .saveAsTable("metadata_bucketed")
```

**Caching Strategy:**

```python
# Cache small, frequently reused DataFrames
from pyspark.storagelevel import StorageLevel

# Metadata: Cache in memory (reused in all jobs)
metadata_cached = metadata.persist(StorageLevel.MEMORY_AND_DISK)

# Joined data: Cache only if reused 3+ times in same job
joined_df = interactions.join(broadcast(metadata_cached), "user_id")
if multiple_aggregations_needed:
    joined_df.persist(StorageLevel.MEMORY_AND_DISK_SER)  # Serialized to save space

# Best practices:
# 1. Cache AFTER filtering and column pruning
# 2. Use MEMORY_AND_DISK (not MEMORY_ONLY) to avoid recomputation
# 3. Use serialized storage if memory constrained
# 4. Call .count() or .cache() to trigger caching
# 5. Unpersist when no longer needed: df.unpersist()
```

**Partitioning Decision Matrix:**

| Use Case | Partitioning Strategy | Reasoning |
|----------|----------------------|-----------|
| Time-series queries | Partition by date | Enables partition pruning for date ranges |
| Geographic analysis | Partition by country | Parallel processing per region |
| User lookups | Bucketing by user_id | Co-locates user data, avoids shuffle in joins |
| Large fact tables | Partition by date + bucketing | Combines benefits of both |
| Small dimension tables | No partitioning or broadcast | Overhead not worth it |

---

### Task 2: User Engagement Analysis

#### 2.a Daily/Monthly Active Users (DAU/MAU)

**Definition of "Active User":**
- User with at least 1 interaction in the time period
- Interactions include: page_view, edit, create, delete, share

**Implementation:**

```python
from pyspark.sql.functions import countDistinct, date_trunc, to_date

# DAU Calculation
dau = interactions.withColumn("date", to_date("timestamp")) \
    .groupBy("date") \
    .agg(
        countDistinct("user_id").alias("dau"),
        count("*").alias("total_interactions"),
        sum("duration_ms").alias("total_duration_ms")
    ) \
    .withColumn("avg_duration_per_user", col("total_duration_ms") / col("dau"))

# MAU Calculation
mau = interactions.withColumn("month", date_trunc("month", "timestamp")) \
    .groupBy("month") \
    .agg(
        countDistinct("user_id").alias("mau"),
        count("*").alias("total_interactions")
    )

# DAU/MAU Ratio (Stickiness)
# Join DAU with MAU on month
dau_with_month = dau.withColumn("month", date_trunc("month", "date"))
stickiness = dau_with_month.groupBy("month") \
    .agg(avg("dau").alias("avg_dau")) \
    .join(mau, "month") \
    .withColumn("stickiness_ratio", col("avg_dau") / col("mau"))
```

**Output to PostgreSQL:**

```python
# Write to PostgreSQL for Superset
dau.write \
    .format("jdbc") \
    .option("url", "jdbc:postgresql://postgres:5432/analytics") \
    .option("dbtable", "goodnote_analytics.daily_active_users") \
    .option("user", "analytics_user") \
    .option("password", "secure_password") \
    .option("driver", "org.postgresql.Driver") \
    .mode("overwrite") \
    .save()
```

#### 2.b Power Users (Top 1%)

**Outlier Handling Strategy:**
- Duration > 8 hours (28,800,000 ms) in single session → cap or flag as anomaly
- Total duration per day > 16 hours → data quality issue, investigate
- Use percentile_approx for efficient calculation on large datasets

**Implementation:**

```python
from pyspark.sql.functions import sum, percentile_approx, ntile
from pyspark.sql.window import Window

# Step 1: Filter outliers (duration > 8 hours is suspicious)
MAX_SINGLE_DURATION_MS = 8 * 60 * 60 * 1000  # 8 hours
interactions_cleaned = interactions.filter(
    col("duration_ms").between(0, MAX_SINGLE_DURATION_MS)
)

# Step 2: Calculate user engagement metrics
user_engagement = interactions_cleaned.groupBy("user_id") \
    .agg(
        sum("duration_ms").alias("total_duration_ms"),
        count("*").alias("total_interactions"),
        countDistinct("page_id").alias("unique_pages"),
        countDistinct(to_date("timestamp")).alias("days_active")
    ) \
    .withColumn("avg_duration_per_interaction",
                col("total_duration_ms") / col("total_interactions"))

# Step 3: Calculate percentile thresholds
percentiles = user_engagement.select(
    percentile_approx("total_duration_ms", [0.90, 0.95, 0.99]).alias("percentiles")
).collect()[0][0]

p90_threshold = percentiles[0]
p95_threshold = percentiles[1]
p99_threshold = percentiles[2]

# Step 4: Identify power users (top 1%)
power_users = user_engagement.filter(col("total_duration_ms") >= p99_threshold)

# Step 5: Enrich with metadata
power_users_enriched = power_users.join(metadata, "user_id") \
    .withColumn("hours_spent", col("total_duration_ms") / 3600000.0) \
    .withColumn("percentile_rank", lit(99.0))

# Step 6: Add engagement score
# Engagement Score = (normalized_duration * 0.5) + (normalized_interactions * 0.3) + (normalized_days_active * 0.2)
window_spec = Window.orderBy("total_duration_ms")
power_users_scored = power_users_enriched.withColumn(
    "duration_rank", percent_rank().over(window_spec)
).withColumn(
    "engagement_score",
    col("duration_rank") * 0.5 +
    col("total_interactions") / col("days_active") * 0.3 +
    col("days_active") * 0.2
)
```

**Scalability Considerations:**
- Use `percentile_approx` instead of `percentile` for large datasets (faster, less memory)
- Approximate accuracy: 0.01 (1%) is sufficient for top 1% calculation
- Consider sampling for initial exploration: `interactions.sample(0.1)`

#### 2.c Cohort Retention Analysis

**Cohort Definition:**
- Cohort = Users who joined in the same week
- Retention = % of cohort active in week N after joining
- Analysis period: Past 6 months (26 weeks)

**Implementation:**

```python
from pyspark.sql.functions import datediff, weekofyear, year

# Step 1: Define cohorts by join week
cohorts = metadata.withColumn(
    "cohort_week", date_trunc("week", "join_date")
).select("user_id", "cohort_week")

# Step 2: Calculate user activity weeks
user_activity = interactions.withColumn("activity_week", date_trunc("week", "timestamp")) \
    .select("user_id", "activity_week") \
    .distinct()

# Step 3: Join cohorts with activity
cohort_activity = cohorts.join(user_activity, "user_id") \
    .withColumn("weeks_since_join",
                datediff(col("activity_week"), col("cohort_week")) / 7)

# Step 4: Calculate retention rates
cohort_sizes = cohorts.groupBy("cohort_week") \
    .agg(count("user_id").alias("cohort_size"))

retention = cohort_activity.groupBy("cohort_week", "weeks_since_join") \
    .agg(countDistinct("user_id").alias("active_users")) \
    .join(cohort_sizes, "cohort_week") \
    .withColumn("retention_rate", col("active_users") / col("cohort_size") * 100) \
    .filter(col("weeks_since_join").between(0, 26))  # 6 months

# Step 5: Pivot for visualization (optional)
retention_pivot = retention.groupBy("cohort_week").pivot("weeks_since_join").agg(
    first("retention_rate")
)
```

**Visualization Strategy:**
- Heatmap in Superset: cohort_week (rows) × weeks_since_join (columns)
- Color gradient: Green (high retention) → Red (low retention)
- Enable drill-down to see cohort details

---

### Task 3: Performance Metrics

#### 3.a 95th Percentile Page Load Times by App Version

**Challenge:** Potentially hundreds of app versions (major.minor.patch)
**Solution:** Use approximate percentiles and aggregate minor versions

**Implementation:**

```python
# Calculate P50, P95, P99 for each app version
performance_by_version = interactions.groupBy("app_version", to_date("timestamp").alias("date")) \
    .agg(
        count("*").alias("total_interactions"),
        percentile_approx("duration_ms", 0.50).alias("p50_duration_ms"),
        percentile_approx("duration_ms", 0.95).alias("p95_duration_ms"),
        percentile_approx("duration_ms", 0.99).alias("p99_duration_ms"),
        avg("duration_ms").alias("avg_duration_ms"),
        stddev("duration_ms").alias("stddev_duration_ms")
    )

# Aggregate by major version for high-level view
performance_major_version = interactions.withColumn(
    "major_version", split(col("app_version"), "\\.").getItem(0)
).groupBy("major_version", to_date("timestamp").alias("date")) \
    .agg(
        percentile_approx("duration_ms", 0.95).alias("p95_duration_ms"),
        count("*").alias("total_interactions")
    )
```

**Near Real-Time Updates:**
- Use Spark Structured Streaming with tumbling windows
- Micro-batch processing: 5-minute windows
- Update PostgreSQL incrementally

```python
# Structured Streaming example (for real-time scenario)
streaming_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "user-interactions") \
    .load()

performance_stream = streaming_df.groupBy(
    window("timestamp", "5 minutes"),
    "app_version"
).agg(
    percentile_approx("duration_ms", 0.95).alias("p95_duration_ms")
)

query = performance_stream.writeStream \
    .foreachBatch(write_to_postgres) \
    .outputMode("update") \
    .start()
```

#### 3.b Device Type and Performance Correlation

**Correlation Metric:** Spearman Rank Correlation
**Reasoning:** Non-linear relationships, robust to outliers

**Implementation:**

```python
from pyspark.ml.stat import Correlation
from pyspark.ml.feature import VectorAssembler

# Step 1: Aggregate metrics by device type
device_metrics = interactions.join(metadata, "user_id") \
    .groupBy("device_type") \
    .agg(
        avg("duration_ms").alias("avg_duration"),
        percentile_approx("duration_ms", 0.95).alias("p95_duration"),
        count("*").alias("interaction_count"),
        countDistinct("user_id").alias("unique_users")
    ) \
    .withColumn("interactions_per_user", col("interaction_count") / col("unique_users"))

# Step 2: Prepare features for correlation
assembler = VectorAssembler(
    inputCols=["avg_duration", "p95_duration", "interactions_per_user"],
    outputCol="features"
)
device_features = assembler.transform(device_metrics)

# Step 3: Calculate correlation matrix
correlation_matrix = Correlation.corr(device_features, "features", "spearman")

# Step 4: More intuitive analysis - compare devices
device_comparison = device_metrics.orderBy(col("avg_duration").desc())
```

**Visualization for Non-Technical Stakeholders:**
- Bar chart: Device type (x-axis) vs Avg load time (y-axis)
- Color-code by performance: Green (fast), Yellow (medium), Red (slow)
- Add annotations: "iPad users experience 30% faster load times"

#### 3.c Anomaly Detection

**Anomaly Definition:**
- Statistical: |value - μ| > 3σ (Z-score > 3)
- Temporal: 50% increase/decrease compared to same hour last week
- Behavioral: User performs 10x more actions than their average

**Implementation:**

```python
from pyspark.sql.functions import mean, stddev, lag
from pyspark.sql.window import Window

# Method 1: Statistical Anomaly Detection (Z-score)
# Calculate baseline metrics per hour
hourly_stats = interactions.withColumn("hour", date_trunc("hour", "timestamp")) \
    .groupBy("hour") \
    .agg(
        count("*").alias("interaction_count"),
        avg("duration_ms").alias("avg_duration"),
        stddev("duration_ms").alias("stddev_duration")
    )

# Calculate Z-scores
global_avg = interactions.agg(avg("duration_ms")).collect()[0][0]
global_stddev = interactions.agg(stddev("duration_ms")).collect()[0][0]

anomalies_statistical = interactions.withColumn(
    "z_score", (col("duration_ms") - lit(global_avg)) / lit(global_stddev)
).filter(abs(col("z_score")) > 3)

# Method 2: Temporal Anomaly Detection
window_spec = Window.partitionBy("user_id").orderBy("timestamp")
user_baseline = interactions.withColumn(
    "prev_duration", lag("duration_ms", 1).over(window_spec)
).withColumn(
    "duration_change_pct",
    (col("duration_ms") - col("prev_duration")) / col("prev_duration") * 100
).filter(abs(col("duration_change_pct")) > 50)

# Method 3: Behavioral Anomaly Detection
user_avg_interactions = interactions.groupBy("user_id", to_date("timestamp").alias("date")) \
    .agg(count("*").alias("daily_interactions"))

user_baseline_behavior = user_avg_interactions.groupBy("user_id") \
    .agg(avg("daily_interactions").alias("avg_daily_interactions"))

anomalies_behavioral = user_avg_interactions.join(user_baseline_behavior, "user_id") \
    .filter(col("daily_interactions") > col("avg_daily_interactions") * 10)
```

**Automated Reporting:**
```python
# Write anomalies to PostgreSQL with severity
anomalies_combined = anomalies_statistical.select(
    col("timestamp"),
    lit("statistical").alias("anomaly_type"),
    col("user_id"),
    col("z_score").alias("severity_score")
).union(
    anomalies_behavioral.select(
        col("timestamp"),
        lit("behavioral").alias("anomaly_type"),
        col("user_id"),
        col("daily_interactions").alias("severity_score")
    )
)

# Add severity classification
anomalies_with_severity = anomalies_combined.withColumn(
    "severity",
    when(col("severity_score") > 10, "critical")
    .when(col("severity_score") > 5, "high")
    .when(col("severity_score") > 3, "medium")
    .otherwise("low")
)
```

---

### Task 4: Session-Based Analysis

**Session Definition:**
- Interactions within 30-minute window belong to same session
- Session ends after 30 minutes of inactivity

**Implementation:**

```python
from pyspark.sql.functions import lag, unix_timestamp, sum as _sum
from pyspark.sql.window import Window

# Step 1: Order interactions by user and timestamp
window_user_time = Window.partitionBy("user_id").orderBy("timestamp")

# Step 2: Calculate time difference from previous interaction
interactions_with_diff = interactions.withColumn(
    "prev_timestamp", lag("timestamp").over(window_user_time)
).withColumn(
    "time_diff_seconds",
    unix_timestamp("timestamp") - unix_timestamp("prev_timestamp")
)

# Step 3: Mark session boundaries (30 minutes = 1800 seconds)
SESSION_TIMEOUT_SECONDS = 1800
sessions = interactions_with_diff.withColumn(
    "is_new_session",
    when((col("time_diff_seconds") > SESSION_TIMEOUT_SECONDS) |
         col("prev_timestamp").isNull(), 1)
    .otherwise(0)
)

# Step 4: Assign session IDs
sessions_with_id = sessions.withColumn(
    "session_id",
    concat(
        col("user_id"),
        lit("_"),
        _sum("is_new_session").over(window_user_time).cast("string")
    )
)

# Step 5: Calculate session metrics
session_metrics = sessions_with_id.groupBy("user_id", "session_id") \
    .agg(
        min("timestamp").alias("session_start"),
        max("timestamp").alias("session_end"),
        count("*").alias("actions_per_session"),
        sum("duration_ms").alias("total_session_duration_ms"),
        countDistinct("page_id").alias("unique_pages_viewed"),
        countDistinct("action_type").alias("action_variety")
    ) \
    .withColumn(
        "session_duration_ms",
        unix_timestamp("session_end") - unix_timestamp("session_start")
    )

# Step 6: Calculate bounce rate (sessions with only 1 action)
bounce_rate = session_metrics.groupBy("user_id") \
    .agg(
        count("*").alias("total_sessions"),
        sum(when(col("actions_per_session") == 1, 1).otherwise(0)).alias("bounce_sessions")
    ) \
    .withColumn("bounce_rate", col("bounce_sessions") / col("total_sessions") * 100)

# Step 7: Aggregate by dimensions for Superset
session_analytics = sessions_with_id.join(metadata, "user_id") \
    .groupBy(
        to_date("timestamp").alias("date"),
        "device_type",
        "country",
        "subscription_type"
    ) \
    .agg(
        avg(unix_timestamp("session_end") - unix_timestamp("session_start")).alias("avg_session_duration_ms"),
        avg("actions_per_session").alias("avg_actions_per_session"),
        count("session_id").alias("total_sessions"),
        (count("session_id") / countDistinct("user_id")).alias("sessions_per_user")
    )
```

**Key Session Metrics:**
- **Session Duration** - Total time from first to last interaction
- **Actions per Session** - Number of interactions in session
- **Session Frequency** - Sessions per user per day/week/month
- **Bounce Rate** - % of single-action sessions
- **Session Depth** - Unique pages viewed per session

---

### Task 5: Spark UI Analysis

**Key Areas to Analyze:**

#### 5.a Identifying Bottlenecks

**Metric 1: Task Duration Skew**
- Navigate to: Stages → Stage Details → Task Metrics
- Look for: Max task duration >> Median task duration (>3x)
- Cause: Data skew on join/groupBy keys
- Solution: Apply salting or increase parallelism

**Metric 2: Shuffle Read/Write Volume**
- Navigate to: Stages → Stage Details → Shuffle Read/Write
- Look for: Shuffle size > 2x input data size
- Cause: Inefficient join strategy or missing predicate pushdown
- Solution: Filter earlier, use broadcast joins

**Metric 3: GC Time**
- Navigate to: Executors → Summary Metrics
- Look for: GC Time > 10% of task time
- Cause: Insufficient executor memory or too many cached objects
- Solution: Increase executor memory, tune memory fractions

**Metric 4: Spilled Memory/Disk**
- Navigate to: Stages → Stage Details → Spill (Memory/Disk)
- Look for: Any spill to disk
- Cause: Executor memory too small for shuffle operations
- Solution: Increase spark.executor.memory and spark.sql.shuffle.partitions

**Metric 5: Task Failures**
- Navigate to: Stages → Failed Tasks
- Look for: OOM errors, fetch failures, connection timeouts
- Cause: Skew, network issues, or resource constraints
- Solution: Increase resources, retry configuration

#### 5.b Optimization Hypotheses

**Example Analysis:**

```
Bottleneck #1: Stage 3 (Join) - Task Duration Skew
- Observation: Max task = 45 min, Median task = 2 min (22.5x difference)
- Hypothesis: User "u000042" has 100x more interactions than average (power user)
- Solution: Apply salting with factor=10 to distribute hot key
- Expected Impact: Reduce max task time to ~5 min (9x improvement)

Bottleneck #2: Stage 5 (GroupBy) - Excessive Shuffle
- Observation: Shuffle write = 2.5 TB for 1 TB input
- Hypothesis: GroupBy on high-cardinality key without pre-aggregation
- Solution: Add partial aggregation + increase shuffle partitions from 200 to 2000
- Expected Impact: Reduce shuffle to 1.2 TB, improve stage time by 40%

Bottleneck #3: Executor GC Time - Memory Pressure
- Observation: Executor GC time = 18% of task time
- Hypothesis: Cached DataFrame too large + insufficient memory
- Solution: Use MEMORY_AND_DISK_SER instead of MEMORY_ONLY, increase executor memory from 8g to 16g
- Expected Impact: Reduce GC time to <8%, improve overall job time by 25%
```

#### 5.c Implementation and Validation

**Before Optimization:**
```python
# Original code with issues
user_engagement = interactions.join(metadata, "user_id") \  # Skew on join
    .groupBy("user_id") \  # Skew on groupBy
    .agg(sum("duration_ms").alias("total_duration")) \
    .cache()  # MEMORY_ONLY causes GC pressure

# Spark UI Metrics (Before):
# - Total Job Time: 45 minutes
# - Stage 3 (Join): 35 minutes (max task: 30 min, median: 2 min)
# - Shuffle Write: 2.5 TB
# - GC Time: 18%
```

**After Optimization:**
```python
# Optimized code
from pyspark.sql.functions import broadcast

# 1. Broadcast small table
metadata_broadcast = broadcast(metadata)

# 2. Apply salting for hot keys
hot_users = interactions.groupBy("user_id").count().filter(col("count") > 100000)
SALT_FACTOR = 10

interactions_salted = interactions.join(broadcast(hot_users), "user_id", "left") \
    .withColumn("salt", when(col("user_id").isNotNull(), (rand() * SALT_FACTOR).cast("int")).otherwise(lit(0))) \
    .withColumn("user_id_salted", concat(col("user_id"), lit("_"), col("salt")))

metadata_exploded = metadata_broadcast.join(broadcast(hot_users), "user_id", "left") \
    .withColumn("salt", when(col("user_id").isNotNull(), explode(array([lit(i) for i in range(SALT_FACTOR)]))).otherwise(lit(0))) \
    .withColumn("user_id_salted", concat(col("user_id"), lit("_"), col("salt")))

# 3. Join with salted keys
joined = interactions_salted.join(metadata_exploded, "user_id_salted")

# 4. Increase shuffle partitions
spark.conf.set("spark.sql.shuffle.partitions", "2000")

# 5. Use efficient caching
user_engagement = joined.groupBy("user_id") \
    .agg(sum("duration_ms").alias("total_duration")) \
    .persist(StorageLevel.MEMORY_AND_DISK_SER)

# Spark UI Metrics (After):
# - Total Job Time: 18 minutes (60% improvement)
# - Stage 3 (Join): 12 minutes (max task: 5 min, median: 2 min) - 66% improvement
# - Shuffle Write: 1.2 TB (52% reduction)
# - GC Time: 7% (61% improvement)
```

---

### Task 6: Monitoring and Custom Accumulators

**Custom Accumulators for Tracking:**

```python
# Define custom accumulators
record_counter = spark.sparkContext.accumulator(0)
skipped_records = spark.sparkContext.accumulator(0)
data_quality_errors = spark.sparkContext.accumulator(0)

def process_record_with_tracking(row):
    """Process record and track metrics"""
    record_counter.add(1)

    # Data quality checks
    if row.duration_ms < 0:
        data_quality_errors.add(1)
        return None

    if row.duration_ms > 28800000:  # > 8 hours
        skipped_records.add(1)
        return None

    return row

# Apply transformation with tracking
processed_df = interactions.rdd.map(process_record_with_tracking).filter(lambda x: x is not None).toDF()

# Log accumulator values
print(f"Total records processed: {record_counter.value}")
print(f"Records skipped (outliers): {skipped_records.value}")
print(f"Data quality errors: {data_quality_errors.value}")
```

**Key Accumulators to Implement:**
1. **Record Counter** - Track total records processed
2. **Skipped Records** - Count outliers and invalid data
3. **Data Quality Errors** - Track validation failures
4. **Partition Skew Detector** - Track max/min partition sizes

---

## Optimization Techniques

### Summary of All Optimizations

| Technique | Purpose | Expected Impact |
|-----------|---------|-----------------|
| Broadcast Join | Avoid shuffle for small tables | 50-70% faster joins |
| Salting | Distribute skewed keys | Eliminate straggler tasks |
| Adaptive Query Execution | Auto-optimize join strategy | 10-30% overall improvement |
| Predicate Pushdown | Filter early | 30-50% less data to process |
| Column Pruning | Read only needed columns | 20-40% less I/O |
| Optimal Shuffle Partitions | Balance parallelism | 20-40% faster shuffles |
| Efficient Caching | Reuse computations | 2-5x faster for reused data |
| Off-Heap Memory | Reduce GC pressure | 10-20% overall improvement |
| Partitioning | Enable partition pruning | 50-90% less data scanned |
| Bucketing | Co-locate join keys | 30-60% faster repeated joins |

---

## Development Phases

### Phase 1: Infrastructure Setup (1 hour)

**Deliverables:**
- Docker Compose environment running
- Spark cluster (1 master, 2 workers) operational
- PostgreSQL database initialized with schema
- Apache Superset configured and accessible
- Sample data generated (scaled version for testing)

**Validation:**
- Access Spark UI at http://localhost:8080
- Access Superset at http://localhost:8088
- Connect to PostgreSQL: `psql -h localhost -U analytics_user -d analytics`
- Run test Spark job: `spark-submit --version`

### Phase 2: Core Data Processing (3-4 hours)

**Deliverables:**
- Job 1: Optimized join with skew handling
- Job 2: User engagement metrics (DAU/MAU/cohorts)
- Job 3: Performance analytics (percentiles, correlation)
- Job 4: Session analysis with sessionization
- All jobs write to PostgreSQL

**Validation:**
- All jobs complete successfully
- Data quality checks pass
- PostgreSQL tables populated
- Unit tests pass (>80% coverage)

### Phase 3: Superset Dashboards (2-3 hours)

**Deliverables:**
- 4 interactive dashboards configured
- 30+ charts created
- Native filters and cross-filtering enabled
- Dashboard JSONs exported for version control

**Validation:**
- All charts render correctly
- Filters work as expected
- Drill-down functionality operational
- Screenshots captured for documentation

### Phase 4: Optimization & Analysis (2 hours)

**Deliverables:**
- Spark UI analysis with screenshots
- 3+ bottlenecks identified and fixed
- Before/after performance metrics documented
- Custom accumulators implemented

**Validation:**
- Performance improvements validated
- No regressions introduced
- All optimization techniques documented

### Phase 5: Documentation (1-2 hours)

**Deliverables:**
- Comprehensive REPORT.md
- ARCHITECTURE.md with diagrams
- SUPERSET_GUIDE.md for end users
- Updated README.md
- Code comments and docstrings

**Validation:**
- Documentation is clear and complete
- Setup instructions work on fresh environment
- All code is well-commented

---

## Success Metrics

### Technical Metrics
- ✅ All Spark jobs complete without OOM errors
- ✅ Maximum task duration < 3x median task duration (no skew)
- ✅ GC time < 10% of execution time
- ✅ No memory/disk spill detected
- ✅ Unit test coverage > 80%

### Performance Metrics
- ✅ Job completion time < 2 hours for full dataset
- ✅ 50%+ improvement after optimization
- ✅ Shuffle volume < 1.5x input data size
- ✅ Query response time in Superset < 5 seconds

### Business Metrics
- ✅ All 6 tasks completed successfully
- ✅ 4 interactive dashboards operational
- ✅ Insights actionable for product team
- ✅ Documentation enables reproducibility

---

## Next Steps

1. Review and approve this implementation plan
2. Begin Phase 1: Infrastructure setup
3. Iteratively develop through Phases 2-5
4. Conduct final review and validation
5. Commit all code and documentation
6. Push to designated branch: `claude/goodnote-challenge-011CV5PhVoxvJPFFU55NUG8D`

---

## Appendix

### A. Spark Configuration Template
### B. PostgreSQL Schema DDL
### C. Superset Dashboard Designs
### D. Unit Test Examples
### E. Troubleshooting Guide

(See separate documents for detailed appendices)
