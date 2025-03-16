import os
from http.server import SimpleHTTPRequestHandler, HTTPServer
import urllib.parse
import json

from functions.arxiv import fetch_arxiv_papers
from functions.elastic_api import get_elastic
# from functions.elastic_api import elastic_to_elastic
# from random_functions.gemini_api import analyze_sentences_from_documents
from functions.elastic_api import turn_to_text
from functions.elastic_api import latex_to_text;
from functions.elastic_api import check_duplicate_ids;

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

        elif path == "/turn-to-text":
            # query = query_params.get("query", ["Blackholes"])[0]
            # max_results = int(query_params.get("max_results", [5])[0])

            papers = turn_to_text()
            response_body = json.dumps(papers, indent=2)

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(response_body.encode("utf-8"))
        # elif path == "/get_tokens":
        #     # Get query and max_results from the URL parameters

        #     # Call the get_elastic function with the parameters
        #     elastic_fetch =  get_tokens()
        #     print(elastic_fetch)  # Debugging line


        #     # Convert result to JSON string
        #     response_body = json.dumps(elastic_fetch, indent=2)

        #     self.send_response(200)
        #     self.send_header("Content-type", "application/json")
        #     self.end_headers(input_file, output_file, api_key, model_name="gemini-pro")
        #     self.wfile.write(response_body.encode("utf-8"))  # Send response

        # elif path == "/gemini":
        #     # Get query and max_results from the URL parameters
        #     api_key = "AIzaSyCDBXTa1xCwtjr2qCnCXwq1JeYXW_OBAMM" #Hardcoded API key here.

        #     # Replace with your actual file paths
        #     input_file = "articles_data_blackholes_updated.json" #Hardcoded input file path here.
        #     output_file = "analysis_results.json" #Hardcoded output file path here.

        #     # Call the get_elastic function with the parameters
        #     elastic_fetch = analyze_sentences_from_documents(input_file, output_file, api_key, model_name="gemini-2.0")
        #     print(elastic_fetch)  # Debugging line


        #     # Convert result to JSON string
        #     response_body = json.dumps(elastic_fetch, indent=2)

        #     self.send_response(200)
        #     self.send_header("Content-type", "application/json")
        #     self.end_headers()
        #     self.wfile.write(response_body.encode("utf-8"))  # Send response


        # elif path == "/elastic_to_elastic":
        #     # Get query and max_results from the URL parameters

        #     # Call the get_elastic function with the parameters
        #     elastic_fetch =  elastic_to_elastic()
        #     # print(elastic_fetch)  # Debugging line


        #     # Convert result to JSON string
        #     response_body = json.dumps(elastic_fetch, indent=2)

        #     self.send_response(200)
        #     self.send_header("Content-type", "application/json")
        #     self.end_headers()
        #     self.wfile.write(response_body.encode("utf-8"))  # Send response



        else:
            self.send_error(404, "Not Found")

PORT = 8080
server = HTTPServer(("0.0.0.0", PORT), MyHandler)
print(f"Server running on port {PORT}")
server.serve_forever()
