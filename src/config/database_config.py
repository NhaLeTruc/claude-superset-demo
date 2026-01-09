"""
Database Configuration (Compatibility Shim)

This module maintains backward compatibility by re-exporting all functions
from the new postgres package structure.

New code should import directly from src.config.postgres instead.
"""
from .postgres import (
    get_postgres_connection_props,
    create_connection_string,
    validate_database_config,
    read_from_postgres,
    execute_sql,
    get_table_row_count,
    write_to_postgres
)

__all__ = [
    "get_postgres_connection_props",
    "create_connection_string",
    "validate_database_config",
    "read_from_postgres",
    "execute_sql",
    "get_table_row_count",
    "write_to_postgres",
]
