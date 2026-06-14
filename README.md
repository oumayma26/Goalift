# 🎯 Goals Manager

Application desktop moderne de gestion d'objectifs personnels développée en Python avec une interface graphique CustomTkinter et une base de données SQLite.

---

## 📋 Table des matières

- [Fonctionnalités](#-fonctionnalités)
- [Prérequis](#-prérequis)
- [Installation](#-installation)
- [Lancement](#-lancement)
- [Structure du projet](#-structure-du-projet)
- [Utilisation](#-utilisation)
- [Résolution de problèmes](#-résolution-de-problèmes)

---

## ✨ Fonctionnalités

### Gestion des Goals
- ✅ Créer, modifier, supprimer des objectifs
- ✅ Titre, description, date cible, priorité (Faible/Moyenne/Haute)
- ✅ Statut automatique : Non commencé → En cours → Terminé

### Gestion des Tâches
- ✅ Ajouter des tâches à un goal
- ✅ Modifier, supprimer, marquer comme terminée
- ✅ Progression automatique calculée en temps réel

### Tableau de Bord
- ✅ Statistiques globales (goals, tâches, progression)
- ✅ Graphiques Matplotlib (camembert, jauge)
- ✅ Liste des goals récents

### Interface
- ✅ Design moderne avec CustomTkinter
- ✅ Mode sombre/clair avec persistance
- ✅ Filtres par statut, priorité, recherche textuelle
- ✅ Fenêtre redimensionnable

---

## 🔧 Prérequis

- **Python 3.10+** (recommandé : 3.11 ou 3.12)
- **pip** (gestionnaire de paquets Python)

### Vérifier l'installation

```bash
python --version
# ou
python3 --version