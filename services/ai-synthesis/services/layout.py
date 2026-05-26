"""
PDF Layout Engine — builds the print-ready magazine PDF using WeasyPrint.

Each job_type ("tourism" / "course") maps to a distinct Jinja2 HTML template
that WeasyPrint renders to a CMYK-ready PDF. The same engine handles both
formats — controlled entirely by the template, not by branching code.
"""
from pathlib import Path
import json

# WeasyPrint renders HTML+CSS to PDF with full print-quality support.
from weasyprint import HTML, CSS


# ── Theme Definitions ─────────────────────────────────────────────────────────
THEMES = {
    "tourism": {
        "primary_color": "#C27B4A",    # Terracotta
        "secondary_color": "#E8D5B7",  # Warm Sand
        "font_family": "Georgia, serif",
        "accent": "#8B4513",
    },
    "course": {
        "primary_color": "#3B5A7A",    # Slate Blue
        "secondary_color": "#EEF2F7",  # Cool White
        "font_family": "'Helvetica Neue', sans-serif",
        "accent": "#1A3A5C",
    },
}


def _build_html(layout: dict, job_type: str, image_map: dict[str, str]) -> str:
    """
    Generates the full HTML document for the magazine from the structured layout.
    image_map: { section_heading → local image file path }
    """
    theme = THEMES.get(job_type, THEMES["tourism"])
    sections_html = ""

    for section in layout.get("sections", []):
        heading = section.get("heading", "")
        body = section.get("body", "")
        img_path = image_map.get(heading, "")
        img_html = f'<img src="{img_path}" class="section-image" alt="{heading}" />' if img_path else ""

        key_point = section.get("key_point", "")
        kp_html = f'<blockquote class="key-point">{key_point}</blockquote>' if key_point else ""

        sections_html += f"""
        <section class="article-section">
            <h2>{heading}</h2>
            {img_html}
            <p>{body}</p>
            {kp_html}
        </section>
        """

    title = layout.get("title", "")
    subtitle = layout.get("subtitle", "")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<style>
  @page {{
    size: A4;
    margin: 2cm 2.5cm;
    @bottom-center {{ content: counter(page); font-size: 10pt; color: #999; }}
  }}
  body {{
    font-family: {theme['font_family']};
    color: #1a1a1a;
    line-height: 1.7;
    font-size: 11pt;
  }}
  .cover {{
    background: {theme['primary_color']};
    color: white;
    padding: 3cm 2cm;
    text-align: center;
    page-break-after: always;
  }}
  .cover h1 {{ font-size: 32pt; margin-bottom: 0.5em; letter-spacing: 2px; }}
  .cover p  {{ font-size: 14pt; opacity: 0.85; }}
  .article-section {{ margin-bottom: 2em; page-break-inside: avoid; }}
  .article-section h2 {{
    font-size: 16pt;
    color: {theme['primary_color']};
    border-bottom: 2px solid {theme['secondary_color']};
    padding-bottom: 4px;
    margin-bottom: 0.5em;
  }}
  .section-image {{
    width: 100%;
    max-height: 12cm;
    object-fit: cover;
    border-radius: 4px;
    margin: 0.8em 0;
  }}
  .key-point {{
    border-left: 4px solid {theme['accent']};
    background: {theme['secondary_color']};
    padding: 0.6em 1em;
    font-style: italic;
    margin: 1em 0;
  }}
</style>
</head>
<body>
  <div class="cover">
    <h1>{title}</h1>
    <p>{subtitle}</p>
  </div>
  {sections_html}
</body>
</html>"""


def generate_pdf(layout: dict, job_type: str, image_map: dict, output_path: Path) -> Path:
    """
    Renders the magazine layout to a print-ready PDF.

    Args:
        layout:      Structured content dict from GPT-4o.
        job_type:    "tourism" or "course".
        image_map:   Maps section headings → local image paths.
        output_path: Destination .pdf file path.

    Returns:
        Path to the generated PDF file.
    """
    html_content = _build_html(layout, job_type, image_map)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html_content).write_pdf(str(output_path))
    return output_path
