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
    var lines = block.innerHTML.split('\n');
    // Remove trailing empty line
    if (lines[lines.length - 1] === '') lines.pop();
    block.innerHTML = lines.map(function (l) {
      return '<span class="code-line">' + l + '</span>';
    }).join('\n');
    if (block.parentElement) block.parentElement.classList.add('line-numbers');
  });
});
