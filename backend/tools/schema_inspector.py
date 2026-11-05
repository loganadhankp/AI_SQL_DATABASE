"""
Dynamic Database Schema Inspector.
Uses SQLAlchemy inspection tools to extract tables, columns, constraints, foreign keys,
and generate LLM-friendly schema representations for SQL generation.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Any, Optional
from sqlalchemy import inspect, text, Engine
from backend.schemas.schema_info import (
    ColumnMetadata,
    ForeignKeyMetadata,
    TableMetadata,
    DatabaseSchemaMetadata,
    TablePreview,
)


class SchemaInspector:
    """
    Introspects live relational databases using SQLAlchemy.
    Caches schema per engine to optimize performance.
    """

    _cache: Dict[str, DatabaseSchemaMetadata] = {}

    @classmethod
    def get_table_names(cls, engine: Engine) -> List[str]:
        """Returns sorted list of accessible table names in the database."""
        inspector = inspect(engine)
        return sorted(inspector.get_table_names())

    @classmethod
    def get_table_metadata(cls, engine: Engine, table_name: str) -> TableMetadata:
        """Inspects and returns detailed metadata for a single table."""
        inspector = inspect(engine)
        columns_raw = inspector.get_columns(table_name)
        pk_dict = inspector.get_pk_constraint(table_name) or {}
        pk_columns = set(pk_dict.get("constrained_columns", []))
        fks_raw = inspector.get_foreign_keys(table_name) or []

        columns: List[ColumnMetadata] = []
        for col in columns_raw:
            col_name = col["name"]
            columns.append(
                ColumnMetadata(
                    name=col_name,
                    data_type=str(col["type"]),
                    nullable=bool(col.get("nullable", True)),
                    primary_key=col_name in pk_columns,
                    default=str(col.get("default")) if col.get("default") is not None else None,
                )
            )

        foreign_keys: List[ForeignKeyMetadata] = []
        for fk in fks_raw:
            foreign_keys.append(
                ForeignKeyMetadata(
                    constrained_columns=fk.get("constrained_columns", []),
                    referred_table=fk.get("referred_table", ""),
                    referred_columns=fk.get("referred_columns", []),
                )
            )

        # Retrieve estimated or exact row count safely
        row_count = 0
        try:
            with engine.connect() as conn:
                # Quoting table name safely using dialect quote_identifier
                quoted_table = engine.dialect.identifier_preparer.quote(table_name)
                res = conn.execute(text(f"SELECT COUNT(*) FROM {quoted_table}"))
                row_count = res.scalar() or 0
        except Exception:
            row_count = 0

        return TableMetadata(
            name=table_name,
            columns=columns,
            primary_keys=list(pk_columns),
            foreign_keys=foreign_keys,
            estimated_row_count=row_count,
        )

    @classmethod
    def inspect_database(
        cls, engine: Engine, database_name: str, force_refresh: bool = False
    ) -> DatabaseSchemaMetadata:
        """
        Extracts complete database schema with tables, columns, and relationships.
        Caches results unless force_refresh is True.
        """
        cache_key = f"{str(engine.url)}_{database_name}"
        if not force_refresh and cache_key in cls._cache:
            return cls._cache[cache_key]

        table_names = cls.get_table_names(engine)
        tables: List[TableMetadata] = []
        relationships: List[str] = []

        for name in table_names:
            tbl_meta = cls.get_table_metadata(engine, name)
            tables.append(tbl_meta)
            for fk in tbl_meta.foreign_keys:
                src_cols = ", ".join(fk.constrained_columns)
                target_cols = ", ".join(fk.referred_columns)
                rel_str = f"{name}({src_cols}) -> {fk.referred_table}({target_cols})"
                relationships.append(rel_str)

        schema_metadata = DatabaseSchemaMetadata(
            database_name=database_name,
            dialect=engine.dialect.name,
            tables=tables,
            relationships=relationships,
        )

        cls._cache[cache_key] = schema_metadata
        return schema_metadata

    @classmethod
    def get_table_preview(
        cls, engine: Engine, table_name: str, limit: int = 5
    ) -> TablePreview:
        """
        Retrieves a safe, bounded preview of rows for the database explorer UI.
        Enforces a hard limit of max 20 rows to avoid pulling excessive data.
        """
        safe_limit = min(max(1, limit), 20)
        quoted_table = engine.dialect.identifier_preparer.quote(table_name)

        with engine.connect() as conn:
            query = text(f"SELECT * FROM {quoted_table} LIMIT :limit")
            result = conn.execute(query, {"limit": safe_limit})
            columns = list(result.keys())
            rows_data: List[Dict[str, Any]] = []

            for row in result.fetchall():
                row_dict = {}
                for col_name, val in zip(columns, row):
                    # Convert dates, decimals, and bytes to JSON serializable formats
                    if isinstance(val, (datetime, date)):
                        row_dict[col_name] = val.isoformat()
                    elif isinstance(val, Decimal):
                        row_dict[col_name] = float(val)
                    elif isinstance(val, bytes):
                        row_dict[col_name] = val.decode("utf-8", errors="replace")
                    else:
                        row_dict[col_name] = val
                rows_data.append(row_dict)

        return TablePreview(
            table_name=table_name,
            columns=columns,
            rows=rows_data,
            total_previewed=len(rows_data),
        )

    @classmethod
    def format_schema_for_llm(
        cls,
        engine: Engine,
        database_name: str,
        relevant_tables: Optional[List[str]] = None,
    ) -> str:
        """
        Generates a concise, structured markdown schema text specifically designed
        for LLM prompt context without wasting unnecessary tokens.
        """
        schema_meta = cls.inspect_database(engine, database_name)
        tables_to_include = schema_meta.tables

        if relevant_tables:
            relevant_set = {t.lower() for t in relevant_tables}
            tables_to_include = [
                t for t in schema_meta.tables if t.name.lower() in relevant_set
            ]

        lines = [
            f"Database: {schema_meta.database_name} (Dialect: {schema_meta.dialect.upper()})",
            "Schema Overview:",
        ]

        for table in tables_to_include:
            lines.append(f"\nTable: `{table.name}` (approx {table.estimated_row_count} rows)")
            pk_set = set(table.primary_keys)

            for col in table.columns:
                attributes = []
                if col.name in pk_set:
                    attributes.append("PRIMARY KEY")
                if not col.nullable:
                    attributes.append("NOT NULL")

                attr_str = f" [{', '.join(attributes)}]" if attributes else ""
                lines.append(f"  - `{col.name}`: {col.data_type}{attr_str}")

            if table.foreign_keys:
                for fk in table.foreign_keys:
                    src = ", ".join(fk.constrained_columns)
                    ref = ", ".join(fk.referred_columns)
                    lines.append(f"  - FOREIGN KEY (`{src}`) REFERENCES `{fk.referred_table}`(`{ref}`)")

        if schema_meta.relationships:
            lines.append("\nKey Relationships (Foreign Keys for JOINs):")
            for rel in schema_meta.relationships:
                lines.append(f"  • {rel}")

        return "\n".join(lines)
