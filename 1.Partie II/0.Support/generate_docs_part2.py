#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur de documentation style Doxygen — Python Avancé Partie 2
Reproduit le style visuel de Doxygen 1.10+ (doxygen.nl)
"""

import os
import re
import json
import shutil
import markdown
from pathlib import Path

# ─── Configuration ───────────────────────────────────────────────────────────

SOURCE_DIR = Path(__file__).parent
OUTPUT_DIR = SOURCE_DIR / "docs_output_part2"
PAGES_DIR  = OUTPUT_DIR / "pages"

COURSE_TITLE = "Python Avancé — Partie 2 : POO, Fichiers &amp; Tests"

# Fichiers à ignorer (vides ou doublons)
IGNORE_FILES = {
    "9. Milestone 5 Traçabilité et sécurisation des opérations.md",  # 0 Ko
    "17. Milestone 9 Rapport stock Excel coloré & import bon de commande.md",  # doublon
}

# ─── Définition des pages dans l'ordre numérique ────────────────────────────

CHAPTERS = [
    {"num": "00", "md": "0.La_POO.md",
     "title": "La POO", "icon": "📘"},
    {"num": "02", "md": "2.Les_Méthodes_Magiques.md",
     "title": "Les Méthodes Magiques", "icon": "📘"},
    {"num": "04", "md": "4.Les_Compréhensions.md",
     "title": "Les Compréhensions", "icon": "📘"},
    {"num": "06", "md": "6.Le_Threading_Coroutine.md",
     "title": "Le Threading & Coroutine", "icon": "📘"},
    {"num": "08", "md": "8.Les_décorateurs_descripteurs.md",
     "title": "Les Décorateurs & Descripteurs", "icon": "📘"},
    {"num": "10", "md": "10.Les_Méta_Classes.md",
     "title": "Les Méta-Classes", "icon": "📘"},
    {"num": "12", "md": "12.Aquisition des données-Texte_Regex.md",
     "title": "Acquisition — Texte & Regex", "icon": "📘"},
    {"num": "14", "md": "14.Aquisition des données-Les_CSV.md",
     "title": "Acquisition — Les CSV", "icon": "📘"},
    {"num": "16", "md": "16.Aquisition des données-Les_Excels.md",
     "title": "Acquisition — Les Excel", "icon": "📘"},
    {"num": "18", "md": "18.Aquisition des données-Les_BD.md",
     "title": "Acquisition — Les Bases de Données", "icon": "📘"},
    {"num": "21", "md": "21.Les tests python.md",
     "title": "Les Tests Python", "icon": "📘"},
]

MILESTONES = [
    {"num": "01", "md": "1.Milestone1  Modélisation OO.md",
     "title": "Milestone 1 — Modélisation OO", "icon": "📋", "badge": 1},
    {"num": "03", "md": "3. Milstone 2 Enrichissement du modèle.md",
     "title": "Milestone 2 — Enrichissement du modèle", "icon": "📋", "badge": 2},
    {"num": "05", "md": "5.Milestone3 Optimisation des filtres et rapports.md",
     "title": "Milestone 3 — Optimisation des filtres et rapports", "icon": "📋", "badge": 3},
    {"num": "07", "md": "7.Milestone 4 Surveillance des ruptures en arrière-plan.md",
     "title": "Milestone 4 — Surveillance des ruptures", "icon": "📋", "badge": 4},
    {"num": "09", "md": "9. Milestone 5 Tracabilite et securisation des operations.md",
     "title": "Milestone 5 — Traçabilité et sécurisation", "icon": "📋", "badge": 5},
    {"num": "11", "md": "11.Mile stone 6  Registre automatique des types.md",
     "title": "Milestone 6 — Registre automatique des types", "icon": "📋", "badge": 6},
    {"num": "13", "md": "13.Milestone 7  Validation des saisies et parsing des logs.md",
     "title": "Milestone 7 — Validation et parsing des logs", "icon": "📋", "badge": 7},
    {"num": "15", "md": "15.Milestone 8 Import catalogue & export comptabilité CSV.md",
     "title": "Milestone 8 — Import catalogue &amp; export CSV", "icon": "📋", "badge": 8},
    {"num": "17", "md": "17.Milestone 9 Rapport stock Excel coloré & import bon de commande (livrable).md",
     "title": "Milestone 9 — Rapport Excel &amp; import bon de commande", "icon": "📋", "badge": 9},
    {"num": "19", "md": "19.Milestone 10 Persistance complète .md",
     "title": "Milestone 10 — Persistance complète", "icon": "📋", "badge": 10},
    {"num": "22", "md": "22.Milestone 11 Suite de tests — couverture 80%.md",
     "title": "Milestone 11 — Suite de tests (couverture 80%)", "icon": "📋", "badge": 11},
]

ALL_PAGES = CHAPTERS + MILESTONES

def slug(page):
    """Génère le nom de fichier HTML depuis le numéro et le type."""
    num = page["num"]
    if page in MILESTONES:
        return f"{num}_milestone{page['badge']}.html"
    titles = {
        "00": "la_poo",
        "02": "les_methodes_magiques",
        "04": "les_comprehensions",
        "06": "le_threading_coroutine",
        "08": "les_decorateurs_descripteurs",
        "10": "les_meta_classes",
        "12": "acquisition_regex",
        "14": "acquisition_csv",
        "16": "acquisition_excel",
        "18": "acquisition_bd",
        "21": "les_tests_python",
    }
    return f"{num}_{titles.get(num, 'page')}.html"

# Attacher les slugs
for p in ALL_PAGES:
    p["slug"] = slug(p)

# ─── CSS ─────────────────────────────────────────────────────────────────────

DOXYGEN_CSS = """\
/* ====================================================
   Doxygen 1.10+ style — Python Avancé Partie 2
   ==================================================== */

:root {
  --sidebar-bg:    #1C2A3A;
  --sidebar-text:  #CBD5E1;
  --sidebar-hover: #2D3F52;
  --sidebar-active:#3B82F6;
  --topbar-bg:     #1C2A3A;
  --topbar-text:   #FFFFFF;
  --content-bg:    #FAFAFA;
  --content-text:  #1A202C;
  --header-bg:     #1C2A3A;
  --header-text:   #FFFFFF;
  --note-bg:       #FEF3C7;
  --note-border:   #F59E0B;
  --note-text:     #92400E;
  --code-bg:       #2B2B2B;
  --code-text:     #F8F8F2;
  --link-color:    #2563EB;
  --separator:     #CBD5E1;
  --table-head:    #1C2A3A;
  --table-alt:     #F1F5F9;
  --badge-bg:      #F59E0B;
  --badge-text:    #1C1917;
  --nav-active-bg: #2563EB;
  --font-main:     'Segoe UI', Arial, sans-serif;
  --font-mono:     'Consolas', 'Courier New', monospace;
  --sidebar-width: 280px;
  --topbar-height: 44px;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: var(--font-main);
  background: var(--content-bg);
  color: var(--content-text);
  font-size: 14px;
  line-height: 1.6;
}

/* ── Top bar ── */
#topbar {
  position: fixed;
  top: 0; left: 0; right: 0;
  height: var(--topbar-height);
  background: var(--topbar-bg);
  color: var(--topbar-text);
  display: flex;
  align-items: center;
  padding: 0 16px;
  z-index: 1000;
  box-shadow: 0 2px 6px rgba(0,0,0,0.4);
}

#topbar .logo {
  font-size: 16px;
  font-weight: 700;
  color: #FFFFFF;
  text-decoration: none;
  margin-right: 32px;
  white-space: nowrap;
}

#topbar nav { display: flex; gap: 2px; flex: 1; }

#topbar nav a {
  color: var(--topbar-text);
  text-decoration: none;
  padding: 6px 14px;
  border-radius: 4px 4px 0 0;
  font-size: 13px;
  border-bottom: 2px solid transparent;
  transition: background 0.2s;
}
#topbar nav a:hover { background: rgba(255,255,255,0.1); }
#topbar nav a.active {
  background: rgba(255,255,255,0.15);
  border-bottom: 2px solid #F59E0B;
  color: #FFF;
}

#search-box {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 6px;
}
#search-input {
  background: rgba(255,255,255,0.12);
  border: 1px solid rgba(255,255,255,0.25);
  border-radius: 4px;
  color: #FFF;
  padding: 4px 10px;
  font-size: 13px;
  width: 200px;
  outline: none;
  transition: border-color 0.2s;
}
#search-input::placeholder { color: rgba(255,255,255,0.5); }
#search-input:focus { border-color: var(--sidebar-active); }

/* ── Layout ── */
#layout {
  display: flex;
  margin-top: var(--topbar-height);
  min-height: calc(100vh - var(--topbar-height));
}

/* ── Sidebar ── */
#sidebar {
  width: var(--sidebar-width);
  min-width: var(--sidebar-width);
  background: var(--sidebar-bg);
  color: var(--sidebar-text);
  padding: 12px 0;
  overflow-y: auto;
  position: fixed;
  top: var(--topbar-height);
  left: 0;
  bottom: 0;
  z-index: 900;
}

.sidebar-group-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #94A3B8;
  cursor: pointer;
  user-select: none;
  transition: color 0.2s;
}
.sidebar-group-header:hover { color: #FFF; }

.sidebar-group-header .toggle-arrow {
  font-size: 10px;
  transition: transform 0.25s;
  display: inline-block;
}
.sidebar-group-header.collapsed .toggle-arrow { transform: rotate(-90deg); }

.sidebar-group ul {
  list-style: none;
  overflow: hidden;
  transition: max-height 0.3s ease;
  max-height: 2000px;
}
.sidebar-group.collapsed ul { max-height: 0; }

.sidebar-group ul li a {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 5px 14px 5px 22px;
  color: var(--sidebar-text);
  text-decoration: none;
  font-size: 13px;
  line-height: 1.4;
  border-left: 3px solid transparent;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}
.sidebar-group ul li a:hover {
  background: var(--sidebar-hover);
  color: #FFF;
}
.sidebar-group ul li a.current {
  background: rgba(59,130,246,0.2);
  border-left-color: var(--sidebar-active);
  color: #93C5FD;
  font-weight: 600;
}
.sidebar-group ul li a .page-icon { flex-shrink: 0; }

/* ── Main content ── */
#main-content {
  flex: 1;
  margin-left: var(--sidebar-width);
  padding: 0;
  min-width: 0;
}

/* ── Breadcrumb ── */
#breadcrumb {
  background: #F1F5F9;
  border-bottom: 1px solid var(--separator);
  padding: 6px 24px;
  font-size: 12px;
  color: #64748B;
}
#breadcrumb a { color: var(--link-color); text-decoration: none; }
#breadcrumb a:hover { text-decoration: underline; }
#breadcrumb span { margin: 0 6px; }

/* ── Page header band ── */
.page-header-band {
  background: var(--header-bg);
  color: var(--header-text);
  padding: 20px 28px 18px;
  border-bottom: 3px solid var(--badge-bg);
}
.page-header-band h1 {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.01em;
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.milestone-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: var(--badge-bg);
  color: var(--badge-text);
  font-size: 12px;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 12px;
  vertical-align: middle;
}

/* ── Content body ── */
.content-body {
  padding: 24px 32px 40px;
  max-width: 1000px;
}

/* ── Typography ── */
.content-body h1 { font-size: 20px; color: var(--header-bg); border-bottom: 2px solid var(--separator); padding-bottom: 6px; margin: 28px 0 14px; }
.content-body h2 { font-size: 17px; color: var(--header-bg); border-bottom: 1px solid #E2E8F0; padding-bottom: 4px; margin: 24px 0 12px; }
.content-body h3 { font-size: 15px; color: #1E3A5F; margin: 18px 0 8px; }
.content-body h4 { font-size: 14px; color: #1E3A5F; margin: 14px 0 6px; }
.content-body p  { margin: 8px 0; }
.content-body a  { color: var(--link-color); }
.content-body a:hover { text-decoration: underline; }
.content-body strong { color: #1A202C; font-weight: 700; }
.content-body ul, .content-body ol { margin: 8px 0 8px 24px; }
.content-body li { margin: 3px 0; }
.content-body hr { border: none; border-top: 2px solid var(--header-bg); opacity: 0.15; margin: 20px 0; }

/* ── Code blocks ── */
.content-body pre {
  background: var(--code-bg);
  color: var(--code-text);
  border-radius: 6px;
  margin: 14px 0;
  overflow-x: auto;
  position: relative;
  font-size: 13px;
}
.content-body pre code {
  display: block;
  padding: 16px;
  font-family: var(--font-mono);
  counter-reset: line;
  background: transparent;
}
.content-body :not(pre) > code {
  background: #E2E8F0;
  color: #C0392B;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: var(--font-mono);
  font-size: 13px;
}

/* Line numbers via CSS counter */
.content-body pre.line-numbers code .code-line {
  display: block;
  counter-increment: line;
}
.content-body pre.line-numbers code .code-line::before {
  content: counter(line);
  display: inline-block;
  width: 36px;
  color: #6B7280;
  text-align: right;
  margin-right: 16px;
  border-right: 1px solid #4B5563;
  padding-right: 8px;
  user-select: none;
}

/* ── Note / blockquote boxes ── */
.content-body blockquote {
  background: var(--note-bg);
  border-left: 4px solid var(--note-border);
  color: var(--note-text);
  padding: 12px 16px;
  margin: 14px 0;
  border-radius: 0 6px 6px 0;
  font-size: 13.5px;
}
.content-body blockquote::before {
  content: "📝 Note";
  display: block;
  font-weight: 700;
  margin-bottom: 4px;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #B45309;
}
.content-body blockquote p { margin: 0; }

/* ── Tables ── */
.content-body table {
  width: 100%;
  border-collapse: collapse;
  margin: 14px 0;
  font-size: 13px;
}
.content-body th {
  background: var(--table-head);
  color: #FFFFFF;
  padding: 8px 12px;
  text-align: left;
  font-weight: 600;
}
.content-body td {
  padding: 7px 12px;
  border-bottom: 1px solid #E2E8F0;
}
.content-body tr:nth-child(even) td { background: var(--table-alt); }
.content-body tr:hover td { background: #EBF3FF; }

/* ── Index summary table ── */
.summary-table {
  width: 100%;
  border-collapse: collapse;
  margin: 20px 0;
  font-size: 13.5px;
}
.summary-table th {
  background: var(--table-head);
  color: #FFF;
  padding: 10px 14px;
  text-align: left;
}
.summary-table td { padding: 8px 14px; border-bottom: 1px solid #E2E8F0; }
.summary-table tr:nth-child(even) td { background: var(--table-alt); }
.summary-table tr:hover td { background: #EBF3FF; }
.summary-table a { color: var(--link-color); text-decoration: none; }
.summary-table a:hover { text-decoration: underline; }

/* ── Prev/Next navigation ── */
.page-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 32px;
  border-top: 1px solid var(--separator);
  margin-top: 20px;
  background: #F8FAFC;
}
.page-nav a {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--link-color);
  text-decoration: none;
  font-size: 13px;
  padding: 6px 14px;
  border: 1px solid var(--separator);
  border-radius: 4px;
  background: #FFF;
  transition: background 0.2s, border-color 0.2s;
}
.page-nav a:hover { background: #EBF3FF; border-color: var(--link-color); }
.page-nav .placeholder { flex: 1; }

/* ── Footer ── */
footer {
  background: var(--header-bg);
  color: #94A3B8;
  text-align: center;
  padding: 12px 16px;
  font-size: 12px;
  margin-top: 0;
}
footer a { color: #93C5FD; }

/* ── Search results dropdown ── */
#search-results {
  position: fixed;
  top: var(--topbar-height);
  right: 16px;
  width: 380px;
  max-height: 420px;
  overflow-y: auto;
  background: #FFF;
  border: 1px solid var(--separator);
  border-radius: 0 0 6px 6px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.15);
  z-index: 2000;
  display: none;
}
#search-results .sr-item {
  display: block;
  padding: 10px 14px;
  border-bottom: 1px solid #F1F5F9;
  text-decoration: none;
  color: var(--content-text);
  transition: background 0.15s;
}
#search-results .sr-item:hover { background: #EBF3FF; }
#search-results .sr-title { font-weight: 600; font-size: 13px; color: var(--link-color); }
#search-results .sr-snippet { font-size: 12px; color: #64748B; margin-top: 2px; }

/* ── Responsive ── */
@media (max-width: 768px) {
  #sidebar { transform: translateX(-100%); transition: transform 0.3s; }
  #sidebar.open { transform: translateX(0); }
  #main-content { margin-left: 0; }
  .content-body { padding: 16px; }
}
"""

# ─── JavaScript ──────────────────────────────────────────────────────────────

DOXYGEN_JS = """\
/* Doxygen-style JS — sidebar toggle + search */

document.addEventListener('DOMContentLoaded', function () {

  // ── Sidebar group toggle ──────────────────────────────────────────────
  document.querySelectorAll('.sidebar-group-header').forEach(function (hdr) {
    hdr.addEventListener('click', function () {
      var group = hdr.closest('.sidebar-group');
      group.classList.toggle('collapsed');
      hdr.classList.toggle('collapsed');
    });
  });

  // ── Search ────────────────────────────────────────────────────────────
  var searchInput = document.getElementById('search-input');
  var searchResults = document.getElementById('search-results');
  var searchIndex = null;

  // Determine path prefix to reach root (index.html is at root, pages/ are one level deep)
  var pathPrefix = window.location.pathname.includes('/pages/') ? '../' : '';

  function loadIndex(cb) {
    if (searchIndex) { cb(); return; }
    fetch(pathPrefix + 'search_index.json')
      .then(function (r) { return r.json(); })
      .then(function (data) { searchIndex = data; cb(); })
      .catch(function () { searchIndex = []; cb(); });
  }

  function doSearch(query) {
    if (!query || query.length < 2) { searchResults.style.display = 'none'; return; }
    loadIndex(function () {
      var q = query.toLowerCase();
      var hits = searchIndex.filter(function (item) {
        return item.title.toLowerCase().includes(q) || item.content.toLowerCase().includes(q);
      }).slice(0, 12);

      if (!hits.length) { searchResults.style.display = 'none'; return; }

      searchResults.innerHTML = hits.map(function (item) {
        var snippet = '';
        var idx = item.content.toLowerCase().indexOf(q);
        if (idx >= 0) {
          snippet = item.content.substring(Math.max(0, idx - 40), idx + 80).trim();
          snippet = snippet.replace(/</g, '&lt;').replace(/>/g, '&gt;');
        }
        return '<a class="sr-item" href="' + pathPrefix + 'pages/' + item.slug + '">' +
               '<div class="sr-title">' + item.title + '</div>' +
               (snippet ? '<div class="sr-snippet">…' + snippet + '…</div>' : '') +
               '</a>';
      }).join('');
      searchResults.style.display = 'block';
    });
  }

  if (searchInput) {
    searchInput.addEventListener('input', function () { doSearch(this.value.trim()); });
    searchInput.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { searchResults.style.display = 'none'; searchInput.value = ''; }
    });
  }

  document.addEventListener('click', function (e) {
    if (!searchResults.contains(e.target) && e.target !== searchInput) {
      searchResults.style.display = 'none';
    }
  });

  // ── Highlight.js post-processing: add line numbers ────────────────────
  document.querySelectorAll('pre code').forEach(function (block) {
    // hljs already ran via onload; add .code-line spans for CSS counters
    var lines = block.innerHTML.split('\\n');
    // Remove trailing empty line
    if (lines[lines.length - 1] === '') lines.pop();
    block.innerHTML = lines.map(function (l) {
      return '<span class="code-line">' + l + '</span>';
    }).join('\\n');
    if (block.parentElement) block.parentElement.classList.add('line-numbers');
  });
});
"""

# ─── HTML template helpers ────────────────────────────────────────────────────

def build_sidebar(current_slug=None, root_prefix=""):
    """Génère le HTML de la sidebar avec les groupes chapitres et milestones."""

    def nav_item(page):
        href = root_prefix + "pages/" + page["slug"]
        cls = ' class="current"' if page["slug"] == current_slug else ''
        icon = page["icon"]
        return f'        <li><a href="{href}"{cls}><span class="page-icon">{icon}</span>{page["title"]}</a></li>'

    chapters_html = "\n".join(nav_item(p) for p in CHAPTERS)
    milestones_html = "\n".join(nav_item(p) for p in MILESTONES)

    # Milestones collapsed by default
    ms_collapsed = "" if current_slug and any(p["slug"] == current_slug for p in MILESTONES) else " collapsed"
    ms_hdr_cls = "sidebar-group-header" + (" collapsed" if ms_collapsed else "")

    return f"""<aside id="sidebar">
  <div class="sidebar-group">
    <div class="sidebar-group-header" id="grp-chapters">
      <span class="toggle-arrow">▼</span> 📘 Chapitres
    </div>
    <ul>
{chapters_html}
    </ul>
  </div>
  <div class="sidebar-group{ms_collapsed}">
    <div class="{ms_hdr_cls}" id="grp-milestones">
      <span class="toggle-arrow">▼</span> 📋 Milestones
    </div>
    <ul>
{milestones_html}
    </ul>
  </div>
</aside>"""


def build_topbar(active_tab="main", root_prefix=""):
    tabs = [
        ("main", root_prefix + "index.html", "Main Page"),
        ("chapters", "#", "Related Pages"),
        ("files", "#", "Files"),
    ]
    nav_html = "\n    ".join(
        f'<a href="{href}" class="{"active" if key == active_tab else ""}">{label}</a>'
        for key, href, label in tabs
    )
    return f"""<header id="topbar">
  <a class="logo" href="{root_prefix}index.html">🐍 Python Avancé II</a>
  <nav>
    {nav_html}
  </nav>
  <div id="search-box">
    <input id="search-input" type="search" placeholder="🔍 Rechercher…" autocomplete="off">
  </div>
</header>
<div id="search-results"></div>"""


def build_footer(page_title=""):
    return f"""<footer>
  {page_title + " — " if page_title else ""}Generated by <strong>Doxygen (Claude Edition)</strong> — Python Avancé Partie 2
</footer>"""


def hljs_head():
    return """\
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css">
  <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/python.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/sql.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/json.min.js"></script>
  <script>hljs.highlightAll();</script>"""


def full_page(title, body_inner, root_prefix="", current_slug=None,
              active_tab="main", breadcrumb_html=""):
    sidebar = build_sidebar(current_slug=current_slug, root_prefix=root_prefix)
    topbar  = build_topbar(active_tab=active_tab, root_prefix=root_prefix)
    footer  = build_footer(title)
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} — Python Avancé II</title>
  <link rel="stylesheet" href="{root_prefix}doxygen.css">
  {hljs_head()}
</head>
<body>
{topbar}
<div id="layout">
{sidebar}
  <div id="main-content">
    {('<div id="breadcrumb">' + breadcrumb_html + '</div>') if breadcrumb_html else ''}
{body_inner}
    {build_footer(title)}
  </div>
</div>
<script src="{root_prefix}doxygen.js"></script>
</body>
</html>"""

# ─── Markdown → HTML conversion ──────────────────────────────────────────────

MD_EXTENSIONS = ["tables", "fenced_code", "toc", "attr_list", "nl2br"]


def md_to_html(md_text):
    """Convertit le Markdown en HTML avec les extensions Doxygen."""
    md = markdown.Markdown(extensions=MD_EXTENSIONS,
                           extension_configs={"toc": {"permalink": True}})
    return md.convert(md_text)


def add_cross_references(html, page):
    """Ajoute des liens croisés entre chapitres et milestones."""
    for ms in MILESTONES:
        n = ms["badge"]
        pattern = re.compile(
            r'(?<![/"\'])(?<!\bMilestone\s)(?<!\bhref=")(?<![a-z])(Milestone\s*' + str(n) + r')(?![^<]*</a>)',
            re.IGNORECASE
        )
        href = ms["slug"]
        html = pattern.sub(
            lambda m: f'<a href="{href}">{m.group(0)}</a>',
            html
        )
    return html


def read_md(md_file):
    """Lit un fichier Markdown en UTF-8."""
    path = SOURCE_DIR / md_file
    try:
        with open(path, encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"  ⚠️  Impossible de lire {md_file}: {e}")
        return ""

# ─── Génération des pages ────────────────────────────────────────────────────

def generate_index():
    """Génère index.html — la page d'accueil."""

    chapter_rows = ""
    for i, ch in enumerate(CHAPTERS):
        ms = MILESTONES[i] if i < len(MILESTONES) else None
        ms_link = f'<a href="pages/{ms["slug"]}">{ms["title"]}</a>' if ms else "—"
        chapter_rows += f"""
    <tr>
      <td><a href="pages/{ch['slug']}">{ch['title']}</a></td>
      <td>{ms_link}</td>
    </tr>"""

    body = f"""    <div class="page-header-band">
      <h1>📚 {COURSE_TITLE}</h1>
    </div>
    <div class="content-body">
      <h2>Bienvenue dans la documentation</h2>
      <p>Cette documentation couvre la <strong>Partie 2</strong> du cours Python Avancé,
      organisée en 11 chapitres théoriques et 11 milestones pratiques appliqués
      au projet <em>Al Qalam Stock Manager</em> (papeterie tunisienne).</p>
      <h2>Thèmes abordés</h2>
      <ul>
        <li>🏛️ Programmation Orientée Objet (POO) — classes, héritage, méthodes magiques</li>
        <li>⚡ Compréhensions, décorateurs, descripteurs, métaclasses</li>
        <li>🧵 Threading, coroutines, programmation concurrente</li>
        <li>📂 Acquisition de données — Regex, CSV, Excel, Bases de données</li>
        <li>🧪 Tests Python — pytest, couverture, fixtures</li>
      </ul>
      <h2>Plan du cours</h2>
      <table class="summary-table">
        <thead>
          <tr>
            <th>📘 Chapitre</th>
            <th>📋 Milestone associé</th>
          </tr>
        </thead>
        <tbody>{chapter_rows}
        </tbody>
      </table>
    </div>"""

    html = full_page(
        title="Main Page",
        body_inner=body,
        root_prefix="",
        current_slug=None,
        active_tab="main",
        breadcrumb_html='<a href="index.html">Main Page</a>'
    )

    with open(OUTPUT_DIR / "index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("  ✅ index.html")


def generate_page(page, prev_page=None, next_page=None):
    """Génère une page HTML pour un chapitre ou milestone."""
    md_text = read_md(page["md"])
    if not md_text:
        print(f"  ⚠️  {page['md']} — vide ou illisible, page ignorée")
        return

    content_html = md_to_html(md_text)
    content_html = add_cross_references(content_html, page)

    # Badge pour milestones
    badge_html = ""
    if "badge" in page:
        badge_html = f'<span class="milestone-badge">🏁 Milestone {page["badge"]}</span>'

    # Groupe (chapitres ou milestones)
    is_milestone = "badge" in page
    group_label = "Milestones" if is_milestone else "Chapitres"
    group_href  = "#grp-milestones" if is_milestone else "#grp-chapters"

    # Breadcrumb
    breadcrumb = (
        f'<a href="../index.html">Main Page</a>'
        f'<span>»</span>'
        f'<a href="../index.html#{group_href}">{group_label}</a>'
        f'<span>»</span>{page["title"]}'
    )

    # Prev / Next navigation
    prev_btn = ""
    next_btn = ""
    if prev_page:
        prev_btn = f'<a href="{prev_page["slug"]}">◀ {prev_page["title"]}</a>'
    if next_page:
        next_btn = f'<a href="{next_page["slug"]}">{next_page["title"]} ▶</a>'

    nav_html = f"""    <div class="page-nav">
      {prev_btn if prev_btn else '<span class="placeholder"></span>'}
      {next_btn if next_btn else '<span class="placeholder"></span>'}
    </div>"""

    body = f"""    <div class="page-header-band">
      <h1>{badge_html}{page['title']}</h1>
    </div>
    <div class="content-body">
{content_html}
    </div>
{nav_html}"""

    html = full_page(
        title=page["title"],
        body_inner=body,
        root_prefix="../",
        current_slug=page["slug"],
        active_tab="chapters" if not is_milestone else "main",
        breadcrumb_html=breadcrumb
    )

    out_path = PAGES_DIR / page["slug"]
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  ✅ pages/{page['slug']}")


def generate_search_index():
    """Génère search_index.json avec titre + extrait du contenu de chaque page."""
    index = []
    for page in ALL_PAGES:
        md_text = read_md(page["md"])
        if not md_text:
            continue
        # Retire le markdown pour le texte brut (simplifié)
        clean = re.sub(r'[#*`\[\]()>]', '', md_text)
        clean = re.sub(r'\s+', ' ', clean).strip()
        index.append({
            "slug": page["slug"],
            "title": page["title"],
            "content": clean[:2000],
        })

    with open(OUTPUT_DIR / "search_index.json", "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    print("  ✅ search_index.json")

# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    print("\n🚀 Génération de la documentation style Doxygen — Partie 2\n")

    # Créer les dossiers de sortie
    OUTPUT_DIR.mkdir(exist_ok=True)
    PAGES_DIR.mkdir(exist_ok=True)
    print(f"📁 Dossier de sortie : {OUTPUT_DIR}\n")

    # Écrire les fichiers statiques
    print("📝 Fichiers statiques…")
    with open(OUTPUT_DIR / "doxygen.css", "w", encoding="utf-8") as f:
        f.write(DOXYGEN_CSS)
    print("  ✅ doxygen.css")

    with open(OUTPUT_DIR / "doxygen.js", "w", encoding="utf-8") as f:
        f.write(DOXYGEN_JS)
    print("  ✅ doxygen.js")

    # Index
    print("\n📄 Page principale…")
    generate_index()

    # Chapitres
    print(f"\n📘 Chapitres ({len(CHAPTERS)})…")
    for i, ch in enumerate(CHAPTERS):
        prev_p = CHAPTERS[i - 1] if i > 0 else None
        next_p = CHAPTERS[i + 1] if i < len(CHAPTERS) - 1 else None
        generate_page(ch, prev_page=prev_p, next_page=next_p)

    # Milestones
    print(f"\n📋 Milestones ({len(MILESTONES)})…")
    for i, ms in enumerate(MILESTONES):
        prev_p = MILESTONES[i - 1] if i > 0 else None
        next_p = MILESTONES[i + 1] if i < len(MILESTONES) - 1 else None
        generate_page(ms, prev_page=prev_p, next_page=next_p)

    # Index de recherche
    print("\n🔍 Index de recherche…")
    generate_search_index()

    print(f"\n✨ Documentation générée avec succès dans :")
    print(f"   {OUTPUT_DIR / 'index.html'}\n")


if __name__ == "__main__":
    main()
