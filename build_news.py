
from datetime import date
from html import escape
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parent
ARTICLES_DIR = ROOT / "articles"
NEWS_FILE = ROOT / "news.html"
OUTPUT_DIR = ROOT / "news"

def parse_front_matter(text):
    """Read simple YAML front matter without requiring extra packages."""
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

def markdown_to_html(markdown):
    """Render basic paragraphs and headings safely."""
    blocks = re.split(r"\n\s*\n", markdown.strip())
    output = []

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        if block.startswith("#"):
            heading = len(block) - len(block.lstrip("#"))
            if 1 <= heading <= 6 and block[heading:heading + 1] == " ":
                content = escape(block[heading + 1:].strip())
                output.append(f"<h{heading}>{content}</h{heading}>")
                continue

        paragraphs = escape(block).split("\n")
        output.append("<p>" + "<br>\n".join(paragraphs) + "</p>")

    return "\n".join(output)

def main():
    if not NEWS_FILE.exists():
        raise FileNotFoundError("news.html was not found.")

    ARTICLES_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    articles = []

    for path in ARTICLES_DIR.glob("*.md"):
        metadata, body = parse_front_matter(path.read_text(encoding="utf-8"))

        title = metadata.get("title", "").strip()
        published = metadata.get("date", "").strip()
        cover = metadata.get("cover", "").strip()

        if not title or not published or not cover:
            raise ValueError(f"{path.name} needs title, date and cover fields.")

        try:
            date.fromisoformat(published[:10])
        except ValueError as error:
            raise ValueError(
                f"{path.name} has an invalid publication date: {published}"
            ) from error

        # Only permit local image paths from the website's assets directory.
        cover_path = cover.lstrip("/")
        if cover_path.startswith("assets/"):
            image_url = "/" + cover_path
        elif cover_path.startswith("news/"):
            image_url = "/assets/" + cover_path
        else:
            image_url = "/assets/news/" + Path(cover_path).name

        slug = slugify(path.stem)
        articles.append({
            "title": title,
            "date": published[:10],
            "cover": image_url,
            "body": body,
            "slug": slug,
        })

    articles.sort(key=lambda item: (item["date"], item["title"].lower()), reverse=True)

    for article in articles:
        page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape(article['title'])} | SG Taekwon-Do</title>
  <meta name="description" content="{escape(article['title'])}">
  <link rel="stylesheet" href="../styles.css">
  <style>
    .article-page {{ max-width: 900px; margin: 0 auto; padding: 60px 24px 90px; }}
    .article-page img {{ max-width: 100%; height: auto; border-radius: 12px; }}
    .article-page h1 {{ line-height: 1.2; }}
    .article-date {{ opacity: .75; margin-bottom: 24px; }}
    .article-body {{ line-height: 1.8; margin-top: 30px; }}
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
    <h1>{escape(article['title'])}</h1>
    <p class="article-date">{escape(article['date'])}</p>
    <img src="{escape(article['cover'], quote=True)}" alt="{escape(article['title'], quote=True)}">
    <div class="article-body">
      {markdown_to_html(article['body'])}
    </div>
  </main>

  <script src="../script.js"></script>
</body>
</html>
"""
        (OUTPUT_DIR / f"{article['slug']}.html").write_text(page, encoding="utf-8")

    # Keep the existing News page structure, replacing only the article grid
    # and empty-state message with the generated article tiles.
    news_html = NEWS_FILE.read_text(encoding="utf-8")
    grid_pattern = re.compile(
        r'<div class="article-grid" id="article-grid" hidden>\s*</div>',
        re.S
    )
    empty_pattern = re.compile(
        r'<div class="news-empty" id="news-empty">.*?</div>',
        re.S
    )

    if not grid_pattern.search(news_html) or not empty_pattern.search(news_html):
        raise ValueError(
            "Expected article-grid and news-empty sections were not found in news.html."
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
            + '\n</div>'
        )
        empty_html = ""
    else:
        grid_html = '<div class="article-grid" id="article-grid" hidden>\n</div>'
        empty_html = (
            '<div class="news-empty" id="news-empty">'
            '<h3>Our Latest News Is Coming Soon</h3>'
            '<p>Check back soon for club news, student achievements, '
            'events and updates from SG Taekwon-Do.</p>'
            '</div>'
        )

    news_html = grid_pattern.sub(grid_html, news_html, count=1)
    news_html = empty_pattern.sub(empty_html, news_html, count=1)
    NEWS_FILE.write_text(news_html, encoding="utf-8")

    print(f"Generated {len(articles)} article page(s).")

if __name__ == "__main__":
    main()
