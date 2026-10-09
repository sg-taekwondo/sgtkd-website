
from datetime import date
from html import escape
from pathlib import Path
import re
import subprocess

import markdown

ROOT = Path(__file__).resolve().parent
ARTICLES_DIR = ROOT / "articles"
NEWS_FILE = ROOT / "news.html"
OUTPUT_DIR = ROOT / "news"


def parse_front_matter(text):
    """Parse simple key-value YAML front matter."""
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n?(.*)\Z", text, re.S)
    if not match:
        raise ValueError("Article is missing YAML front matter.")

    metadata = {}

    for line in match.group(1).splitlines():
        if line and not line[0].isspace() and ":" in line:
            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip().strip('"').strip("'")

    return metadata, match.group(2).strip()


def slugify(value):
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "article"


def resolve_cover(cover):
    """Resolve a cover image to a site-relative path."""
    cover_path = cover.strip().lstrip("/")

    if cover_path.startswith("assets/"):
        relative = Path(cover_path)
    elif cover_path.startswith("news/"):
        relative = Path("assets") / cover_path
    else:
        relative = Path("assets/news") / Path(cover_path).name

    resolved = (ROOT / relative).resolve()

    if not resolved.is_relative_to((ROOT / "assets").resolve()):
        raise ValueError(f"Cover image path is not allowed: {cover}")

    if not resolved.is_file():
        raise FileNotFoundError(
            f"Cover image for article not found: {relative.as_posix()}"
        )

    return relative.as_posix()


def markdown_to_html(body):
    """Render article Markdown with common formatting and safe HTML output."""
    return markdown.markdown(
        body,
        extensions=["extra", "sane_lists", "smarty"],
        output_format="html5",
    )


def main():
    if not NEWS_FILE.exists():
        raise FileNotFoundError("news.html was not found.")

    grid_pattern = re.compile(
        r'<div class="article-grid" id="article-grid" hidden>\s*</div>',
        re.S,
    )
    empty_pattern = re.compile(
        r'<div class="news-empty" id="news-empty">.*?</div>',
        re.S,
    )

    original_news = NEWS_FILE.read_text(encoding="utf-8")

    if not grid_pattern.search(original_news):
        raise ValueError("Expected empty article-grid placeholder was not found.")

    if not empty_pattern.search(original_news):
        raise ValueError("Expected news-empty placeholder was not found.")

    ARTICLES_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    articles = []
    used_slugs = set()

    for path in ARTICLES_DIR.glob("*.md"):
        metadata, body = parse_front_matter(
            path.read_text(encoding="utf-8")
        )

        title = metadata.get("title", "").strip()
        published = metadata.get("date", "").strip()
        cover = metadata.get("cover", "").strip()

        if not title or not published or not cover:
            raise ValueError(
                f"{path.name} needs title, date and cover fields."
            )

        try:
            published_date = date.fromisoformat(published[:10])
        except ValueError as error:
            raise ValueError(
                f"{path.name} has an invalid publication date: {published}"
            ) from error

        image_url = resolve_cover(cover)
        slug = slugify(path.stem)

        if slug in used_slugs:
            raise ValueError(f"Duplicate article URL slug: {slug}")

        used_slugs.add(slug)

        articles.append({
            "title": title,
            "date": published_date.isoformat(),
            "cover": image_url,
            "body": body,
            "slug": slug,
        })

    articles.sort(
        key=lambda item: (item["date"], item["title"].lower()),
        reverse=True,
    )

    for article in articles:
        title_html = escape(article["title"])
        cover_html = escape(article["cover"], quote=True)
        date_html = escape(article["date"])
        body_html = markdown_to_html(article["body"])

        page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title_html} | SG Taekwon-Do</title>
  <meta name="description" content="{title_html}">
  <link rel="stylesheet" href="../styles.css">
  <style>
    .article-page {{ max-width: 900px; margin: 0 auto; padding: 60px 24px 90px; }}
    .article-cover-image {{ display: block; width: 100%; height: auto; border-radius: 12px; }}
    .article-page h1 {{ line-height: 1.2; }}
    .article-date {{ opacity: .75; margin-bottom: 24px; }}
    .article-body {{ line-height: 1.8; margin-top: 30px; }}
    .article-body img {{ max-width: 100%; height: auto; }}
    .article-body a {{ text-decoration: underline; }}
    .article-back {{ display: inline-block; margin-top: 35px; }}
  </style>
</head>
<body>
  <header>
    <div class="container nav">
      <a class="brand" href="../index.html">
        <img src="../assets/sg-tkd-logo.png" alt="SG Taekwon-Do logo">
        <span>SG Taekwon-Do</span>
      </a>
      <button class="nav-toggle" aria-label="Open menu">☰</button>
      <ul class="nav-links">
        <li><a href="../index.html">Home</a></li>
        <li><a href="../about.html">About</a></li>
        <li><a href="../classes.html">Classes</a></li>
        <li><a href="../news.html">News</a></li>
        <li><a href="../partners.html">Partners</a></li>
        <li><a href="../contact.html">Contact Us</a></li>
      </ul>
    </div>
  </header>

  <main class="article-page">
    <a href="../news.html" class="article-back">← Back to News</a>
    <h1>{title_html}</h1>
    <p class="article-date">{date_html}</p>
    <img class="article-cover-image" src="../{cover_html}" alt="{title_html}">
    <div class="article-body">
      {body_html}
    </div>
  </main>

  <script src="../script.js"></script>
</body>
</html>
"""
        (OUTPUT_DIR / f"{article['slug']}.html").write_text(
            page, encoding="utf-8"
        )

    cards = []

    for article in articles:
        title = escape(article["title"], quote=True)
        cover = escape(article["cover"], quote=True)
        url = "news/" + article["slug"] + ".html"

        cards.append(
            f'<a class="article-card" href="{url}">'
            f'<img class="article-cover" src="{cover}" alt="" loading="lazy">'
            f'<h2 class="article-title">{title}</h2>'
            f'</a>'
        )

    if cards:
        grid_html = (
            '<div class="article-grid" id="article-grid">\n'
            + "\n".join(cards)
            + "\n</div>"
        )
        empty_html = ""
    else:
        grid_html = (
            '<div class="article-grid" id="article-grid" hidden>\n</div>'
        )
        empty_html = (
            '<div class="news-empty" id="news-empty">'
            '<h3>Our Latest News Is Coming Soon</h3>'
            '<p>Check back soon for club news, student achievements, '
            'events and updates from SG Taekwon-Do.</p>'
            '</div>'
        )

    updated_news = grid_pattern.sub(grid_html, original_news, count=1)
    updated_news = empty_pattern.sub(empty_html, updated_news, count=1)

    # Avoid modifying news.html unless the generated content has changed.
    if updated_news != original_news:
        NEWS_FILE.write_text(updated_news, encoding="utf-8")

    print(f"Generated {len(articles)} article page(s).")


if __name__ == "__main__":
    main()
