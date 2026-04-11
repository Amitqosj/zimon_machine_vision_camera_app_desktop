"""
Convert docs/ZIMON_PROJECT_GUIDE.md to a print-friendly HTML file.
Usage (from repo root): python scripts/export_project_guide_html.py
Open docs/ZIMON_PROJECT_GUIDE.html in a browser → Print → Save as PDF.
"""

from __future__ import annotations

import html
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MD_PATH = ROOT / "docs" / "ZIMON_PROJECT_GUIDE.md"
OUT_PATH = ROOT / "docs" / "ZIMON_PROJECT_GUIDE.html"


def inline_md(s: str) -> str:
    """Minimal inline Markdown: **bold**, `code`. Escapes HTML."""
    if not s:
        return ""
    parts = s.split("**")
    chunks: list[str] = []
    for i, p in enumerate(parts):
        if i % 2 == 1:
            chunks.append(f"<strong>{html.escape(p)}</strong>")
        else:
            chunks.append(_inline_code(p))
    return "".join(chunks)


def _inline_code(s: str) -> str:
    parts = s.split("`")
    chunks: list[str] = []
    for i, p in enumerate(parts):
        if i % 2 == 1:
            chunks.append(f"<code>{html.escape(p)}</code>")
        else:
            chunks.append(html.escape(p))
    return "".join(chunks)


def md_to_html(md: str) -> str:
    lines = md.splitlines()
    out: list[str] = []
    i = 0
    in_code = False
    code_buf: list[str] = []

    def flush_code():
        nonlocal code_buf
        if not code_buf:
            return
        body = html.escape("\n".join(code_buf))
        out.append(f'<pre class="code"><code>{body}</code></pre>')
        code_buf = []

    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("```"):
            if in_code:
                flush_code()
                in_code = False
            else:
                in_code = True
            i += 1
            continue
        if in_code:
            code_buf.append(line)
            i += 1
            continue

        m = re.match(r"^(#{1,3})\s+(.*)$", line)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            tag = f"h{level}"
            out.append(f"<{tag}>{html.escape(text)}</{tag}>")
            i += 1
            continue

        if line.strip() == "---":
            out.append("<hr />")
            i += 1
            continue

        if re.match(r"^\|.+\|$", line.strip()) and "|" in line:
            rows = []
            while i < len(lines) and "|" in lines[i]:
                row_line = lines[i].strip()
                if re.match(r"^\|[\s\-:|]+\|$", row_line):
                    i += 1
                    continue
                cells = [c.strip() for c in row_line.split("|")[1:-1]]
                rows.append(cells)
                i += 1
            if rows:
                out.append("<table>")
                out.append(
                    "<thead><tr>"
                    + "".join(f"<th>{inline_md(c)}</th>" for c in rows[0])
                    + "</tr></thead>",
                )
                if len(rows) > 1:
                    out.append("<tbody>")
                    for r in rows[1:]:
                        out.append(
                            "<tr>"
                            + "".join(f"<td>{inline_md(c)}</td>" for c in r)
                            + "</tr>",
                        )
                    out.append("</tbody>")
                out.append("</table>")
            continue

        if line.strip().startswith("- "):
            items = []
            while i < len(lines) and lines[i].strip().startswith("- "):
                items.append(lines[i].strip()[2:])
                i += 1
            out.append("<ul>" + "".join(f"<li>{inline_md(x)}</li>" for x in items) + "</ul>")
            continue

        if line.strip() == "":
            i += 1
            continue

        para = [line]
        i += 1
        while i < len(lines) and lines[i].strip() != "" and not lines[i].startswith("#") and not lines[i].strip().startswith("- ") and not lines[i].strip().startswith("```"):
            if lines[i].strip().startswith("|"):
                break
            para.append(lines[i])
            i += 1
        text = " ".join(para)
        out.append(f"<p>{inline_md(text)}</p>")

    if in_code:
        flush_code()
    return "\n".join(out)


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>ZIMON — Project configuration &amp; operations guide</title>
  <style>
    body {{ font-family: Segoe UI, system-ui, sans-serif; line-height: 1.45; max-width: 48rem; margin: 2rem auto; padding: 0 1.25rem; color: #1a1a1a; }}
    h1 {{ font-size: 1.75rem; border-bottom: 1px solid #ccc; padding-bottom: 0.35rem; }}
    h2 {{ font-size: 1.35rem; margin-top: 1.75rem; }}
    h3 {{ font-size: 1.1rem; margin-top: 1.25rem; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 0.9rem; margin: 0.75rem 0; }}
    th, td {{ border: 1px solid #ccc; padding: 0.4rem 0.55rem; text-align: left; }}
    th {{ background: #f4f4f4; }}
    pre.code {{ background: #f6f8fa; border: 1px solid #e1e4e8; padding: 0.75rem 1rem; overflow-x: auto; font-size: 0.82rem; }}
    hr {{ border: none; border-top: 1px solid #ddd; margin: 1.5rem 0; }}
    ul {{ padding-left: 1.35rem; }}
    @media print {{
      body {{ margin: 0; max-width: none; }}
      h2 {{ page-break-after: avoid; }}
      table, pre {{ page-break-inside: avoid; }}
    }}
  </style>
</head>
<body>
{body}
</body>
</html>
"""


def main():
    md = MD_PATH.read_text(encoding="utf-8")
    body = md_to_html(md)
    OUT_PATH.write_text(PAGE.format(body=body), encoding="utf-8")
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
