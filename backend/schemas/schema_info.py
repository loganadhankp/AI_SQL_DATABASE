"""
Pydantic models for database schema metadata and table exploration.
Used for API serialization and frontend database tree display.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ColumnMetadata(BaseModel):
    name: str
    data_type: str
    nullable: bool = True
    primary_key: bool = False
    default: Optional[str] = None


class ForeignKeyMetadata(BaseModel):
    constrained_columns: List[str]
    referred_table: str
    referred_columns: List[str]


class TableMetadata(BaseModel):
    name: str
    columns: List[ColumnMetadata] = []
    primary_keys: List[str] = []
    foreign_keys: List[ForeignKeyMetadata] = []
    estimated_row_count: Optional[int] = 0


class DatabaseSchemaMetadata(BaseModel):
    database_name: str
    dialect: str
    tables: List[TableMetadata] = []
    relationships: List[str] = []


class TablePreview(BaseModel):
    table_name: str
    columns: List[str]
    rows: List[Dict[str, Any]]
    total_previewed: int
