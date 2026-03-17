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
/* Material Design 3 */
:root {
  --md-bg:        #f4f6fb;
  --md-surface:   #ffffff;
  --md-surface-v: #eef1f8;
  --md-outline:   #c4c8d4;
  --md-primary:   #1a6fe8;
  --md-on-sv:     #43475a;
  --md-on-surf:   #191c24;
  --elev-1: 0 1px 2px rgba(0,0,0,0.08), 0 1px 3px 1px rgba(0,0,0,0.06);
  --elev-3: 0 4px 8px 3px rgba(0,0,0,0.08), 0 1px 3px rgba(0,0,0,0.10);
  --radius-card: 16px;
  --radius-pill: 999px;
  --radius-sm:   8px;
}
body {
  font-family: 'Google Sans', 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background: var(--md-bg);
  color: var(--md-on-surf);
  min-height: 100vh;
}
/* Top App Bar */
.site-header {
  background: #0d47a1;
  color: #e8eeff;
  padding: 2.2rem 1.5rem 1.8rem;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.20);
}
.site-header h1 {
  font-size: 1.75rem;
  font-weight: 500;
  letter-spacing: 0;
  color: #fff;
}
.site-header p { margin-top: 0.45rem; opacity: 0.55; font-size: 0.85rem; }
.container {
  max-width: 900px;
  margin: 2rem auto;
  padding: 0 1.5rem;
}
.year-group { margin-bottom: 2.25rem; }
/* MD3 section label */
.year-heading {
  font-size: 0.78rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1.2px;
  color: var(--md-primary);
  margin-bottom: 0.85rem;
  padding: 0.4rem 0.75rem;
  background: var(--md-surface);
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--md-primary);
  box-shadow: var(--elev-1);
}
.entry-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
  gap: 0.75rem;
}
/* MD3 Elevated Card */
.entry-card {
  background: var(--md-surface);
  border-radius: var(--radius-card);
  box-shadow: var(--elev-1);
  padding: 1rem 1.1rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  transition: box-shadow 0.22s, transform 0.22s;
}
.entry-card:hover {
  box-shadow: var(--elev-3);
  transform: translateY(-2px);
}
.entry-date {
  font-size: 0.97rem;
  font-weight: 600;
  color: var(--md-on-surf);
  letter-spacing: 0.1px;
}
.entry-weekday {
  font-size: 0.74rem;
  color: var(--md-on-sv);
  letter-spacing: 0.2px;
}
.entry-links { display: flex; gap: 0.4rem; flex-wrap: wrap; margin-top: 0.2rem; }
/* MD3 Tonal Button */
.entry-link {
  display: inline-block;
  padding: 0.18rem 0.65rem;
  border-radius: var(--radius-pill);
  font-size: 0.72rem;
  font-weight: 500;
  text-decoration: none;
  letter-spacing: 0.25px;
  transition: filter 0.15s, box-shadow 0.15s;
  box-shadow: 0 1px 2px rgba(0,0,0,0.08);
}
.entry-link:hover { filter: brightness(0.90); box-shadow: 0 2px 4px rgba(0,0,0,0.14); }
.link-html { color: #1344a0; background: #e3eeff; }
.link-md   { color: #3a3f52; background: var(--md-surface-v); }
.no-data   { text-align: center; padding: 4rem; color: var(--md-on-sv); }
.site-footer {
  text-align: center;
  padding: 1.5rem;
  color: var(--md-on-sv);
  font-size: 0.79rem;
  border-top: 1px solid var(--md-outline);
  margin-top: 2rem;
  background: var(--md-surface);
}
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
