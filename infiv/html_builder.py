"""HTML builder for infiv daily news reports.

Generates a beautiful, self-contained, interactive HTML page from a list of InfoItems.
Features:
  - Card-based paper layout with hover effects
  - Styled link buttons (arXiv / HTML / PDF / Kimi / etc.)
  - Tag / keyword badges
  - Subject-section grouping with colored headers
  - Live search / filter via a text input
  - Collapsible abstracts
"""
import html as _html
import re
from datetime import datetime
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from infiv.types import InfoItem

# ── Link type → display style ────────────────────────────────────────────────
_LINK_STYLES: dict = {
    "arxiv":    {"label": "arXiv",    "color": "#b54a00", "bg": "#fff1ec"},
    "html":     {"label": "HTML",     "color": "#1d4ed8", "bg": "#eff6ff"},
    "pdf":      {"label": "PDF",      "color": "#b91c1c", "bg": "#fef2f2"},
    "kimi":     {"label": "Kimi",     "color": "#6d28d9", "bg": "#f5f3ff"},
    "source":   {"label": "Source",   "color": "#374151", "bg": "#f1f5f9"},
    "bilibili": {"label": "bilibili", "color": "#d65278", "bg": "#fff0f6"},
    "zhihu":    {"label": "知乎",      "color": "#007fff", "bg": "#eff6ff"},
    "cooler":   {"label": "CoolPaper","color": "#0d9488", "bg": "#f0fdfa"},
}

# Palette for subject section accent colours (cycles if more subjects than colours)
_SUBJECT_COLORS = [
    "#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6",
    "#ec4899", "#06b6d4", "#84cc16", "#f97316", "#6366f1",
]

# ── CSS ───────────────────────────────────────────────────────────────────────
_CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg: #f0f2f5;
  --card-bg: #ffffff;
  --text: #1a202c;
  --text-muted: #718096;
  --border: #e2e8f0;
  --shadow: 0 1px 3px rgba(0,0,0,0.07), 0 4px 12px rgba(0,0,0,0.04);
  --shadow-hover: 0 4px 16px rgba(0,0,0,0.11), 0 8px 28px rgba(0,0,0,0.07);
  --radius: 12px;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
  min-height: 100vh;
}

/* ─── Header ──────────────────────────────────── */
.site-header {
  background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
  color: #fff;
  padding: 1.75rem 1.5rem 1.5rem;
  position: sticky;
  top: 0;
  z-index: 200;
  box-shadow: 0 2px 24px rgba(0,0,0,0.35);
}
.header-inner {
  max-width: 1240px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 1.25rem;
  flex-wrap: wrap;
}
.site-header h1 {
  font-size: 1.65rem;
  font-weight: 800;
  letter-spacing: -0.5px;
  flex-shrink: 0;
}
.header-meta {
  font-size: 0.82rem;
  opacity: 0.65;
  flex-shrink: 0;
}
.search-box {
  flex: 1;
  min-width: 160px;
  max-width: 380px;
  position: relative;
  margin-left: auto;
}
.search-box input {
  width: 100%;
  padding: 0.48rem 1rem 0.48rem 2.2rem;
  border-radius: 999px;
  border: none;
  background: rgba(255,255,255,0.13);
  color: #fff;
  font-size: 0.88rem;
  outline: none;
  transition: background 0.2s;
}
.search-box input::placeholder { color: rgba(255,255,255,0.45); }
.search-box input:focus { background: rgba(255,255,255,0.22); }
.search-icon {
  position: absolute;
  left: 0.65rem;
  top: 50%;
  transform: translateY(-50%);
  opacity: 0.5;
  pointer-events: none;
}
.header-archives-btn {
  flex-shrink: 0;
  padding: 0.38rem 1rem;
  border-radius: 999px;
  background: rgba(255,255,255,0.15);
  color: #fff;
  font-size: 0.82rem;
  font-weight: 700;
  text-decoration: none;
  white-space: nowrap;
  transition: background 0.2s;
}
.header-archives-btn:hover { background: rgba(255,255,255,0.28); }

/* ─── Subject nav pills ───────────────────────── */
.subject-nav {
  max-width: 1240px;
  margin: 1.25rem auto 0;
  padding: 0 1.5rem;
  display: flex;
  gap: 0.45rem;
  flex-wrap: wrap;
}
.subject-nav a {
  padding: 0.3rem 0.85rem;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 700;
  text-decoration: none;
  color: #fff;
  transition: opacity 0.15s, transform 0.15s;
  white-space: nowrap;
}
.subject-nav a:hover { opacity: 0.82; transform: translateY(-1px); }

/* ─── Layout ──────────────────────────────────── */
.container {
  max-width: 1240px;
  margin: 0 auto;
  padding: 1.5rem;
}

/* ─── Subject section ─────────────────────────── */
.subject-section { margin-bottom: 2.75rem; }

.subject-section-header {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  margin-bottom: 1rem;
  padding-bottom: 0.45rem;
  border-bottom: 3px solid currentColor;
}
.subject-section-header h2 {
  font-size: 1.35rem;
  font-weight: 800;
}
.subject-count-badge {
  font-size: 0.75rem;
  font-weight: 700;
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
  background: currentColor;
  line-height: 1.5;
}
.subject-count-badge span { color: #fff; mix-blend-mode: difference; }

/* ─── Cards grid ──────────────────────────────── */
.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 1rem;
}

/* ─── Paper card ──────────────────────────────── */
.paper-card {
  background: var(--card-bg);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 1.2rem 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  transition: box-shadow 0.22s, transform 0.22s;
  border: 1px solid var(--border);
}
.paper-card:hover {
  box-shadow: var(--shadow-hover);
  transform: translateY(-2px);
}
.paper-card.hidden { display: none; }

/* Title */
.paper-title {
  font-size: 0.97rem;
  font-weight: 700;
  line-height: 1.45;
  color: var(--text);
}
.paper-title a { color: inherit; text-decoration: none; }
.paper-title a:hover { color: #2563eb; text-decoration: underline; }

/* Meta badges row */
.card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.38rem;
  align-items: center;
}
.badge {
  padding: 0.18rem 0.55rem;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 600;
  white-space: nowrap;
}
.badge-date  { background: #f1f5f9; color: #475569; }
.badge-tag   { background: #eff6ff; color: #1d4ed8; }

/* Link buttons */
.card-links {
  display: flex;
  flex-wrap: wrap;
  gap: 0.38rem;
}
.link-btn {
  display: inline-block;
  padding: 0.22rem 0.68rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 700;
  text-decoration: none;
  transition: filter 0.15s, transform 0.15s;
  letter-spacing: 0.2px;
}
.link-btn:hover { filter: brightness(0.88); transform: translateY(-1px); }

/* Abstract */
.card-abstract {
  font-size: 0.855rem;
  color: var(--text-muted);
  line-height: 1.7;
}
.abstract-inner {
  position: relative;
  overflow: hidden;
}
.abstract-inner.collapsed {
  max-height: 5em;
}
.abstract-inner.collapsed::after {
  content: '';
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 2.2em;
  background: linear-gradient(to bottom, transparent, var(--card-bg));
  pointer-events: none;
}
.toggle-btn {
  background: none;
  border: none;
  color: #3b82f6;
  cursor: pointer;
  font-size: 0.78rem;
  font-weight: 700;
  padding: 0.1rem 0;
  margin-top: 0.2rem;
}
.card-abstract p  { margin-bottom: 0.45rem; }
.card-abstract p:last-child { margin-bottom: 0; }
.card-abstract ul { padding-left: 1.2rem; }
.card-abstract li { margin-bottom: 0.2rem; }
.card-abstract code {
  background: #f1f5f9;
  padding: 0.1em 0.35em;
  border-radius: 4px;
  font-size: 0.9em;
  font-family: 'SFMono-Regular', Consolas, monospace;
}
.card-abstract strong { color: var(--text); font-weight: 700; }

/* No search results */
.no-results {
  text-align: center;
  padding: 4rem 2rem;
  color: var(--text-muted);
  font-size: 1.05rem;
  display: none;
}

/* Footer */
.site-footer {
  text-align: center;
  padding: 1.75rem;
  color: var(--text-muted);
  font-size: 0.82rem;
  border-top: 1px solid var(--border);
  margin-top: 2rem;
}

/* Responsive */
@media (max-width: 640px) {
  .cards-grid { grid-template-columns: 1fr; }
  .site-header h1 { font-size: 1.3rem; }
  .header-inner { gap: 0.6rem; }
  .container { padding: 1rem; }
}
"""

# ── JavaScript ────────────────────────────────────────────────────────────────
_JS = """
function filterCards(query) {
  var q = query.toLowerCase().trim();
  var visibleCount = 0;
  document.querySelectorAll('.paper-card').forEach(function(card) {
    var title    = (card.dataset.title   || '').toLowerCase();
    var tags     = (card.dataset.tags    || '').toLowerCase();
    var subj     = (card.dataset.subject || '').toLowerCase();
    var abstract = (card.querySelector('.abstract-inner') || {}).textContent || '';
    abstract = abstract.toLowerCase();
    var match = !q || title.includes(q) || tags.includes(q) || subj.includes(q) || abstract.includes(q);
    card.classList.toggle('hidden', !match);
    if (match) visibleCount++;
  });
  var nr = document.getElementById('no-results');
  if (nr) nr.style.display = (visibleCount === 0 && q) ? 'block' : 'none';
  document.querySelectorAll('.subject-section').forEach(function(sec) {
    var vis = sec.querySelectorAll('.paper-card:not(.hidden)').length;
    var countEl = sec.querySelector('.subject-count-badge span');
    if (countEl) countEl.textContent = vis;
    sec.style.display = (vis === 0 && q) ? 'none' : '';
  });
}

function toggleAbstract(btn) {
  var inner = btn.previousElementSibling;
  var collapsed = inner.classList.toggle('collapsed');
  btn.textContent = collapsed ? '展开全文 ▼' : '收起 ▲';
}

document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.abstract-inner').forEach(function(el) {
    if (el.scrollHeight > 90) {
      el.classList.add('collapsed');
      var btn = el.nextElementSibling;
      if (btn && btn.classList.contains('toggle-btn')) {
        btn.style.display = 'inline-block';
      }
    }
  });
});
"""


# ── Helper functions ──────────────────────────────────────────────────────────

def _get_link_style(key: str) -> dict:
    key_lower = key.lower()
    for k, style in _LINK_STYLES.items():
        if k in key_lower:
            return style
    return {"label": key, "color": "#374151", "bg": "#f1f5f9"}


def _md_to_html(text: str) -> str:
    """Minimal markdown-to-HTML converter suitable for paper abstracts."""
    # Escape HTML first
    escaped = _html.escape(text)
    # Bold (**text**)
    escaped = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', escaped, flags=re.DOTALL)
    # Italic (*text*)
    escaped = re.sub(r'\*(.+?)\*', r'<em>\1</em>', escaped)
    # Inline code
    escaped = re.sub(r'`([^`]+)`', r'<code>\1</code>', escaped)
    # Markdown links [text](url)
    escaped = re.sub(
        r'\[([^\]]+)\]\(([^)]+)\)',
        r'<a href="\2" target="_blank" rel="noopener">\1</a>',
        escaped
    )
    # Split into paragraphs on blank lines
    paragraphs = re.split(r'\n{2,}', escaped)
    parts = []
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        # Bullet lists
        if re.search(r'^[-*] ', p, re.MULTILINE):
            lines = p.split('\n')
            items_html = ''
            for line in lines:
                m = re.match(r'^[-*] (.+)', line)
                if m:
                    items_html += f'<li>{m.group(1)}</li>'
                elif line.strip():
                    items_html += f'<li>{line}</li>'
            parts.append(f'<ul>{items_html}</ul>')
        else:
            parts.append(f'<p>{p.replace(chr(10), "<br>")}</p>')
    return ''.join(parts) if parts else f'<p>{escaped}</p>'


def _make_link_btn(key: str, url: str) -> str:
    style = _get_link_style(key)
    label = _html.escape(style.get("label", key))
    color = style.get("color", "#374151")
    bg    = style.get("bg", "#f1f5f9")
    safe_url = _html.escape(url)
    return (
        f'<a href="{safe_url}" target="_blank" rel="noopener" class="link-btn" '
        f'style="color:{color};background:{bg};">{label}</a>'
    )


def _make_card(item: "InfoItem") -> str:
    title   = _html.escape(item.get("title", "Untitled"))
    subject = item.get("subject", "")

    # First link → title href
    first_url = ""
    for lnk in item.get("links", []):
        if isinstance(lnk, dict):
            first_url = next(iter(lnk.values()), "")
        elif isinstance(lnk, str):
            first_url = lnk
        if first_url:
            break

    # Title HTML
    if first_url:
        title_html = (
            f'<h3 class="paper-title">'
            f'<a href="{_html.escape(first_url)}" target="_blank" rel="noopener">{title}</a>'
            f'</h3>'
        )
    else:
        title_html = f'<h3 class="paper-title">{title}</h3>'

    # Meta badges
    badges = []
    dt = item.get("pub_datetime")
    if dt:
        date_str = dt.strftime("%Y-%m-%d %H:%M")
        badges.append(f'<span class="badge badge-date">📅 {_html.escape(date_str)}</span>')
    for tag in item.get("tags", []):
        badges.append(f'<span class="badge badge-tag">{_html.escape(str(tag))}</span>')
    meta_html = f'<div class="card-meta">{"".join(badges)}</div>' if badges else ""

    # Link buttons
    link_btns = []
    for lnk in item.get("links", []):
        if isinstance(lnk, dict):
            for k, v in lnk.items():
                link_btns.append(_make_link_btn(k, v))
        elif isinstance(lnk, str):
            link_btns.append(_make_link_btn("source", lnk))
    links_html = (
        f'<div class="card-links">{"".join(link_btns)}</div>'
        if link_btns else ""
    )

    # Abstract
    content = item.get("content", "").strip()
    if content:
        abstract_inner_html = _md_to_html(content)
        abstract_html = (
            f'<div class="card-abstract">'
            f'<div class="abstract-inner">{abstract_inner_html}</div>'
            f'<button class="toggle-btn" onclick="toggleAbstract(this)" style="display:none;">展开全文 ▼</button>'
            f'</div>'
        )
    else:
        abstract_html = ""

    # data-* attributes for JS search
    tags_str = " ".join(item.get("tags", []))

    return (
        f'<article class="paper-card" '
        f'data-title="{title}" '
        f'data-tags="{_html.escape(tags_str)}" '
        f'data-subject="{_html.escape(subject)}">'
        f'{title_html}'
        f'{meta_html}'
        f'{links_html}'
        f'{abstract_html}'
        f'</article>'
    )


# ── Public API ────────────────────────────────────────────────────────────────

def build_html(
    items: List["InfoItem"],
    title: str = "Daily News",
    generated_at: str = "",
    archives_url: str = "",
) -> str:
    """Build a complete, self-contained HTML page from a list of InfoItems.

    Items should already be in the desired display order. Subject grouping is
    preserved in the order subjects first appear.

    archives_url: relative URL to the archives/index page; shown as a nav link
                  in the header when non-empty.
    """
    n = len(items)
    gen_str = generated_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Group by subject, preserving insertion order
    ordered_subjects: List[str] = []
    subject_items: dict = {}
    for item in items:
        s = item.get("subject", "unclass")
        if s not in subject_items:
            ordered_subjects.append(s)
            subject_items[s] = []
        subject_items[s].append(item)

    # Nav pills
    nav_parts = []
    for i, subj in enumerate(ordered_subjects):
        color  = _SUBJECT_COLORS[i % len(_SUBJECT_COLORS)]
        anchor = re.sub(r'[^a-z0-9-]', '-', subj.lower())
        cnt    = len(subject_items[subj])
        nav_parts.append(
            f'<a href="#{anchor}" style="background:{color};">'
            f'{_html.escape(subj)}&nbsp;({cnt})</a>'
        )
    nav_html = f'<nav class="subject-nav">{"".join(nav_parts)}</nav>' if nav_parts else ""

    # Sections
    section_parts = []
    for i, subj in enumerate(ordered_subjects):
        color  = _SUBJECT_COLORS[i % len(_SUBJECT_COLORS)]
        anchor = re.sub(r'[^a-z0-9-]', '-', subj.lower())
        cards  = "\n".join(_make_card(item) for item in subject_items[subj])
        cnt    = len(subject_items[subj])
        section_parts.append(
            f'<section class="subject-section" id="{anchor}">'
            f'<div class="subject-section-header" style="color:{color};">'
            f'<h2>{_html.escape(subj)}</h2>'
            f'<div class="subject-count-badge"><span>{cnt}</span></div>'
            f'</div>'
            f'<div class="cards-grid">{cards}</div>'
            f'</section>'
        )
    sections_html = "\n".join(section_parts)

    safe_title    = _html.escape(title)
    safe_gen      = _html.escape(gen_str)
    archives_btn  = (
        f'<a href="{_html.escape(archives_url)}" class="header-archives-btn">📚 历史存档</a>'
        if archives_url else ""
    )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{safe_title}</title>
  <style>{_CSS}</style>
</head>
<body>

<header class="site-header">
  <div class="header-inner">
    <h1>📰 {safe_title}</h1>
    <div class="header-meta">Generated at {safe_gen} &nbsp;·&nbsp; {n} articles</div>
    {archives_btn}
    <div class="search-box">
      <span class="search-icon">🔍</span>
      <input type="text" placeholder="Search papers, tags…" oninput="filterCards(this.value)" aria-label="search">
    </div>
  </div>
</header>

{nav_html}

<main class="container">
  <div id="no-results" class="no-results">&#128270; No results match your search.</div>
  {sections_html}
</main>

<footer class="site-footer">
  Built by <strong>infiv</strong> · {safe_gen}
</footer>

<script>{_JS}</script>
</body>
</html>"""
