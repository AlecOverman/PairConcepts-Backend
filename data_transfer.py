# This part goes in main.py pn;ly when free trail expires


        elif path == "/elastic_to_elastic":
            # Get query and max_results from the URL parameters

            # Call the get_elastic function with the parameters
            elastic_fetch =  elastic_to_elastic()
            # print(elastic_fetch)  # Debugging line


            # Convert result to JSON string
            response_body = json.dumps(elastic_fetch, indent=2)

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(response_body.encode("utf-8"))  # Send response



# This part goes into elastic_api.py
# def elastic_to_elastic():
#     # Connect to the source Elasticsearch cluster
#     source_es = Elasticsearch(
#         ["https://my-elasticsearch-project-cdb29f.es.us-east-1.aws.elastic.cloud:443"],  # Source cluster URL
#         api_key="Vm8yUGFwVUIxMW9zRlBnSDVtaU06S0x3VXhnYVJHajJ2cHMzcXdZYVlfQQ=="
#     )

#     # Connect to the destination Elasticsearch cluster
#     destination_es = Elasticsearch(
#         ["https://da507f8d778a45289ccac8d865cfa1ff.us-east-2.aws.elastic-cloud.com:443"],  # Destination cluster URL
#         api_key="OS1PTmFwVUJESFRfaUVHMDlJdjY6VURfRk1RTktRdHk2T0V1amo3RVhZZw=="
#     )

#     # Define scroll size and query to fetch documents
#     scroll_size = 1000
#     query = {
#         "query": {
#             "match_all": {}  # Modify to filter specific documents if necessary
#         }
#     }

#     # Start the scroll to fetch documents from the source index
#     result = source_es.search(
#         index="arxiv_sources",  # Source index name
#         body=query,
#         scroll='2m',  # Keep the scroll alive for 2 minutes
#         size=scroll_size
#     )

#     # Initialize scroll ID and fetch the initial batch of documents
#     scroll_id = result['_scroll_id']
#     hits = result['hits']['hits']

#     # Prepare actions for bulk insertion into the destination index
#     actions = []
#     while hits:
#         for hit in hits:
#             doc = hit['_source']
#             action = {
#                 "_op_type": "index",  # Use 'index' for upsert behavior (insert or replace)
#                 "_index": "arxiv_sources",  # Destination index name
#                 "_source": doc
#             }
#             actions.append(action)

#         # Fetch the next batch of results
#         result = source_es.scroll(scroll_id=scroll_id, scroll='2m')
#         scroll_id = result['_scroll_id']
#         hits = result['hits']['hits']

#     # Bulk index documents into the destination index
#     if actions:
#         helpers.bulk(destination_es, actions)

#     return "Data transferred successfully!"

# This will help transform the latex source into text form
# def latex_to_text():

#     # Fetch documents
#     res = es.search(index=index_name, body={"query": {"match_all": {}}}, size=1000)  # Fetch up to 1000 documents
#     docs = res["hits"]["hits"]

#     actions = []
#     for doc in docs:
#         try:
#             if "_source" in doc and "latex_source" in doc["_source"]:
#                 # Convert LaTeX to plain text
#                 plain_text = LatexNodes2Text().latex_to_text(doc["_source"]["latex_source"])
                
#                 # Prepare bulk update action
#                 actions.append({
#                     "_op_type": "update",
#                     "_index": index_name,
#                     "_id": doc["_id"],
#                     "doc": {"latex_source": plain_text}
#                 })
#         except Exception as e:
#             print(f"Error processing document {doc['_id']}: {e}")

#     # Perform bulk update
#     if actions:
#         success, failed = helpers.bulk(es, actions)
#         print(f"Successfully updated {success} documents. Failed: {failed}")

# This is the api call to turn to text from main
        # elif path == "/turn_to_text":
        #     # Get query and max_results from the URL parameters

        #     # Call the get_elastic function with the parameters
        #     elastic_fetch =  turn_to_text()
        #     # print(elastic_fetch)  # Debugging line


        #     # Convert result to JSON string
        #     response_body = json.dumps(elastic_fetch, indent=2)

        #     self.send_response(200)
        #     self.send_header("Content-type", "application/json")
        #     self.end_headers()
        #     self.wfile.write(response_body.encode("utf-8"))  # Send response












        # def turn_to_text(query="Blackholes", max_results=1):
#     # Load spaCy model
#     nlp = spacy.load("en_core_web_sm")

#     # Fetch and process papers from arXiv
#     papers = fetch_arxiv_papers(query=query, max_results=max_results, base_url="http://export.arxiv.org/api/query?")

#     if not papers:
#         print("No papers fetched or processed.")
#         return

#     print(f"Found {len(papers)} papers")

#     processed_tokens = {}
#     bulk_actions_papers = []  # List to hold the bulk actions for paper metadata
#     bulk_actions_tokens = []  # List to hold the bulk actions for token metadata

#     # Process each paper's LaTeX source
#     for paper in papers:
#         try:
#             # Check if the paper already exists in Elasticsearch
#             existing_paper = es.get(index=index_name, id=paper["id"], ignore=404)
#             if existing_paper.get("found"):
#                 print(f"Paper {paper['id']} already exists in Elasticsearch. Skipping.")
#                 continue  # Skip if paper is already indexed

#             # Tokenize LaTeX source using spaCy
#             doc_spacy = nlp(paper["latex_source"])

#             # Tokenize using spaCy and process tokens
#             for token in doc_spacy:
#                 if not token.is_punct and token.text.strip():
#                     token_text = token.text.lower()

#                     # Initialize the token entry if not exists
#                     if token_text not in processed_tokens:
#                         processed_tokens[token_text] = []

#                     # Check if this document is already stored for this token
#                     found = False
#                     for entry in processed_tokens[token_text]:
#                         if entry["source"] == paper["id"]:
#                             entry["positions"].append(token.idx)
#                             found = True
#                             break

#                     # If this document is new for this token, add a new entry
#                     if not found:
#                         processed_tokens[token_text].append({
#                             "source": paper["id"],
#                             "positions": [token.idx]
#                         })

#             # Add the paper's metadata to bulk actions for indexing
#             bulk_actions_papers.append({
#                 "_op_type": "index",
#                 "_index": index_name,  # Replace with your actual papers index
#                 "_id": paper["id"],  # Using paper's ID as the document ID
#                 "_source": {
#                     "id": paper["id"],
#                     "title": paper["title"],
#                     "authors": paper["authors"],
#                     "summary": paper["summary"],
#                     "published": paper["published"],
#                     "category": paper["category"],
#                     "arxiv_url": paper["arxiv_url"],
#                     "source_url": paper["source_url"],
#                     "latex_source": paper["latex_source"],  # LaTeX source content
#                 }
#             })

#         except Exception as e:
#             print(f"Error processing paper {paper['id']}: {e}")

#     # Bulk insert tokens into Elasticsearch
#     if processed_tokens:
#         for token_text, sources in processed_tokens.items():
#             # Check if the token already exists in Elasticsearch
#             existing_token = es.get(index="your_token_index", id=token_text, ignore=404)

#             if existing_token.get("found"):
#                 # If the token exists, update it by appending new sources and positions
#                 bulk_actions_tokens.append({
#                     "_op_type": "update",  # Use update operation to append data
#                     "_index": token_index,
#                     "_id": token_text,
#                     "script": {
#                         "source": """
#                             if (ctx._source.sources == null) {
#                                 ctx._source.sources = params.sources;
#                             } else {
#                                 for (source in params.sources) {
#                                     // Check if the source already exists in the list
#                                     boolean found = false;
#                                     for (s in ctx._source.sources) {
#                                         if (s.source == source.source) {
#                                             s.positions.addAll(source.positions);
#                                             found = true;
#                                             break;
#                                         }
#                                     }
#                                     // If the source doesn't exist, add it
#                                     if (!found) {
#                                         ctx._source.sources.add(source);
#                                     }
#                                 }
#                             }
#                         """,
#                         "params": {
#                             "sources": sources
#                         }
#                     }
#                 })
#             else:
#                 # If the token does not exist, index it as a new document
#                 bulk_actions_tokens.append({
#                     "_op_type": "index",
#                     "_index": token_index,  # Replace with your actual token index
#                     "_id": token_text,  # Use token text as document ID to avoid duplicates
#                     "_source": {
#                         "token": token_text,
#                         "sources": sources  # List of papers containing this token with positions
#                     }
#                 })

#     # Bulk insert into Elasticsearch for tokens
#     if bulk_actions_tokens:
#         success, failed = bulk(es, bulk_actions_tokens)
#         print(f"Successfully indexed {success} token documents. Failed: {failed}")
        
#     # Bulk insert papers into Elasticsearch
#     if bulk_actions_papers:
#         success, failed = bulk(es, bulk_actions_papers)
#         print(f"Successfully indexed {success} paper documents. Failed: {failed}")

#     return "done!"













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