#!/bin/bash
#
# Spark Optimization Analysis Script
#
# This script runs Spark jobs and captures performance metrics for optimization analysis.
# It generates both before/after comparisons and detailed execution statistics.
#
# Usage:
#   ./scripts/run_optimization_analysis.sh --size small
#   ./scripts/run_optimization_analysis.sh --size medium --iterations 3
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
DATASET_SIZE="small"
ITERATIONS=2
OUTPUT_DIR="optimization_results"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --size)
      DATASET_SIZE="$2"
      shift 2
      ;;
    --iterations)
      ITERATIONS="$2"
      shift 2
      ;;
    --output-dir)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--size small|medium|large] [--iterations N] [--output-dir DIR]"
      exit 1
      ;;
  esac
done

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Spark Optimization Analysis - GoodNote Analytics        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "📊 Dataset Size: ${GREEN}${DATASET_SIZE}${NC}"
echo -e "🔄 Iterations: ${GREEN}${ITERATIONS}${NC}"
echo -e "📁 Output Directory: ${GREEN}${OUTPUT_DIR}${NC}"
echo ""

# Create output directory
mkdir -p "${OUTPUT_DIR}"
RESULTS_FILE="${OUTPUT_DIR}/analysis_${TIMESTAMP}.txt"

# Log function
log() {
  echo -e "$1" | tee -a "${RESULTS_FILE}"
}

log "═══════════════════════════════════════════════════════════"
log "Spark Optimization Analysis Report"
log "Generated: $(date)"
log "═══════════════════════════════════════════════════════════"
log ""

# Step 1: Generate sample data
log "${YELLOW}Step 1: Generating Sample Data${NC}"
log "───────────────────────────────────────────────────────────"

if [ -f "data/raw/user_interactions.csv" ] && [ -f "data/raw/user_metadata.csv" ]; then
  log "✓ Sample data already exists. Skipping generation."
  log "  (Delete data/raw/*.csv to regenerate)"
else
  log "Generating ${DATASET_SIZE} dataset..."
  python3 scripts/generate_sample_data.py --${DATASET_SIZE} --seed 42 | tee -a "${RESULTS_FILE}"
fi

log ""

# Step 2: Check Spark availability
log "${YELLOW}Step 2: Checking Spark Environment${NC}"
log "───────────────────────────────────────────────────────────"

if command -v spark-submit &> /dev/null; then
  SPARK_VERSION=$(spark-submit --version 2>&1 | grep "version" | head -1)
  log "✓ Spark found: ${SPARK_VERSION}"
else
  log "${RED}✗ Spark not found. Please ensure Spark is installed and in PATH.${NC}"
  log "  Alternatively, use Docker: docker-compose up spark-master spark-worker-1 spark-worker-2"
  exit 1
fi

log ""

# Step 3: Run baseline (without optimizations)
log "${YELLOW}Step 3: Running Baseline Tests (Without Optimizations)${NC}"
log "───────────────────────────────────────────────────────────"

BASELINE_DIR="${OUTPUT_DIR}/baseline_${TIMESTAMP}"
mkdir -p "${BASELINE_DIR}"

log "Running ${ITERATIONS} baseline iterations..."
for i in $(seq 1 ${ITERATIONS}); do
  log ""
  log "  Baseline Run #${i}..."

  START_TIME=$(date +%s)

  # Run with minimal optimizations
  spark-submit \
    --master local[2] \
    --driver-memory 1g \
    --executor-memory 1g \
    --conf spark.sql.adaptive.enabled=false \
    --conf spark.sql.autoBroadcastJoinThreshold=-1 \
    --conf spark.sql.shuffle.partitions=200 \
    src/jobs/01_data_processing.py \
    --enriched-path data/processed/enriched_interactions_baseline.parquet \
    2>&1 | tee "${BASELINE_DIR}/run_${i}.log"

  END_TIME=$(date +%s)
  DURATION=$((END_TIME - START_TIME))

  log "    Duration: ${DURATION}s"
  echo "${DURATION}" >> "${BASELINE_DIR}/durations.txt"
done

# Calculate baseline average
BASELINE_AVG=$(awk '{ total += $1; count++ } END { print total/count }' "${BASELINE_DIR}/durations.txt")
log ""
log "✓ Baseline Average: ${BASELINE_AVG}s"

log ""

# Step 4: Run optimized (with all optimizations)
log "${YELLOW}Step 4: Running Optimized Tests (With All Optimizations)${NC}"
log "───────────────────────────────────────────────────────────"

OPTIMIZED_DIR="${OUTPUT_DIR}/optimized_${TIMESTAMP}"
mkdir -p "${OPTIMIZED_DIR}"

log "Running ${ITERATIONS} optimized iterations..."
for i in $(seq 1 ${ITERATIONS}); do
  log ""
  log "  Optimized Run #${i}..."

  START_TIME=$(date +%s)

  # Run with full optimizations
  spark-submit \
    --master local[2] \
    --driver-memory 1g \
    --executor-memory 1g \
    --conf spark.sql.adaptive.enabled=true \
    --conf spark.sql.adaptive.coalescePartitions.enabled=true \
    --conf spark.sql.adaptive.skewJoin.enabled=true \
    --conf spark.sql.autoBroadcastJoinThreshold=104857600 \
    --conf spark.sql.shuffle.partitions=200 \
    --conf spark.sql.adaptive.advisoryPartitionSizeInBytes=64MB \
    src/jobs/01_data_processing.py \
    --enriched-path data/processed/enriched_interactions_optimized.parquet \
    2>&1 | tee "${OPTIMIZED_DIR}/run_${i}.log"

  END_TIME=$(date +%s)
  DURATION=$((END_TIME - START_TIME))

  log "    Duration: ${DURATION}s"
  echo "${DURATION}" >> "${OPTIMIZED_DIR}/durations.txt"
done

# Calculate optimized average
OPTIMIZED_AVG=$(awk '{ total += $1; count++ } END { print total/count }' "${OPTIMIZED_DIR}/durations.txt")
log ""
log "✓ Optimized Average: ${OPTIMIZED_AVG}s"

log ""

# Step 5: Calculate improvement
log "${YELLOW}Step 5: Performance Analysis${NC}"
log "───────────────────────────────────────────────────────────"

IMPROVEMENT=$(echo "scale=2; (($BASELINE_AVG - $OPTIMIZED_AVG) / $BASELINE_AVG) * 100" | bc)
SPEEDUP=$(echo "scale=2; $BASELINE_AVG / $OPTIMIZED_AVG" | bc)

log ""
log "📊 Performance Comparison:"
log "  Baseline Average:  ${BASELINE_AVG}s"
log "  Optimized Average: ${OPTIMIZED_AVG}s"
log "  Improvement:       ${IMPROVEMENT}%"
log "  Speedup:           ${SPEEDUP}x"
log ""

if (( $(echo "$IMPROVEMENT >= 30" | bc -l) )); then
  log "${GREEN}✓ Performance target achieved! (>30% improvement)${NC}"
elif (( $(echo "$IMPROVEMENT >= 20" | bc -l) )); then
  log "${YELLOW}⚠ Good improvement, but below 30% target${NC}"
else
  log "${RED}✗ Below performance target${NC}"
fi

log ""

# Step 6: Extract metrics from logs
log "${YELLOW}Step 6: Extracting Detailed Metrics${NC}"
log "───────────────────────────────────────────────────────────"

log ""
log "Analyzing Spark logs for detailed metrics..."

# Extract shuffle read/write metrics
BASELINE_SHUFFLE=$(grep -i "shuffle" "${BASELINE_DIR}/run_1.log" | head -5 || echo "N/A")
OPTIMIZED_SHUFFLE=$(grep -i "shuffle" "${OPTIMIZED_DIR}/run_1.log" | head -5 || echo "N/A")

log ""
log "Baseline Shuffle Metrics:"
log "${BASELINE_SHUFFLE}"
log ""
log "Optimized Shuffle Metrics:"
log "${OPTIMIZED_SHUFFLE}"
log ""

# Step 7: Generate summary
log "${YELLOW}Step 7: Summary & Recommendations${NC}"
log "───────────────────────────────────────────────────────────"

log ""
log "Optimizations Applied:"
log "  ✓ Adaptive Query Execution (AQE)"
log "  ✓ Dynamic Partition Coalescing"
log "  ✓ Skew Join Optimization"
log "  ✓ Broadcast Join (threshold: 100MB)"
log "  ✓ Optimized Shuffle Partitions"
log ""

log "Next Steps:"
log "  1. Review detailed logs in: ${OUTPUT_DIR}"
log "  2. Access Spark UI: http://localhost:4040 (during job execution)"
log "  3. Capture screenshots of:"
log "     • Stages page (execution timeline)"
log "     • Tasks page (task distribution)"
log "     • Executors page (resource utilization)"
log "     • SQL page (query plans)"
log "  4. Compare baseline vs. optimized execution"
log ""

log "═══════════════════════════════════════════════════════════"
log "Analysis Complete!"
log "═══════════════════════════════════════════════════════════"
log ""
log "📄 Full report saved to: ${RESULTS_FILE}"
log "📁 Logs available in:"
log "   • Baseline: ${BASELINE_DIR}"
log "   • Optimized: ${OPTIMIZED_DIR}"
log ""

echo -e "${GREEN}✅ Optimization analysis complete!${NC}"
echo ""
echo "To view the report:"
echo "  cat ${RESULTS_FILE}"
echo ""
