import os
from http.server import SimpleHTTPRequestHandler, HTTPServer
import urllib.parse
import json
from elasticsearch import Elasticsearch

from functions.arxiv import fetch_arxiv_papers

# ✅ Load Elasticsearch credentials from environment variables
ES_URL = os.getenv("http_elastic")  # Set this in Render
ES_API_KEY = os.getenv("key_elastic")  # Set this in Render

# ✅ Initialize Elasticsearch client securely
es = Elasticsearch(ES_URL, api_key=ES_API_KEY)

index_name = "arxiv_sources"

# Ensure index exists before inserting documents
if not es.indices.exists(index=index_name):
    es.indices.create(index=index_name)


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
