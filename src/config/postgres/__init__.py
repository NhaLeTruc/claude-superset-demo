"""
PostgreSQL Database Operations Package

Provides comprehensive PostgreSQL connectivity for Spark:
- Connection management and validation
- Optimized read operations with partitioning
- Optimized write operations with batching
- SQL query execution
- Utility functions

All public APIs are re-exported for convenience.
"""
from .connection import (
    get_postgres_connection_props,
    create_connection_string,
    validate_database_config
)
from .reader import (
    read_from_postgres,
    execute_sql,
    get_table_row_count
)
from .writer import write_to_postgres

__all__ = [
    # Connection
    "get_postgres_connection_props",
    "create_connection_string",
    "validate_database_config",
    # Reader
    "read_from_postgres",
    "execute_sql",
    "get_table_row_count",
    # Writer
    "write_to_postgres",
]
