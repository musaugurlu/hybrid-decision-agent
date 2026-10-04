"""
scripts/convert_report_to_pdf.py - Converts docs/experiment_report.md to high-fidelity PDF
using GitHub-styled HTML and Chrome headless. Guarantees all 13 columns fit without truncation.
"""

import os
import re
import subprocess
from pathlib import Path
import markdown

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
MD_FILE = DOCS_DIR / "experiment_report.md"
HTML_FILE = DOCS_DIR / "experiment_report.html"
PDF_FILE = DOCS_DIR / "experiment_report.pdf"


CSS_STYLE = """
<style>
  @page {
    size: A4 portrait;
    margin: 10mm 6mm 10mm 6mm;
    @bottom-right {
      content: counter(page);
    }
  }

  *, *::before, *::after {
    box-sizing: border-box;
  }

  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: #1f2328;
    background: #ffffff;
    line-height: 1.42;
    font-size: 9.5pt;
    margin: 0;
    padding: 0;
  }

  h1 {
    font-size: 16pt;
    font-weight: 700;
    color: #0969da;
    border-bottom: 2px solid #d0d7de;
    padding-bottom: 4px;
    margin-top: 0;
    margin-bottom: 8px;
  }

  h2 {
    font-size: 12pt;
    font-weight: 600;
    color: #1f2328;
    border-bottom: 1px solid #d8dee4;
    padding-bottom: 3px;
    margin-top: 14px;
    margin-bottom: 6px;
    page-break-after: avoid;
  }

  h3 {
    font-size: 10.5pt;
    font-weight: 600;
    color: #24292f;
    margin-top: 10px;
    margin-bottom: 4px;
    page-break-after: avoid;
  }

  p, ul, ol {
    margin-top: 0;
    margin-bottom: 6px;
  }

  li {
    margin-bottom: 2px;
  }

  hr {
    height: 1px;
    background-color: #d0d7de;
    border: none;
    margin: 10px 0;
  }

  /* Table base styling */
  table {
    border-collapse: collapse;
    width: 100% !important;
    max-width: 100% !important;
    table-layout: fixed !important;
    margin: 8px 0 12px 0;
    font-size: 6.8pt;
    page-break-inside: auto;
  }

  tr {
    page-break-inside: avoid;
    page-break-after: auto;
  }

  thead {
    display: table-header-group;
  }

  th, td {
    padding: 3.5px 2px !important;
    border: 1px solid #cbd5e1;
    vertical-align: middle;
    word-break: break-word;
    overflow-wrap: anywhere;
  }

  th {
    background-color: #f1f5f9;
    color: #0f172a;
    font-weight: 600;
    text-align: left;
    font-size: 6.6pt;
    line-height: 1.15;
  }

  tbody tr:nth-child(even) {
    background-color: #f8fafc;
  }

  /* Code & Badges inside table */
  code {
    font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
    font-size: 6.2pt;
    background-color: #eff1f3;
    padding: 1px 2px;
    border-radius: 2px;
    color: #0969da;
    word-break: break-all;
    white-space: normal;
  }

  pre {
    background-color: #f6f8fa;
    border-radius: 6px;
    padding: 8px 10px;
    overflow-x: auto;
    font-size: 7.5pt;
    line-height: 1.4;
    border: 1px solid #d0d7de;
    page-break-inside: avoid;
  }

  pre code {
    background-color: transparent;
    padding: 0;
    color: #24292f;
  }

  blockquote {
    border-left: 3px solid #0969da;
    color: #57606a;
    padding: 4px 10px;
    margin: 6px 0;
    background-color: #f6f8fa;
    border-radius: 0 4px 4px 0;
  }

  .mermaid {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 8px;
    margin: 8px 0;
    text-align: center;
    page-break-inside: avoid;
  }
</style>
"""


def convert_markdown_to_html(md_text: str) -> str:
    """Converts Markdown text to full HTML with responsive column widths and Mermaid."""
    html_body = markdown.markdown(
        md_text,
        extensions=[
            "tables",
            "fenced_code",
            "codehilite",
            "toc",
            "nl2br",
            "sane_lists",
        ],
    )

    # Inject explicit colgroup for the 13-column benchmark table
    # Columns: # (3%), Scenario (15%), Type (5.5%), Target Tool (10.5%), Laya Decision (11%),
    # LLM Decision (9.5%), Agreed (5.5%), Base Tokens (7%), Laya Tokens (6%), Saved Tokens (9%),
    # Base Latency (6%), Laya Latency (6%), Speedup (6%) = Total 100%
    col_widths = [
        "3%", "15%", "5.5%", "10.5%", "11%", "9.5%", "5.5%", "7%", "6%", "9%", "6%", "6%", "6%"
    ]
    cg = "<colgroup>" + "".join(f'<col style="width: {w};">' for w in col_widths) + "</colgroup>"

    # Match the benchmark table by its header starting with <th>#</th>
    html_body = re.sub(
        r"<table>(?=\s*<thead>\s*<tr>\s*<th>#</th>)",
        f"<table>{cg}",
        html_body,
    )

    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Laya Decision Model Experiment Report</title>
  {CSS_STYLE}
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>
    document.addEventListener("DOMContentLoaded", function() {{
      mermaid.initialize({{ startOnLoad: true, theme: 'neutral' }});
    }});
  </script>
</head>
<body>
  {html_body}
</body>
</html>
"""
    return full_html


def generate_pdf():
    if not MD_FILE.exists():
        raise FileNotFoundError(f"Markdown file not found: {MD_FILE}")

    print(f"[1/3] Reading Markdown from: {MD_FILE}")
    with open(MD_FILE, "r", encoding="utf-8") as f:
        md_content = f.read()

    # Preprocess mermaid fenced code blocks if any
    md_content_processed = md_content.replace("```mermaid", '<div class="mermaid">').replace("```\n\n---", "</div>\n\n---")

    print("[2/3] Rendering HTML with proportional column widths...")
    html_content = convert_markdown_to_html(md_content_processed)
    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"[3/3] Printing PDF via Google Chrome Headless to: {PDF_FILE}")
    chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

    cmd = [
        chrome_path,
        "--headless=new",
        "--disable-gpu",
        "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=2500",
        "--no-pdf-header-footer",
        f"--print-to-pdf={PDF_FILE}",
        str(HTML_FILE),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 and not PDF_FILE.exists():
        print(f"Chrome error: {result.stderr}")
        raise RuntimeError("Failed to generate PDF via Chrome")

    pdf_size_kb = PDF_FILE.stat().st_size / 1024.0
    print(f"✅ Success! PDF created: {PDF_FILE} ({pdf_size_kb:.1f} KB)")
    print(f"📄 Markdown preserved:   {MD_FILE}")


if __name__ == "__main__":
    generate_pdf()
