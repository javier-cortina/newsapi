from pathlib import Path

from dagster import definitions, load_from_defs_folder, Definitions
from newsapi_dentsu.defs.resources import duckdb_resource, get_io_manager


@definitions
def defs():
    loaded = load_from_defs_folder(path_within_project=Path(__file__).parent)

    # Merge with our resources
    # Uses environment-based I/O manager (DuckDB for dev, PostgreSQL for prod)
    return Definitions.merge(
        loaded,
        Definitions(
            resources={
                "duckdb": duckdb_resource,
                "io_manager": get_io_manager(),
            }
        ),
    )
