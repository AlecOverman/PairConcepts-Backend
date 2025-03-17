import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'functions'))
from http.server import SimpleHTTPRequestHandler, HTTPServer
import urllib.parse
import json

from functions.arxiv import fetch_arxiv_papers
from functions.elastic_api import get_elastic
from functions.elastic_api import turn_to_text
from functions.elastic_api import latex_to_text
from functions.elastic_api import check_duplicate_ids
from functions.gemini_api import user_input

class MyHandler(SimpleHTTPRequestHandler):
    def send_response(self, code, message=None):
        """Override send_response to suppress default headers"""
        # Call the parent method to handle the response code
        super().send_response(code, message)
        
        # Remove the 'Server' header
        if "Server" in self.headers:
            del self.headers["Server"]

        # Remove the 'Date' header
        if "Date" in self.headers:
            del self.headers["Date"]
    
    def do_GET(self):
        # Handle the preflight request for CORS
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        query_params = urllib.parse.parse_qs(parsed_path.query)
        print(f"Parsed query params: {query_params}")

        # if path == "/":
        #     self.send_response(200)
        #     self.send_header("Content-type", "text/plain")
        #     self.end_headers()
        #     self.wfile.write(b"Hello from my raw Python backend!")

        if path == "/":
            try:
                # Serve the desired JSON file (articles_data_blackholes_updated.json)
                with open("articles_data_blackholes_updated.json", "r", encoding="utf-8") as file:
                    data = json.load(file)
                
                response_body = json.dumps(data, indent=2)  # Convert to JSON string
                
                
                self.wfile.write(response_body.encode("utf-8"))  # Send JSON response
            
            except FileNotFoundError:
                self.send_error(404, "JSON file not found")  # Handle missing file error
            
            except json.JSONDecodeError:
                self.send_error(500, "Error decoding JSON file")  # Handle JSON decoding error

        elif path == "/fetch-papers":
            query = query_params.get("query", ["Blackholes"])[0]
            max_results = int(query_params.get("max_results", [5])[0])

            papers = fetch_arxiv_papers("CS", 100)
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

        # elif path == "/elastic_search":
        #     # Get query and max_results from the URL parameters

        #     # Call the get_elastic function with the parameters
        #     elastic_fetch =  token_search()
        #     print(elastic_fetch)  # Debugging line


        #     # Convert result to JSON string
        #     response_body = json.dumps(elastic_fetch, indent=2)

        #     self.send_response(200)
        #     self.send_header("Content-type", "application/json")
        #     self.end_headers()
        #     self.wfile.write(response_body.encode("utf-8"))  # Send response

        elif path == "/latex_to_text":
            # query = query_params.get("query", ["Blackholes"])[0]
            # max_results = int(query_params.get("max_results", [5])[0])

            papers = latex_to_text()
            response_body = json.dumps(papers, indent=2)

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(response_body.encode("utf-8"))

        elif path == "/duplicate":
            # query = query_params.get("query", ["Blackholes"])[0]
            # max_results = int(query_params.get("max_results", [5])[0])

            papers = check_duplicate_ids()
            response_body = json.dumps(papers, indent=2)

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(response_body.encode("utf-8"))

        elif path == "/gemini":
            # Retrieve the input from the query parameters (for example, "?input=some_input")
            input = query_params.get("input", [None])[0]
            
            # If no input is provided, return an error
            if not input:
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing input parameter"}).encode("utf-8"))
                return

            # Call the user_input function to process the input
            papers = user_input(input)

            # Prepare the JSON response body
            response_body = json.dumps(papers, indent=2)

            # Send the response header

            # Send the response body (the JSON result)
            self.wfile.write(response_body.encode("utf-8"))


        elif path == "/turn-to-text":
            # query = query_params.get("query", ["Blackholes"])[0]
            # max_results = int(query_params.get("max_results", [5])[0])

            papers = turn_to_text()
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
