import os
import dagster as dg
from dagster_duckdb import DuckDBResource
from dagster_duckdb_pandas import DuckDBPandasIOManager
from pathlib import Path


# Get the database path relative to the project root
def get_database_path():
    """Get absolute path to the DuckDB database file"""
    project_root = Path(__file__).parent.parent.parent.parent
    db_path = project_root / "data" / "news.duckdb"
    db_path.parent.mkdir(exist_ok=True)
    return str(db_path)


def get_io_manager():
    """
    Get the appropriate I/O manager based on environment configuration.

    In development (USE_POSTGRES=false or not set):
        Uses DuckDB for local file-based storage

    In production (USE_POSTGRES=true):
        Uses PostgreSQL for scalable cloud deployment
        Requires: POSTGRES_HOST, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD

    Returns:
        IOManager: Either DuckDBPandasIOManager or PostgresPandasIOManager
    """
    use_postgres = os.getenv("USE_POSTGRES", "false").lower() == "true"

    if use_postgres:
        # PostgreSQL configuration for production
        from dagster_postgres.utils import get_conn_string
        from dagster_postgres import PostgresPandasIOManager

        conn_string = get_conn_string(
            username=os.getenv("POSTGRES_USER", "dagster"),
            password=os.getenv("POSTGRES_PASSWORD"),
            hostname=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            db_name=os.getenv("POSTGRES_DB", "dagster"),
        )

        return PostgresPandasIOManager(
            conn_string=conn_string,
            schema="raw",  # Default schema
        )
    else:
        # DuckDB configuration for local development
        return DuckDBPandasIOManager(
            database=get_database_path(),
            schema="raw",  # Default schema for assets without key_prefix
        )


# DuckDB resource for custom queries and operations (local dev only)
duckdb_resource = DuckDBResource(database=get_database_path())
