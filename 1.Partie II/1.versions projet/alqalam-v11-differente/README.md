# Guide Utilisateur — Al Qalam Stock Manager (V11)

Ce document explique comment installer, lancer et utiliser **Al Qalam Stock Manager** au quotidien.

## 1. Objectif du logiciel

Al Qalam Stock Manager est une application de gestion de stock pour papeterie.
Vous pouvez:

- gérer les produits (ajout, consultation)
- enregistrer les entrées et sorties
- surveiller les ruptures
- suivre l'historique des mouvements
- importer un catalogue CSV
- exporter les données en CSV et Excel
- consulter les statistiques en temps réel

## 2. Prérequis

- Windows 10/11
- Python 3.11+ (ou via `py -3`)
- Dépendances Python:

```bash
pip install customtkinter pandas openpyxl pytest pytest-cov
```

## 3. Démarrage de l'application

### Méthode simple (double-clic)

- Ouvrir le dossier du projet
- Double-cliquer sur `launch_app.bat`

### Méthode terminal

```bash
py -3 main.py
```

## 4. Écran d'accueil et structure UI

Au lancement:

1. Un **splash screen** s'affiche
2. La fenêtre principale s'ouvre avec:
- une **sidebar** à gauche pour naviguer
- la zone de contenu au centre
- une **barre de statut** en bas
- un bouton **☀️/🌙** pour le thème clair/sombre

## 5. Navigation (sidebar)

Sections disponibles:

- `📦 Stock`
- `📥 Entrée`
- `📤 Sortie`
- `📊 Tableau de bord`
- `📁 Import / Export`
- `🕐 Historique`
- `📜 Journal`
- `⚙️ À propos`

## 6. Expérience complète par usage

### 6.1 Consulter le stock (`📦 Stock`)

- Le tableau affiche: référence, nom, catégorie, quantité, prix vente, statut
- Les produits en alerte sont visuellement marqués
- Double-clic sur une ligne: ouvre la fiche détail du produit

Actions directes:

- `+ Nouveau` pour créer un produit
- `↑ Entrée` pour aller au formulaire d'entrée
- `↓ Sortie` pour aller au formulaire de sortie

Recherche et filtre:

- la recherche texte filtre en direct (`ref`, `nom`, `catégorie`)
- filtre catégorie via liste déroulante
- tri des colonnes via clic sur l'entête

### 6.2 Créer un produit (`+ Nouveau`)

Depuis la section Stock:

1. Cliquer `+ Nouveau`
2. Renseigner les champs (ref, nom, catégorie, prix, qté, seuil)
3. Cliquer `Créer`

Résultat:

- le produit est enregistré en base SQLite
- il apparaît immédiatement dans le tableau

### 6.3 Enregistrer une entrée (`📥 Entrée`)

1. Saisir la référence produit
2. Saisir une quantité positive
3. Ajouter une note (optionnel)
4. Valider

Résultat:

- la quantité augmente
- un mouvement `entree` est ajouté à l'historique
- les statistiques sont mises à jour

### 6.4 Enregistrer une sortie (`📤 Sortie`)

1. Saisir la référence
2. Saisir la quantité à retirer
3. Valider

Règles:

- sortie refusée si stock insuffisant
- message d'erreur clair affiché

Résultat:

- la quantité diminue
- un mouvement `sortie` est historisé

### 6.5 Surveiller la santé du stock (`📊 Tableau de bord`)

La section affiche:

- nombre total de produits
- valeur totale du stock (TND)
- nombre d'alertes
- statistiques par catégorie

Exports depuis ce même écran:

- bouton `Exporter CSV`
- bouton `Exporter Rapport Excel`

### 6.6 Importer un catalogue (`📁 Import / Export`)

1. Cliquer `Importer un catalogue CSV`
2. Sélectionner un fichier CSV
3. Lire le rapport affiché

Format attendu (colonnes):

- `ref, nom, categorie, prix_achat, prix_vente, qte, seuil_min`

Résultat d'import:

- `importés`: nouveaux produits créés
- `mis à jour`: références existantes mises à jour
- `rejetés`: lignes invalides avec motif d'erreur

### 6.7 Exporter les données

#### Export CSV

- depuis `📊 Tableau de bord` > `Exporter CSV`
- génère un fichier réimportable

#### Export Excel

- depuis `📊 Tableau de bord` > `Exporter Rapport Excel`
- génère un `.xlsx` multi-feuilles:
  - `Stock`
  - `Alertes`
  - `Statistiques`
- mise en forme appliquée automatiquement

### 6.8 Consulter l'historique (`🕐 Historique`)

Affiche tous les mouvements avec:

- date
- référence
- type
- quantité
- avant/après
- note

Filtres:

- par référence
- par type (`entree`, `sortie`, `retour`, `inventaire`)

### 6.9 Consulter les logs (`📜 Journal`)

- Affiche les logs applicatifs
- Champ `Pattern regex` pour filtrer les lignes
- Utile pour audit et diagnostic

Exemples de recherche:

- `sortie`
- `CRAY-001`
- `ERROR|erreur`

### 6.10 Informations produit (`⚙️ À propos`)

Affiche:

- nom de l'application
- version
- stack technique

## 7. Alertes et notifications

- Un thread de surveillance vérifie les ruptures en arrière-plan
- Si alertes: un bandeau de notification s'affiche
- La barre de statut affiche en continu:
  - état surveillance
  - nb produits
  - valeur stock
  - nb alertes
  - heure courante

## 8. Raccourcis clavier

- `Ctrl+N`: ouvrir le formulaire Nouveau produit
- `Ctrl+E`: aller à la zone d'export (tableau de bord)
- `F5`: rafraîchir les vues

## 9. Données et persistance

Fichiers générés automatiquement dans `data/`:

- `stock.db` (SQLite)
- `alqalam.log` (journal technique)
- `imports/` et `exports/`

Les données sont conservées entre redémarrages.

## 10. Erreurs courantes et solutions

### Le BAT n'ouvre rien

- Vérifier que Python est installé
- Tester en terminal: `py -3 --version`

### Message dépendance manquante

Installer:

```bash
pip install customtkinter pandas openpyxl
```

### Import CSV rejeté

- vérifier l'en-tête exact des colonnes
- vérifier le format référence (`CRAY-001`)
- vérifier les quantités/prix

### Sortie impossible

- stock insuffisant: réduire la quantité demandée

## 11. Validation technique (développeur/formation)

Lancer les tests:

```bash
py -3 -m pytest tests -v
```

Couverture:

```bash
py -3 -m pytest tests --cov=. --cov-report=term-missing
```

## 12. Support pédagogique

Ce projet est conçu pour la progression atelier par atelier.
La V11 correspond à la version finale livrable, avec:

- architecture modulaire
- persistance SQLite
- import/export industriel
- UI complète
- tests automatisés
