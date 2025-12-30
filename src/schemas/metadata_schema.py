"""
Schema definition for user metadata.

This module defines the schema for user metadata/profile information.
"""
from pyspark.sql.types import StructType, StructField, StringType, TimestampType


METADATA_SCHEMA = StructType([
    StructField("user_id", StringType(), False),
    StructField("country", StringType(), False),
    StructField("device_type", StringType(), False),
    StructField("subscription_type", StringType(), False),
    StructField("registration_date", TimestampType(), False),
    StructField("app_version", StringType(), False),
])