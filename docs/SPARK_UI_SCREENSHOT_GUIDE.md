# Spark UI Screenshot Capture Guide

This guide provides step-by-step instructions for capturing Spark UI screenshots for optimization analysis documentation.

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Accessing Spark UI](#accessing-spark-ui)
4. [Screenshots to Capture](#screenshots-to-capture)
5. [Before/After Comparison Strategy](#beforeafter-comparison-strategy)
6. [Screenshot Naming Convention](#screenshot-naming-convention)
7. [Analysis Checklist](#analysis-checklist)

---

## Overview

Spark UI provides detailed insights into job execution, helping identify performance bottlenecks and validate optimization improvements. This guide helps you systematically capture the necessary screenshots for comprehensive optimization analysis.

**Goal**: Document 30-60% performance improvement through before/after comparisons.

---

## Prerequisites

- ✅ Sample data generated: `python scripts/generate_sample_data.py --medium`
- ✅ Spark jobs ready to run
- ✅ Browser with screenshot capability (Chrome/Firefox recommended)
- ✅ Screenshot tool (built-in or Lightshot/Greenshot)

---

## Accessing Spark UI

### During Job Execution

When a Spark job is running, the Spark UI is accessible at:

```
http://localhost:4040
```

**Note**: The port increments if multiple Spark applications are running (4041, 4042, etc.)

### Using Docker Compose

If using the docker-compose setup:

```bash
# Start Spark cluster
docker-compose up spark-master spark-worker-1 spark-worker-2

# Submit job to cluster
docker-compose exec spark-master spark-submit \
  --master spark://spark-master:7077 \
  /app/src/jobs/01_data_processing.py

# Access Spark Master UI
http://localhost:8080

# Access application UI (link from Master UI)
http://localhost:4040
```

### Using Spark History Server (Post-Execution)

If jobs have completed:

```bash
# Start history server
$SPARK_HOME/sbin/start-history-server.sh

# Access at:
http://localhost:18080
```

---

## Screenshots to Capture

### 1. Jobs Page (Overview)

**URL**: `http://localhost:4040/jobs/`

**What to Capture**:
- Full page showing all completed jobs
- Job IDs, descriptions, and durations
- Success/failure status
- Number of stages per job

**Key Metrics**:
- Total job duration
- Number of completed stages
- Active/failed task counts

**Screenshot Name**: `01_jobs_overview_[baseline|optimized].png`

![Example: Jobs Overview](../screenshots/placeholder_jobs_overview.png)

---

### 2. Stages Page (Detailed Timeline)

**URL**: `http://localhost:4040/stages/`

**What to Capture**:
- Event timeline showing stage execution
- Stage durations and overlap
- Input/output data sizes
- Shuffle read/write sizes

**Key Metrics to Note**:
- Stage duration (expand each stage)
- Shuffle read/write bytes
- Input/output records
- Task metrics (min, median, max)

**Screenshots Needed**:
1. `02_stages_overview_[baseline|optimized].png` - Full stages list
2. `03_stage_detail_[stage_id]_[baseline|optimized].png` - Detailed view of each critical stage

---

### 3. Tasks Page (Distribution Analysis)

**URL**: `http://localhost:4040/stages/stage/?id=[stage_id]&attempt=0`

**What to Capture** (for each critical stage):
- Task execution timeline (Gantt chart)
- Task duration distribution
- Data skew indicators
- Scheduler delay, task execution time, shuffle metrics

**Key Metrics**:
- Task duration: Min / Median / Max
- GC Time percentage
- Shuffle read/write per task
- Skew ratio (Max / Median)

**Look for**:
- ✓ Green: Uniform task distribution (good)
- ⚠️ Yellow: Some variance (acceptable)
- ❌ Red: Significant skew (bad - needs salting)

**Screenshot Name**: `04_tasks_timeline_stage[stage_id]_[baseline|optimized].png`

---

### 4. Executors Page (Resource Utilization)

**URL**: `http://localhost:4040/executors/`

**What to Capture**:
- Executor list with resource allocation
- Memory usage (storage + execution)
- GC time
- Shuffle read/write totals
- Failed tasks count

**Key Metrics**:
- Memory used / available per executor
- GC time / Total duration (target: <10%)
- Shuffle spill (memory + disk)
- Active/completed/failed tasks

**Screenshot Name**: `05_executors_[baseline|optimized].png`

---

### 5. SQL Page (Query Plans)

**URL**: `http://localhost:4040/SQL/`

**What to Capture**:
- Completed queries list
- Query descriptions
- Duration for each query
- Detailed query plans (physical + logical)

**What to Click**:
1. Click on each query to see detailed plan
2. Expand "Physical Plan" section
3. Look for:
   - Broadcast joins vs. Sort-Merge joins
   - Filter pushdown
   - Column pruning
   - AQE optimizations (if enabled)

**Screenshots Needed**:
1. `06_sql_queries_overview_[baseline|optimized].png`
2. `07_sql_query_plan_[query_id]_[baseline|optimized].png` - For join queries
3. `08_sql_aqe_plan_[query_id]_optimized.png` - Show AQE transformations

---

### 6. Environment Page (Configuration)

**URL**: `http://localhost:4040/environment/`

**What to Capture**:
- Spark Properties tab (showing all spark.* configurations)
- System Properties
- Classpath entries (optional)

**Key Configurations to Verify**:
```
# Baseline (before optimization)
spark.sql.adaptive.enabled = false
spark.sql.autoBroadcastJoinThreshold = -1
spark.sql.shuffle.partitions = 200

# Optimized (after optimization)
spark.sql.adaptive.enabled = true
spark.sql.adaptive.coalescePartitions.enabled = true
spark.sql.adaptive.skewJoin.enabled = true
spark.sql.autoBroadcastJoinThreshold = 104857600
spark.sql.shuffle.partitions = 200
```

**Screenshot Name**: `09_environment_config_[baseline|optimized].png`

---

## Before/After Comparison Strategy

### Step-by-Step Process

1. **Run Baseline (Without Optimizations)**
   ```bash
   # Run with minimal optimizations
   spark-submit \
     --conf spark.sql.adaptive.enabled=false \
     --conf spark.sql.autoBroadcastJoinThreshold=-1 \
     src/jobs/01_data_processing.py
   ```

2. **Capture Baseline Screenshots**
   - Immediately access `http://localhost:4040`
   - Capture all screenshots listed above with `_baseline` suffix
   - Note total execution time

3. **Run Optimized (With All Optimizations)**
   ```bash
   # Run with full optimizations
   spark-submit \
     --conf spark.sql.adaptive.enabled=true \
     --conf spark.sql.adaptive.coalescePartitions.enabled=true \
     --conf spark.sql.adaptive.skewJoin.enabled=true \
     --conf spark.sql.autoBroadcastJoinThreshold=104857600 \
     src/jobs/01_data_processing.py
   ```

4. **Capture Optimized Screenshots**
   - Capture same pages with `_optimized` suffix
   - Compare side-by-side with baseline

5. **Document Improvements**
   - Calculate percentage improvements
   - Highlight specific optimizations that made the biggest impact
   - Add annotations to screenshots showing key differences

---

## Screenshot Naming Convention

Use this consistent naming scheme:

```
screenshots/
├── baseline/
│   ├── 01_jobs_overview_baseline.png
│   ├── 02_stages_overview_baseline.png
│   ├── 03_stage_detail_0_baseline.png
│   ├── 04_tasks_timeline_stage0_baseline.png
│   ├── 05_executors_baseline.png
│   ├── 06_sql_queries_overview_baseline.png
│   ├── 07_sql_query_plan_0_baseline.png
│   └── 09_environment_config_baseline.png
│
├── optimized/
│   ├── 01_jobs_overview_optimized.png
│   ├── 02_stages_overview_optimized.png
│   ├── 03_stage_detail_0_optimized.png
│   ├── 04_tasks_timeline_stage0_optimized.png
│   ├── 05_executors_optimized.png
│   ├── 06_sql_queries_overview_optimized.png
│   ├── 07_sql_query_plan_0_optimized.png
│   ├── 08_sql_aqe_plan_0_optimized.png  # AQE-specific
│   └── 09_environment_config_optimized.png
│
└── comparisons/
    ├── execution_time_comparison.png
    ├── shuffle_comparison.png
    ├── task_distribution_comparison.png
    └── memory_usage_comparison.png
```

---

## Analysis Checklist

Use this checklist while capturing screenshots:

### Job-Level Metrics
- [ ] Total job execution time (baseline vs. optimized)
- [ ] Number of stages (should be similar or reduced)
- [ ] Number of tasks (may increase with salting, decrease with AQE)
- [ ] Success rate (should be 100% for both)

### Stage-Level Metrics
- [ ] Stage duration for each stage
- [ ] Input data size per stage
- [ ] Shuffle read/write per stage
- [ ] Output records per stage

### Task-Level Metrics
- [ ] Task duration distribution (Min / Median / Max)
- [ ] Skew ratio (Max / Median) - Target: <3x
- [ ] GC time percentage - Target: <10%
- [ ] Shuffle spill (memory + disk) - Lower is better

### Executor-Level Metrics
- [ ] Memory utilization per executor
- [ ] GC time across all executors
- [ ] Total shuffle read/write
- [ ] Failed tasks count (should be 0)

### SQL-Level Metrics
- [ ] Join strategy (Sort-Merge vs. Broadcast)
- [ ] Filter pushdown evidence
- [ ] Column pruning evidence
- [ ] AQE optimizations applied (optimized only)

### Performance Targets
- [ ] Overall speedup: >1.3x (30%+ improvement)
- [ ] Shuffle reduction: >20%
- [ ] Task skew: Max/Median <3x
- [ ] GC time: <10% of execution time

---

## Expected Improvements

Based on the optimizations applied, you should see:

### 1. Adaptive Query Execution (AQE)
- **Impact**: 15-25% improvement
- **Evidence**:
  - "AQE Coalesced" stages in SQL plan
  - Reduced partition count in later stages
  - Screenshot: `08_sql_aqe_plan_*_optimized.png`

### 2. Broadcast Join
- **Impact**: 20-40% improvement for joins
- **Evidence**:
  - "BroadcastHashJoin" instead of "SortMergeJoin" in physical plan
  - Eliminated shuffle for small table joins
  - Screenshot: `07_sql_query_plan_*_optimized.png`

### 3. Skew Join Optimization (with Salting)
- **Impact**: 30-60% improvement on skewed data
- **Evidence**:
  - More uniform task duration distribution
  - Skew ratio reduced from >10x to <3x
  - Screenshot: `04_tasks_timeline_*_optimized.png`

### 4. Dynamic Partition Coalescing
- **Impact**: 10-20% improvement
- **Evidence**:
  - Fewer partitions in later stages
  - Reduced task scheduling overhead
  - Screenshot: `02_stages_overview_optimized.png`

---

## Tips for Quality Screenshots

1. **Full Page Capture**: Use browser extensions for full-page screenshots
   - Chrome: "Full Page Screen Capture"
   - Firefox: Built-in (Ctrl+Shift+S → "Save full page")

2. **High Resolution**: Capture at 100% zoom for clarity

3. **Annotations**: Add red boxes/arrows to highlight key differences
   - Use tools like Greenshot, Snagit, or Photoshop

4. **Consistent Timing**: Capture baseline and optimized at same stages

5. **Multiple Runs**: Average results from 2-3 runs for reliability

---

## Quick Reference: Screenshot Workflow

```bash
# 1. Generate sample data
python scripts/generate_sample_data.py --medium

# 2. Run optimization analysis script
./scripts/run_optimization_analysis.sh --size medium --iterations 2

# 3. During execution, capture screenshots:
#    - Open http://localhost:4040 in browser
#    - Navigate through tabs
#    - Save screenshots with naming convention

# 4. After completion, review logs:
cat optimization_results/analysis_*.txt

# 5. Add screenshots to docs/REPORT.md Section 8
```

---

## Troubleshooting

### Spark UI Not Accessible

**Problem**: Cannot access `http://localhost:4040`

**Solutions**:
- Check if Spark job is still running: `ps aux | grep spark`
- Try next port: `http://localhost:4041`
- Check firewall settings
- Use `docker-compose logs spark-master` to see port bindings

### Missing Metrics

**Problem**: Some metrics not showing in UI

**Solutions**:
- Enable event logging: `--conf spark.eventLog.enabled=true`
- Increase UI retention: `--conf spark.ui.retainedJobs=100`
- Use Spark History Server for completed jobs

### Screenshots Too Large

**Problem**: Full-page screenshots are huge files

**Solutions**:
- Compress with PNG optimization tools
- Resize to max width 1920px
- Use JPEG for large timeline screenshots
- Focus on critical sections only

---

## Next Steps

After capturing screenshots:

1. **Organize**: Place screenshots in `screenshots/baseline/` and `screenshots/optimized/`
2. **Analyze**: Compare side-by-side to identify specific improvements
3. **Document**: Add screenshots to `docs/REPORT.md` Section 8
4. **Calculate**: Document exact performance improvements with percentages
5. **Commit**: `git add screenshots/ && git commit -m "Add Spark UI optimization screenshots"`

---

**Last Updated**: 2025-11-13
**Version**: 1.0
**Related**: docs/REPORT.md Section 8 (Performance Benchmarks)
