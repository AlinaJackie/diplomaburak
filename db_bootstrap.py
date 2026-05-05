from sqlalchemy import text


def _get_existing_columns(db, table_name: str) -> set[str]:
    rows = db.session.execute(
        text(f"PRAGMA table_info({table_name})")).fetchall()
    return {row[1] for row in rows}


def _add_column_if_missing(db, table_name: str, column_name: str, ddl: str) -> None:
    existing_columns = _get_existing_columns(db, table_name)
    if column_name not in existing_columns:
        db.session.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {ddl}"))


def ensure_database_schema(db) -> None:
    """
    М'яке вирівнювання локальної SQLite-схеми під поточні моделі.
    Не чіпає існуючі дані, лише додає відсутні колонки.
    """
    engine_name = db.engine.url.get_backend_name()
    if engine_name != "sqlite":
        db.session.commit()
        return

    tables = db.session.execute(
        text("SELECT name FROM sqlite_master WHERE type='table'")
    ).fetchall()
    existing_tables = {row[0] for row in tables}

    if "restaurants" in existing_tables:
        _add_column_if_missing(
            db, "restaurants", "address", "address VARCHAR(255)"
        )
        _add_column_if_missing(
            db, "restaurants", "latitude", "latitude FLOAT"
        )
        _add_column_if_missing(
            db, "restaurants", "longitude", "longitude FLOAT"
        )

    if "orders" in existing_tables:
        _add_column_if_missing(
            db, "orders", "delivery_type", "delivery_type VARCHAR(50)"
        )
        _add_column_if_missing(
            db, "orders", "delivery_fee", "delivery_fee INTEGER"
        )
        _add_column_if_missing(
            db, "orders", "eta_minutes", "eta_minutes INTEGER"
        )

    db.session.commit()
