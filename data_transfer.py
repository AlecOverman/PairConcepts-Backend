# This part goes in main.py pn;ly when free trail expires


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



# This part goes into elastic_api.py

    # def elastic_to_elastic():
    #     # Connect to the source cluster
    #     source_es = Elasticsearch(
    #         ["https://my-elasticsearch-project-bd33e8.es.us-east-1.aws.elastic.cloud:443"],  # Source Elasticsearch cluster URL
    #         api_key="cUlVeks1VUJmZ29FbGtfRFBZVmc6WDR6eUZfXzR2eGotQ0Fkd0tVNmN0UQ=="
    #     )

    #     # Connect to the destination cluster
    #     destination_es = Elasticsearch(
    #         ["https://my-elasticsearch-project-cdb29f.es.us-east-1.aws.elastic.cloud:443"],  # Destination Elasticsearch cluster URL
    #         api_key= "OU1OTEs1VUJVcEs4d3RkMEpXOFc6dHIzaWF6akliVEcxcnhMYTUxUl85QQ=="
    #     )

    #     # Get the documents from the source index using scrolling
    #     scroll_size = 1000
    #     query = {
    #         "query": {
    #             "match_all": {}  # You can modify this to filter specific documents
    #         }
    #     }

    #     # Start the scroll
    #     result = source_es.search(
    #         index="tokens",
    #         body=query,
    #         scroll='2m',  # Keep the scroll alive for 2 minutes
    #         size=scroll_size
    #     )

    #     # Scroll through the source index to fetch all documents
    #     scroll_id = result['_scroll_id']
    #     hits = result['hits']['hits']

    #     # Prepare bulk data for destination index
    #     actions = []
    #     while hits:
    #         for hit in hits:
    #             doc = hit['_source']
    #             action = {
    #                 "_op_type": "index",  # Use 'index' for upsert behavior (insert or replace)
    #                 "_index": "tokens",
    #                 "_source": doc
    #             }
    #             actions.append(action)

    #         # Fetch the next batch of results
    #         result = source_es.scroll(scroll_id=scroll_id, scroll='2m')
    #         scroll_id = result['_scroll_id']
    #         hits = result['hits']['hits']

    #     # Bulk index documents to the destination index
    #     if actions:
    #         helpers.bulk(destination_es, actions)

    #     return "Data transferred successfully!"