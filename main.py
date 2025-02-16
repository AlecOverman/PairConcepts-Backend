import os
from http.server import SimpleHTTPRequestHandler, HTTPServer
import urllib.parse
import json

from functions.arxiv import fetch_arxiv_papers
from functions.elastic_api import get_elastic

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

        elif path == "/elastic_api":
            # Get query and max_results from the URL parameters
            query = query_params.get("query", ["Blackholes"])[0]
            max_results = int(query_params.get("max_results", [5])[0])

            # Call the get_elastic function with the parameters
            elastic_fetch = get_elastic(query, max_results)
            print(elastic_fetch)  # Debugging line

            # Convert result to JSON string
            response_body = json.dumps(elastic_fetch, indent=2)

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(response_body.encode("utf-8"))  # Send response


        else:
            self.send_error(404, "Not Found")

PORT = 8080
server = HTTPServer(("0.0.0.0", PORT), MyHandler)
print(f"Server running on port {PORT}")
server.serve_forever()
