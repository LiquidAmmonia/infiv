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
    "arxiv":    {"label": "arXiv",    "color": "#9a3412", "bg": "#ffedd5"},  # orange-800 / orange-100
    "html":     {"label": "HTML",     "color": "#1d4ed8", "bg": "#dbeafe"},  # blue-700 / blue-100
    "pdf":      {"label": "PDF",      "color": "#b91c1c", "bg": "#fee2e2"},  # red-700 / red-100
    "kimi":     {"label": "Kimi",     "color": "#6d28d9", "bg": "#ede9fe"},  # violet-700 / violet-100
    "source":   {"label": "Source",   "color": "#475569", "bg": "#f1f5f9"},  # slate-600 / slate-100
    "bilibili": {"label": "bilibili", "color": "#be185d", "bg": "#fce7f3"},  # pink-700 / pink-100
    "zhihu":    {"label": "知乎",      "color": "#1d4ed8", "bg": "#dbeafe"},  # blue-700 / blue-100
    "cooler":   {"label": "CoolPaper","color": "#0e7490", "bg": "#cffafe"},  # cyan-700 / cyan-100
}

# Palette for subject section accent colours (cycles if more subjects than colours)
_SUBJECT_COLORS = [
    "#4f46e5",  # indigo-600
    "#0891b2",  # cyan-600
    "#059669",  # emerald-600
    "#d97706",  # amber-600
    "#dc2626",  # red-600
    "#7c3aed",  # violet-600
    "#db2777",  # pink-600
    "#0284c7",  # sky-600
    "#16a34a",  # green-600
    "#ea580c",  # orange-600
]

# ── CSS ───────────────────────────────────────────────────────────────────────
_CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

/* Material Design 3 tokens */
:root {
  /* MD3 surface tones */
  --md-bg:           #f4f6fb;      /* surface-dim */
  --md-surface:      #ffffff;      /* surface */
  --md-surface-v:    #eef1f8;      /* surface-variant */
  --md-outline:      #c4c8d4;      /* outline-variant */
  --md-primary:      #4f46e5;      /* primary (indigo-600) */
  --md-primary-c:    #ffffff;      /* on-primary */
  --md-on-surface:   #191c24;      /* on-surface */
  --md-on-sv:        #43475a;      /* on-surface-variant */
  --md-scrim:        rgba(25,28,36,0.06);
  /* elevation shadows (MD3 uses tonal + shadow) */
  --elev-1: 0 1px 2px rgba(0,0,0,0.08), 0 1px 3px 1px rgba(0,0,0,0.06);
  --elev-2: 0 1px 2px rgba(0,0,0,0.10), 0 2px 6px 2px rgba(0,0,0,0.08);
  --elev-3: 0 4px 8px 3px rgba(0,0,0,0.08), 0 1px 3px rgba(0,0,0,0.10);
  --radius-card: 16px;
  --radius-pill: 999px;
  --radius-sm:   8px;
}

body {
  font-family: 'Google Sans', 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background: var(--md-bg);
  color: var(--md-on-surface);
  line-height: 1.6;
  min-height: 100vh;
}

/* ─── Top App Bar (MD3) ───────────────────────── */
.site-header {
  /* MD3 primary container */
  background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
  color: #e0e7ff;
  padding: 0.9rem 1.5rem;
  position: sticky;
  top: 0;
  z-index: 200;
  /* MD3 elevation-2 tonal header */
  box-shadow: 0 2px 4px rgba(0,0,0,0.20), 0 0 0 1px rgba(255,255,255,0.04) inset;
}
.header-inner {
  max-width: 1280px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}
.site-header h1 {
  font-size: 1.35rem;
  font-weight: 500;               /* MD3 Title Large */
  letter-spacing: 0;
  flex-shrink: 0;
  color: #ffffff;
}
.header-meta {
  font-size: 0.78rem;
  opacity: 0.55;
  flex-shrink: 0;
  letter-spacing: 0.1px;
}

/* Search field — MD3 filled text field shape */
.search-box {
  flex: 1;
  min-width: 160px;
  max-width: 360px;
  position: relative;
  margin-left: auto;
}
.search-box input {
  width: 100%;
  padding: 0.46rem 1rem 0.46rem 2.2rem;
  border-radius: var(--radius-pill);
  border: none;
  background: rgba(255,255,255,0.12);
  color: #fff;
  font-size: 0.85rem;
  outline: none;
  transition: background 0.2s;
  caret-color: #90caf9;
}
.search-box input::placeholder { color: rgba(255,255,255,0.38); }
.search-box input:focus {
  background: rgba(255,255,255,0.20);
  box-shadow: 0 0 0 2px rgba(144,202,249,0.45);
}
.search-icon {
  position: absolute;
  left: 0.65rem;
  top: 50%;
  transform: translateY(-50%);
  opacity: 0.45;
  pointer-events: none;
  font-size: 0.9rem;
}

/* MD3 Outlined button (header) */
.header-archives-btn {
  flex-shrink: 0;
  padding: 0.35rem 1rem;
  border-radius: var(--radius-pill);
  border: 1px solid rgba(255,255,255,0.30);
  background: transparent;
  color: #e8eeff;
  font-size: 0.8rem;
  font-weight: 500;
  text-decoration: none;
  white-space: nowrap;
  letter-spacing: 0.25px;
  transition: background 0.18s, border-color 0.18s;
}
.header-archives-btn:hover {
  background: rgba(255,255,255,0.10);
  border-color: rgba(255,255,255,0.55);
}

/* ─── Subject chip nav ────────────────────────── */
.subject-nav {
  max-width: 1280px;
  margin: 0.85rem auto 0;
  padding: 0 1.5rem;
  display: flex;
  gap: 0.4rem;
  flex-wrap: wrap;
}
/* Assist chips — MD3 */
.subject-nav a {
  padding: 0.26rem 0.9rem;
  border-radius: var(--radius-pill);
  font-size: 0.76rem;
  font-weight: 500;
  text-decoration: none;
  color: #fff;
  letter-spacing: 0.1px;
  opacity: 0.92;
  transition: opacity 0.15s, box-shadow 0.15s;
  box-shadow: 0 1px 2px rgba(0,0,0,0.18);
}
.subject-nav a:hover {
  opacity: 1;
  box-shadow: 0 2px 6px rgba(0,0,0,0.26);
}

/* ─── Layout ──────────────────────────────────── */
.container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 1.5rem;
}

/* ─── Subject section ─────────────────────────── */
.subject-section { margin-bottom: 2.5rem; }

.subject-section-header {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-bottom: 1rem;
  padding: 0.5rem 0.75rem;
  border-radius: var(--radius-sm);
  background: var(--md-surface);
  box-shadow: var(--elev-1);
  border-left: 4px solid currentColor;
}
.subject-section-header h2 {
  font-size: 1.05rem;
  font-weight: 600;               /* MD3 Title Medium */
  letter-spacing: 0.1px;
}
.subject-count-badge {
  font-size: 0.72rem;
  font-weight: 600;
  padding: 0.12rem 0.5rem;
  border-radius: var(--radius-pill);
  background: currentColor;
  line-height: 1.6;
  opacity: 0.9;
}
.subject-count-badge span { color: #fff; mix-blend-mode: difference; }

/* ─── Cards grid ──────────────────────────────── */
.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 0.9rem;
}

/* ─── Paper card (MD3 Elevated Card) ─────────── */
.paper-card {
  background: var(--md-surface);
  border-radius: var(--radius-card);
  box-shadow: var(--elev-1);
  padding: 1.1rem 1.2rem 1.2rem;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  transition: box-shadow 0.22s, transform 0.22s;
  /* no border — MD3 elevated cards use shadow only */
}
.paper-card:hover {
  box-shadow: var(--elev-3);
  transform: translateY(-2px);
}
.paper-card.hidden { display: none; }

/* Title — MD3 Body Large */
.paper-title {
  font-size: 0.94rem;
  font-weight: 600;
  line-height: 1.5;
  color: var(--md-on-surface);
}
.paper-title a { color: inherit; text-decoration: none; }
.paper-title a:hover {
  color: var(--md-primary);
  text-decoration: underline;
  text-underline-offset: 2px;
}

/* Meta chips row */
.card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  align-items: center;
}
/* MD3 Input chip */
.badge {
  padding: 0.15rem 0.6rem;
  border-radius: var(--radius-pill);
  font-size: 0.7rem;
  font-weight: 500;
  white-space: nowrap;
  letter-spacing: 0.1px;
}
.badge-date {
  background: var(--md-surface-v);
  color: var(--md-on-sv);
}
.badge-tag {
  background: #e0e7ff;
  color: #3730a3;
}

/* MD3 Tonal Buttons for links */
.card-links {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}
.link-btn {
  display: inline-block;
  padding: 0.2rem 0.7rem;
  border-radius: var(--radius-pill);   /* pill — MD3 filled tonal */
  font-size: 0.72rem;
  font-weight: 500;
  text-decoration: none;
  letter-spacing: 0.25px;
  transition: box-shadow 0.15s, filter 0.15s;
  box-shadow: 0 1px 2px rgba(0,0,0,0.10);
}
.link-btn:hover {
  filter: brightness(0.92);
  box-shadow: 0 2px 4px rgba(0,0,0,0.16);
}

/* Abstract */
.card-abstract {
  font-size: 0.84rem;
  color: var(--md-on-sv);
  line-height: 1.75;
}
.abstract-inner {
  position: relative;
  overflow: hidden;
}
.abstract-inner.collapsed { max-height: 5em; }
.abstract-inner.collapsed::after {
  content: '';
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 2.4em;
  background: linear-gradient(to bottom, transparent, var(--md-surface));
  pointer-events: none;
}
.toggle-btn {
  background: none;
  border: none;
  color: var(--md-primary);
  cursor: pointer;
  font-size: 0.76rem;
  font-weight: 500;
  padding: 0.1rem 0;
  margin-top: 0.15rem;
  letter-spacing: 0.25px;
}
.card-abstract p  { margin-bottom: 0.4rem; }
.card-abstract p:last-child { margin-bottom: 0; }
.card-abstract ul { padding-left: 1.2rem; }
.card-abstract li { margin-bottom: 0.2rem; }
.card-abstract code {
  background: var(--md-surface-v);
  padding: 0.1em 0.35em;
  border-radius: 4px;
  font-size: 0.88em;
  font-family: 'Roboto Mono', 'SFMono-Regular', Consolas, monospace;
}
.card-abstract strong { color: var(--md-on-surface); font-weight: 600; }

/* No search results */
.no-results {
  text-align: center;
  padding: 4rem 2rem;
  color: var(--md-on-sv);
  font-size: 1rem;
  display: none;
}

/* Footer */
.site-footer {
  text-align: center;
  padding: 1.5rem;
  color: var(--md-on-sv);
  font-size: 0.79rem;
  border-top: 1px solid var(--md-outline);
  margin-top: 2rem;
  background: var(--md-surface);
}

/* Responsive */
@media (max-width: 640px) {
  .cards-grid { grid-template-columns: 1fr; }
  .site-header h1 { font-size: 1.15rem; }
  .header-inner { gap: 0.6rem; }
  .container { padding: 1rem; }
  .header-archives-btn { display: none; }
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
