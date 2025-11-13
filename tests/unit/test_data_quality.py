"""
Unit tests for data quality validation functions.

Following TDD approach - tests written before implementation.
Reference: docs/TDD_SPEC.md - Task 5 (Data Quality Specifications)
"""
import pytest
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, LongType, TimestampType
from src.utils.data_quality import validate_schema, detect_nulls
from datetime import datetime


class TestValidateSchema:
    """Tests for validate_schema() function."""

    def test_validate_schema_valid(self, spark):
        """
        GIVEN: DataFrame with exact schema match
        WHEN: validate_schema() is called
        THEN: Returns (True, [])
        """
        # Arrange
        expected_schema = StructType([
            StructField("user_id", StringType(), nullable=False),
            StructField("count", IntegerType(), nullable=False)
        ])

        data = [("u001", 100), ("u002", 200)]
        df = spark.createDataFrame(data, schema=expected_schema)

        # Act
        is_valid, errors = validate_schema(df, expected_schema, strict=True)

        # Assert
        assert is_valid is True
        assert errors == []

    def test_validate_schema_missing_column(self, spark):
        """
        GIVEN: DataFrame missing 'app_version' column
        WHEN: validate_schema() is called
        THEN: Returns (False, ["Missing column: 'app_version'"])
        """
        # Arrange
        expected_schema = StructType([
            StructField("user_id", StringType(), nullable=False),
            StructField("count", IntegerType(), nullable=False),
            StructField("app_version", StringType(), nullable=False)
        ])

        # DataFrame with only user_id and count (missing app_version)
        actual_schema = StructType([
            StructField("user_id", StringType(), nullable=False),
            StructField("count", IntegerType(), nullable=False)
        ])

        data = [("u001", 100), ("u002", 200)]
        df = spark.createDataFrame(data, schema=actual_schema)

        # Act
        is_valid, errors = validate_schema(df, expected_schema, strict=True)

        # Assert
        assert is_valid is False
        assert len(errors) == 1
        assert "Missing column: 'app_version'" in errors[0]

    def test_validate_schema_wrong_type(self, spark):
        """
        GIVEN: DataFrame with 'duration_ms' as IntegerType instead of LongType
        WHEN: validate_schema() is called
        THEN: Returns (False, ["Column 'duration_ms' has type IntegerType but expected LongType"])
        """
        # Arrange
        expected_schema = StructType([
            StructField("user_id", StringType(), nullable=False),
            StructField("duration_ms", LongType(), nullable=False)
        ])

        # DataFrame with duration_ms as IntegerType (wrong!)
        actual_schema = StructType([
            StructField("user_id", StringType(), nullable=False),
            StructField("duration_ms", IntegerType(), nullable=False)  # Wrong type
        ])

        data = [("u001", 5000), ("u002", 3000)]
        df = spark.createDataFrame(data, schema=actual_schema)

        # Act
        is_valid, errors = validate_schema(df, expected_schema, strict=True)

        # Assert
        assert is_valid is False
        assert len(errors) == 1
        assert "duration_ms" in errors[0]
        assert "IntegerType" in errors[0] or "int" in errors[0].lower()
        assert "LongType" in errors[0] or "long" in errors[0].lower()


class TestDetectNulls:
    """Tests for detect_nulls() function."""

    def test_detect_nulls_none(self, spark):
        """
        GIVEN: DataFrame with no NULL values
        WHEN: detect_nulls() is called
        THEN: Returns empty DataFrame
        """
        # Arrange
        schema = StructType([
            StructField("user_id", StringType(), nullable=True),
            StructField("timestamp", TimestampType(), nullable=True),
            StructField("count", IntegerType(), nullable=True)
        ])

        data = [
            ("u001", datetime(2023, 1, 1, 10, 0, 0), 100),
            ("u002", datetime(2023, 1, 2, 11, 0, 0), 200),
            ("u003", datetime(2023, 1, 3, 12, 0, 0), 300)
        ]
        df = spark.createDataFrame(data, schema=schema)

        non_nullable_columns = ["user_id", "timestamp"]

        # Act
        result_df = detect_nulls(df, non_nullable_columns)

        # Assert
        assert result_df.count() == 0, "Expected empty DataFrame when no NULLs present"

    def test_detect_nulls_present(self, spark):
        """
        GIVEN:
            - Row 1: user_id=NULL, timestamp=2023-01-01 (NULL user_id)
            - Row 2: user_id=u001, timestamp=NULL (NULL timestamp)
            - Row 3: user_id=u002, timestamp=2023-01-02 (no NULLs)
        WHEN: detect_nulls(non_nullable_columns=["user_id", "timestamp"])
        THEN:
            - Returns 2 rows (rows 1 and 2)
            - Row 1: null_columns = ["user_id"]
            - Row 2: null_columns = ["timestamp"]
        """
        # Arrange
        schema = StructType([
            StructField("user_id", StringType(), nullable=True),
            StructField("timestamp", TimestampType(), nullable=True),
            StructField("count", IntegerType(), nullable=True)
        ])

        data = [
            (None, datetime(2023, 1, 1, 10, 0, 0), 100),          # NULL user_id
            ("u001", None, 200),                                   # NULL timestamp
            ("u002", datetime(2023, 1, 2, 11, 0, 0), 300)         # No NULLs
        ]
        df = spark.createDataFrame(data, schema=schema)

        non_nullable_columns = ["user_id", "timestamp"]

        # Act
        result_df = detect_nulls(df, non_nullable_columns)

        # Assert
        assert result_df.count() == 2, "Expected 2 rows with NULLs"

        # Verify schema includes null_columns
        assert "null_columns" in result_df.columns, "Expected 'null_columns' column in result"

        # Collect results and verify null_columns content
        results = result_df.collect()

        # Row 1 should have NULL user_id
        row1_nulls = results[0]["null_columns"]
        assert "user_id" in row1_nulls, "Expected 'user_id' in null_columns for row 1"

        # Row 2 should have NULL timestamp
        row2_nulls = results[1]["null_columns"]
        assert "timestamp" in row2_nulls, "Expected 'timestamp' in null_columns for row 2"
