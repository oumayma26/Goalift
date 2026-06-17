#!/usr/bin/env python3
"""
scripts/migrate.py
Script CLI complet pour gerer les migrations.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def show_help():
    print("""
Usage: python scripts/migrate.py <command> [options]

Commands:
    generate, g       Generer une nouvelle migration manuelle
    auto, a           Detecter automatiquement et generer une migration
    run, r            Executer les migrations en attente
    status, s         Voir le statut des migrations
    help, h           Afficher cette aide

Examples:
    python scripts/migrate.py generate --name "ajout_colonne_email"
    python scripts/migrate.py g -n "ajout_table_notifications"
    python scripts/migrate.py auto
    python scripts/migrate.py run
    python scripts/migrate.py status
""")


def show_status():
    import sqlite3
    from pathlib import Path
    
    db_path = "database.db"
    if not os.path.exists(db_path):
        print("Base de donnees non trouvee")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT version, applied_at, description FROM schema_migrations ORDER BY version")
        rows = cursor.fetchall()
        
        if not rows:
            print("Aucune migration appliquee")
        else:
            print(f"Migrations appliquees ({len(rows)} total):")
            print("-" * 60)
            for version, applied_at, desc in rows:
                print(f"  v{version:03d}  {applied_at}  {desc}")
            
            migrations_dir = Path(__file__).parent.parent / "database" / "migrations"
            from database.migrations.generator import get_next_version
            next_v = get_next_version(migrations_dir)
            
            if next_v > len(rows) + 1:
                pending = list(range(len(rows) + 1, next_v))
                print(f"\nMigrations en attente : {pending}")
            else:
                print("\nToutes les migrations sont a jour")
                
    except sqlite3.OperationalError:
        print("Table schema_migrations non trouvee - la base n'est pas initialisee")
    finally:
        conn.close()


def main():
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command in ("generate", "g"):
        from database.migrations.generator import main as generate_migration
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        generate_migration()
    
    elif command in ("auto", "a"):
        from database.migrations.schema_detector import auto_detect_and_generate
        auto_detect_and_generate()
    
    elif command in ("run", "r"):
        from database.migrations import run_migrations
        run_migrations("database.db")
    
    elif command in ("status", "s"):
        show_status()
    
    elif command in ("help", "h", "--help", "-h"):
        show_help()
    
    else:
        print(f"Commande inconnue : {command}")
        show_help()


if __name__ == "__main__":
    main()