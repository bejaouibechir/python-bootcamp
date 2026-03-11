# 📚 Al Qalam — Gestion de Stock

### Logiciel de gestion de stock pour papeterie · Version 1.0.0

---

## 🚀 Lancement rapide

Double-cliquez sur **`Lancer_AlQalam.bat`** — c'est tout.

> Le fichier batch installe automatiquement les dépendances si nécessaire.

**Ou depuis un terminal :**

```bash
cd alqalam
py -3 main.py
```

---

## 🖥️ Présentation de l'interface

```
┌─────────────────────────────────────────────────────────────────┐
│  📚  Al Qalam — Gestion de Stock                    v1.0.0      │
├─────────────────────────────────────────────────────────────────┤
│  [ + Nouveau produit ]  [ ↑ Entrée stock ]  [ ↓ Sortie stock ] │
│                                                                  │
│  Référence    Nom              Catégorie   Qté   Statut         │
│  ──────────────────────────────────────────────────────────     │
│  CRAY-001     Crayon HB        Écriture    150   ✅ OK          │
│  CRAY-002     Crayon 2B        Écriture      8   ⚠️ Alerte      │
│  STYL-001     Stylo Bleu       Écriture    200   ✅ OK          │
│  STYL-002     Stylo Rouge      Écriture      4   ⚠️ Alerte      │
│                                                                  │
│  📦 10 produits en stock | Valeur totale : 944.40 TND  ⚠️ 4 alertes │
└─────────────────────────────────────────────────────────────────┘
```

L'interface se compose de :

| Zone                 | Description                                 |
| -------------------- | ------------------------------------------- |
| **Barre de titre**   | Nom de l'application et version             |
| **Barre d'actions**  | Boutons pour les opérations principales     |
| **Tableau de stock** | Liste de tous les produits avec leur statut |
| **Barre de statut**  | Nombre de produits, valeur totale, alertes  |

---

## 📋 Guide des fonctionnalités

---

### 1. Consulter le stock

Au démarrage, le tableau affiche automatiquement tous les produits.

**Lecture du tableau :**

| Colonne        | Description                              |
| -------------- | ---------------------------------------- |
| **Référence**  | Code unique du produit (ex : `CRAY-001`) |
| **Nom**        | Nom commercial du produit                |
| **Catégorie**  | Famille (Écriture, Papier, Coupe…)       |
| **Prix Achat** | Prix payé au fournisseur (en TND)        |
| **Prix Vente** | Prix facturé au client (en TND)          |
| **Quantité**   | Stock disponible actuellement            |
| **Seuil Min**  | Quantité minimale avant alerte           |
| **Statut**     | ✅ OK ou ⚠️ Alerte                        |

**Code couleur des lignes :**

- 🟥 **Rouge clair** → produit en rupture (quantité ≤ seuil minimum)
- ⬜ **Blanc / gris** → produit en stock normal

---

### 2. Ajouter un nouveau produit

**Étapes :**

1. Cliquer sur le bouton **`+ Nouveau produit`**
2. Remplir le formulaire :

| Champ             | Obligatoire | Exemple            |
| ----------------- | ----------- | ------------------ |
| Référence         | ✅ Oui       | `STYL-003`         |
| Nom               | ✅ Oui       | `Stylo Vert`       |
| Catégorie         | ✅ Oui       | `Écriture`         |
| Prix d'achat      | ✅ Oui       | `0.30` ou `0,30`   |
| Prix de vente     | ✅ Oui       | `0.90`             |
| Quantité initiale | Non         | `100` (défaut : 0) |
| Seuil d'alerte    | Non         | `20` (défaut : 5)  |

3. Cliquer sur **`✓ Ajouter`**

**Résultat :** Le produit apparaît immédiatement dans le tableau et est sauvegardé.

> ⚠️ La référence doit être **unique**. Si elle existe déjà, un message d'erreur s'affiche.

---

### 3. Enregistrer une entrée de stock

Une entrée de stock correspond à une **réception de marchandise** (livraison fournisseur).

**Étapes :**

1. *(Optionnel)* Cliquer sur la ligne du produit dans le tableau pour le pré-sélectionner
2. Cliquer sur le bouton **`↑ Entrée stock`**
3. Dans le dialogue :
   - **Produit** : choisir dans la liste déroulante
   - **Quantité** : saisir le nombre d'unités reçues (ex : `50`)
   - **Note** : commentaire optionnel (ex : `Commande fournisseur #42`)
4. Cliquer sur **`✓ Valider`**

**Résultat :** La quantité du produit augmente et le statut se met à jour.

---

### 4. Enregistrer une sortie de stock

Une sortie de stock correspond à une **vente** ou une **consommation interne**.

**Étapes :**

1. *(Optionnel)* Cliquer sur la ligne du produit dans le tableau
2. Cliquer sur le bouton **`↓ Sortie stock`**
3. Dans le dialogue :
   - **Produit** : choisir dans la liste déroulante
   - **Quantité** : saisir le nombre d'unités vendues
   - **Note** : commentaire optionnel (ex : `Vente client`)
4. Cliquer sur **`✓ Valider`**

**Résultat :** La quantité diminue. Si elle passe sous le seuil, la ligne devient rouge.

> ⚠️ Si la quantité demandée dépasse le stock disponible, l'opération est **refusée** avec un message d'erreur explicite.

---

### 5. Comprendre les alertes de rupture

Une alerte se déclenche automatiquement quand :

```
quantité en stock ≤ seuil minimum
```

**Exemple :**

- Produit `CRAY-002` · Qté : `8` · Seuil : `20` → ⚠️ **ALERTE**
- Produit `CRAY-001` · Qté : `150` · Seuil : `20` → ✅ **OK**

Le compteur d'alertes dans la **barre de statut** (en bas) affiche en permanence le nombre de produits en rupture.

**Action recommandée :** Faire une **entrée de stock** pour le produit concerné.

---

### 6. Rafraîchir l'affichage

Cliquer sur le bouton **`⟳ Rafraîchir`** pour recharger le tableau depuis le fichier de données.

> Le tableau se rafraîchit automatiquement après chaque opération (ajout, entrée, sortie).

---

### 7. Quitter l'application

Cliquer sur la **croix** de la fenêtre ou fermer l'application.

Une boîte de confirmation apparaît. Toutes les données sont **déjà sauvegardées** en temps réel — aucune perte possible.

---

## 💾 Sauvegarde des données

Les données sont sauvegardées automatiquement dans :

```
alqalam/data/stock.json
```

Ce fichier est créé au premier lancement. Il est mis à jour **immédiatement** après chaque opération. Vous pouvez l'ouvrir avec un éditeur de texte pour consultation.

**Exemple de contenu :**

```json
[
  {
    "ref": "CRAY-001",
    "nom": "Crayon HB",
    "categorie": "Écriture",
    "prix_achat": 0.15,
    "prix_vente": 0.50,
    "qte": 150,
    "seuil_min": 20
  },
  ...
]
```

---

## 📦 Produits de démonstration

Au premier lancement, 10 produits sont insérés automatiquement :

| Référence | Nom            | Catégorie | Qté | Seuil | Statut    |
| --------- | -------------- | --------- | --- | ----- | --------- |
| CRAY-001  | Crayon HB      | Écriture  | 150 | 20    | ✅ OK      |
| CRAY-002  | Crayon 2B      | Écriture  | 8   | 20    | ⚠️ Alerte |
| STYL-001  | Stylo Bleu     | Écriture  | 200 | 30    | ✅ OK      |
| STYL-002  | Stylo Rouge    | Écriture  | 4   | 30    | ⚠️ Alerte |
| GOM-001   | Gomme Blanche  | Effaçage  | 60  | 10    | ✅ OK      |
| PAP-A4    | Rame Papier A4 | Papier    | 300 | 50    | ✅ OK      |
| PAP-A3    | Rame Papier A3 | Papier    | 6   | 10    | ⚠️ Alerte |
| CIS-001   | Ciseaux 17cm   | Coupe     | 25  | 5     | ✅ OK      |
| REG-001   | Règle 30cm     | Mesure    | 40  | 10    | ✅ OK      |
| CAR-001   | Carnet A5      | Papier    | 3   | 10    | ⚠️ Alerte |

---

## ⚙️ Prérequis techniques

| Élément       | Requis                                       |
| ------------- | -------------------------------------------- |
| Python        | 3.11 ou supérieur                            |
| customtkinter | 5.x (installé automatiquement par le `.bat`) |
| Système       | Windows 10 / 11                              |

**Installation manuelle si nécessaire :**

```bash
py -3 -m pip install customtkinter
```

---

## 🗂️ Structure du projet

```
alqalam/
├── Lancer_AlQalam.bat       ← double-clic pour démarrer
├── README.md                ← ce guide
├── main.py                  ← point d'entrée Python
├── config.py                ← paramètres de l'application
│
├── models/                  ← objets métier
│   ├── produit.py           ← classe Produit
│   ├── categorie.py         ← classe Categorie
│   └── mouvement.py         ← classe Mouvement (entrée/sortie)
│
├── services/                ← logique métier
│   └── stock_service.py     ← gestion du stock + sauvegarde JSON
│
├── ui/                      ← interface graphique
│   ├── app.py               ← fenêtre principale
│   └── frames/
│       ├── stock_frame.py   ← tableau des produits
│       └── dialogs.py       ← formulaires (ajout, entrée, sortie)
│
└── data/
    └── stock.json           ← données persistées (créé automatiquement)
```

---

## 🔮 Versions futures

Ce logiciel évoluera en 11 versions progressives :

| Version  | Nouveauté                                         |
| -------- | ------------------------------------------------- |
| **V1** ✅ | Interface de base, tableau de stock, JSON         |
| V2       | Tri des colonnes, fiche détail d'un produit       |
| V3       | Tableau de bord, statistiques, recherche          |
| V4       | Surveillance des alertes en arrière-plan          |
| V5       | Journal des opérations, validation renforcée      |
| V6       | Architecture professionnelle (Singleton)          |
| V7       | Validation des saisies par expressions régulières |
| V8       | Import / Export CSV (catalogue fournisseur)       |
| V9       | Rapports Excel professionnels colorés             |
| V10      | Base de données SQLite, historique complet        |
| V11      | Suite de tests automatisés (couverture 80%)       |

---

*Al Qalam Stock Manager — Formation Python Partie II · Bechir Bejaoui*
