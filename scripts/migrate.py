#!/usr/bin/env python3
"""
scripts/migrate.py
Script CLI simplifié pour exécuter les migrations.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.migrations.generator import run_migrations, _migration_registry


def show_help():
    print("""
Usage: python scripts/migrate.py <command>

Commands:
    run      Exécute toutes les migrations en attente
    status   Affiche les migrations enregistrées
    help     Affiche cette aide
    """)


def show_status():
    print(f"\n📋 Migrations enregistrées : {len(_migration_registry)}")
    for version, func in sorted(_migration_registry.items()):
        desc = getattr(func, '_description', 'Unknown')
        print(f"   {version:03d} — {desc}")
    print()


def main():
    if len(sys.argv) < 2:
        show_help()
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "run":
        run_migrations()
    elif cmd == "status":
        show_status()
    elif cmd == "help":
        show_help()
    else:
        print(f"❌ Commande inconnue : {cmd}")
        show_help()
        sys.exit(1)


if __name__ == "__main__":
    main()