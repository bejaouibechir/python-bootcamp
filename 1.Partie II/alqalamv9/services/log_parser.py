# [V7 - Regex] LogParser — convertit le journal en texte structuré,
# puis l'analyse avec des expressions régulières.
#
# FLUX :
#   1. JournalService.get_entrees() → liste d'EntreeJournal
#   2. LogParser.formater_journal()  → texte multiligne (log brut)
#   3. LogParser.analyser()          → dict de statistiques extraites par regex
#
# Ce module illustre les regex en contexte réel :
#   - re.findall()    → toutes les occurrences (compter les refs, les opérations)
#   - re.finditer()   → itérer avec groupes nommés (parsing ligne par ligne)
#   - re.search()     → première occurrence (recherche rapide)
#   - re.MULTILINE    → ^ et $ par ligne

import re
from dataclasses import dataclass
from collections import Counter
from typing import Optional

from validators.regex_validators import REGEX


# ── Format d'une ligne de log ──────────────────────────────────────────────────
# [2025-03-09 10:42:01] [entree   ] ✅ CRAY-001 | Entrée stock   | +50 unités
# [2025-03-09 10:43:15] [sortie   ] ✅ STYL-001 | Sortie stock   | -5 unités
# [2025-03-09 10:44:00] [ajout    ] ✅ NEW-001  | Nouveau produit| ref=NEW-001
# [2025-03-09 10:45:00] [sortie   ] ❌ REG-001  | Sortie stock   | stock insuffisant

LOG_TEMPLATE = "[{date} {heure}] [{operation:<9}] {icone} {ref:<10} | {label:<16} | {details}"


@dataclass
class StatutLog:
    """Résultat d'analyse d'un journal par regex."""
    nb_total        : int
    nb_erreurs      : int
    nb_succes       : int
    par_operation   : Counter          # {"entree": 5, "sortie": 3, ...}
    refs_actives    : list[str]        # références les plus mouvementées
    lignes_erreur   : list[str]        # lignes de log où ❌ apparaît
    texte_brut      : str              # le journal complet formaté


class LogParser:
    """
    Analyse le journal d'opérations du StockService avec des regex.

    Usage :
        parser = LogParser(journal_service)
        statut = parser.analyser()
        resultats = parser.rechercher("CRAY")
    """

    def __init__(self, journal_service):
        self._journal = journal_service

    # ── Étape 1 : Formatage en texte structuré ─────────────────────────────

    def formater_journal(self) -> str:
        """
        Convertit les EntreeJournal en texte brut multiligne.

        Chaque ligne suit le format LOG_TEMPLATE — ce texte sera ensuite
        analysé par les méthodes regex ci-dessous.
        """
        lignes = []
        for e in self._journal.get_entrees():
            ligne = LOG_TEMPLATE.format(
                date      = e.date_formatee().replace("/", "-")[:10],
                heure     = e.heure_formatee(),
                operation = e.operation,
                icone     = "✅" if e.succes else "❌",
                ref       = e.ref or "-",
                label     = e.label_operation(),
                details   = (e.details or "-") + (f" | ERR: {e.erreur}" if e.erreur else ""),
            )
            lignes.append(ligne)
        return "\n".join(lignes)

    # ── Étape 2 : Analyse regex ────────────────────────────────────────────

    def analyser(self) -> StatutLog:
        """
        Analyse complète du journal.

        Utilise :
        - re.findall(r"✅", texte) pour compter les succès
        - re.findall(r"❌", texte) pour compter les erreurs
        - re.findall("^.*erreur.*$", texte, re.MULTILINE) pour lignes d'erreur
        - REGEX["ref_dans_texte"].findall() pour trouver les refs actives
        - Counter sur les opérations extraites par regex
        """
        texte = self.formater_journal()
        if not texte.strip():
            return StatutLog(0, 0, 0, Counter(), [], [], "")

        # Compter les succès et erreurs avec les icônes (re.findall)
        nb_succes  = len(re.findall(r"✅", texte))
        nb_erreurs = len(re.findall(r"❌", texte))
        nb_total   = nb_succes + nb_erreurs

        # Extraire les lignes d'erreur (contenant ❌) — re.MULTILINE + re.findall
        # ^ et $ ancrent sur chaque ligne grâce à re.MULTILINE
        lignes_erreur = re.findall(r"^.*❌.*$", texte, re.MULTILINE | re.UNICODE)

        # Compter les opérations — groupe nommé "operation" via re.finditer
        # Pattern : cherche [entree  ] ou [sortie  ] dans chaque ligne
        pattern_op = re.compile(r"\[(?P<op>[a-z]+)\s*\]", re.IGNORECASE)
        operations = [m.group("op") for m in pattern_op.finditer(texte)]
        par_operation = Counter(operations)

        # Trouver les références les plus présentes — REGEX["ref_dans_texte"]
        toutes_refs   = REGEX["ref_dans_texte"].findall(texte)
        compteur_refs = Counter(toutes_refs)
        # Top 5 références par fréquence de mouvement
        refs_actives  = [ref for ref, _ in compteur_refs.most_common(5)]

        return StatutLog(
            nb_total      = nb_total,
            nb_erreurs    = nb_erreurs,
            nb_succes     = nb_succes,
            par_operation = par_operation,
            refs_actives  = refs_actives,
            lignes_erreur = lignes_erreur,
            texte_brut    = texte,
        )

    # ── Recherche interactive ──────────────────────────────────────────────

    def rechercher(self, motif: str, ignorer_casse: bool = True) -> list[str]:
        """
        Recherche les lignes du journal correspondant au motif (regex).

        re.MULTILINE + re.findall → retourne toutes les lignes correspondantes.
        Si le motif est invalide (regex mal formée), retourne une liste vide.

        Utilisé dans l'onglet Analyseur pour filtrer le journal en temps réel.
        """
        texte = self.formater_journal()
        if not texte.strip() or not motif.strip():
            return texte.splitlines()

        flags = re.MULTILINE | re.UNICODE
        if ignorer_casse:
            flags |= re.IGNORECASE

        try:
            # Construit un pattern qui trouve les lignes contenant le motif
            pattern = re.compile(rf"^.*{motif}.*$", flags)
            return pattern.findall(texte)
        except re.error:
            # Motif regex invalide → retourne toutes les lignes sans filtrage
            return texte.splitlines()

    def extraire_par_operation(self, type_op: str) -> list[str]:
        """
        Filtre les lignes du journal pour un type d'opération donné.

        Utilise re.findall avec re.MULTILINE — cherche les lignes contenant
        le type d'opération entre crochets.
        """
        texte = self.formater_journal()
        if not texte.strip():
            return []
        # Cherche les lignes contenant [entree ] ou [sortie ] etc.
        pattern = re.compile(
            rf"^\[.*\]\s\[{type_op}\s*\].*$",
            re.MULTILINE | re.IGNORECASE | re.UNICODE,
        )
        return pattern.findall(texte)

    def extraire_par_ref(self, ref: str) -> list[str]:
        """
        Filtre les lignes du journal pour une référence produit donnée.

        Utilise re.findall avec re.MULTILINE.
        """
        texte = self.formater_journal()
        if not texte.strip():
            return []
        # ref est cherché comme mot délimité (word boundary)
        pattern = re.compile(
            rf"^.*\b{re.escape(ref)}\b.*$",
            re.MULTILINE | re.IGNORECASE | re.UNICODE,
        )
        return pattern.findall(texte)
