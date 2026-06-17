# Système de Migrations - Goals Manager

## Structure

```
database/
├── __init__.py              # (vide ou exports)
├── database.py              # DatabaseManager (refactorisé)
└── migrations/
    ├── __init__.py          # MIGRATIONS dict + MigrationRunner
    ├── 001_initial.py       # (déjà dans __init__.py)
    ├── 002_add_habits.py    # (déjà dans __init__.py)
    └── 006_add_user_preferences.py  # Exemple
```

## Comment ajouter une migration

### 1. Créer un nouveau fichier

```bash
# Nom : XXX_description_courte.py
touch database/migrations/007_ajout_colonne_xyz.py
```

### 2. Écrire la migration

```python
"""
database/migrations/007_ajout_colonne_xyz.py
"""

import sqlite3
from database.migrations import migration


@migration(7, "Description de la migration")
def _migration_007(cursor: sqlite3.Cursor) -> None:
    """
    Toujours idempotent : vérifie avant d'altérer.
    """
    # Vérifier si la colonne existe déjà
    cursor.execute("PRAGMA table_info(nom_table)")
    columns = {row[1] for row in cursor.fetchall()}

    if "nouvelle_colonne" not in columns:
        cursor.execute("""
            ALTER TABLE nom_table 
            ADD COLUMN nouvelle_colonne TEXT DEFAULT 'valeur'
        """)

    # Pour les nouvelles tables : CREATE TABLE IF NOT EXISTS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nouvelle_table (
            id INTEGER PRIMARY KEY,
            ...
        )
    """)
```

### 3. Relancer l'application

```bash
python main.py
```

Le système détecte automatiquement la nouvelle migration et l'applique.

## Règles d'or

| Règle | Pourquoi |
|-------|----------|
| **Toujours idempotent** | `IF NOT EXISTS`, `PRAGMA table_info` |
| **Jamais DROP TABLE** | = perte de données irréversible |
| **Backup auto** | Fait automatiquement par MigrationRunner |
| **Numéros séquentiels** | Pas de trous, pas de doublons |
| **Une migration = un changement** | Facilite le debug et le rollback |

## Types de changements courants

### Ajouter une colonne
```python
cursor.execute("PRAGMA table_info(users)")
columns = {row[1] for row in cursor.fetchall()}

if "email" not in columns:
    cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
```

### Créer une nouvelle table
```python
cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY,
        habit_id INTEGER REFERENCES habits(id),
        time TEXT NOT NULL,
        enabled INTEGER DEFAULT 1
    )
""")
```

### Migrer des données
```python
# 1. Créer nouvelle table
cursor.execute("CREATE TABLE new_goals (...)")

# 2. Copier données
cursor.execute("""
    INSERT INTO new_goals (id, title, ...)
    SELECT id, title, ... FROM goals
""")

# 3. Supprimer ancienne (seulement si données copiées !)
cursor.execute("DROP TABLE goals")
cursor.execute("ALTER TABLE new_goals RENAME TO goals")
```

## Rollback manuel

Si une migration plante :

```bash
# 1. Restaurer le backup
mv database.db.backup_20260116_143022 database.db

# 2. Corriger la migration
# 3. Relancer
python main.py
```

## Vérifier l'état des migrations

```python
from database import DatabaseManager
import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# Version actuelle
cursor.execute("SELECT * FROM schema_migrations ORDER BY version")
for row in cursor.fetchall():
    print(f"v{row[0]} : {row[2]} (appliquée le {row[1]})")
```
