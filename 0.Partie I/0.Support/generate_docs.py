"""
Générateur de documentation style Doxygen authentique.
Transforme les fichiers Markdown du cours Python en site HTML professionnel.
Auteur: Claude Code — style fidèle à doxygen.nl
"""

import os
import re
import sys
import json
import shutil
import markdown
from pathlib import Path

# Forcer UTF-8 pour les print() sur Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
from datetime import datetime

# ─── Configuration ────────────────────────────────────────────────────────────

BASE_DIR   = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "docs_output"
PAGES_DIR  = OUTPUT_DIR / "pages"

# Ordre et métadonnées des fichiers source
FILES = [
    {"src": "0.Chapitre introductif.md",            "slug": "00_chapitre_introductif",         "title": "Introduction à Python",               "milestone": False},
    {"src": "1.Operations mathematiques de base.md", "slug": "01_operations_mathematiques",      "title": "Opérations mathématiques de base",    "milestone": False},
    {"src": "2.Projet mile stone 1.md",              "slug": "02_milestone_1",                   "title": "Projet Milestone 1",                  "milestone": True},
    {"src": "3.Les_Types.md",                        "slug": "03_les_types",                     "title": "Les Types",                           "milestone": False},
    {"src": "4.Les_Types_Chaines.md",                "slug": "04_les_types_chaines",             "title": "Les Types — Chaînes",                 "milestone": False},
    {"src": "5.Les_Types_Collections.md",            "slug": "05_les_types_collections",         "title": "Les Types — Collections",             "milestone": False},
    {"src": "6.Projet mile stone 2.md",              "slug": "06_milestone_2",                   "title": "Projet Milestone 2",                  "milestone": True},
    {"src": "7.Les_Variables_Constantes_Litteral.md","slug": "07_variables_constantes",          "title": "Variables, Constantes & Littéraux",   "milestone": False},
    {"src": "8.Les_dates.md",                        "slug": "08_les_dates",                     "title": "Les Dates",                           "milestone": False},
    {"src": "9.Les_flux_conditionels.md",            "slug": "09_flux_conditionnels",            "title": "Les Flux Conditionnels",              "milestone": False},
    {"src": "10.Projet mile stone 3.md",             "slug": "10_milestone_3",                   "title": "Projet Milestone 3",                  "milestone": True},
    {"src": "11.Les_Flux_Iteratifs.md",              "slug": "11_flux_iteratifs",                "title": "Les Flux Itératifs",                  "milestone": False},
    {"src": "12.Projet mile stone 4.md",             "slug": "12_milestone_4",                   "title": "Projet Milestone 4",                  "milestone": True},
    {"src": "13.Les_Fonctions.md",                   "slug": "13_les_fonctions",                 "title": "Les Fonctions",                       "milestone": False},
    {"src": "14.Projet mile stone 5.md",             "slug": "14_milestone_5",                   "title": "Projet Milestone 5",                  "milestone": True},
    {"src": "15.Les_Erreurs.md",                     "slug": "15_les_erreurs",                   "title": "Les Erreurs & Exceptions",            "milestone": False},
    {"src": "16.Les_Modules_ Pacakages.md",          "slug": "16_modules_packages",              "title": "Les Modules & Packages",              "milestone": False},
    {"src": "17.Projet mile stone 6.md",             "slug": "17_milestone_6",                   "title": "Projet Milestone 6",                  "milestone": True},
]

CHAPTERS   = [f for f in FILES if not f["milestone"]]
MILESTONES = [f for f in FILES if f["milestone"]]

# ─── CSS Doxygen authentique ──────────────────────────────────────────────────

DOXYGEN_CSS = """
/* =====================================================
   Doxygen-style CSS — faithful replica of doxygen.nl
   ===================================================== */

:root {
  --sidebar-bg:       #1C2A3A;
  --sidebar-text:     #C8D0D8;
  --sidebar-active:   #4D9FEC;
  --sidebar-hover:    #2A3D52;
  --sidebar-width:    260px;
  --topbar-bg:        #1C2A3A;
  --topbar-height:    42px;
  --navtab-active:    #4D9FEC;
  --content-bg:       #FAFAFA;
  --content-text:     #2C2C2C;
  --title-band-bg:    #2C3E50;
  --title-band-text:  #FFFFFF;
  --section-color:    #1A3A5C;
  --code-bg:          #2B2B2B;
  --code-text:        #F8F8F2;
  --note-bg:          #FFF8E1;
  --note-border:      #F9A825;
  --note-icon:        #F57F17;
  --table-header-bg:  #E8EDF2;
  --table-border:     #C0C8D0;
  --link-color:       #2A6496;
  --breadcrumb-color: #6C757D;
  --separator:        #D0D8E0;
  --footer-bg:        #F0F4F8;
  --footer-text:      #6C757D;
  --milestone-badge:  #E67E22;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: "Segoe UI", Arial, sans-serif;
  font-size: 14px;
  color: var(--content-text);
  background: var(--content-bg);
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

/* ── Top navigation bar ── */
#top-nav {
  position: fixed;
  top: 0; left: 0; right: 0;
  height: var(--topbar-height);
  background: var(--topbar-bg);
  display: flex;
  align-items: stretch;
  z-index: 200;
  border-bottom: 1px solid #0D1B27;
}

#top-nav .logo {
  display: flex;
  align-items: center;
  padding: 0 16px;
  color: #FFFFFF;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 0.5px;
  min-width: var(--sidebar-width);
  background: #162230;
  border-right: 1px solid #0D1B27;
  text-decoration: none;
  white-space: nowrap;
  overflow: hidden;
}

#top-nav .logo span.sub {
  font-size: 11px;
  font-weight: 400;
  color: #8aacc8;
  margin-left: 8px;
}

#nav-tabs {
  display: flex;
  align-items: stretch;
  flex: 1;
}

#nav-tabs a {
  display: flex;
  align-items: center;
  padding: 0 18px;
  color: #A0B4C8;
  text-decoration: none;
  font-size: 13px;
  border-bottom: 3px solid transparent;
  transition: color 0.2s, border-color 0.2s;
}

#nav-tabs a:hover { color: #FFFFFF; background: rgba(255,255,255,0.05); }
#nav-tabs a.active {
  color: #FFFFFF;
  border-bottom-color: var(--navtab-active);
}

#search-box {
  display: flex;
  align-items: center;
  padding: 0 12px;
  margin-left: auto;
}

#search-box input {
  background: rgba(255,255,255,0.1);
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 4px;
  padding: 5px 10px;
  color: #FFFFFF;
  font-size: 12px;
  width: 200px;
  outline: none;
  transition: background 0.2s;
}

#search-box input::placeholder { color: #7090A8; }
#search-box input:focus { background: rgba(255,255,255,0.18); }

/* ── Layout ── */
#layout {
  display: flex;
  flex: 1;
  padding-top: var(--topbar-height);
}

/* ── Sidebar ── */
#sidebar {
  position: fixed;
  top: var(--topbar-height);
  left: 0;
  bottom: 0;
  width: var(--sidebar-width);
  background: var(--sidebar-bg);
  overflow-y: auto;
  overflow-x: hidden;
  z-index: 100;
  scrollbar-width: thin;
  scrollbar-color: #2A3D52 transparent;
}

#sidebar::-webkit-scrollbar { width: 6px; }
#sidebar::-webkit-scrollbar-track { background: transparent; }
#sidebar::-webkit-scrollbar-thumb { background: #2A3D52; border-radius: 3px; }

.sidebar-group {
  padding: 0;
}

.sidebar-group-title {
  display: flex;
  align-items: center;
  padding: 10px 14px 8px;
  color: #8AACC8;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1.2px;
  cursor: pointer;
  user-select: none;
  border-top: 1px solid rgba(255,255,255,0.05);
  transition: color 0.2s;
}

.sidebar-group-title:hover { color: #C8D0D8; }

.sidebar-group-title .toggle-icon {
  margin-right: 7px;
  font-size: 9px;
  transition: transform 0.2s;
  display: inline-block;
}

.sidebar-group-title.collapsed .toggle-icon { transform: rotate(-90deg); }

.sidebar-group-content { list-style: none; }
.sidebar-group-content.hidden { display: none; }

.sidebar-group-content li a {
  display: flex;
  align-items: center;
  padding: 6px 14px 6px 28px;
  color: var(--sidebar-text);
  text-decoration: none;
  font-size: 12.5px;
  line-height: 1.4;
  border-left: 3px solid transparent;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-group-content li a:hover {
  background: var(--sidebar-hover);
  color: #FFFFFF;
}

.sidebar-group-content li a.active {
  background: rgba(77,159,236,0.15);
  color: var(--sidebar-active);
  border-left-color: var(--sidebar-active);
  font-weight: 500;
}

.badge-milestone {
  font-size: 9px;
  background: var(--milestone-badge);
  color: #fff;
  border-radius: 3px;
  padding: 1px 5px;
  margin-left: 6px;
  flex-shrink: 0;
  font-weight: 600;
  letter-spacing: 0.3px;
}

/* ── Main content area ── */
#content {
  margin-left: var(--sidebar-width);
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - var(--topbar-height));
}

.content-inner {
  flex: 1;
  padding: 24px 40px 40px;
  max-width: 980px;
}

/* ── Breadcrumb ── */
.breadcrumb {
  font-size: 12px;
  color: var(--breadcrumb-color);
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
}

.breadcrumb a { color: var(--link-color); text-decoration: none; }
.breadcrumb a:hover { text-decoration: underline; }
.breadcrumb .sep { color: #B0BEC5; }

/* ── Page title band (Doxygen class/function header) ── */
.page-title-band {
  background: var(--title-band-bg);
  color: var(--title-band-text);
  padding: 14px 20px;
  margin-bottom: 24px;
  border-radius: 3px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-title-band h1 {
  font-size: 20px;
  font-weight: 600;
  letter-spacing: 0.3px;
  border: none;
  margin: 0;
  padding: 0;
  background: none;
  color: #FFFFFF;
}

.page-title-band .milestone-chip {
  background: var(--milestone-badge);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 9px;
  border-radius: 10px;
  letter-spacing: 0.5px;
  white-space: nowrap;
}

/* ── Section headings ── */
.content-inner h1 {
  font-size: 20px;
  color: var(--section-color);
  font-weight: 700;
  margin: 28px 0 12px;
  padding-bottom: 6px;
  border-bottom: 2px solid var(--separator);
}

.content-inner h2 {
  font-size: 17px;
  color: var(--section-color);
  font-weight: 700;
  margin: 24px 0 10px;
  padding-bottom: 4px;
  border-bottom: 1px solid var(--separator);
}

.content-inner h3 {
  font-size: 15px;
  color: #2C4A6E;
  font-weight: 600;
  margin: 18px 0 8px;
}

.content-inner h4 {
  font-size: 14px;
  color: #2C4A6E;
  font-weight: 600;
  margin: 14px 0 6px;
}

/* ── Paragraphs & lists ── */
.content-inner p {
  margin: 8px 0 12px;
  line-height: 1.75;
}

.content-inner ul, .content-inner ol {
  margin: 8px 0 12px 24px;
  line-height: 1.75;
}

.content-inner li { margin-bottom: 4px; }

/* ── Links ── */
.content-inner a {
  color: var(--link-color);
  text-decoration: none;
}
.content-inner a:hover { text-decoration: underline; }

/* ── Inline code ── */
.content-inner code {
  background: #EEF1F5;
  color: #C0392B;
  padding: 1px 5px;
  border-radius: 3px;
  font-family: "Consolas", "Courier New", monospace;
  font-size: 13px;
}

/* ── Code blocks (overrides inline style) ── */
.content-inner pre {
  background: var(--code-bg);
  border-radius: 4px;
  margin: 14px 0;
  padding: 0;
  overflow: hidden;
  border: 1px solid #1A1A1A;
  position: relative;
}

.content-inner pre code {
  display: block;
  background: transparent;
  color: var(--code-text);
  padding: 14px 16px;
  font-size: 13px;
  line-height: 1.6;
  overflow-x: auto;
  white-space: pre;
  border-radius: 0;
}

.code-header {
  background: #1A1A1A;
  padding: 6px 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #333;
}

.code-lang {
  font-size: 11px;
  color: #888;
  font-family: "Consolas", monospace;
  text-transform: lowercase;
  letter-spacing: 0.5px;
}

/* ── Note / blockquote boxes ── */
.content-inner blockquote {
  background: var(--note-bg);
  border-left: 4px solid var(--note-border);
  border-radius: 0 4px 4px 0;
  padding: 10px 16px;
  margin: 14px 0;
  font-size: 13.5px;
  line-height: 1.7;
}

.content-inner blockquote::before {
  content: "📌 Note";
  display: block;
  font-weight: 700;
  color: var(--note-icon);
  font-size: 12px;
  margin-bottom: 6px;
  letter-spacing: 0.5px;
}

.content-inner blockquote p { margin: 0; }
.content-inner blockquote code {
  background: rgba(0,0,0,0.07);
  color: #8B4513;
}

/* ── Tables ── */
.content-inner table {
  border-collapse: collapse;
  width: 100%;
  margin: 14px 0;
  font-size: 13.5px;
}

.content-inner th {
  background: var(--table-header-bg);
  color: var(--section-color);
  font-weight: 700;
  padding: 8px 12px;
  border: 1px solid var(--table-border);
  text-align: left;
}

.content-inner td {
  padding: 7px 12px;
  border: 1px solid var(--table-border);
  vertical-align: top;
  line-height: 1.6;
}

.content-inner tr:nth-child(even) td { background: #F3F6FA; }

/* ── Horizontal rule ── */
.content-inner hr {
  border: none;
  border-top: 1px solid var(--separator);
  margin: 20px 0;
}

/* ── Prev / Next navigation ── */
.page-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 40px;
  padding-top: 16px;
  border-top: 1px solid var(--separator);
}

.page-nav a {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  background: #EEF1F5;
  border: 1px solid var(--table-border);
  border-radius: 4px;
  color: var(--link-color);
  text-decoration: none;
  font-size: 13px;
  transition: background 0.2s;
}

.page-nav a:hover { background: #DDE4EC; }
.page-nav .spacer { flex: 1; }

/* ── Footer ── */
#footer {
  background: var(--footer-bg);
  border-top: 1px solid var(--separator);
  padding: 12px 40px;
  font-size: 12px;
  color: var(--footer-text);
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-left: var(--sidebar-width);
}

#footer a { color: var(--link-color); text-decoration: none; }

/* ── Search results ── */
#search-results {
  display: none;
  position: fixed;
  top: var(--topbar-height);
  right: 0;
  width: 360px;
  background: #fff;
  border: 1px solid var(--separator);
  border-top: none;
  max-height: 400px;
  overflow-y: auto;
  z-index: 150;
  box-shadow: -2px 4px 12px rgba(0,0,0,0.15);
}

#search-results.visible { display: block; }

.search-result-item {
  padding: 10px 16px;
  border-bottom: 1px solid #ECEFF1;
  cursor: pointer;
  transition: background 0.15s;
}

.search-result-item:hover { background: #F3F6FA; }
.search-result-item .result-title { font-weight: 600; color: var(--section-color); font-size: 13px; }
.search-result-item .result-preview { font-size: 12px; color: #6C757D; margin-top: 3px; line-height: 1.5; }
.search-result-item mark { background: #FFF176; padding: 0 2px; border-radius: 2px; }

/* ── Responsive ── */
@media (max-width: 768px) {
  #sidebar { transform: translateX(-100%); transition: transform 0.3s; }
  #sidebar.open { transform: translateX(0); }
  #content, #footer { margin-left: 0; }
  .content-inner { padding: 16px 20px; }
  #top-nav .logo { min-width: auto; }
}
"""

# ─── JavaScript ───────────────────────────────────────────────────────────────

DOXYGEN_JS = """
// Doxygen-style JS — sidebar toggle + search
document.addEventListener('DOMContentLoaded', function () {

  // ── Sidebar group toggle ──
  document.querySelectorAll('.sidebar-group-title').forEach(function (title) {
    title.addEventListener('click', function () {
      var content = title.nextElementSibling;
      var icon    = title.querySelector('.toggle-icon');
      if (content) {
        content.classList.toggle('hidden');
        title.classList.toggle('collapsed');
      }
    });
  });

  // ── Search ──
  var searchInput   = document.getElementById('search-input');
  var searchResults = document.getElementById('search-results');
  var searchIndex   = null;

  // Load the search index
  var indexPath = document.body.dataset.root + 'search_index.json';
  fetch(indexPath)
    .then(function (r) { return r.json(); })
    .then(function (data) { searchIndex = data; })
    .catch(function () { /* offline fallback */ });

  if (searchInput) {
    searchInput.addEventListener('input', function () {
      var q = searchInput.value.trim().toLowerCase();
      if (!q || !searchIndex) {
        searchResults.classList.remove('visible');
        return;
      }
      var hits = searchIndex.filter(function (item) {
        return item.title.toLowerCase().includes(q) ||
               item.content.toLowerCase().includes(q);
      }).slice(0, 8);

      if (hits.length === 0) {
        searchResults.classList.remove('visible');
        return;
      }

      searchResults.innerHTML = hits.map(function (item) {
        var excerpt = item.content;
        var idx = excerpt.toLowerCase().indexOf(q);
        if (idx > -1) {
          var start  = Math.max(0, idx - 40);
          var end    = Math.min(excerpt.length, idx + q.length + 60);
          var before = excerpt.slice(start, idx);
          var match  = excerpt.slice(idx, idx + q.length);
          var after  = excerpt.slice(idx + q.length, end);
          excerpt = (start > 0 ? '…' : '') + before +
                    '<mark>' + match + '</mark>' + after +
                    (end < excerpt.length ? '…' : '');
        } else {
          excerpt = excerpt.slice(0, 100) + '…';
        }
        return '<div class="search-result-item" onclick="location.href=\\'' +
               document.body.dataset.root + item.url + '\\'">' +
               '<div class="result-title">' + item.title + '</div>' +
               '<div class="result-preview">' + excerpt + '</div>' +
               '</div>';
      }).join('');
      searchResults.classList.add('visible');
    });

    document.addEventListener('click', function (e) {
      if (!searchResults.contains(e.target) && e.target !== searchInput) {
        searchResults.classList.remove('visible');
      }
    });

    searchInput.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') searchResults.classList.remove('visible');
    });
  }
});
"""

# ─── Template HTML ────────────────────────────────────────────────────────────

def page_path(slug, from_pages=True):
    """Retourne le chemin relatif vers une page."""
    return f"{slug}.html" if from_pages else f"pages/{slug}.html"

def sidebar_html(active_slug, root_prefix="../"):
    """Génère le HTML de la sidebar avec groupes chapitres / milestones."""
    chapter_items   = "\n".join(_sidebar_item(f, active_slug, root_prefix) for f in CHAPTERS)
    milestone_items = "\n".join(_sidebar_item(f, active_slug, root_prefix) for f in MILESTONES)

    # Les milestones sont repliés par défaut
    ms_collapsed = " collapsed"
    ms_hidden    = " hidden"

    return f"""
<div class="sidebar-group">
  <div class="sidebar-group-title" title="Cliquer pour réduire/agrandir">
    <span class="toggle-icon">&#9660;</span>Chapitres du cours
  </div>
  <ul class="sidebar-group-content">
{chapter_items}
  </ul>
</div>
<div class="sidebar-group">
  <div class="sidebar-group-title{ms_collapsed}" title="Cliquer pour réduire/agrandir">
    <span class="toggle-icon">&#9660;</span>Projets Milestone
  </div>
  <ul class="sidebar-group-content{ms_hidden}">
{milestone_items}
  </ul>
</div>
"""

def _sidebar_item(f, active_slug, root_prefix):
    active = ' class="active"' if f["slug"] == active_slug else ""
    badge  = '<span class="badge-milestone">MS</span>' if f["milestone"] else ""
    href   = f'{root_prefix}pages/{f["slug"]}.html'
    title  = f["title"]
    return f'    <li><a href="{href}"{active}>{title}{badge}</a></li>'

def topnav_html(active_tab, root_prefix):
    """Génère la barre de navigation supérieure."""
    tabs = [
        ("main",  f"{root_prefix}index.html",       "Page principale"),
        ("pages", f"{root_prefix}index.html#pages",  "Chapitres"),
        ("files", f"{root_prefix}index.html#files",  "Fichiers"),
    ]
    tabs_html = ""
    for key, href, label in tabs:
        cls = ' class="active"' if key == active_tab else ""
        tabs_html += f'<a href="{href}"{cls}>{label}</a>\n'

    return f"""
<nav id="top-nav">
  <a class="logo" href="{root_prefix}index.html">
    Python — Bechir Bejaoui<span class="sub">Cours complet</span>
  </a>
  <div id="nav-tabs">
    {tabs_html}
  </div>
  <div id="search-box">
    <input type="text" id="search-input" placeholder="Rechercher...">
  </div>
</nav>
<div id="search-results"></div>
"""

def full_page(title, body_html, active_slug, root_prefix, breadcrumb, page_nav="", is_milestone=False):
    """Construit une page HTML complète."""
    milestone_chip = '<span class="milestone-chip">📋 Milestone</span>' if is_milestone else ""
    gen_date = datetime.now().strftime("%d %B %Y")

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} — Cours Python</title>
  <link rel="stylesheet" href="{root_prefix}doxygen.css">
  <link rel="stylesheet"
        href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css">
  <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
  <script>hljs.highlightAll();</script>
</head>
<body data-root="{root_prefix}">

{topnav_html("pages", root_prefix)}

<div id="layout">
  <nav id="sidebar">
    <a href="{root_prefix}index.html" style="
      display:block; padding:14px 16px 12px;
      color:#FFFFFF; font-size:13px; text-decoration:none;
      border-bottom:1px solid rgba(255,255,255,0.07);
      font-weight:600;">
      🏠 Page principale
    </a>
    {sidebar_html(active_slug, root_prefix)}
  </nav>

  <main id="content">
    <div class="content-inner">
      <div class="breadcrumb">
        {breadcrumb}
      </div>

      <div class="page-title-band">
        <h1>{title}</h1>
        {milestone_chip}
      </div>

      {body_html}

      {page_nav}
    </div>

    <footer id="footer">
      <span>{title}</span>
      <span>Généré par <strong>Doxygen (Claude Edition)</strong> · {gen_date}</span>
    </footer>
  </main>
</div>

<script src="{root_prefix}doxygen.js"></script>
</body>
</html>"""

# ─── Conversion Markdown → HTML ───────────────────────────────────────────────

def md_to_html(md_text):
    """
    Convertit le Markdown en HTML avec toutes les extensions utiles.
    Post-traitement pour envelopper les blocs de code avec .code-header.
    """
    md = markdown.Markdown(extensions=[
        "tables",
        "fenced_code",
        "toc",
        "attr_list",
        "nl2br",
        "sane_lists",
        "smarty",
    ])
    html = md.convert(md_text)

    # Ajouter un en-tête de language aux blocs <pre><code class="language-xxx">
    def wrap_code_block(m):
        pre_attrs = m.group(1) or ""
        code_open = m.group(2)
        code_body = m.group(3)

        # Déterminer le nom du language
        lang_match = re.search(r'class="language-(\w+)"', code_open)
        lang_label = lang_match.group(1) if lang_match else "code"

        header = f'<div class="code-header"><span class="code-lang">{lang_label}</span></div>'
        return f'<pre{pre_attrs}>{header}{code_open}{code_body}</code></pre>'

    html = re.sub(
        r'<pre([^>]*)>(<code[^>]*>)([\s\S]*?)</code></pre>',
        wrap_code_block,
        html
    )
    return html

# ─── Génération des pages ─────────────────────────────────────────────────────

def prev_next(index):
    """Retourne les liens Précédent / Suivant."""
    prev_link = ""
    next_link = ""

    if index > 0:
        p = FILES[index - 1]
        prev_link = f'<a href="{p["slug"]}.html">&#8592; {p["title"]}</a>'
    else:
        prev_link = '<span></span>'

    if index < len(FILES) - 1:
        n = FILES[index + 1]
        next_link = f'<a href="{n["slug"]}.html">{n["title"]} &#8594;</a>'
    else:
        next_link = '<span></span>'

    return f'<div class="page-nav">{prev_link}<div class="spacer"></div>{next_link}</div>'


def generate_page(f, index):
    """Génère le HTML d'une page de chapitre."""
    src_path = BASE_DIR / f["src"]
    if not src_path.exists():
        print(f"  ⚠️  Fichier introuvable : {f['src']}")
        return

    md_text  = src_path.read_text(encoding="utf-8")
    body     = md_to_html(md_text)

    category = "Projets Milestone" if f["milestone"] else "Chapitres"
    breadcrumb = (
        f'<a href="../index.html">Page principale</a>'
        f' <span class="sep">»</span> '
        f'<span>{category}</span>'
        f' <span class="sep">»</span> '
        f'<span>{f["title"]}</span>'
    )

    nav = prev_next(index)
    html = full_page(
        title       = f["title"],
        body_html   = body,
        active_slug = f["slug"],
        root_prefix = "../",
        breadcrumb  = breadcrumb,
        page_nav    = nav,
        is_milestone= f["milestone"],
    )

    out_path = PAGES_DIR / f"{f['slug']}.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"  ✔  {f['slug']}.html")


def generate_index():
    """Génère index.html — la page principale."""
    # Contenu de bienvenue depuis le chapitre 0
    intro_src = BASE_DIR / FILES[0]["src"]
    intro_md  = intro_src.read_text(encoding="utf-8") if intro_src.exists() else "# Bienvenue"
    intro_html = md_to_html(intro_md)

    # Table de toutes les pages
    rows = ""
    for f in FILES:
        badge = '<span class="badge-milestone">Milestone</span>' if f["milestone"] else ""
        rows += f"""
        <tr>
          <td><a href="pages/{f['slug']}.html">{f['title']}</a></td>
          <td>{"📋 Projet" if f['milestone'] else "📖 Cours"}{badge}</td>
          <td>{f['src']}</td>
        </tr>"""

    files_li = "".join(
        f'<li><a href="pages/{item["slug"]}.html"><code>{item["src"]}</code></a></li>'
        for item in FILES
    )
    pages_table = f"""
<h2 id="pages">Tous les chapitres</h2>
<table>
  <thead>
    <tr><th>Titre</th><th>Type</th><th>Source</th></tr>
  </thead>
  <tbody>
    {rows}
  </tbody>
</table>
<hr>
<h2 id="files">Fichiers source</h2>
<ul>
{files_li}
</ul>
"""

    body = intro_html + pages_table
    gen_date = datetime.now().strftime("%d %B %Y")

    # Sidebar pour index (root_prefix = "")
    sidebar = sidebar_html(active_slug="", root_prefix="")

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Cours Python — Bechir Bejaoui</title>
  <link rel="stylesheet" href="doxygen.css">
  <link rel="stylesheet"
        href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css">
  <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
  <script>hljs.highlightAll();</script>
</head>
<body data-root="">

{topnav_html("main", "")}

<div id="layout">
  <nav id="sidebar">
    <a href="index.html" style="
      display:block; padding:14px 16px 12px;
      color:#FFFFFF; font-size:13px; text-decoration:none;
      border-bottom:1px solid rgba(255,255,255,0.07);
      font-weight:600; background:rgba(77,159,236,0.15);
      border-left:3px solid #4D9FEC;">
      🏠 Page principale
    </a>
    {sidebar}
  </nav>

  <main id="content">
    <div class="content-inner">
      <div class="page-title-band">
        <h1>Cours Python — Documentation complète</h1>
      </div>

      {body}
    </div>

    <footer id="footer">
      <span>Cours Python — Bechir Bejaoui</span>
      <span>Généré par <strong>Doxygen (Claude Edition)</strong> · {gen_date}</span>
    </footer>
  </main>
</div>

<script src="doxygen.js"></script>
</body>
</html>"""

    (OUTPUT_DIR / "index.html").write_text(html, encoding="utf-8")
    print("  ✔  index.html")


def generate_search_index():
    """Construit search_index.json avec titre + extrait de contenu."""
    index = []
    for f in FILES:
        src_path = BASE_DIR / f["src"]
        if not src_path.exists():
            continue
        text = src_path.read_text(encoding="utf-8")
        # Retire le markdown pour ne garder que le texte brut
        plain = re.sub(r'[#*`>\[\]()_~]', '', text)
        plain = re.sub(r'\s+', ' ', plain).strip()
        index.append({
            "title":   f["title"],
            "url":     f"pages/{f['slug']}.html",
            "content": plain[:600],
        })

    (OUTPUT_DIR / "search_index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("  ✔  search_index.json")


# ─── Point d'entrée ───────────────────────────────────────────────────────────

def main():
    print("\n🚀 Génération de la documentation style Doxygen...\n")

    # Préparer les dossiers de sortie
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir()
    PAGES_DIR.mkdir()

    # Écrire les assets partagés
    (OUTPUT_DIR / "doxygen.css").write_text(DOXYGEN_CSS, encoding="utf-8")
    print("  ✔  doxygen.css")
    (OUTPUT_DIR / "doxygen.js").write_text(DOXYGEN_JS, encoding="utf-8")
    print("  ✔  doxygen.js")

    # Page principale
    print("\n📄 Page principale :")
    generate_index()

    # Pages individuelles
    print("\n📚 Chapitres et milestones :")
    for i, f in enumerate(FILES):
        generate_page(f, i)

    # Index de recherche
    print("\n🔍 Index de recherche :")
    generate_search_index()

    print(f"\n✅ Documentation générée dans : {OUTPUT_DIR}")
    print(f"   Ouvrir : {OUTPUT_DIR / 'index.html'}\n")


if __name__ == "__main__":
    main()
