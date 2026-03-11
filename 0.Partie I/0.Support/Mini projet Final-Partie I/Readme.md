# 📦 STOCK MANAGER — Guide de montage pas à pas

Application de gestion de stock en ligne de commande (TUI)  
Construite avec **Python** et la bibliothèque **Rich**  
18 étapes progressives · 6 707 lignes · Sans POO

---

## 🗂️ Table des matières

1. [Prérequis](#-pr%C3%A9requis)
2. [Installation](#-installation)
3. [Structure du projet](#-structure-du-projet)
4. [Parcours pédagogique](#-parcours-p%C3%A9dagogique)
5. [Étapes en détail](#-%C3%A9tapes-en-d%C3%A9tail)
6. [Lancer l'application finale](#-lancer-lapplication-finale)
7. [Tester chaque étape isolément](#-tester-chaque-%C3%A9tape-isol%C3%A9ment)
8. [Arborescence de fichiers générée](#-arborescence-de-fichiers-g%C3%A9n%C3%A9r%C3%A9e)
9. [Concepts Python couverts](#-concepts-python-couverts)
10. [Dépannage](#-d%C3%A9pannage)

---

## ✅ Prérequis

| Outil    | Version minimale                 | Vérification       |
| -------- | -------------------------------- | ------------------ |
| Python   | 3.10+                            | `python --version` |
| pip      | récent                           | `pip --version`    |
| Terminal | UTF-8, 200 colonnes recommandées | —                  |

> **Windows** : utilisez Windows Terminal ou PowerShell — évitez l'invite de commande classique (mauvais rendu Unicode).  
> **macOS/Linux** : n'importe quel terminal convient.

---

## 🚀 Installation

### 1. Cloner ou copier les fichiers

Placez tous les fichiers `etape_*.py` dans un même dossier :

```
stock_manager/
├── etape_01_decouverte_rich.py
├── etape_02_splash_screen.py
├── ...
└── etape_18_version_finale.py
```

### 2. Créer un environnement virtuel (recommandé)

```bash
# Créer l'environnement
python -m venv venv

# L'activer
# Windows :
venv\Scripts\activate
# macOS / Linux :
source venv/bin/activate
```

### 3. Installer la seule dépendance externe

```bash
pip install rich
```

C'est tout. Aucune autre bibliothèque n'est nécessaire.  
Toutes les autres importations (`json`, `csv`, `pathlib`, `datetime`, `logging`, `shutil`, `re`, `math`) font partie de la bibliothèque standard Python.

### 4. Vérifier l'installation

```bash
python -c "from rich.console import Console; Console().print('[bold green]Rich OK ✓[/bold green]')"
```

---

## 📁 Structure du projet

```
stock_manager/
│
├── etape_01_decouverte_rich.py     ← Départ : couleurs Rich
├── etape_02_splash_screen.py       ← Animation de démarrage
├── etape_03_modele_produit.py      ← Modèle de données
├── etape_04_catalogue_dashboard.py ← Tableau de bord
├── etape_05_saisie_validation.py   ← Formulaires + validation
├── etape_06_menu_navigation.py     ← Navigation hiérarchique
├── etape_07_crud.py                ← CRUD complet
├── etape_08_persistance.py         ← JSON + backup automatique
├── etape_09_mouvements.py          ← Entrées / sorties / historique
├── etape_10_recherche_filtres.py   ← Recherche multi-critères
├── etape_11_rapports.py            ← Rapports et analyses
├── etape_12_export.py              ← Export CSV et TXT
├── etape_13_alertes.py             ← Alertes automatiques
├── etape_14_statistiques.py        ← Graphes ASCII
├── etape_15_parametres.py          ← Configuration dynamique
├── etape_16_erreurs_logs.py        ← Gestion des erreurs et logs
├── etape_17_architecture.py        ← Guide d'architecture modulaire
├── etape_18_version_finale.py      ← Application complète assemblée
│
└── README.md                       ← Ce fichier
```

**Dossiers créés automatiquement à l'exécution :**

```
data/
├── stock.json          ← Catalogue des produits
├── stock_backup.json   ← Sauvegarde automatique
├── historique.json     ← Mouvements de stock
└── config.json         ← Paramètres de l'application

exports/
└── catalogue_*.csv     ← Fichiers exportés

logs/
└── stock_manager.log   ← Journal d'activité
```

---

## 🎓 Parcours

Le projet est découpé en **4 phases** de 4 à 5 étapes chacune.  
Chaque étape est **autonome** et exécutable indépendamment.

```
Phase 1 — FONDATIONS        (étapes 01–06)  ~60 min
  ↓ Découvrir Rich, construire l'interface de base

Phase 2 — DONNÉES           (étapes 07–09)  ~45 min
  ↓ CRUD, persistance JSON, historique des mouvements

Phase 3 — ANALYSE           (étapes 10–12)  ~60 min
  ↓ Recherche avancée, rapports, export CSV/TXT

Phase 4 — PRODUCTION        (étapes 13–18)  ~75 min
  ↓ Alertes, graphes, paramètres, logs, architecture, version finale
```

**Durée totale estimée : 4 à 6 heures** selon le niveau.

---

## 📋 Étapes en détail

### Phase 1 — Fondations

---

#### Étape 01 — Découverte de Rich `(89 lignes)`

**Ce qu'on apprend :**

- `from rich.console import Console`
- `console.print()` avec balises de style `[bold red]texte[/bold red]`
- `console.rule()` pour les séparateurs
- f-strings et interpolation

**Concepts Python :** variables, print, f-strings, import

```bash
python etape_01_decouverte_rich.py
```

**Sortie attendue :** textes colorés, titres encadrés, règles horizontales.

---

#### Étape 02 — Splash Screen `(163 lignes)`

**Ce qu'on apprend :**

- `Panel`, `Text`, `Align` de Rich
- `Progress` avec `SpinnerColumn` et `BarColumn`
- Logo ASCII art
- `datetime.now()` pour l'horodatage

**Concepts Python :** `import datetime`, `time.sleep()`, boucles `for`

```bash
python etape_02_splash_screen.py
```

**Sortie attendue :** logo animé avec barre de chargement.

---

#### Étape 03 — Modèle de données `(232 lignes)`

**Ce qu'on apprend :**

- Structure dict d'un produit (13 champs)
- Fonctions de calcul : `valeur_stock()`, `marge_pct()`
- `etat_stock()` → retourne un tuple `(code, libellé, couleur)`
- `jours_avant_expiration()` avec `datetime.timedelta`
- `afficher_fiche()` avec `Table` colorée

**Concepts Python :** dict, tuple, fonctions, conditions, datetime

```bash
python etape_03_modele_produit.py
```

**Sortie attendue :** fiche produit colorée avec tous les indicateurs.

---

#### Étape 04 — Catalogue et Dashboard `(235 lignes)`

**Ce qu'on apprend :**

- `Table` avec `row_styles` alternés
- `Columns([Panel(), Panel(), Panel()])` pour la mise en page
- KPI : total articles, alertes, valeur, marge
- Regroupement par catégorie avec un dict

**Concepts Python :** listes, dict, `sorted()`, `sum()`, `max()`

```bash
python etape_04_catalogue_dashboard.py
```

**Sortie attendue :** tableau catalogue + 3 panneaux KPI côte à côte.

---

#### Étape 05 — Saisie et Validation `(275 lignes)`

**Ce qu'on apprend :**

- `Prompt.ask()`, `IntPrompt`, `FloatPrompt`, `Confirm`
- `re.match()` pour valider une référence avec regex
- Validation de date future
- Formulaire complet avec récapitulatif

**Concepts Python :** `import re`, `try/except ValueError`, boucles `while True`

```bash
python etape_05_saisie_validation.py
```

**Sortie attendue :** formulaire interactif avec validation en temps réel.

---

#### Étape 06 — Menu et Navigation `(287 lignes)`

**Ce qu'on apprend :**

- Pattern `while True` pour la boucle principale
- `effacer()` multi-plateforme avec `os.system()`
- `entete()` persistant (fil d'Ariane, horodatage)
- `afficher_menu()` générique réutilisable
- Menus hiérarchiques (principal → sous-menu)

**Concepts Python :** `import os`, fonctions, dict comme table de dispatch

```bash
python etape_06_menu_navigation.py
```

**Sortie attendue :** navigation complète avec menus imbriqués.

---

### Phase 2 — Données

---

#### Étape 07 — CRUD `(322 lignes)`

**Ce qu'on apprend :**

- `ajouter_produit()` avec vérification de doublon
- `trouver_par_ref()` recherche par référence
- `rechercher()` recherche multi-champs
- `modifier_produit()` avec `CHAMPS_PROTEGES`
- `supprimer_produit()` avec `list.pop(i)`
- `trier()` avec `sorted(key=lambda)`

**Concepts Python :** `enumerate()`, `list.pop()`, `sorted()`, lambda, set

```bash
python etape_07_crud.py
```

**Sortie attendue :** démonstration des 4 opérations CRUD avec résultats affichés.

---

#### Étape 08 — Persistance JSON `(303 lignes)`

**Ce qu'on apprend :**

- `json.dump()` / `json.load()`
- `pathlib.Path` pour les chemins de fichiers
- `shutil.copy2()` pour le backup automatique
- `try/except json.JSONDecodeError` + restauration backup
- Métadonnées dans le fichier (date, nb_produits)

**Concepts Python :** `import json`, `import pathlib`, `import shutil`, `with open()`

```bash
python etape_08_persistance.py
```

**Sortie attendue :** création de `data/stock.json` et `data/stock_backup.json`.

---

#### Étape 09 — Mouvements de stock `(314 lignes)`

**Ce qu'on apprend :**

- `enregistrer_mouvement()` : entrée / sortie / ajustement
- `historique.insert(0, mouvement)` : plus récent en premier
- Audit trail : `qte_avant` / `qte_apres`
- `afficher_historique()` avec tableau coloré
- Formulaires `formulaire_entree()` / `formulaire_sortie()`

**Concepts Python :** `list.insert()`, dict, conditions, datetime

```bash
python etape_09_mouvements.py
```

**Sortie attendue :** historique des mouvements avec codes couleur entrée/sortie.

---

### Phase 3 — Analyse

---

#### Étape 10 — Recherche et Filtres `(424 lignes)`

**Ce qu'on apprend :**

- `recherche_avancee()` avec 6 critères cumulables
- Filtres : terme, catégorie, fournisseur, prix_max, en_alerte, expirant_dans
- `datetime.timedelta(days=X)` pour les dates limites
- `trier_resultats()` avec 10 clés de tri
- Affichage paginé avec navigation

**Concepts Python :** list comprehension, `sorted(key=lambda)`, `timedelta`

```bash
python etape_10_recherche_filtres.py
```

**Sortie attendue :** résultats filtrés et paginés avec navigation.

---

#### Étape 11 — Rapports `(494 lignes)`

**Ce qu'on apprend :**

- `rapport_valorisation()` : valeur par catégorie avec totaux
- `rapport_marges()` : top N et flop N des marges
- `rapport_expirations()` : coût financier à risque
- `rapport_fournisseur()` : analyse par fournisseur
- `t.add_section()` pour les lignes de total

**Concepts Python :** dict, `sum()`, `max()`, `sorted()`, lambda

```bash
python etape_11_rapports.py
```

**Sortie attendue :** 4 rapports distincts avec tableaux et totaux.

---

#### Étape 12 — Export CSV et TXT `(434 lignes)`

**Ce qu'on apprend :**

- `csv.writer(delimiter=';')` pour Excel français
- `encoding='utf-8-sig'` (BOM pour Excel Windows)
- Virgule décimale : `.replace('.', ',')`
- Rapport TXT avec alignement `f"{'texte':<12}"` et `f"{nombre:>10.3f}"`
- Rotation automatique des noms de fichiers avec horodatage

**Concepts Python :** `import csv`, `open()` avec `with`, f-strings formatés

```bash
python etape_12_export.py
```

**Sortie attendue :** fichiers créés dans `exports/` avec confirmation.

---

### Phase 4 — Production

---

#### Étape 13 — Alertes `(423 lignes)`

**Ce qu'on apprend :**

- `analyser_alertes()` : moteur séparé de l'affichage
- `badge_alertes()` : résumé compact pour l'en-tête
- `afficher_bulletin_alertes()` : bulletin complet
- Calcul du coût de réapprovisionnement
- `Text()` pour assembler du texte multi-style

**Concepts Python :** dict de listes, conditions imbriquées, `sum()`

```bash
python etape_13_alertes.py
```

**Sortie attendue :** badge court + bulletin d'alertes complet.

---

#### Étape 14 — Statistiques Visuelles `(480 lignes)`

**Ce qu'on apprend :**

- `barre(valeur, maximum, largeur)` avec `█` et `░`
- `barre_bicolore()` avec seuils de couleur
- `graphe_stocks_categorie()` / `graphe_marges()` / `graphe_top_valeur()`
- `sparkline()` avec caractères `▁▂▃▄▅▆▇█`
- `graphe_evolution_historique()` : entrées vs sorties par jour

**Concepts Python :** `round()`, `min()`, `max()`, caractères Unicode

```bash
python etape_14_statistiques.py
```

**Sortie attendue :** barres ASCII, graphes par catégorie, sparklines de tendance.

---

#### Étape 15 — Paramètres Dynamiques `(390 lignes)`

**Ce qu'on apprend :**

- `CONFIG_DEFAUT` avec toutes les clés et valeurs initiales
- Fusion `{**CONFIG_DEFAUT, **config_chargee}` pour garantir toutes les clés
- `Prompt.ask(default=valeur_actuelle)` pour les formulaires de modification
- Sauvegarde automatique à la sortie du menu
- 4 sections de configuration (identité, finance, seuils, affichage)

**Concepts Python :** dict fusion `{**a, **b}`, `json.dump/load`, `pathlib`

```bash
python etape_15_parametres.py
```

**Sortie attendue :** affichage config + création de `data/config.json`.

---

#### Étape 16 — Erreurs et Logs `(383 lignes)`

**Ce qu'on apprend :**

- `logging.basicConfig()` : configuration complète
- Niveaux : `DEBUG` / `INFO` / `WARNING` / `ERROR` / `CRITICAL`
- `try / except / finally` avec hiérarchie des exceptions
- `operation_securisee(nom, fonction, *args)` → `(True, résultat)` ou `(False, None)`
- Décorateur `@securiser()` pour protéger une fonction
- `afficher_derniers_logs()` : consultation dans le terminal

**Concepts Python :** `import logging`, `import traceback`, décorateurs, `*args`

```bash
python etape_16_erreurs_logs.py
```

**Sortie attendue :** démonstration d'erreurs capturées + consultation du log.

---

#### Étape 17 — Architecture Modulaire `(353 lignes)`

> Cette étape est un **guide visuel**, pas une application à exécuter.  
> Elle explique comment découper le projet en modules séparés.

**Ce qu'on apprend :**

- Structure `modules/` avec `__init__.py`
- Règles d'imports (unidirectionnels, pas de cycles)
- `if __name__ == "__main__"` dans chaque module
- `__all__` pour définir l'API publique
- `sys.path.insert(0, ...)` pour les imports relatifs

```bash
python etape_17_architecture.py
```

**Sortie attendue :** schéma de l'architecture avec règles et commandes.

---

#### Étape 18 — Version Finale `(1106 lignes)` ⭐

**Application complète assemblée.**  
Toutes les étapes précédentes intégrées en un seul fichier autonome.

**Contenu :**

- Splash screen animé
- CRUD produits complet avec formulaires
- Persistance JSON avec backup
- Mouvements (entrées/sorties) avec historique
- Rapports et tableau de bord
- Graphes ASCII
- Alertes automatiques au démarrage
- Export CSV
- Paramètres dynamiques
- Logs et gestion des erreurs
- Navigation hiérarchique complète

```bash
python etape_18_version_finale.py
```

---

## ▶️ Lancer l'application finale

```bash
# Depuis le dossier stock_manager/
python etape_18_version_finale.py
```

**Séquence de démarrage :**

1. Création automatique des dossiers `data/`, `exports/`, `logs/`
2. Splash screen animé
3. Chargement des données (ou catalogue vide si première exécution)
4. Vérification des alertes
5. Menu principal

**Navigation :**

```
Menu principal
├── 1. Gestion des produits
│   ├── 1. Ajouter
│   ├── 2. Afficher le catalogue
│   ├── 3. Voir la fiche
│   ├── 4. Modifier
│   ├── 5. Supprimer
│   └── 6. Recherche rapide
├── 2. Mouvements de stock
│   ├── 1. Entrée en stock
│   ├── 2. Sortie de stock
│   └── 3. Voir l'historique
├── 3. Rapports & statistiques
│   ├── 1. Tableau de bord
│   ├── 2. Graphe visuel
│   ├── 3. Bulletin d'alertes
│   └── 4. Exporter CSV
├── 4. Paramètres
└── 0. Quitter
```

---

## 🧪 Tester chaque étape isolément

Chaque fichier contient un bloc `if __name__ == "__main__":` avec des données de test intégrées. Il suffit de lancer le fichier directement :

```bash
# Tester les rapports sans toucher à l'application complète
python etape_11_rapports.py

# Tester le CRUD
python etape_07_crud.py

# Tester les graphes ASCII
python etape_14_statistiques.py
```

Chaque test est **autonome** — il crée ses propres données de test, n'a besoin d'aucun fichier JSON existant, et n'écrit rien sur le disque (sauf étapes 08, 12, 15, 16 qui créent des fichiers dans `data/`, `exports/`, `logs/`).

---

## 📂 Arborescence de fichiers générée

Après un premier lancement de l'application :

```
stock_manager/
├── data/
│   ├── stock.json            ← Catalogue (créé au premier lancement)
│   ├── stock_backup.json     ← Copie automatique avant chaque sauvegarde
│   ├── historique.json       ← Tous les mouvements de stock
│   └── config.json           ← Paramètres de l'application
│
├── exports/
│   ├── catalogue_20250218_143022.csv   ← Export CSV horodaté
│   └── rapport_20250218_143155.txt     ← Rapport TXT horodaté
│
└── logs/
    ├── stock_manager.log      ← Journal courant
    └── stock_manager.log.bak  ← Rotation automatique si > 1 MB
```

---

## 🧠 Concepts Python couverts

| Concept                                             | Étapes |
| --------------------------------------------------- | ------ |
| Variables, print, f-strings                         | 01     |
| `import datetime`, `time.sleep()`                   | 02     |
| dict, tuple, fonctions, conditions                  | 03     |
| Listes, `sorted()`, `sum()`, `max()`                | 04     |
| `import re`, `try/except`, `while True`             | 05     |
| `import os`, fonctions, dispatch table              | 06     |
| `enumerate()`, `list.pop()`, lambda                 | 07     |
| `import json`, `pathlib`, `shutil`, `with open()`   | 08     |
| `list.insert()`, audit trail                        | 09     |
| list comprehension, `timedelta`                     | 10     |
| `t.add_section()`, dict de calcul                   | 11     |
| `import csv`, encodage BOM, f-strings alignés       | 12     |
| `Text()`, conditions imbriquées                     | 13     |
| `round()`, caractères Unicode `█▁▂`                 | 14     |
| `{**dict_a, **dict_b}`, fusion config               | 15     |
| `import logging`, `import traceback`, décorateurs   | 16     |
| `__name__`, `__all__`, `sys.path`, imports relatifs | 17     |
| Assemblage complet, `KeyboardInterrupt`             | 18     |

---

## 🛠️ Dépannage

### Caractères illisibles dans le terminal

```bash
# Windows PowerShell — forcer UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001

# Ou lancer Python avec la variable d'environnement
set PYTHONIOENCODING=utf-8
python etape_18_version_finale.py
```

### `ModuleNotFoundError: No module named 'rich'`

```bash
pip install rich
# ou avec pip3 si plusieurs versions de Python
pip3 install rich
```

### Affichage trop étroit (tableaux cassés)

Agrandissez votre fenêtre de terminal à **au moins 160 colonnes**.  
Rich adapte automatiquement la largeur à la taille du terminal.

### Fichier `data/stock.json` corrompu

L'application restaure automatiquement `data/stock_backup.json` au démarrage.  
Si les deux fichiers sont corrompus, supprimez-les — l'application repart d'un catalogue vide.

### Les barres ASCII s'affichent en `?` ou en carrés

Votre terminal ne supporte pas Unicode. Changez la police du terminal pour une police compatible : **Cascadia Code**, **Fira Code**, **JetBrains Mono**, ou **Consolas**.

---

## 📌 Conseils pour progresser

1. **Ne pas copier-coller** — tapez le code à la main pour l'intégrer.
2. **Exécuter après chaque fonction ajoutée** — ne pas tout écrire puis tester.
3. **Lire les commentaires** — chaque fichier explique le "pourquoi" des choix.
4. **Faire les exercices** (bloc `🏋️ EXERCICE` en bas de chaque fichier) avant de passer à l'étape suivante.
5. **Utiliser `python -m pdb etape_XX.py`** pour déboguer pas à pas.

---

## 📄 Licence

Projet pédagogique — libre de modification et d'utilisation.
