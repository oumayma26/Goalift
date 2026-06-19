def run_migrations(db_path: str = "database.db") -> None:
    """Exécute toutes les migrations en attente."""
    migrations_dir = Path(__file__).parent
    
    if migrations_dir.exists():
        for f in sorted(migrations_dir.glob("*.py")):
            # Ignore les fichiers système
            if f.name in ("__init__.py", "generator.py", "schema_detector.py"):
                continue
            
            # Import dynamique du fichier de migration
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location(f"migration_{f.stem}", f)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    print(f"  📄 Chargé: {f.name}")
            except Exception as e:
                print(f"  ⚠️  Ignoré {f.name}: {e}")

    applied = get_applied_versions(db_path)
    pending = sorted(v for v in _migration_registry if v not in applied)

    if not pending:
        print("✅ Aucune migration en attente.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        for version in pending:
            func = _migration_registry[version]
            desc = getattr(func, '_description', 'Unknown')
            print(f"⬆️  Migration {version:03d}: {desc}")
            func(cursor)
            record_migration(cursor, version, desc)
        
        conn.commit()
        print(f"✅ {len(pending)} migration(s) appliquée(s).")
    except Exception as e:
        conn.rollback()
        print(f"❌ Erreur migration: {e}")
        raise
    finally:
        conn.close()