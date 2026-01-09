"""
Unit tests for sessionization transforms.

Tests sessionize_interactions() function from session transforms.
"""
import pytest
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, LongType,
    TimestampType, DoubleType
)
from datetime import datetime, timedelta
from src.transforms.session import sessionize_interactions


class TestSessionizeInteractions:
    """Tests for sessionize_interactions() function."""

    def test_sessionize_interactions_single_session(self, spark):
        """
        GIVEN: u001 has 3 interactions within 30 minutes
        WHEN: sessionize_interactions() is called with 1800s timeout
        THEN: All 3 interactions assigned to same session_id
        """
        # Arrange
        schema = StructType([
            StructField("user_id", StringType(), nullable=False),
            StructField("timestamp", TimestampType(), nullable=False),
            StructField("action_type", StringType(), nullable=False),
            StructField("page_id", StringType(), nullable=False),
            StructField("duration_ms", LongType(), nullable=False)
        ])

        data = [
            ("u001", datetime(2023, 1, 1, 10, 0, 0), "page_view", "p001", 5000),
            ("u001", datetime(2023, 1, 1, 10, 10, 0), "edit", "p001", 120000),
            ("u001", datetime(2023, 1, 1, 10, 25, 0), "save", "p001", 2000),
        ]
        df = spark.createDataFrame(data, schema=schema)

        # Act
        result_df = sessionize_interactions(df, session_timeout_seconds=1800)

        # Assert
        results = result_df.collect()
        assert len(results) == 3

        # All should have same session_id
        session_ids = [row["session_id"] for row in results]
        assert len(set(session_ids)) == 1
        assert session_ids[0] is not None

    def test_sessionize_interactions_multiple_sessions(self, spark):
        """
        GIVEN: u001 has interactions with >30 min gaps
        WHEN: sessionize_interactions() is called
        THEN: Interactions split into separate sessions
        """
        # Arrange
        schema = StructType([
            StructField("user_id", StringType(), nullable=False),
            StructField("timestamp", TimestampType(), nullable=False),
            StructField("action_type", StringType(), nullable=False),
            StructField("page_id", StringType(), nullable=False),
            StructField("duration_ms", LongType(), nullable=False)
        ])

        data = [
            # Session 1
            ("u001", datetime(2023, 1, 1, 10, 0, 0), "page_view", "p001", 5000),
            ("u001", datetime(2023, 1, 1, 10, 10, 0), "edit", "p001", 120000),
            # Session 2 (40 min later)
            ("u001", datetime(2023, 1, 1, 10, 50, 0), "page_view", "p002", 3000),
            ("u001", datetime(2023, 1, 1, 11, 0, 0), "save", "p002", 2000),
        ]
        df = spark.createDataFrame(data, schema=schema)

        # Act
        result_df = sessionize_interactions(df, session_timeout_seconds=1800)

        # Assert
        results = result_df.orderBy("timestamp").collect()
        assert len(results) == 4

        # First 2 should have same session_id
        assert results[0]["session_id"] == results[1]["session_id"]
        # Last 2 should have same session_id but different from first 2
        assert results[2]["session_id"] == results[3]["session_id"]
        assert results[0]["session_id"] != results[2]["session_id"]

    def test_sessionize_interactions_multiple_users(self, spark):
        """
        GIVEN: Multiple users with concurrent sessions
        WHEN: sessionize_interactions() is called
        THEN: Sessions are separate per user
        """
        # Arrange
        schema = StructType([
            StructField("user_id", StringType(), nullable=False),
            StructField("timestamp", TimestampType(), nullable=False),
            StructField("action_type", StringType(), nullable=False),
            StructField("page_id", StringType(), nullable=False),
            StructField("duration_ms", LongType(), nullable=False)
        ])

        data = [
            ("u001", datetime(2023, 1, 1, 10, 0, 0), "page_view", "p001", 5000),
            ("u002", datetime(2023, 1, 1, 10, 0, 0), "page_view", "p002", 3000),
            ("u001", datetime(2023, 1, 1, 10, 10, 0), "edit", "p001", 120000),
            ("u002", datetime(2023, 1, 1, 10, 10, 0), "save", "p002", 2000),
        ]
        df = spark.createDataFrame(data, schema=schema)

        # Act
        result_df = sessionize_interactions(df, session_timeout_seconds=1800)

        # Assert
        u001_sessions = result_df.filter(F.col("user_id") == "u001").select("session_id").distinct().collect()
        u002_sessions = result_df.filter(F.col("user_id") == "u002").select("session_id").distinct().collect()

        assert len(u001_sessions) == 1
        assert len(u002_sessions) == 1
        assert u001_sessions[0]["session_id"] != u002_sessions[0]["session_id"]

    def test_sessionize_interactions_exact_timeout(self, spark):
        """
        GIVEN: Interactions exactly 30 minutes apart
        WHEN: sessionize_interactions() is called
        THEN: Creates new session (>=timeout triggers new session)
        """
        # Arrange
        schema = StructType([
            StructField("user_id", StringType(), nullable=False),
            StructField("timestamp", TimestampType(), nullable=False),
            StructField("action_type", StringType(), nullable=False),
            StructField("page_id", StringType(), nullable=False),
            StructField("duration_ms", LongType(), nullable=False)
        ])

        data = [
            ("u001", datetime(2023, 1, 1, 10, 0, 0), "page_view", "p001", 5000),
            ("u001", datetime(2023, 1, 1, 10, 30, 0), "page_view", "p002", 3000),
        ]
        df = spark.createDataFrame(data, schema=schema)

        # Act
        result_df = sessionize_interactions(df, session_timeout_seconds=1800)

        # Assert
        results = result_df.orderBy("timestamp").collect()
        # Should be separate sessions (>=timeout)
        assert results[0]["session_id"] != results[1]["session_id"]
