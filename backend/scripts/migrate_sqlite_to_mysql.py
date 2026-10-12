"""Copy existing TradePilot rows from SQLite into an already-migrated empty MySQL database.

Usage: python scripts/migrate_sqlite_to_mysql.py sqlite:///tradepilot.db "$DATABASE_URL"
The source is read-only; destination must contain no business rows. Take a backup first.
"""

from __future__ import annotations

import sys

from sqlalchemy import create_engine, insert, inspect, select

from tradepilot.customer import Customer  # noqa: F401
from tradepilot.db import Base
from tradepilot.inventory import (  # noqa: F401
    Inventory,
    InventoryAdjustment,
    InventoryMovement,
)
from tradepilot.models import (  # noqa: F401
    AgentRun,
    ApprovalHistory,
    Product,
    QuoteRecord,
    RefreshToken,
    User,
)


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: migrate_sqlite_to_mysql.py <sqlite-url> <mysql-url>")
    source_engine = create_engine(sys.argv[1], connect_args={"check_same_thread": False})
    target_engine = create_engine(sys.argv[2])
    source_tables = set(inspect(source_engine).get_table_names())
    target_tables = set(inspect(target_engine).get_table_names())
    business_tables = [table for table in Base.metadata.sorted_tables if table.name in source_tables and table.name in target_tables]

    with target_engine.begin() as target:
        for table in business_tables:
            if target.scalar(select(table.c[next(iter(table.primary_key.columns.keys()))]).limit(1)) is not None:
                raise SystemExit(f"Destination table {table.name} is not empty; refusing to merge or overwrite data")

        with source_engine.connect() as source:
            for table in business_tables:
                source_columns = {column["name"] for column in inspect(source_engine).get_columns(table.name)}
                columns = [column for column in table.columns if column.name in source_columns and column.name != "alembic_version"]
                names = [column.name for column in columns]
                rows = source.execute(select(*[table.c[name] for name in names])).mappings().all()
                for offset in range(0, len(rows), 500):
                    target.execute(insert(table).values([dict(row) for row in rows[offset : offset + 500]]))
                print(f"{table.name}: copied {len(rows)} rows")

    source_engine.dispose()
    target_engine.dispose()


if __name__ == "__main__":
    main()
