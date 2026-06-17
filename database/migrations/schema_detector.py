"""
database/migrations/schema_detector.py
Detecte automatiquement les differences entre le schema actuel et le schema cible.
Usage: python database/migrations/schema_detector.py
"""

import sqlite3
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from pathlib import Path


@dataclass
class Column:
    name: str
    type: str
    nullable: bool = True
    default: Optional[str] = None
    primary_key: bool = False


@dataclass
class Index:
    name: str
    table: str
    columns: List[str]
    unique: bool = False


@dataclass
class Table:
    name: str
    columns: List[Column] = field(default_factory=list)
    indexes: List[Index] = field(default_factory=list)
    foreign_keys: List[Dict] = field(default_factory=list)


class Schema:
    def __init__(self):
        self.tables: Dict[str, Table] = {}

    def table(self, name: str):
        return TableBuilder(self, name)

    def get_table(self, name: str) -> Optional[Table]:
        return self.tables.get(name)


class TableBuilder:
    def __init__(self, schema: Schema, name: str):
        self.schema = schema
        self.table = Table(name=name)

    def col(self, name: str, type: str, *, nullable: bool = True,
            default: Optional[str] = None, primary_key: bool = False):
        self.table.columns.append(Column(
            name=name, type=type, nullable=nullable,
            default=default, primary_key=primary_key
        ))
        return self

    def index(self, name: str, *columns: str, unique: bool = False):
        self.table.indexes.append(Index(
            name=name, table=self.table.name, columns=list(columns), unique=unique
        ))
        return self

    def fk(self, column: str, ref_table: str, ref_column: str,
           on_delete: str = "CASCADE"):
        self.table.foreign_keys.append({
            "column": column,
            "ref_table": ref_table,
            "ref_column": ref_column,
            "on_delete": on_delete
        })
        return self

    def build(self) -> Table:
        self.schema.tables[self.table.name] = self.table
        return self.table


def parse_current_schema(db_path: str) -> Dict[str, Table]:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    tables = {}

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name != 'schema_migrations'")
    table_names = [row[0] for row in cursor.fetchall()]

    for table_name in table_names:
        table = Table(name=table_name)

        cursor.execute(f"PRAGMA table_info({table_name})")
        for row in cursor.fetchall():
            table.columns.append(Column(
                name=row[1],
                type=row[2] or "TEXT",
                nullable=not row[3],
                default=str(row[4]) if row[4] is not None else None,
                primary_key=bool(row[5])
            ))

        cursor.execute(f"PRAGMA index_list({table_name})")
        for row in cursor.fetchall():
            idx_name = row[1]
            if idx_name.startswith("sqlite_"):
                continue
            idx_unique = bool(row[2])
            cursor.execute(f"PRAGMA index_info({idx_name})")
            idx_columns = [r[2] for r in cursor.fetchall()]
            table.indexes.append(Index(
                name=idx_name, table=table_name,
                columns=idx_columns, unique=idx_unique
            ))

        cursor.execute(f"PRAGMA foreign_key_list({table_name})")
        for row in cursor.fetchall():
            table.foreign_keys.append({
                "column": row[3],
                "ref_table": row[2],
                "ref_column": row[4],
                "on_delete": row[6] or "NO ACTION"
            })

        tables[table_name] = table

    conn.close()
    return tables


@dataclass
class SchemaDiff:
    tables_to_create: List[Table] = field(default_factory=list)
    tables_to_drop: List[str] = field(default_factory=list)
    columns_to_add: List[Tuple[str, Column]] = field(default_factory=list)
    columns_to_remove: List[Tuple[str, str]] = field(default_factory=list)
    indexes_to_create: List[Index] = field(default_factory=list)
    indexes_to_drop: List[Tuple[str, str]] = field(default_factory=list)

    def has_changes(self) -> bool:
        return any([
            self.tables_to_create, self.tables_to_drop,
            self.columns_to_add, self.columns_to_remove,
            self.indexes_to_create, self.indexes_to_drop
        ])

    def __str__(self) -> str:
        lines = ["Schema differences detected:"]
        if self.tables_to_create:
            lines.append(f"  Tables to create: {[t.name for t in self.tables_to_create]}")
        if self.tables_to_drop:
            lines.append(f"  Tables to drop: {self.tables_to_drop}")
        if self.columns_to_add:
            lines.append(f"  Columns to add: {[(t, c.name) for t, c in self.columns_to_add]}")
        if self.columns_to_remove:
            lines.append(f"  Columns to remove: {self.columns_to_remove}")
        if self.indexes_to_create:
            lines.append(f"  Indexes to create: {[i.name for i in self.indexes_to_create]}")
        if self.indexes_to_drop:
            lines.append(f"  Indexes to drop: {self.indexes_to_drop}")
        return "\n".join(lines) if len(lines) > 1 else "No differences detected"


def compare_schemas(target: Dict[str, Table], current: Dict[str, Table]) -> SchemaDiff:
    diff = SchemaDiff()
    target_tables = set(target.keys())
    current_tables = set(current.keys())

    for name in target_tables - current_tables:
        diff.tables_to_create.append(target[name])
    diff.tables_to_drop = list(current_tables - target_tables)

    for name in target_tables & current_tables:
        target_table = target[name]
        current_table = current[name]

        target_cols = {c.name: c for c in target_table.columns}
        current_cols = {c.name: c for c in current_table.columns}

        for col_name in target_cols:
            if col_name not in current_cols:
                diff.columns_to_add.append((name, target_cols[col_name]))
        for col_name in current_cols:
            if col_name not in target_cols:
                diff.columns_to_remove.append((name, col_name))

        target_idx = {i.name: i for i in target_table.indexes}
        current_idx = {i.name: i for i in current_table.indexes}

        for idx_name in target_idx:
            if idx_name not in current_idx:
                diff.indexes_to_create.append(target_idx[idx_name])
        for idx_name in current_idx:
            if idx_name not in target_idx:
                diff.indexes_to_drop.append((name, idx_name))

    return diff

def generate_migration_code(diff: SchemaDiff, version: int, description: str) -> str:
    parts = []
    parts.append('"""')
    parts.append(f'database/migrations/{version:03d}_auto_schema_update.py')
    parts.append(f'Migration {version} : {description}')
    parts.append(f'Generee automatiquement par schema_detector')
    parts.append('"""')
    parts.append('')
    parts.append('import sqlite3')
    parts.append('from database.migrations.generator import migration')
    parts.append('')
    parts.append('')
    parts.append(f'@migration({version}, "{description}")')
    parts.append(f'def _migration_{version:03d}(cursor: sqlite3.Cursor) -> None:')
    parts.append('    """')
    parts.append('    Migration auto-generee.')
    parts.append('    """')
    parts.append('')

    for table in diff.tables_to_create:
        col_defs = []
        for col in table.columns:
            def_str = f"{col.name} {col.type}"
            if col.primary_key:
                def_str += " PRIMARY KEY"
            if not col.nullable:
                def_str += " NOT NULL"
            if col.default is not None:
                def_str += f" DEFAULT {col.default}"
            col_defs.append(def_str)
        for fk in table.foreign_keys:
            col_defs.append(f"FOREIGN KEY ({fk['column']}) REFERENCES {fk['ref_table']}({fk['ref_column']}) ON DELETE {fk['on_delete']}")
        cols_sql = ",\n        ".join(col_defs)
        parts.append(f"    # Creation table {table.name}")
        parts.append("    cursor.execute(''")
        parts.append(f"        CREATE TABLE IF NOT EXISTS {table.name} (")
        parts.append(f"        {cols_sql}")
        parts.append("        )")
        parts.append("    ''")
        parts.append("")
        for idx in table.indexes:
            unique = "UNIQUE " if idx.unique else ""
            cols = ", ".join(idx.columns)
            parts.append("    cursor.execute(''")
            parts.append(f"        CREATE {unique}INDEX IF NOT EXISTS {idx.name}")
            parts.append(f"        ON {idx.table} ({cols})")
            parts.append("    ''")
            parts.append("")

    for table_name, column in diff.columns_to_add:
        parts.append(f"    # Ajout colonne {column.name} a {table_name}")
        parts.append(f"    cursor.execute(\"PRAGMA table_info({table_name})\")")
        parts.append("    columns = {row[1] for row in cursor.fetchall()}")
        parts.append("")
        parts.append(f"    if '{column.name}' not in columns:")
        alter = f"ALTER TABLE {table_name} ADD COLUMN {column.name} {column.type}"
        if not column.nullable:
            alter += " NOT NULL"
        if column.default is not None:
            alter += f" DEFAULT {column.default}"
        parts.append(f"        cursor.execute(\"{alter}\")")
        parts.append("")

    for table_name, col_name in diff.columns_to_remove:
        parts.append(f"    # Attention: Colonne '{col_name}' a supprimer de '{table_name}'")
        parts.append("    # SQLite ne supporte pas DROP COLUMN directement.")
        parts.append("    # TODO : Implementer la suppression manuellement")
        parts.append("")

    for idx in diff.indexes_to_create:
        unique = "UNIQUE " if idx.unique else ""
        cols = ", ".join(idx.columns)
        parts.append(f"    # Creation index {idx.name}")
        parts.append("    cursor.execute(''")
        parts.append(f"        CREATE {unique}INDEX IF NOT EXISTS {idx.name}")
        parts.append(f"        ON {idx.table} ({cols})")
        parts.append("    ''")
        parts.append("")

    for table_name, idx_name in diff.indexes_to_drop:
        parts.append(f"    # Suppression index {idx_name}")
        parts.append(f"    cursor.execute(\"DROP INDEX IF EXISTS {idx_name}\")")
        parts.append("")

    return "\n".join(parts)


def define_target_schema() -> Schema:
    s = Schema()

    s.table("goals")\
        .col("id", "INTEGER", nullable=False, primary_key=True)\
        .col("title", "TEXT", nullable=False)\
        .col("description", "TEXT")\
        .col("created_at", "TEXT", nullable=False, default="CURRENT_TIMESTAMP")\
        .col("target_date", "TEXT")\
        .col("priority", "TEXT", nullable=False, default="'Moyenne'")\
        .col("status", "TEXT", nullable=False, default="'Non commencé'")\
        .col("color", "TEXT", default="'#3B82F6'")\
        .col("image_path", "TEXT")\
        .col("updated_at", "TEXT", nullable=False, default="CURRENT_TIMESTAMP")\
        .index("idx_goals_status", "status")\
        .index("idx_goals_priority", "priority")\
        .index("idx_goals_created_at", "created_at")\
        .build()

    s.table("tasks")\
        .col("id", "INTEGER", nullable=False, primary_key=True)\
        .col("goal_id", "INTEGER", nullable=False)\
        .col("name", "TEXT", nullable=False)\
        .col("description", "TEXT")\
        .col("status", "TEXT", nullable=False, default="'À faire'")\
        .col("created_at", "TEXT", nullable=False, default="CURRENT_TIMESTAMP")\
        .col("updated_at", "TEXT", nullable=False, default="CURRENT_TIMESTAMP")\
        .fk("goal_id", "goals", "id", on_delete="CASCADE")\
        .index("idx_tasks_goal_id", "goal_id")\
        .index("idx_tasks_updated_at", "updated_at")\
        .build()

    s.table("vision_board")\
        .col("goal_id", "INTEGER", nullable=False, primary_key=True)\
        .col("motivation_text", "TEXT", default="'''")\
        .col("pos_x", "REAL", default="0")\
        .col("pos_y", "REAL", default="0")\
        .col("width", "INTEGER", default="300")\
        .col("height", "INTEGER", default="220")\
        .col("font_size", "INTEGER", default="13")\
        .col("text_position", "TEXT", default="'bottom'")\
        .col("text_color", "TEXT", default="'#FFFFFF'")\
        .col("text_bold", "INTEGER", default="1")\
        .col("celebrated", "INTEGER", default="0")\
        .fk("goal_id", "goals", "id", on_delete="CASCADE")\
        .build()

    s.table("habits")\
        .col("id", "INTEGER", nullable=False, primary_key=True)\
        .col("title", "TEXT", nullable=False)\
        .col("description", "TEXT")\
        .col("goal_id", "INTEGER")\
        .col("task_id", "INTEGER")\
        .col("frequency", "TEXT", default="'daily'")\
        .col("target_days", "TEXT")\
        .col("color", "TEXT", default="'#3B82F6'")\
        .col("icon", "TEXT")\
        .col("created_at", "TEXT", nullable=False, default="CURRENT_TIMESTAMP")\
        .col("archived_at", "TEXT")\
        .fk("goal_id", "goals", "id", on_delete="SET NULL")\
        .fk("task_id", "tasks", "id", on_delete="SET NULL")\
        .index("idx_habits_task", "task_id")\
        .index("idx_habits_goal", "goal_id")\
        .index("idx_habits_archived", "archived_at")\
        .build()

    s.table("habit_logs")\
        .col("id", "INTEGER", nullable=False, primary_key=True)\
        .col("habit_id", "INTEGER", nullable=False)\
        .col("log_date", "TEXT", nullable=False)\
        .col("status", "TEXT", nullable=False)\
        .col("note", "TEXT")\
        .col("created_at", "TEXT", nullable=False, default="CURRENT_TIMESTAMP")\
        .fk("habit_id", "habits", "id", on_delete="CASCADE")\
        .index("idx_habit_logs_date", "habit_id", "log_date")\
        .build()
    
    s.table("vision_board_texts")\
        .col("id", "INTEGER", nullable=False, primary_key=True)\
        .col("text", "TEXT", nullable=False)\
        .col("x", "REAL", default="100")\
        .col("y", "REAL", default="100")\
        .col("font_family", "TEXT", default="'Arial'")\
        .col("font_size", "INTEGER", default="16")\
        .col("bold", "INTEGER", default="0")\
        .col("italic", "INTEGER", default="0")\
        .col("color", "TEXT", default="'#1E293B'")\
        .col("background", "TEXT")\
        .col("opacity", "INTEGER", default="0")\
        .build()

    s.table("vision_board_mood")\
        .col("id", "INTEGER", nullable=False, primary_key=True)\
        .col("image_path", "TEXT", nullable=False)\
        .col("title", "TEXT", default="''")\
        .col("x", "REAL", default="100")\
        .col("y", "REAL", default="100")\
        .col("width", "REAL", default="280")\
        .col("height", "REAL", default="190")\
        .col("color", "TEXT", default="'#3B82F6'")\
        .col("rotation", "REAL", default="0")\
        .col("created_at", "TEXT", default="CURRENT_TIMESTAMP")\
        .build()

    return s


def auto_detect_and_generate(db_path: str = "database.db") -> Optional[Path]:
    from database.migrations.generator import get_next_version
    target_schema = define_target_schema()
    current_schema = parse_current_schema(db_path)
    diff = compare_schemas(target_schema.tables, current_schema)

    if not diff.has_changes():
        print("Schema up to date - no migration needed")
        return None

    print(diff)
    migrations_dir = Path(__file__).parent
    version = get_next_version(migrations_dir)
    code = generate_migration_code(diff, version, "Auto schema update")
    filename = f"{version:03d}_auto_schema_update.py"
    filepath = migrations_dir / filename
    filepath.write_text(code, encoding="utf-8")
    print(f"\nAuto-generated migration: {filepath}")
    print("   Review the code before executing!")
    print("   Then run: python scripts/migrate.py run")
    return filepath


if __name__ == "__main__":
    auto_detect_and_generate()