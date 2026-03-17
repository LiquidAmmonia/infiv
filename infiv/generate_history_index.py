"""Generate history index pages for all historical report files."""
import html as _html
import logging
import os
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

_WEEKDAYS_ZH = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

_INDEX_CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
:root {
  --bg: #f0f2f5;
  --card-bg: #fff;
  --text: #1a202c;
  --text-muted: #718096;
  --border: #e2e8f0;
  --shadow: 0 1px 3px rgba(0,0,0,0.07), 0 4px 12px rgba(0,0,0,0.04);
  --radius: 12px;
}
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
}
.site-header {
  background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
  color: #fff;
  padding: 2.5rem 1.5rem 2rem;
  text-align: center;
}
.site-header h1 { font-size: 2rem; font-weight: 800; letter-spacing: -0.5px; }
.site-header p  { margin-top: 0.5rem; opacity: 0.65; font-size: 0.9rem; }
.container {
  max-width: 860px;
  margin: 2rem auto;
  padding: 0 1.5rem;
}
.year-group { margin-bottom: 2.5rem; }
.year-heading {
  font-size: 1.25rem;
  font-weight: 800;
  color: #3b82f6;
  margin-bottom: 1rem;
  padding-bottom: 0.4rem;
  border-bottom: 3px solid #3b82f6;
}
.entry-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 0.75rem;
}
.entry-card {
  background: var(--card-bg);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  border: 1px solid var(--border);
  padding: 1rem 1.1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  transition: box-shadow 0.2s, transform 0.2s;
}
.entry-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.11); transform: translateY(-2px); }
.entry-date { font-size: 1rem; font-weight: 700; }
.entry-weekday { font-size: 0.78rem; color: var(--text-muted); }
.entry-links { display: flex; gap: 0.45rem; flex-wrap: wrap; }
.entry-link {
  display: inline-block;
  padding: 0.2rem 0.6rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 700;
  text-decoration: none;
  transition: filter 0.15s;
}
.entry-link:hover { filter: brightness(0.88); }
.link-html { color: #1d4ed8; background: #eff6ff; }
.link-md   { color: #374151; background: #f1f5f9; }
.no-data { text-align: center; padding: 4rem; color: var(--text-muted); }
.site-footer { text-align: center; padding: 2rem; color: var(--text-muted); font-size: 0.82rem; border-top: 1px solid var(--border); margin-top: 2rem; }
@media (max-width: 480px) { .entry-grid { grid-template-columns: 1fr 1fr; } }
"""


def _build_index_html(entries: list, total: int, generated_at: str) -> str:
    """entries: list of dicts with keys: date_str, display_date, weekday, has_html, has_md"""
    # Group by year
    from itertools import groupby
    entries_sorted = sorted(entries, key=lambda e: e["date_str"], reverse=True)
    year_groups = {}
    for entry in entries_sorted:
        year = entry["date_str"][:4]
        year_groups.setdefault(year, []).append(entry)

    year_sections = []
    for year in sorted(year_groups.keys(), reverse=True):
        cards = []
        for e in year_groups[year]:
            links_html = ""
            if e["has_html"]:
                href = _html.escape(f"history/{e['date_str']}.html")
                links_html += f'<a href="{href}" class="entry-link link-html">HTML</a>'
            if e["has_md"]:
                href = _html.escape(f"history/{e['date_str']}.md")
                links_html += f'<a href="{href}" class="entry-link link-md">Markdown</a>'
            cards.append(
                f'<div class="entry-card">'
                f'<div class="entry-date">{_html.escape(e["date_str"])}</div>'
                f'<div class="entry-weekday">{_html.escape(e["weekday"])}</div>'
                f'<div class="entry-links">{links_html}</div>'
                f'</div>'
            )
        year_sections.append(
            f'<div class="year-group">'
            f'<div class="year-heading">{_html.escape(year)}</div>'
            f'<div class="entry-grid">{"".join(cards)}</div>'
            f'</div>'
        )

    body = "\n".join(year_sections) if year_sections else '<div class="no-data">暂无历史报告</div>'
    safe_gen = _html.escape(generated_at)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Daily News Archive</title>
  <style>{_INDEX_CSS}</style>
</head>
<body>
<header class="site-header">
  <div style="display:flex;align-items:center;justify-content:center;gap:1rem;flex-wrap:wrap;">
    <h1>📚 Daily News Archive</h1>
    <a href="./" style="padding:0.38rem 1rem;border-radius:999px;background:rgba(255,255,255,0.15);color:#fff;font-size:0.82rem;font-weight:700;text-decoration:none;white-space:nowrap;">📰 最新报告</a>
  </div>
  <p style="margin-top:0.5rem;">共 {total} 份报告 &nbsp;·&nbsp; 更新于 {safe_gen}</p>
</header>
<main class="container">
  {body}
</main>
<footer class="site-footer">Built by <strong>infiv</strong></footer>
</body>
</html>"""


def main():
    """Generate index.html (and index.md) with links to all historical report files."""
    history_dir = Path("history")

    if not history_dir.exists():
        logger.warning("History directory does not exist")
        return

    # Collect all dated files
    date_stems: set = set()
    for f in history_dir.iterdir():
        if f.suffix in (".md", ".html"):
            try:
                datetime.strptime(f.stem, "%Y-%m-%d")
                date_stems.add(f.stem)
            except ValueError:
                pass

    if not date_stems:
        logger.warning("No dated report files found in history directory")
        return

    entries = []
    for stem in sorted(date_stems, reverse=True):
        file_date = datetime.strptime(stem, "%Y-%m-%d")
        weekday_zh = _WEEKDAYS_ZH[file_date.weekday()]
        entries.append({
            "date_str": stem,
            "weekday": weekday_zh,
            "has_html": (history_dir / f"{stem}.html").exists(),
            "has_md":   (history_dir / f"{stem}.md").exists(),
        })

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Write HTML index
    html_content = _build_index_html(entries, len(entries), generated_at)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    logger.info(f"Generated HTML index at index.html with {len(entries)} entries")

    # Also keep a simple markdown index for compatibility
    md_lines = [
        "# Historical Daily News Archive",
        "",
        f"Total reports: {len(entries)}",
        "",
        "## Archive by Date",
        "",
    ]
    for e in entries:
        if e["has_html"]:
            md_lines.append(f"- [{e['date_str']} ({e['weekday']})](history/{e['date_str']}.html)")
        elif e["has_md"]:
            md_lines.append(f"- [{e['date_str']} ({e['weekday']})](history/{e['date_str']}.md)")
    with open("index.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    logger.info("Generated markdown index at index.md")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()
