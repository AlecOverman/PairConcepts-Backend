import requests
import feedparser

def fetch_arxiv_papers(query="Blackholes", max_results=5):
    """Fetches papers from arXiv API with source links."""
    base_url = "http://export.arxiv.org/api/query?"
    search_query = f"search_query=all:{query}&max_results={max_results}"
    url = base_url + search_query

    response = requests.get(url)
    
    if response.status_code != 200:
        return {"error": f"Failed to fetch papers (Status {response.status_code})"}

    feed = feedparser.parse(response.text)
    papers = []

    for entry in feed.entries:
        paper_id = entry.id.split("/")[-1]
        paper = {
            "id": paper_id,
            "title": entry.title,
            "authors": ", ".join(author.name for author in entry.authors),
            "summary": entry.summary,
            "published": entry.published,
            "category": entry.tags[0]["term"] if entry.tags else "Unknown",
            "arxiv_url": entry.link,
            "source_url": f"https://arxiv.org/e-print/{paper_id}"
        }
        papers.append(paper)

    return papers
