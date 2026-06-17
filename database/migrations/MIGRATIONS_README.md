# 🗄️ Migrations - Goalift

## Commandes

```bash
# Vérifier le schéma
cd Goalift
python -m database.migrations.schema_detector

# Créer une migration manuelle
python -m database.migrations.generator create "ajouter colonne category"

# Exécuter les migrations
python -m database.migrations.generator run

# Voir les migrations appliquées
python -c "
import sqlite3
c = sqlite3.connect('database.db').cursor()
c.execute('SELECT version, description FROM schema_migrations ORDER BY version')
for r in c.fetchall(): print(f'  {r[0]:03d} | {r[1]}')
"
```

## Workflow : Ajouter une colonne

| Étape | Action | Fichier |
|-------|--------|---------|
| 1 | Ajouter colonne dans `CREATE TABLE` | `database.py` |
| 2 | Ajouter `.col(...)` dans le schéma cible | `schema_detector.py` |
| 3 | Générer la migration | `python -m database.migrations.schema_detector` |
| 4 | Relire le fichier `00X_xxx.py` | — |
| 5 | Exécuter | `python -m database.migrations.generator run` |
| 6 | Mettre à jour `create_goal()` et `update_goal()` | `database.py` |

## ⚠️ Limitations SQLite

| Opération | Support | Solution |
|-----------|---------|----------|
| `ADD COLUMN` | ✅ Auto | Migration auto |
| `DROP COLUMN` | ❌ Non | Recréer la table manuellement |
| Modifier type | ❌ Non | Recréer la table manuellement |

## 🆘 Dépannage

**Erreur `ModuleNotFoundError: No module named 'database'`**

→ Lancer depuis le dossier `Goalift/` avec `python -m`.

**Migration échoue**

```bash
copy database.db database.db.backup   # restauration
```

## Règles d'or

1. **Sauvegarder** avant : `copy database.db database.db.backup`
2. **Relire** chaque migration avant exécution
3. **Ne jamais modifier** un fichier `00X_` déjà exécuté
