"""
Unit tests for anomaly detection transforms.

Tests detect_anomalies_statistical() function from performance transforms.
"""
import pytest
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, LongType,
    TimestampType, DateType, DoubleType
)
from datetime import datetime, date
from src.transforms.performance import detect_anomalies_statistical


class TestDetectAnomaliesStatistical:
    """Tests for detect_anomalies_statistical() function."""

    def test_detect_anomalies_statistical_basic(self, spark):
        """
        GIVEN:
            - date=2023-01-01: avg_duration_ms = 1000
            - date=2023-01-02: avg_duration_ms = 1100
            - date=2023-01-03: avg_duration_ms = 1050
            - date=2023-01-04: avg_duration_ms = 5000 (anomaly!)
            - date=2023-01-05: avg_duration_ms = 1000
        WHEN: detect_anomalies_statistical() with threshold=3.0
        THEN:
            - Returns 1 row (2023-01-04)
            - is_anomaly = True
            - z_score > 3.0
        """
        # Arrange
        schema = StructType([
            StructField("date", DateType(), nullable=False),
            StructField("avg_duration_ms", DoubleType(), nullable=False)
        ])

        data = [
            (date(2023, 1, 1), 1000.0),
            (date(2023, 1, 2), 1100.0),
            (date(2023, 1, 3), 1050.0),
            (date(2023, 1, 4), 5000.0),  # Anomaly
            (date(2023, 1, 5), 1000.0)
        ]
        df = spark.createDataFrame(data, schema=schema)

        # Act
        result_df = detect_anomalies_statistical(
            df,
            value_column="avg_duration_ms",
            threshold=3.0
        )

        # Assert - filter only anomalies
        anomalies_df = result_df.filter(F.col("is_anomaly") == True)
        assert anomalies_df.count() == 1, "Expected 1 anomaly"

        anomaly = anomalies_df.collect()[0]
        assert anomaly["date"] == date(2023, 1, 4)
        assert anomaly["is_anomaly"] == True
        assert anomaly["z_score"] > 3.0

    def test_detect_anomalies_statistical_grouped(self, spark):
        """
        GIVEN:
            - app_version=1.0.0: [1000, 1100, 1050, 5000, 1000] (1 anomaly)
            - app_version=2.0.0: [2000, 2100, 2050, 2000, 2100] (0 anomalies)
        WHEN: detect_anomalies_statistical() grouped by app_version
        THEN:
            - Returns 1 anomaly (v1.0.0, value=5000)
            - No anomalies for v2.0.0
        """
        # Arrange
        schema = StructType([
            StructField("app_version", StringType(), nullable=False),
            StructField("date", DateType(), nullable=False),
            StructField("avg_duration_ms", DoubleType(), nullable=False)
        ])

        data = [
            # v1.0.0 - has anomaly
            ("1.0.0", date(2023, 1, 1), 1000.0),
            ("1.0.0", date(2023, 1, 2), 1100.0),
            ("1.0.0", date(2023, 1, 3), 1050.0),
            ("1.0.0", date(2023, 1, 4), 5000.0),  # Anomaly
            ("1.0.0", date(2023, 1, 5), 1000.0),
            # v2.0.0 - no anomalies
            ("2.0.0", date(2023, 1, 1), 2000.0),
            ("2.0.0", date(2023, 1, 2), 2100.0),
            ("2.0.0", date(2023, 1, 3), 2050.0),
            ("2.0.0", date(2023, 1, 4), 2000.0),
            ("2.0.0", date(2023, 1, 5), 2100.0)
        ]
        df = spark.createDataFrame(data, schema=schema)

        # Act
        result_df = detect_anomalies_statistical(
            df,
            value_column="avg_duration_ms",
            group_by_columns=["app_version"],
            threshold=3.0
        )

        # Assert
        anomalies_df = result_df.filter(F.col("is_anomaly") == True)
        assert anomalies_df.count() == 1, "Expected 1 anomaly"

        anomaly = anomalies_df.collect()[0]
        assert anomaly["app_version"] == "1.0.0"
        assert anomaly["date"] == date(2023, 1, 4)
        assert anomaly["avg_duration_ms"] == 5000.0

        # Check v2.0.0 has no anomalies
        v2_anomalies = anomalies_df.filter(F.col("app_version") == "2.0.0").count()
        assert v2_anomalies == 0, "v2.0.0 should have no anomalies"

    def test_detect_anomalies_statistical_no_anomalies(self, spark):
        """
        GIVEN: DataFrame with normal distribution (no outliers)
        WHEN: detect_anomalies_statistical() is called
        THEN: Returns 0 anomalies
        """
        # Arrange
        schema = StructType([
            StructField("date", DateType(), nullable=False),
            StructField("avg_duration_ms", DoubleType(), nullable=False)
        ])

        # Create data with small variance (no anomalies)
        data = [
            (date(2023, 1, i), 1000.0 + (i % 3) * 50.0)
            for i in range(1, 31)  # 30 days
        ]
        df = spark.createDataFrame(data, schema=schema)

        # Act
        result_df = detect_anomalies_statistical(
            df,
            value_column="avg_duration_ms",
            threshold=3.0
        )

        # Assert
        anomalies_df = result_df.filter(F.col("is_anomaly") == True)
        assert anomalies_df.count() == 0, "Expected no anomalies"
