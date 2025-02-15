import os
from http.server import SimpleHTTPRequestHandler, HTTPServer
import urllib.parse
import json
import requests
import feedparser
from elasticsearch import Elasticsearch

# ✅ Load Elasticsearch credentials from environment variables
ES_URL = os.getenv("ELASTICSEARCH_URL")  # Set this in Render
ES_API_KEY = os.getenv("ELASTICSEARCH_API_KEY")  # Set this in Render

# ✅ Initialize Elasticsearch client securely
es = Elasticsearch(ES_URL, api_key=ES_API_KEY)

index_name = "arxiv_sources"

# Ensure index exists before inserting documents
if not es.indices.exists(index=index_name):
    es.indices.create(index=index_name)

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

class MyHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        query_params = urllib.parse.parse_qs(parsed_path.query)

        if path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Hello from my raw Python backend!")

        elif path == "/fetch-papers":
            query = query_params.get("query", ["Blackholes"])[0]
            max_results = int(query_params.get("max_results", [5])[0])

            papers = fetch_arxiv_papers(query, max_results)
            response_body = json.dumps(papers, indent=2)

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(response_body.encode("utf-8"))

        else:
            self.send_error(404, "Not Found")

PORT = 8080
server = HTTPServer(("0.0.0.0", PORT), MyHandler)
print(f"Server running on port {PORT}")
server.serve_forever()
