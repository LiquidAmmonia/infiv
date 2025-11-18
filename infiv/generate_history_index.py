"""Generate history index page for all historical markdown files."""
import logging
import os
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


def main():
    """Generate index.md with links to all historical markdown files."""
    history_dir = Path("history")
    
    if not history_dir.exists():
        logger.warning("History directory does not exist")
        return
    
    # Get all markdown files in history directory
    md_files = sorted(history_dir.glob("*.md"), reverse=True)
    
    if not md_files:
        logger.warning("No markdown files found in history directory")
        return
    
    # Generate index content
    index_lines = [
        "# Historical Daily News Archive",
        "",
        f"Total reports: {len(md_files)}",
        "",
        "## Archive by Date",
        ""
    ]
    
    for md_file in md_files:
        # Extract date from filename (format: YYYY-MM-DD.md)
        filename = md_file.stem
        try:
            file_date = datetime.strptime(filename, "%Y-%m-%d")
            display_date = file_date.strftime("%Y-%m-%d (%A)")
        except ValueError:
            display_date = filename
        
        # Create relative link
        relative_path = f"history/{md_file.name}"
        index_lines.append(f"- [{display_date}]({relative_path})")
    
    # Write index file
    index_content = "\n".join(index_lines)
    with open("index.md", "w") as f:
        f.write(index_content)
    
    logger.info(f"Generated history index with {len(md_files)} entries")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()
